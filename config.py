import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'stock.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de estanterías
    NUM_ESTANTERIAS = 4
    NUM_BALDAS = 4
    NUM_POSICIONES_PANELES = 6  # 6 huecos por balda para paneles (estanterías 1-3)
    NUM_POSICIONES_MAZOS = 5    # 5 huecos por balda para mazos (estantería 4)
    
    # Capacidades por tipo de producto (unidades por balda)
    # Mazos: balda de 5 huecos (estantería 4)
    CAPACIDAD_MAZO = 5  # 1 mazo = 1 hueco (20%)
    # Paneles: balda de 6 huecos (estanterías 1-3)
    CAPACIDAD_PANEL_GRANDE = 2  # 1 panel grande = 3 huecos (50%)
    CAPACIDAD_PANEL_MEDIANO = 3  # 1 panel mediano = 2 huecos (33.33%)
    CAPACIDAD_PANEL_PEQUEÑO = 6  # 1 panel pequeño = 1 hueco (16.67%)
