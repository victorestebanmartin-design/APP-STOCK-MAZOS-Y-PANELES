# Sistema de Gestión de Stock - Mazos y Paneles

Aplicación web Flask para controlar el inventario de paneles y mazos en una nave industrial con 4 estanterías.

## Características

✅ **Dashboard Visual Interactivo**
- Vista grid de 4 estanterías con 4 baldas cada una
- Sistema dual de posiciones: 5 para mazos (20% c/u) y 6 para paneles (16.67% c/u)
- Códigos de colores por tipo de producto con emojis
- Animaciones y resaltado para localización rápida
- Badges de posición según ocupación (P1-P2, P1-P3, etc.)
- Visualización de proyecto limpia (sin prefijos CABINA, CAB, etc.)
- Impresión individual por estantería en A4 horizontal
- Métricas precisas: Baldas llenas (>90%), parciales (10-90%), libres (<10%)

✅ **Entrada de Material**
- Lectura de código de barras USB o entrada manual
- Asignación automática de ubicación óptima con posicionamiento correcto
- Agrupación inteligente por tipo para evitar fragmentación
- Modal de confirmación que espera tecla Enter para continuar
- Validación de espacio disponible antes de asignar
- Reglas de posicionamiento:
  * Panel grande: ocupa 3 posiciones (50%), solo P1 o P4
  * Panel mediano: ocupa 2 posiciones (33.33%), solo P1, P3 o P5
  * Panel pequeño: ocupa 1 posición (16.67%), cualquier P1-P6
  * Mazo: ocupa 1 posición (20%), cualquier P1-P5

✅ **Salida de Material (FIFO)**
- Sistema First-In-First-Out automático
- Indicación visual de ubicación exacta con resaltado
- Salida unitaria o total
- Confirmación de recogida
- Actualización automática de métricas

✅ **Control de Stock Consolidado** ⭐ NUEVO
- Vista de inventario completa en una sola pantalla
- Tarjetas de resumen por tipo (Mazos, Paneles Grandes/Medianos/Pequeños)
- Tabla detallada con:
  * Cantidad total por producto
  * Número de ubicaciones donde está almacenado
  * Detalle de ubicaciones con formato E#-B#-P#(cantidad)
  * Días en stock desde entrada más antigua
  * Nivel de stock (alto/medio/bajo) con código de colores
- Búsqueda en tiempo real por código, descripción o proyecto
- Filtros por tipo de producto
- Exportación a Excel con timestamp

✅ **Reubicación Manual**
- Click en producto para seleccionar origen
- Click en celda vacía para destino
- Panel flotante no intrusivo con información
- Validación de posiciones consecutivas para productos multi-posición
- Confirmación instantánea

✅ **Motor de Optimización**
- Algoritmo inteligente que respeta reglas de posicionamiento
- Prioriza agrupar productos del mismo tipo en misma balda
- Busca baldas vacías para dedicar por tipo
- Evita mezclar tipos diferentes en una balda
- Previene solapamientos de posiciones

✅ **Catálogo de Productos**
- CRUD completo de productos
- Configuración de tipos (panel grande/mediano/pequeño/mazo)
- Importación/exportación CSV
- Asociación con máquinas
- Estado activo/inactivo para control de entrada

✅ **Historial y Reportes**
- Registro completo de movimientos (entrada/salida/reubicación)
- Filtros avanzados por tipo, fecha, producto
- Exportación a Excel
- Métricas de ocupación precisas
- Información de antigüedad de stock

## Requisitos

- Python 3.8+
- Lector de código de barras USB (opcional)

## Instalación

### 1. Clonar o descargar el proyecto

```powershell
cd "C:\Users\estebanv\APP STOCK MAZOS Y PANELES"
```

### 2. Crear entorno virtual (recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Iniciar la aplicación

```powershell
python app.py
```

La aplicación se iniciará en: **http://localhost:5000**

## Primer Uso

### Inicialización Automática

Al ejecutar `app.py` por primera vez:

