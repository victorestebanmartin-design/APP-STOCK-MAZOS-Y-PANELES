"""
Script de verificación del sistema
"""

def verificar_sistema():
    print("="*60)
    print("VERIFICACIÓN DEL SISTEMA - Stock Mazos y Paneles")
    print("="*60)
    print()
    
    # 1. Verificar Python
    import sys
    print(f"✓ Python version: {sys.version}")
    print()
    
    # 2. Verificar módulos
    modulos = [
        ('Flask', 'flask'),
        ('SQLAlchemy', 'flask_sqlalchemy'),
        ('Pandas', 'pandas'),
        ('OpenPyXL', 'openpyxl'),
        ('DateUtil', 'dateutil')
    ]
    
    print("Verificando módulos instalados:")
    for nombre, modulo in modulos:
        try:
            __import__(modulo)
            print(f"  ✓ {nombre}")
        except ImportError:
            print(f"  ✗ {nombre} - NO INSTALADO")
    print()
    
    # 3. Verificar archivos
    import os
    archivos_criticos = [
        'app.py',
        'routes.py',
        'models.py',
        'config.py',
        'requirements.txt',
        'templates/base.html',
        'templates/dashboard.html',
        'static/css/styles.css',
        'static/js/main.js',
        'utils/optimizer.py'
    ]
    
    print("Verificando archivos del proyecto:")
    todos_ok = True
    for archivo in archivos_criticos:
        if os.path.exists(archivo):
            print(f"  ✓ {archivo}")
        else:
            print(f"  ✗ {archivo} - NO ENCONTRADO")
            todos_ok = False
    print()
    
    # 4. Verificar base de datos
    if os.path.exists('stock.db'):
        print("✓ Base de datos encontrada: stock.db")
        
        # Intentar conectar
        try:
            from models import db, Producto, Ubicacion, Stock
            from routes import app
            
            with app.app_context():
                num_productos = Producto.query.count()
                num_ubicaciones = Ubicacion.query.count()
                num_stock = Stock.query.count()
                
                print(f"  - Productos en catálogo: {num_productos}")
                print(f"  - Ubicaciones creadas: {num_ubicaciones}")
                print(f"  - Registros de stock: {num_stock}")
        except Exception as e:
            print(f"  ⚠ Error al leer base de datos: {e}")
    else:
        print("⚠ Base de datos no encontrada (se creará al iniciar)")
    print()
    
    # 5. Resumen
    print("="*60)
    if todos_ok:
        print("✅ SISTEMA LISTO PARA USAR")
        print()
        print("Para iniciar la aplicación:")
        print("  1. Ejecutar: iniciar.bat")
        print("  2. Abrir navegador: http://localhost:5000")
    else:
        print("⚠ SISTEMA INCOMPLETO")
        print()
        print("Ejecutar instalar.bat para completar la instalación")
    print("="*60)


if __name__ == '__main__':
    try:
        verificar_sistema()
    except Exception as e:
        print(f"Error en verificación: {e}")
    
    input("\nPresione Enter para salir...")
