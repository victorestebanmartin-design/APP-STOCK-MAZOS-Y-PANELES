#!/bin/bash
# Script de instalación para Raspberry Pi
# Ejecutar con: bash instalar_raspberry.sh

echo "============================================"
echo "Instalando Stock Mazos y Paneles"
echo "en Raspberry Pi"
echo "============================================"
echo ""

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt-get update
sudo apt-get upgrade -y

# Instalar Python y pip si no están instalados
echo "🐍 Instalando Python3 y pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Crear entorno virtual
echo "📁 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para iniciar la aplicación ejecuta:"
echo "    bash iniciar_raspberry.sh"
echo ""