1. ✅ Se crea la base de datos SQLite (`stock.db`)
2. ✅ Se generan automáticamente 96 ubicaciones (4 estanterías × 4 baldas × 6 posiciones)
3. ✅ Se importa el catálogo inicial con ~90 productos

### Configurar Tipos de Productos

Después de la importación inicial, debe configurar los tipos de cada producto:

1. Ir a **Catálogo** en el menú
2. Para cada producto, hacer clic en **Editar** (icono lápiz)
3. Configurar:
   - **Tipo Panel**: Grande (2/balda) o Pequeño (6/balda)
   - **Es Mazo**: Marcar si es un mazo (5/balda)
   - **Código Máquina**: Código del producto que representa la máquina

## Configuración del Lector de Código de Barras

Los lectores USB que emulan teclado funcionan automáticamente:

1. Conectar el lector USB al PC
2. Hacer clic en el campo "Código de Producto"
3. Escanear el código de barras
4. El código se introduce automáticamente

## Estructura del Proyecto

```
APP STOCK MAZOS Y PANELES/
├── app.py                 # Aplicación principal y script de inicialización
├── routes.py              # Rutas y lógica de negocio
├── models.py              # Modelos de base de datos
├── config.py              # Configuración
├── requirements.txt       # Dependencias Python
├── stock.db              # Base de datos SQLite (se crea automáticamente)
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── entrada.html
│   ├── salida.html
│   ├── control_stock.html  # Vista consolidada de inventario
│   ├── catalogo.html
│   ├── historial.html
│   └── reportes.html
├── static/               # Archivos estáticos
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
└── utils/                # Utilidades
    └── optimizer.py      # Motor de optimización
```

## Flujo de Trabajo

### Entrada de Material

1. **Dashboard** → Botón "Entrada de Material" o menú "Entrada"
2. **Seleccionar producto** del catálogo visual con búsqueda y filtros
3. **Especificar cantidad** a ingresar
4. **Sistema calcula ubicación óptima** respetando:
   - Tipo de producto y posiciones válidas
   - Agrupación por tipo en misma balda
   - Espacios consecutivos para productos multi-posición
5. **Modal muestra ubicación asignada** (ej: E2-B3-P1)
6. **Operario coloca material** en la ubicación indicada
7. **Pulsar Enter** para continuar (o esperar timeout)
8. **Sistema registra entrada** y actualiza dashboard

### Salida de Material (FIFO)

1. **Dashboard** → Botón "Salida de Material" o menú "Salida"
2. **Buscar producto** por código (escáner o manual)
3. **Sistema localiza stock FIFO** (más antiguo primero)
4. **Muestra modal con:**
   - Ubicación exacta con resaltado
   - Cantidad disponible
   - Días en stock
   - Proyecto asociado
5. **Operario recoge material** de la ubicación indicada
6. **Seleccionar cantidad** a sacar (unitaria o total)
7. **Confirmar salida**
8. **Sistema actualiza** inventario y métricas

### Control de Stock

1. **Dashboard** → Botón "Control de Stock" o menú "Control Stock"
2. **Ver resumen consolidado**:
   - Total productos y unidades
   - Desglose por tipo (mazos, paneles grandes/medianos/pequeños)
3. **Usar filtros** para buscar productos específicos:
   - Búsqueda por código, descripción o proyecto
   - Filtro por tipo de producto
4. **Ver detalles** de cada producto:
   - Cantidad total en almacén
   - Ubicaciones específicas con cantidades
   - Antigüedad del stock
   - Nivel de stock (alto/medio/bajo)
5. **Exportar a Excel** para análisis externo

### Reubicación Manual

1. En el **Dashboard**, hacer clic en un producto para seleccionarlo
2. **Panel flotante** muestra información del producto seleccionado
3. Hacer clic en una **celda vacía** como destino
4. **Sistema valida** que hay espacio para el producto (verifica posiciones consecutivas)
5. Si es válido, **mueve el producto** automáticamente
6. **Dashboard se actualiza** mostrando nueva ubicación

### Impresión de Estanterías

