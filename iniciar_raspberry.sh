#!/bin/bash
# Script de inicio para Raspberry Pi
# Ejecutar con: bash iniciar_raspberry.sh

echo "============================================"
echo "Iniciando Stock Mazos y Paneles"
echo "============================================"
echo ""

# Activar entorno virtual
source venv/bin/activate

# Obtener IP de la Raspberry
IP=$(hostname -I | awk '{print $1}')

echo "🚀 Iniciando servidor Flask..."
echo ""
echo "La aplicación estará disponible en:"
echo ""
echo "    http://$IP:8080"
echo "    http://localhost:8080"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Iniciar aplicación
python app.py
