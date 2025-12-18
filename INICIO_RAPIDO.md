# 🚀 GUÍA RÁPIDA DE INICIO

## Instalación en 3 Pasos

### 1️⃣ Ejecutar Instalador
```
Doble clic en: instalar.bat
```

Esto instalará automáticamente:
- ✅ Dependencias Python
- ✅ Base de datos SQLite
- ✅ 96 ubicaciones (4 estanterías × 4 baldas × 6 posiciones)
- ✅ Catálogo inicial con ~90 productos

### 2️⃣ Iniciar Aplicación
```
Doble clic en: iniciar.bat
```

La aplicación se abrirá en: **http://localhost:5000**

### 3️⃣ Configurar Productos (Primera Vez)

1. Ir a **Catálogo**
2. Para cada producto, hacer clic en 📝 Editar
3. Configurar:
   - **Tipo Panel**: Grande (2/balda) o Pequeño (6/balda)
   - **Es Mazo**: ☑️ si es un mazo (5/balda)
   - **Código Máquina**: Código del producto (máquina donde monta)

---

## Uso Diario

### 📥 ENTRADA DE MATERIAL

1. Clic en **"Entrada de Material"**
2. Escanear código de barras O escribir código
3. Confirmar cantidad
4. **Colocar en ubicación indicada** (ej: E2-B3-P1)
5. ✅ Listo

### 📤 SALIDA DE MATERIAL (FIFO)

1. Clic en **"Salida de Material"**
2. Escanear código de barras O escribir código
3. **IR A la ubicación indicada** (la más antigua)
4. Recoger material
5. Confirmar cantidad
6. ✅ Listo

---

## Funciones Principales

| Función | Descripción |
|---------|-------------|
| 🏠 **Dashboard** | Vista visual de las 4 estanterías |
| 📥 **Entrada** | Registrar entrada de material |
| 📤 **Salida** | Sacar material (FIFO automático) |
| 📋 **Catálogo** | Gestionar productos |
| 🕐 **Historial** | Ver todos los movimientos |
| 📊 **Reportes** | Métricas y optimización |

---

## Códigos de Colores

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Balda vacía |
| 🟡 Amarillo | Balda parcialmente ocupada |
| 🔴 Rojo | Balda llena |

---

## Lector de Código de Barras

### Configuración (USB que emula teclado):

1. Conectar lector USB al PC
2. En la app, hacer clic en campo "Código"
3. Escanear código
4. ✅ Se introduce automáticamente

**No requiere configuración adicional** - Funciona como teclado

---

## Reorganización de Stock

### Cuando no hay espacio:

1. Sistema detecta falta de espacio
2. Sugiere reorganización óptima
3. Muestra lista de movimientos paso a paso
4. Marcar ☑️ cada paso completado
5. Sistema actualiza ubicaciones

### Optimización global:

1. Ir a **Reportes**
2. Ver métricas de eficiencia
3. Clic en **"Generar Plan de Optimización"**
4. Ejecutar reorganización

---

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `Enter` | Confirmar código escaneado |
| `Tab` | Siguiente campo |
| `Esc` | Cerrar modal |

---

## Backup de Datos

### Manual:
1. Copiar archivo: `stock.db`
2. Guardar con fecha: `stock_backup_20251209.db`

### Restaurar:
1. Cerrar aplicación
2. Reemplazar `stock.db` con backup
3. Reiniciar aplicación

---

## Soporte Técnico

### La app no inicia:
```bat
1. Verificar Python instalado: python --version
2. Reinstalar: ejecutar instalar.bat nuevamente
```

### Error en base de datos:
```bat
1. Cerrar aplicación
2. Eliminar archivo: stock.db
3. Ejecutar: iniciar.bat
4. Sistema recreará base de datos
```

### Lector no funciona:
```bat
1. Probar escribiendo manualmente
2. Verificar cursor en campo de código
3. Verificar configuración lector (modo teclado)
```

---

## Pantallas Principales

### 1. Dashboard
```
┌─────────────────────────────────────┐
│  📥 ENTRADA    📤 SALIDA            │
├─────────────────────────────────────┤
│  Estantería 1 [▼]                  │
│  ├─ Balda 1: [🟢][🟢][🟡][🟢][🟢][🟢]│
│  ├─ Balda 2: [🟡][🟡][🔴][🟡][🟢][🟢]│
│  ├─ Balda 3: [🟢][🟢][🟢][🟢][🟢][🟢]│
│  └─ Balda 4: [🟢][🟢][🟢][🟢][🟢][🟢]│
└─────────────────────────────────────┘
```

### 2. Entrada
```
┌─────────────────────────────────────┐
│  Código: [____________]  [🔍]       │
│  Cantidad: [1]                      │
│  [✅ Registrar Entrada]             │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  📍 COLOCAR EN: E2-B3-P1           │
│  Producto: H0436602                 │
│  Cantidad: 2 unidades               │
└─────────────────────────────────────┘
```

### 3. Salida
```
┌─────────────────────────────────────┐
│  Código: [____________]  [🔍]       │
│  [🔍 Buscar y Sacar Material]       │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  📍 IR A: E1-B2-P4                 │
│  Código: H0436602                   │
│  Disponible: 3 unidades             │
│  Días almacenado: 15 días           │
│  Cantidad: [3] ▼                    │
│  [✅ Confirmar Recogida]            │
└─────────────────────────────────────┘
```

---

**¡Listo para usar! 🎉**

Para cualquier duda, consultar el README.md completo.