1. En el **Dashboard**, hacer clic en el botón **"Imprimir"** de cualquier estantería
2. Se abre vista de impresión en **formato A4 horizontal**
3. Muestra estantería completa con:
   - Todas las baldas y posiciones
   - Productos con códigos y cantidades
   - Badges de tipo y posición
4. **Ctrl+P** para imprimir o guardar como PDF

## Capacidades y Reglas de Posicionamiento

### Sistema Dual de Posiciones

La aplicación utiliza dos sistemas de posicionamiento según el tipo:

| Tipo de Balda | Posiciones | % por Posición | Productos Permitidos |
|---------------|-----------|----------------|---------------------|
| **Mazos** (E4) | P1-P5 | 20% | Solo mazos |
| **Paneles** (E1-E3) | P1-P6 | 16.67% | Paneles grandes/medianos/pequeños |

### Ocupación por Tipo de Producto

| Tipo           | Posiciones Ocupadas | % de Balda | Posiciones Válidas | Unidades por Balda |
|----------------|-------------------|------------|-------------------|-------------------|
| **Panel Grande** | 3 consecutivas | 50% | Solo P1 o P4 | 2 |
| **Panel Mediano** | 2 consecutivas | 33.33% | Solo P1, P3 o P5 | 3 |
| **Panel Pequeño** | 1 posición | 16.67% | Cualquier P1-P6 | 6 |
| **Mazo** | 1 posición | 20% | Cualquier P1-P5 | 5 |

### Ejemplos de Posicionamiento Correcto

**Balda de Paneles (6 posiciones):**
- ✅ 2 Panel Grande: P1 (ocupa P1-P2-P3) + P4 (ocupa P4-P5-P6) = 100%
- ✅ 3 Panel Mediano: P1 (ocupa P1-P2) + P3 (ocupa P3-P4) + P5 (ocupa P5-P6) = 100%
- ✅ 6 Panel Pequeño: P1 + P2 + P3 + P4 + P5 + P6 = 100%
- ✅ Combinación: P1 Panel Grande (P1-P2-P3) + P4, P5, P6 Panel Pequeño = 100%

**Balda de Mazos (5 posiciones):**
- ✅ 5 Mazos: P1 + P2 + P3 + P4 + P5 = 100%
- ✅ 3 Mazos: P1 + P3 + P5 = 60%

### Reglas de Asignación Automática

1. **Prioridad 1**: Busca baldas del mismo tipo con espacio disponible
2. **Prioridad 2**: Busca baldas completamente vacías
3. **Prioridad 3**: Busca cualquier balda con espacio (sin mezclar tipos)
4. **Validación**: Verifica posiciones consecutivas libres según producto
5. **Rechazo**: Si no hay espacio válido, informa al usuario

## Base de Datos

### Modelos Principales

- **CodigoFisico**: Catálogo de productos con códigos, descripciones y tipo
- **Ubicacion**: 80 ubicaciones físicas (E1-B1-P1 a E4-B4-P6/P5)
  * Estanterías 1-3: 6 posiciones por balda (P1-P6) para paneles
  * Estantería 4: 5 posiciones por balda (P1-P5) para mazos
- **Stock**: Registros de inventario actual con cantidad y fecha de entrada
- **Movimiento**: Historial completo (entrada/salida/reubicación)
- **ProductoMaquina**: Máquinas asociadas a productos
- **TareaReorganizacion**: Tareas de reorganización pendientes (legacy)

### Backup

Para hacer backup de la base de datos:

