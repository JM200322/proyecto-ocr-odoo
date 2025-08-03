# backend/odoo_client.py
import xmlrpc.client
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OdooClient:
    def __init__(self, config_path='../config/credentials.json'):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado: {self.config_path}")
            return self.create_default_config()
        except json.JSONDecodeError:
            logger.error("Error al leer el archivo de configuración JSON")
            return self.create_default_config()
    
    def create_default_config(self):
        """Crear configuración por defecto"""
        default_config = {
            "odoo_instances": {
                "production": {
                    "url": "https://tu-odoo.com",
                    "database": "tu_bd",
                    "username": "admin@company.com",
                    "password": "contraseña_segura"
                },
                "staging": {
                    "url": "https://test-odoo.com",
                    "database": "test_bd",
                    "username": "test@company.com",
                    "password": "test_password"
                }
            },
            "default_mappings": {
                "contacts": {
                    "model": "res.partner",
                    "field": "comment"
                },
                "invoices": {
                    "model": "account.move",
                    "field": "narration"
                },
                "tasks": {
                    "model": "project.task",
                    "field": "description"
                }
            }
        }
        
        # Crear directorio si no existe
        os.makedirs('../config', exist_ok=True)
        
        # Guardar configuración por defecto
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Configuración por defecto creada en: {self.config_path}")
        return default_config
    
    def get_instance_config(self, instance_name='production'):
        """Obtener configuración de una instancia específica"""
        return self.config.get("odoo_instances", {}).get(instance_name)
    
    def authenticate(self, instance_name='production'):
        """Autenticar con Odoo"""
        config = self.get_instance_config(instance_name)
        if not config:
            logger.error(f"Configuración no encontrada para instancia: {instance_name}")
            return None
        
        try:
            common = xmlrpc.client.ServerProxy(f'{config["url"]}/xmlrpc/2/common')
            uid = common.authenticate(
                config["database"],
                config["username"],
                config["password"],
                {}
            )
            logger.info(f"Autenticación exitosa para instancia {instance_name}, UID: {uid}")
            return uid
        except Exception as e:
            logger.error(f"Error de autenticación en {instance_name}: {e}")
            return None
    
    def create_record(self, model, data, instance_name='production'):
        """Crear un registro en Odoo"""
        config = self.get_instance_config(instance_name)
        uid = self.authenticate(instance_name)
        
        if not uid or not config:
            return None
        
        try:
            models = xmlrpc.client.ServerProxy(f'{config["url"]}/xmlrpc/2/object')
            record_id = models.execute_kw(
                config["database"],
                uid,
                config["password"],
                model,
                'create',
                [data]
            )
            logger.info(f"Registro creado exitosamente: {record_id} en modelo {model}")
            return record_id
        except Exception as e:
            logger.error(f"Error creando registro en {model}: {e}")
            return None
    
    def get_mapping(self, mapping_type):
        """Obtener configuración de mapeo"""
        return self.config.get("default_mappings", {}).get(mapping_type)