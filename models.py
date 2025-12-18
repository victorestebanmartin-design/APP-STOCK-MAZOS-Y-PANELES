from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Tabla de relación N:M entre CodigoFisico y ProductoMaquina
codigo_maquina_association = db.Table('codigo_maquina_rel',
    db.Column('codigo_fisico_id', db.Integer, db.ForeignKey('codigos_fisicos.id'), primary_key=True),
    db.Column('producto_maquina_id', db.Integer, db.ForeignKey('productos_maquina.id'), primary_key=True)
)


class ProductoMaquina(db.Model):
    """Tabla informativa de máquinas/productos finales"""
    __tablename__ = 'productos_maquina'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    denominacion = db.Column(db.String(200), nullable=False)
    
    # Relaciones con códigos físicos (puede tener varios paneles y mazos)
    codigos_fisicos = db.relationship('CodigoFisico', secondary=codigo_maquina_association, 
                                      back_populates='productos_maquina')
    
    def __repr__(self):
        return f'<ProductoMaquina {self.codigo} - {self.denominacion}>'


class CodigoFisico(db.Model):
    """Códigos físicos reales (paneles y mazos) que se escanean y almacenan"""
    __tablename__ = 'codigos_fisicos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'mazo', 'panel_grande', 'panel_mediano', 'panel_pequeño'
    descripcion = db.Column(db.String(200), nullable=True)  # Descripción opcional
    activo = db.Column(db.Boolean, default=True, nullable=False)  # Si está activo para entrada
    
    # Relaciones
    productos_maquina = db.relationship('ProductoMaquina', secondary=codigo_maquina_association, 
                                        back_populates='codigos_fisicos')
    stock_items = db.relationship('Stock', back_populates='codigo_fisico', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CodigoFisico {self.codigo} - {self.tipo}>'
    
    @property
    def capacidad_por_balda(self):
        """Retorna cuántas unidades caben en una balda según el tipo"""
        from config import Config
        if self.tipo == 'mazo':
            return Config.CAPACIDAD_MAZO
        elif self.tipo == 'panel_grande':
            return Config.CAPACIDAD_PANEL_GRANDE
        elif self.tipo == 'panel_mediano':
            return Config.CAPACIDAD_PANEL_MEDIANO
        elif self.tipo == 'panel_pequeño':
            return Config.CAPACIDAD_PANEL_PEQUEÑO
        return 1
    
    @property
    def tipo_display(self):
        """Retorna el tipo formateado para mostrar"""
        tipos_map = {
            'mazo': 'Mazo',
            'panel_grande': 'Panel Grande',
            'panel_mediano': 'Panel Mediano',
            'panel_pequeño': 'Panel Pequeño'
        }
        return tipos_map.get(self.tipo, self.tipo)
    
    @property
    def stock_total(self):
        """Retorna la cantidad total en stock"""
        return sum(item.cantidad for item in self.stock_items if item.cantidad > 0)
    
    @property
    def maquinas_info(self):
        """Retorna lista de máquinas a las que pertenece (info)"""
        return [f"{m.codigo} - {m.denominacion}" for m in self.productos_maquina]


class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    estanteria = db.Column(db.Integer, nullable=False)  # 1-4
    balda = db.Column(db.Integer, nullable=False)  # 1-4
    posicion = db.Column(db.Integer, nullable=False)  # 1-6
    
    # Relaciones
    stock_items = db.relationship('Stock', back_populates='ubicacion')
    
    __table_args__ = (
        db.UniqueConstraint('estanteria', 'balda', 'posicion', name='uix_ubicacion'),
    )
    
    def __repr__(self):
        return f'<Ubicacion {self.formato_display}>'
    
    @property
    def formato_display(self):
        """Retorna formato E{X}-B{Y}-P{Z}"""
        return f'E{self.estanteria}-B{self.balda}-P{self.posicion}'
    
    @staticmethod
    def from_formato(formato):
        """Parsea formato E1-B2-P3 y retorna dict con estanteria, balda, posicion"""
        try:
            partes = formato.split('-')
            return {
                'estanteria': int(partes[0].replace('E', '')),
                'balda': int(partes[1].replace('B', '')),
                'posicion': int(partes[2].replace('P', ''))
            }
        except:
            return None


class Stock(db.Model):
    __tablename__ = 'stock'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_fisico_id = db.Column(db.Integer, db.ForeignKey('codigos_fisicos.id'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    fecha_entrada = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    codigo_fisico = db.relationship('CodigoFisico', back_populates='stock_items')
    ubicacion = db.relationship('Ubicacion', back_populates='stock_items')
    
    def __repr__(self):
        return f'<Stock {self.codigo_fisico.codigo} en {self.ubicacion.formato_display} x{self.cantidad}>'
    
    @property
    def dias_almacenado(self):
        """Retorna días desde la entrada"""
        return (datetime.utcnow() - self.fecha_entrada).days


class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada', 'salida', 'reubicacion'
    producto_codigo = db.Column(db.String(50), nullable=False)
    ubicacion_origen = db.Column(db.String(20), nullable=True)  # Formato E1-B2-P3
    ubicacion_destino = db.Column(db.String(20), nullable=True)  # Formato E1-B2-P3
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    observaciones = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<Movimiento {self.tipo} {self.producto_codigo} - {self.timestamp}>'


class TareaReorganizacion(db.Model):
    """Tabla para guardar tareas de reorganización pendientes"""
    __tablename__ = 'tareas_reorganizacion'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_codigo = db.Column(db.String(50), nullable=False)
    ubicacion_origen = db.Column(db.String(20), nullable=False)
    ubicacion_destino = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=True)
    completada = db.Column(db.Boolean, default=False)
    orden = db.Column(db.Integer, nullable=False)  # Para mantener orden de ejecución
    session_id = db.Column(db.String(50), nullable=False)  # Para agrupar reorganizaciones
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tarea {self.producto_codigo} {self.ubicacion_origen} → {self.ubicacion_destino}>'