```powershell
Copy-Item stock.db -Destination "stock_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

## Personalización

### Cambiar Número de Estanterías/Baldas/Posiciones

Editar `config.py`:

```python
NUM_ESTANTERIAS = 4      # Total de estanterías
NUM_BALDAS = 4           # Baldas por estantería
NUM_POSICIONES_PANELES = 6  # Posiciones para paneles (E1-E3)
NUM_POSICIONES_MAZOS = 5    # Posiciones para mazos (E4)
```

⚠️ **Importante**: 
- Después de cambiar, eliminar `stock.db` y reiniciar `app.py`
- El sistema recreará automáticamente las ubicaciones
- Se perderán los datos existentes (hacer backup primero)

### Cambiar Capacidades por Tipo

Editar `config.py`:

```python
CAPACIDAD_MAZO = 5              # Mazos por balda
CAPACIDAD_PANEL_GRANDE = 2      # Panel grandes por balda
CAPACIDAD_PANEL_MEDIANO = 3     # Panel medianos por balda
CAPACIDAD_PANEL_PEQUEÑO = 6     # Panel pequeños por balda
```

### Personalizar Reglas de Posicionamiento

Las reglas están implementadas en `utils/optimizer.py` función `buscar_ubicacion_optima()`:

```python
# Panel grande: solo P1 o P4
posiciones_validas = [1, 4]
posiciones_ocupadas_por_producto = 3

# Panel mediano: solo P1, P3, P5
posiciones_validas = [1, 3, 5]
posiciones_ocupadas_por_producto = 2
```

### Cambiar Criterios de Nivel de Stock

En `routes.py` función `control_stock()`:

```python
# Para mazos
nivel = 'alto' if cantidad >= 10 else 'medio' if cantidad >= 5 else 'bajo'

# Para paneles
nivel = 'alto' if cantidad >= 6 else 'medio' if cantidad >= 3 else 'bajo'
```

## Solución de Problemas

### La aplicación no inicia

```powershell
# Verificar que las dependencias están instaladas
pip install -r requirements.txt

# Verificar versión de Python
python --version  # Debe ser 3.8 o superior

# Limpiar archivos de caché
Remove-Item -Recurse -Force __pycache__
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Error en la base de datos

```powershell
# Hacer backup primero
Copy-Item stock.db -Destination "stock_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# Eliminar base de datos y recrear
Remove-Item stock.db
python app.py
```

### Error "Column expression expected" o errores de SQLAlchemy

```powershell
# Limpiar caché de Python y reiniciar
Remove-Item -Recurse -Force __pycache__
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
python app.py
```

### El lector de código de barras no funciona

1. Verificar que el cursor está en el campo de código
2. Probar escribir manualmente para descartar error de aplicación
3. Verificar configuración del lector (debe emular teclado)
4. Verificar que el lector añade Enter automáticamente al final

### Los productos no se muestran correctamente en el dashboard

