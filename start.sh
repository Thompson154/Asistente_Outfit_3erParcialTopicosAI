#!/bin/bash

echo "🚀 Iniciando Outfit Assistant AI..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "Por favor crea un archivo .env con tu OPENAI_API_KEY"
    exit 1
fi

# Check if virtual environment is set up
if [ ! -d .venv ]; then
    echo "📦 Instalando dependencias..."
    uv sync
fi

echo "✅ Todo listo!"
echo ""
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "📱 Abre tu navegador y visita: http://localhost:8000"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

uv run fastapi dev api.py
