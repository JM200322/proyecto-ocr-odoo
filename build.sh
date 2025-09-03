#!/usr/bin/env bash
# build.sh

echo "🚀 Starting build process..."

# Instalar dependencias del backend
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements_render.txt

# Verificar si Node.js está disponible
if command -v node &> /dev/null; then
    echo "📦 Node.js found, building Vue frontend..."
    
    # Construir el frontend Vue
    cd ../frontend-vue
    npm install
    npm run build
    
    # Copiar el build al directorio static del backend
    echo "📁 Copying Vue build to backend/static..."
    cd ..
    rm -rf backend/static/*
    cp -r frontend-vue/dist/* backend/static/
else
    echo "⚠️ Node.js not found, skipping Vue build"
fi

echo "✅ Build complete!"