1. Verificar que el producto tiene tipo asignado en Catálogo
2. Comprobar que la cantidad en Stock es mayor a 0
3. Revisar que la ubicación existe y es válida (E#-B#-P#)

### Las posiciones se solapan o no respetan las reglas

1. Ejecutar corrección manual de datos (contactar administrador)
2. Verificar en Control de Stock las ubicaciones exactas
3. Usar reubicación manual para corregir productos mal posicionados

### Los porcentajes de ocupación no son correctos

El sistema calcula ocupación basándose en:
- **Baldas llenas**: >90% de ocupación
- **Baldas parciales**: 10-90% de ocupación  
- **Baldas libres**: <10% de ocupación o vacías

Si los números parecen incorrectos, verificar en Control de Stock el detalle por producto.

## Navegación de la Aplicación

### Menú Principal

| Sección | Función | Acceso |
|---------|---------|--------|
| **Dashboard** | Vista principal de estanterías | Menú "Dashboard" |
| **Entrada** | Registrar entrada de material | Menú "Entrada" o botón en Dashboard |
| **Salida** | Procesar salida FIFO | Menú "Salida" o botón en Dashboard |
| **Control Stock** | Inventario consolidado | Menú "Control Stock" o botón en Dashboard |
| **Catálogo** | Gestión de productos | Menú "Catálogo" |
| **Historial** | Registro de movimientos | Menú "Historial" |
| **Reportes** | Estadísticas y métricas | Menú "Reportes" |

### Atajos de Teclado

| Tecla | Función |
|-------|---------|
| **Enter** | Confirmar operación en modales |
| **Esc** | Cerrar modales (en algunos casos) |
| **Ctrl+P** | Imprimir estantería (en vista de impresión) |

## Mejores Prácticas

### Para Operarios

1. **Entrada de Material**:
   - Verificar dos veces la ubicación asignada antes de colocar
   - Usar el escáner cuando esté disponible para evitar errores
   - Esperar a que aparezca el modal de confirmación
   - Pulsar Enter después de colocar el material

2. **Salida de Material**:
   - Seguir siempre el sistema FIFO (no sacar de otra ubicación)
   - Verificar visualmente el producto antes de confirmar salida
   - Actualizar el sistema inmediatamente después de recoger

3. **Reubicación**:
   - Consultar con supervisor antes de reubicar manualmente
   - Verificar que el destino tiene espacio suficiente
   - Actualizar el sistema inmediatamente

### Para Administradores

1. **Mantenimiento Regular**:
   - Hacer backup de `stock.db` semanalmente
   - Revisar Control de Stock mensualmente para detectar inconsistencias
   - Verificar métricas de ocupación para planificar expansiones

2. **Configuración de Productos**:
   - Asignar tipo correcto a cada producto (grande/mediano/pequeño/mazo)
   - Mantener descripciones claras y consistentes
   - Usar código de máquina para productos relacionados

3. **Auditoría**:
   - Comparar Control de Stock con inventario físico mensualmente
   - Revisar Historial para detectar patrones de uso
   - Exportar reportes para análisis externos

## Características Técnicas

### Tecnologías Utilizadas

- **Backend**: Flask 3.1.0 (Python 3.13)
- **Base de Datos**: SQLite con SQLAlchemy 2.0
- **Frontend**: Bootstrap 5.3 + Vanilla JavaScript
- **Exportación**: openpyxl 3.1.5 + pandas 2.2.3

### Requisitos del Sistema

- **Mínimo**: 
  - Windows 10/11
  - 4GB RAM
  - Python 3.8+
  - Navegador moderno (Chrome, Firefox, Edge)

- **Recomendado**:
  - Windows 11
  - 8GB RAM
  - Python 3.10+
  - Chrome o Edge (últimas versiones)
  - Pantalla 1920x1080 o superior

### Rendimiento

- Soporte para hasta **500 productos** simultáneos
- Respuesta instantánea para búsquedas y filtros
- Generación de reportes Excel en <3 segundos
- Base de datos optimizada con índices

## Seguridad y Backup

### Backup Automático (Recomendado)

Crear script de PowerShell para backup automático:

```powershell
# backup_stock.ps1
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"
$origen = "C:\Users\estebanv\APP STOCK MAZOS Y PANELES\stock.db"
$destino = "C:\Backups\Stock\stock_$fecha.db"

Copy-Item $origen -Destination $destino
Write-Host "Backup creado: $destino"

# Limpiar backups antiguos (mantener últimos 30 días)
Get-ChildItem "C:\Backups\Stock\" -Filter "stock_*.db" | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item
```

Programar con Programador de Tareas de Windows (diario a las 23:00).

### Restaurar Backup

```powershell
# Detener aplicación primero
# Luego:
Copy-Item "C:\Backups\Stock\stock_20251218_230000.db" -Destination "stock.db"
# Reiniciar aplicación
```

## Soporte

Para preguntas o problemas, contactar con el administrador del sistema.

### Registro de Cambios

**v2.0 - Diciembre 2025**
- ✅ Sistema dual de posiciones (5 mazos, 6 paneles)
- ✅ Control de Stock consolidado con exportación Excel
- ✅ Reubicación manual con validación de espacio
- ✅ Reglas de posicionamiento automático
- ✅ Mejoras visuales (badges, emojis, colores)
- ✅ Impresión A4 horizontal por estantería
- ✅ Modal de entrada con confirmación Enter
- ✅ Métricas precisas de ocupación
- ✅ Limpieza automática de descripciones de proyecto

**v1.0 - Noviembre 2025**
- ✅ Sistema básico de gestión de stock
- ✅ Dashboard con vista de estanterías
- ✅ Entrada y salida de material
- ✅ Catálogo de productos
- ✅ Historial de movimientos

---

**Versión**: 2.0  
**Última Actualización**: 18 de Diciembre 2025  
**Desarrollado para**: Gestión de Stock - Nave Industrial
