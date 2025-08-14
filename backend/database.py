#!/usr/bin/env python3
"""
Sistema de base de datos SQLite para historial de OCR
"""

import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = 'ocr_history.db'):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Obtener conexión thread-safe a la base de datos"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        else:
            self._local.connection.commit()
    
    def init_database(self):
        """Inicializar la base de datos con las tablas necesarias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla principal de jobs OCR
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ocr_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    image_hash TEXT UNIQUE,
                    image_size INTEGER,
                    image_dimensions TEXT,
                    extracted_text TEXT,
                    confidence REAL,
                    processing_time REAL,
                    ocr_engine TEXT,
                    ocr_provider TEXT,
                    preprocessing_params TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de records enviados a Odoo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS odoo_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ocr_job_id INTEGER,
                    odoo_instance TEXT,
                    odoo_model TEXT,
                    odoo_record_id INTEGER,
                    field_mapping TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ocr_job_id) REFERENCES ocr_jobs (id)
                )
            ''')
            
            # Tabla de estadísticas de rendimiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_jobs INTEGER,
                    successful_jobs INTEGER,
                    avg_confidence REAL,
                    avg_processing_time REAL,
                    total_processing_time REAL,
                    most_used_engine TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para optimizar consultas
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ocr_jobs_user_id ON ocr_jobs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ocr_jobs_session_id ON ocr_jobs(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ocr_jobs_image_hash ON ocr_jobs(image_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ocr_jobs_created_at ON ocr_jobs(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_odoo_records_job_id ON odoo_records(ocr_job_id)')
            
            logger.info("✅ Base de datos inicializada correctamente")
    
    def calculate_image_hash(self, image_data: bytes) -> str:
        """Calcular hash único de la imagen"""
        return hashlib.sha256(image_data).hexdigest()
    
    def create_ocr_job(self, **kwargs) -> int:
        """Crear un nuevo job de OCR en la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calcular hash de imagen si se proporciona
            if 'image_data' in kwargs:
                kwargs['image_hash'] = self.calculate_image_hash(kwargs['image_data'])
                kwargs['image_size'] = len(kwargs['image_data'])
                del kwargs['image_data']  # No guardar los bytes directamente
            
            # Convertir parámetros complejos a JSON
            if 'preprocessing_params' in kwargs and isinstance(kwargs['preprocessing_params'], dict):
                kwargs['preprocessing_params'] = json.dumps(kwargs['preprocessing_params'])
            
            if 'image_dimensions' in kwargs and isinstance(kwargs['image_dimensions'], (list, tuple)):
                kwargs['image_dimensions'] = json.dumps(kwargs['image_dimensions'])
            
            # Preparar la consulta dinámicamente
            columns = list(kwargs.keys())
            placeholders = ['?' for _ in columns]
            values = list(kwargs.values())
            
            query = f'''
                INSERT INTO ocr_jobs ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            '''
            
            cursor.execute(query, values)
            job_id = cursor.lastrowid
            
            logger.info(f"✅ OCR job creado con ID: {job_id}")
            return job_id
    
    def update_ocr_job(self, job_id: int, **kwargs) -> bool:
        """Actualizar un job de OCR existente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convertir parámetros complejos a JSON
            if 'preprocessing_params' in kwargs and isinstance(kwargs['preprocessing_params'], dict):
                kwargs['preprocessing_params'] = json.dumps(kwargs['preprocessing_params'])
            
            # Agregar timestamp de actualización
            kwargs['updated_at'] = datetime.now().isoformat()
            
            # Preparar la consulta dinámicamente
            set_clauses = [f"{column} = ?" for column in kwargs.keys()]
            values = list(kwargs.values()) + [job_id]
            
            query = f'''
                UPDATE ocr_jobs 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            '''
            
            cursor.execute(query, values)
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"✅ OCR job {job_id} actualizado")
            else:
                logger.warning(f"⚠️ OCR job {job_id} no encontrado para actualizar")
            
            return updated
    
    def get_ocr_job(self, job_id: int) -> Optional[Dict]:
        """Obtener un job de OCR por ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ocr_jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            
            if row:
                job = dict(row)
                # Convertir JSON strings de vuelta a objetos
                if job.get('preprocessing_params'):
                    try:
                        job['preprocessing_params'] = json.loads(job['preprocessing_params'])
                    except json.JSONDecodeError:
                        pass
                
                if job.get('image_dimensions'):
                    try:
                        job['image_dimensions'] = json.loads(job['image_dimensions'])
                    except json.JSONDecodeError:
                        pass
                
                return job
            return None
    
    def find_by_image_hash(self, image_hash: str) -> Optional[Dict]:
        """Buscar job por hash de imagen (para cache)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM ocr_jobs WHERE image_hash = ? AND success = 1 ORDER BY created_at DESC LIMIT 1',
                (image_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                job = dict(row)
                if job.get('preprocessing_params'):
                    try:
                        job['preprocessing_params'] = json.loads(job['preprocessing_params'])
                    except json.JSONDecodeError:
                        pass
                return job
            return None
    
    def create_odoo_record(self, ocr_job_id: int, **kwargs) -> int:
        """Crear registro de envío a Odoo"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            kwargs['ocr_job_id'] = ocr_job_id
            
            # Convertir field_mapping a JSON si es necesario
            if 'field_mapping' in kwargs and isinstance(kwargs['field_mapping'], dict):
                kwargs['field_mapping'] = json.dumps(kwargs['field_mapping'])
            
            columns = list(kwargs.keys())
            placeholders = ['?' for _ in columns]
            values = list(kwargs.values())
            
            query = f'''
                INSERT INTO odoo_records ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            '''
            
            cursor.execute(query, values)
            record_id = cursor.lastrowid
            
            logger.info(f"✅ Registro Odoo creado con ID: {record_id}")
            return record_id
    
    def get_user_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Obtener historial de un usuario"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT j.*, 
                       o.odoo_instance, o.odoo_model, o.odoo_record_id, o.success as odoo_success
                FROM ocr_jobs j
                LEFT JOIN odoo_records o ON j.id = o.ocr_job_id
                WHERE j.user_id = ?
                ORDER BY j.created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas básicas
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_jobs,
                    AVG(CASE WHEN success = 1 THEN confidence ELSE NULL END) as avg_confidence,
                    AVG(processing_time) as avg_processing_time,
                    SUM(processing_time) as total_processing_time
                FROM ocr_jobs 
                WHERE created_at >= datetime('now', '-{} days')
            '''.format(days))
            
            stats = dict(cursor.fetchone())
            
            # Engine más usado
            cursor.execute('''
                SELECT ocr_engine, COUNT(*) as count
                FROM ocr_jobs 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY ocr_engine
                ORDER BY count DESC
                LIMIT 1
            '''.format(days))
            
            engine_row = cursor.fetchone()
            stats['most_used_engine'] = engine_row['ocr_engine'] if engine_row else None
            
            # Estadísticas por día
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as jobs_count,
                    AVG(CASE WHEN success = 1 THEN confidence ELSE NULL END) as avg_confidence
                FROM ocr_jobs 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            '''.format(days))
            
            stats['daily_stats'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """Limpiar registros antiguos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar jobs antiguos
            cursor.execute('''
                DELETE FROM ocr_jobs 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days))
            
            deleted_count = cursor.rowcount
            logger.info(f"🧹 Eliminados {deleted_count} registros antiguos")
            
            return deleted_count
    
    def export_data(self, format: str = 'json', user_id: str = None) -> str:
        """Exportar datos en formato JSON o CSV"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT j.*, o.odoo_instance, o.odoo_model, o.odoo_record_id
                FROM ocr_jobs j
                LEFT JOIN odoo_records o ON j.id = o.ocr_job_id
            '''
            params = []
            
            if user_id:
                query += ' WHERE j.user_id = ?'
                params.append(user_id)
            
            query += ' ORDER BY j.created_at DESC'
            
            cursor.execute(query, params)
            data = [dict(row) for row in cursor.fetchall()]
            
            if format == 'json':
                return json.dumps(data, indent=2, default=str)
            elif format == 'csv':
                import csv
                import io
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                return output.getvalue()
            
            return str(data)

# Instancia global del administrador de base de datos
db_manager = DatabaseManager()