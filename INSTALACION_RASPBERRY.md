# 🍓 Guía de Instalación en Raspberry Pi

## 📋 Requisitos previos
- Raspberry Pi con Raspberry Pi OS instalado
- Conexión a internet (para instalar dependencias)
- Acceso SSH o monitor/teclado conectado

## 🚀 Pasos de instalación

### 1. Transferir archivos a la Raspberry Pi

**Opción A: Usando USB**
1. Copia toda la carpeta del proyecto a una memoria USB
2. Conecta la USB a la Raspberry Pi
3. Copia los archivos a `/home/pi/stock-app/`

**Opción B: Usando SCP (desde Windows)**
```powershell
# Desde tu PC, en PowerShell
scp -r "C:\Users\estebanv\APP STOCK MAZOS Y PANELES" pi@IP_DE_TU_RASPBERRY:/home/pi/stock-app/
```

**Opción C: Usando FileZilla u otro cliente SFTP**
- Conecta por SFTP a la IP de tu Raspberry
- Usuario: pi
- Contraseña: la que configuraste
- Copia toda la carpeta

### 2. Conectarse a la Raspberry Pi

**Por SSH desde Windows:**
```powershell
ssh pi@IP_DE_TU_RASPBERRY
```

**O conecta monitor y teclado directamente**

### 3. Instalar la aplicación

```bash
cd /home/pi/stock-app
bash instalar_raspberry.sh
```

Esto instalará:
- Python 3 y pip
- Entorno virtual
- Todas las dependencias necesarias

### 4. Iniciar la aplicación

```bash
bash iniciar_raspberry.sh
```

El script mostrará la IP para acceder desde otros dispositivos.

### 5. Acceder desde tus PCs

Desde cualquier navegador en la red:
```
http://IP_DE_LA_RASPBERRY:8080
```

## 🔄 Inicio automático al encender (opcional)

Para que la app inicie automáticamente cuando enciendas la Raspberry:

1. Editar crontab:
```bash
crontab -e
```

2. Agregar al final:
```bash
@reboot sleep 30 && cd /home/pi/stock-app && bash iniciar_raspberry.sh
```

3. Guardar y salir (Ctrl+X, Y, Enter)

## 📡 Configurar IP estática (recomendado)

Para que la Raspberry siempre tenga la misma IP:

1. Editar configuración:
```bash
sudo nano /etc/dhcpcd.conf
```

2. Agregar al final (ajusta según tu red):
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

3. Reiniciar:
```bash
sudo reboot
```

## 🔍 Comandos útiles

**Ver la IP actual:**
```bash
hostname -I
```

**Detener la aplicación:**
```
Ctrl + C
```

**Ver logs si hay errores:**
```bash
cd /home/pi/stock-app
source venv/bin/activate
python app.py
```

## ✅ Ventajas de usar Raspberry Pi

- ✅ Servidor dedicado 24/7
- ✅ Bajo consumo eléctrico (~5W)
- ✅ Sin restricciones corporativas
- ✅ Todos pueden acceder simultáneamente
- ✅ Base de datos centralizada
- ✅ Puede estar físicamente en el almacén

## 🆘 Solución de problemas

**Si no se conecta desde otros PCs:**
- Verifica que todas las PCs estén en la misma red
- Haz ping a la Raspberry: `ping IP_RASPBERRY`
- Verifica que el puerto 8080 no esté bloqueado en el router

**Si falla la instalación:**
- Verifica conexión a internet en la Raspberry
- Ejecuta: `sudo apt-get update && sudo apt-get upgrade -y`

**Si la aplicación no inicia:**
- Verifica que el entorno virtual esté activo
- Revisa el archivo `requirements.txt` existe
- Ejecuta manualmente: `python app.py` para ver errores
