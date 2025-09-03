#!/bin/bash

# Instalar dependencias del backend
cd backend
pip install -r requirements.txt

# Compilar frontend Vue (si tienes Node.js en Render)
cd ../frontend-vue
npm install
npm run build

# Copiar el build al backend
cp -r dist/* ../backend/static/

cd ../backend