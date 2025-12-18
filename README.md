# Sistema de Gestión de Stock - Mazos y Paneles

Aplicación web Flask para controlar el inventario de paneles y mazos en una nave industrial con 4 estanterías.

## Características

✅ **Dashboard Visual Interactivo**
- Vista grid de 4 estanterías con 4 baldas cada una
- 6 posiciones por balda
- Códigos de colores para estado de ocupación
- Animaciones de resaltado para localización

✅ **Entrada de Material**
- Lectura de código de barras USB o entrada manual
- Asignación automática de ubicación óptima
- Agrupación inteligente por tipo y máquina
- Validación de capacidad con sugerencias de reorganización

✅ **Salida de Material (FIFO)**
- Sistema First-In-First-Out automático
- Indicación visual de ubicación exacta
- Salida unitaria o total
- Confirmación de recogida

✅ **Motor de Optimización**
- Algoritmo bin packing para minimizar baldas ocupadas
- Reorganización inteligente del stock
- Checklist paso a paso para reorganizaciones
- Métricas de eficiencia

✅ **Catálogo de Productos**
- CRUD completo de productos
- Configuración de tipos (panel grande/pequeño/mazo)
- Importación/exportación CSV
- Asociación con máquinas

✅ **Historial y Reportes**
- Registro completo de movimientos
- Filtros avanzados
- Exportación a Excel
- Gráficos de ocupación
- Métricas de rotación y antigüedad

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

1. **Inicio** → Botón "Entrada de Material"
2. **Escanear/Escribir** código del producto
3. **Sistema verifica** espacio disponible:
   - ✅ **Si hay espacio**: Asigna ubicación óptima
   - ⚠️ **Si NO hay espacio**: Muestra opciones de reorganización
4. **Operario coloca** material en ubicación indicada
5. **Confirmar** entrada

### Salida de Material (FIFO)

1. **Inicio** → Botón "Salida de Material"
2. **Escanear/Escribir** código del producto
3. **Sistema busca** stock más antiguo (FIFO)
4. **Muestra ubicación exacta** con resaltado visual
5. **Operario recoge** material
6. **Seleccionar cantidad** (unitaria o total)
7. **Confirmar** salida

### Reorganización

1. **Opción A** - Entrada sin espacio:
   - Sistema sugiere reorganización
   - Muestra checklist paso a paso
   - Operario ejecuta movimientos
   - Confirma cada paso

2. **Opción B** - Optimización global:
   - Ir a **Reportes**
   - Ver métricas de eficiencia
   - Clic en "Generar Plan de Optimización"
   - Ejecutar reorganización

## Capacidades por Tipo

| Tipo           | Unidades por Balda |
|----------------|-------------------|
| Panel Grande   | 2                 |
| Panel Pequeño  | 6                 |
| Mazo          | 5                 |

## Base de Datos

### Modelos Principales

- **Producto**: Catálogo de productos con códigos y configuración
- **Ubicacion**: 96 ubicaciones físicas (E1-B1-P1 a E4-B4-P6)
- **Stock**: Registros de inventario actual
- **Movimiento**: Historial de todas las operaciones
- **TareaReorganizacion**: Tareas pendientes de reorganización

### Backup

Para hacer backup de la base de datos:

```powershell
Copy-Item stock.db -Destination "stock_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

## Personalización

### Cambiar Número de Estanterías/Baldas

Editar `config.py`:

```python
NUM_ESTANTERIAS = 4  # Cambiar aquí
NUM_BALDAS = 4       # Cambiar aquí
NUM_POSICIONES = 6   # Cambiar aquí
```

⚠️ **Importante**: Después de cambiar, eliminar `stock.db` y reiniciar `app.py`

### Cambiar Capacidades

Editar `config.py`:

```python
CAPACIDAD_MAZO = 5
CAPACIDAD_PANEL_GRANDE = 2
CAPACIDAD_PANEL_PEQUEÑO = 6
```

## Solución de Problemas

### La aplicación no inicia

```powershell
# Verificar que las dependencias están instaladas
pip install -r requirements.txt

# Verificar versión de Python
python --version  # Debe ser 3.8 o superior
```

### Error en la base de datos

```powershell
# Eliminar base de datos y recrear
Remove-Item stock.db
python app.py
```

### El lector de código de barras no funciona

1. Verificar que el cursor está en el campo de código
2. Probar escribir manualmente
3. Verificar configuración del lector (debe emular teclado)

## Soporte

Para preguntas o problemas, contactar con el administrador del sistema.

---

**Versión**: 1.0  
**Fecha**: Diciembre 2025  
**Desarrollado para**: Gestión de Stock - Nave Industrial
