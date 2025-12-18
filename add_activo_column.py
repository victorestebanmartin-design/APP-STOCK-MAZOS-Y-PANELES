import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

try:
    # Añadir columna activo
    cursor.execute('ALTER TABLE codigos_fisicos ADD COLUMN activo BOOLEAN DEFAULT 1 NOT NULL')
    conn.commit()
    print("✅ Columna 'activo' añadida correctamente")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("⚠️  La columna 'activo' ya existe")
    else:
        print(f"❌ Error: {e}")
finally:
    conn.close()
