"""
Módulo de optimización de ubicaciones para minimizar baldas ocupadas
Usa algoritmo bin packing para consolidar productos del mismo tipo
"""

from models import Stock, CodigoFisico, Ubicacion, db
from config import Config
from collections import defaultdict
from datetime import datetime
import uuid


def calcular_reorganizacion_optima(session_id=None):
    """
    Calcula la reorganización óptima del stock actual para minimizar baldas ocupadas
    
    Returns:
        dict con:
        - lista_movimientos: lista de dicts con info de cada movimiento
        - baldas_antes: número de baldas ocupadas actualmente
        - baldas_despues: número de baldas que quedarían ocupadas
        - baldas_liberadas: número de baldas que se liberarían
        - eficiencia_porcentaje: mejora porcentual
        - session_id: ID de sesión para agrupar tareas
    """
    
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    # 1. Obtener stock actual agrupado por tipo
    stock_actual = Stock.query.join(CodigoFisico).filter(Stock.cantidad > 0).all()
    
    if not stock_actual:
        return {
            'lista_movimientos': [],
            'baldas_antes': 0,
            'baldas_despues': 0,
            'baldas_liberadas': 0,
            'eficiencia_porcentaje': 0,
            'session_id': session_id
        }
    
    # 2. Contar baldas ocupadas actualmente
    baldas_ocupadas = set()
    for stock_item in stock_actual:
        baldas_ocupadas.add((stock_item.ubicacion.estanteria, stock_item.ubicacion.balda))
    baldas_antes = len(baldas_ocupadas)
    
    # 3. Agrupar por tipo de código físico
    grupos = defaultdict(list)
    for stock_item in stock_actual:
        codigo = stock_item.codigo_fisico
        tipo_key = codigo.tipo
        grupos[tipo_key].append({
            'stock_item': stock_item,
            'codigo_fisico': codigo,
            'capacidad': codigo.capacidad_por_balda,
            'cantidad': stock_item.cantidad,
            'ubicacion': stock_item.ubicacion
        })
    
    # 4. Para cada grupo, calcular distribución óptima usando bin packing
    movimientos = []
    baldas_necesarias = 0
    orden = 0
    
    # Obtener todas las ubicaciones disponibles ordenadas
    todas_ubicaciones = Ubicacion.query.order_by(
        Ubicacion.estanteria, Ubicacion.balda, Ubicacion.posicion
    ).all()
    ubicaciones_disponibles = iter(todas_ubicaciones)
    
    for tipo_key, items in grupos.items():
        # Ordenar items por fecha (FIFO) para mantener orden
        items_ordenados = sorted(items, key=lambda x: x['stock_item'].fecha_entrada)
        
        if not items_ordenados:
            continue
            
        capacidad_balda = items_ordenados[0]['capacidad']
        
        # Calcular cuántas baldas necesitamos para este grupo
        total_cantidad = sum(item['cantidad'] for item in items_ordenados)
        baldas_grupo = (total_cantidad + capacidad_balda - 1) // capacidad_balda
        baldas_necesarias += baldas_grupo
        
        # Distribuir items en baldas óptimas
        balda_actual = None
        cantidad_en_balda = 0
        
        for item in items_ordenados:
            cantidad_restante = item['cantidad']
            ubicacion_origen = item['ubicacion'].formato_display
            
            while cantidad_restante > 0:
                if balda_actual is None or cantidad_en_balda >= capacidad_balda:
                    try:
                        nueva_ubicacion = next(ubicaciones_disponibles)
                        balda_actual = nueva_ubicacion.formato_display
                        cantidad_en_balda = 0
                    except StopIteration:
                        break
                
                espacio_disponible = capacidad_balda - cantidad_en_balda
                cantidad_a_mover = min(cantidad_restante, espacio_disponible)
                
                if balda_actual != ubicacion_origen:
                    movimientos.append({
                        'id_temp': orden,
                        'producto_codigo': item['codigo_fisico'].codigo,
                        'producto_denominacion': item['codigo_fisico'].descripcion or item['codigo_fisico'].tipo_display,
                        'ubicacion_actual': ubicacion_origen,
                        'ubicacion_nueva': balda_actual,
                        'cantidad': cantidad_a_mover,
                        'motivo': f"Consolidar {tipo_key}",
                        'session_id': session_id
                    })
                    orden += 1
                
                cantidad_en_balda += cantidad_a_mover
                cantidad_restante -= cantidad_a_mover
    
    # 5. Calcular métricas
    baldas_despues = baldas_necesarias
    baldas_liberadas = baldas_antes - baldas_despues
    eficiencia_porcentaje = (baldas_liberadas / baldas_antes * 100) if baldas_antes > 0 else 0
    
    return {
        'lista_movimientos': movimientos,
        'baldas_antes': baldas_antes,
        'baldas_despues': baldas_despues,
        'baldas_liberadas': baldas_liberadas,
        'eficiencia_porcentaje': round(eficiencia_porcentaje, 2),
        'session_id': session_id
    }


def buscar_ubicacion_optima(codigo_fisico, cantidad=1):
    """
    Busca la ubicación óptima para un código físico considerando:
    1. Agrupar productos del MISMO TIPO en la misma balda (evita fragmentación)
    2. Baldas vacías si no hay del mismo tipo
    3. Primera ubicación disponible como último recurso
    
    REGLAS DE POSICIONAMIENTO:
    - Panel grande: ocupa 3 posiciones (50%), solo puede ir en P1 o P4
    - Panel mediano: ocupa 2 posiciones (33.33%), solo puede ir en P1, P3, P5
    - Panel pequeño: ocupa 1 posición (16.67%), puede ir en cualquier P1-P6
    - Mazo: ocupa 1 posición (20%), puede ir en cualquier P1-P5
    
    Args:
        codigo_fisico: Objeto CodigoFisico
        cantidad: Cantidad a ubicar (siempre 1 en el flujo actual)
        
    Returns:
        Ubicacion object o None si no hay espacio
    """
    from models import Stock, CodigoFisico, Ubicacion
    from config import Config
    
    # Determinar posiciones posibles según el tipo
    if codigo_fisico.tipo == 'panel_grande':
        posiciones_validas = [1, 4]  # Solo P1 o P4
        posiciones_ocupadas_por_producto = 3  # Ocupa P1-P2-P3 o P4-P5-P6
    elif codigo_fisico.tipo == 'panel_mediano':
        posiciones_validas = [1, 3, 5]  # Solo P1, P3, P5
        posiciones_ocupadas_por_producto = 2  # Ocupa 2 posiciones consecutivas
    elif codigo_fisico.tipo == 'panel_pequeño':
        posiciones_validas = list(range(1, 7))  # P1-P6
        posiciones_ocupadas_por_producto = 1
    elif codigo_fisico.tipo == 'mazo':
        posiciones_validas = list(range(1, 6))  # P1-P5
        posiciones_ocupadas_por_producto = 1
    else:
        posiciones_validas = list(range(1, 7))
        posiciones_ocupadas_por_producto = 1
    
    # PRIORIDAD 1: Intentar ubicar junto a productos del MISMO TIPO en la misma balda
    baldas_mismo_tipo = db.session.query(
        Ubicacion.estanteria, Ubicacion.balda
    ).join(Stock).join(CodigoFisico).filter(
        CodigoFisico.tipo == codigo_fisico.tipo,
        Stock.cantidad > 0
    ).distinct().all()
    
    for est, bald in baldas_mismo_tipo:
        # Obtener todas las posiciones ocupadas en esta balda (considerando las posiciones que ocupa cada producto)
        posiciones_ocupadas = set()
        items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
            Ubicacion.estanteria == est,
            Ubicacion.balda == bald,
            Stock.cantidad > 0
        ).all()
        
        for item in items:
            pos_inicio = item.ubicacion.posicion
            if item.codigo_fisico.tipo == 'panel_grande':
                # Ocupa 3 posiciones consecutivas
                posiciones_ocupadas.update([pos_inicio, pos_inicio + 1, pos_inicio + 2])
            elif item.codigo_fisico.tipo == 'panel_mediano':
                # Ocupa 2 posiciones consecutivas
                posiciones_ocupadas.update([pos_inicio, pos_inicio + 1])
            else:
                # Mazo o panel pequeño: ocupa 1 posición
                posiciones_ocupadas.add(pos_inicio)
        
        # Buscar la primera posición válida disponible
        for pos in posiciones_validas:
            # Verificar que esta posición y las siguientes (según el tipo) estén libres
            posiciones_necesarias = set(range(pos, pos + posiciones_ocupadas_por_producto))
            if not posiciones_necesarias.intersection(posiciones_ocupadas):
                # Posición disponible
                ubicacion = Ubicacion.query.filter(
                    Ubicacion.estanteria == est,
                    Ubicacion.balda == bald,
                    Ubicacion.posicion == pos
                ).first()
                
                if ubicacion:
                    return ubicacion
    
    # PRIORIDAD 2: Buscar baldas completamente vacías (dedicar balda al tipo)
    # Mazos van a estantería 4, paneles a estanterías 1-3
    if codigo_fisico.tipo == 'mazo':
        estanterias_preferidas = [4]
    else:
        estanterias_preferidas = [1, 2, 3]
    
    for est in estanterias_preferidas:
        for bald in range(1, Config.NUM_BALDAS + 1):
            items_count = Stock.query.join(Ubicacion).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == bald,
                Stock.cantidad > 0
            ).count()
            
            if items_count == 0:
                # Balda vacía, tomar primera posición válida
                ubicacion = Ubicacion.query.filter(
                    Ubicacion.estanteria == est,
                    Ubicacion.balda == bald,
                    Ubicacion.posicion == posiciones_validas[0]
                ).first()
                
                if ubicacion:
                    return ubicacion
    
    # PRIORIDAD 3: Buscar cualquier balda con espacio en cualquier estantería
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        for bald in range(1, Config.NUM_BALDAS + 1):
            # Obtener items de esta balda
            items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == bald,
                Stock.cantidad > 0
            ).all()
            
            # Si la balda tiene productos, verificar si son del mismo tipo
            if items:
                tipos_en_balda = set(item.codigo_fisico.tipo for item in items)
                # Si hay mezcla de tipos O el tipo no coincide, saltar esta balda
                if len(tipos_en_balda) > 1 or codigo_fisico.tipo not in tipos_en_balda:
                    continue
            
            # Obtener posiciones ocupadas
            posiciones_ocupadas = set()
            for item in items:
                pos_inicio = item.ubicacion.posicion
                if item.codigo_fisico.tipo == 'panel_grande':
                    posiciones_ocupadas.update([pos_inicio, pos_inicio + 1, pos_inicio + 2])
                elif item.codigo_fisico.tipo == 'panel_mediano':
                    posiciones_ocupadas.update([pos_inicio, pos_inicio + 1])
                else:
                    posiciones_ocupadas.add(pos_inicio)
            
            # Buscar primera posición válida disponible
            for pos in posiciones_validas:
                posiciones_necesarias = set(range(pos, pos + posiciones_ocupadas_por_producto))
                if not posiciones_necesarias.intersection(posiciones_ocupadas):
                    ubicacion = Ubicacion.query.filter(
                        Ubicacion.estanteria == est,
                        Ubicacion.balda == bald,
                        Ubicacion.posicion == pos
                    ).first()
                    
                    if ubicacion:
                        return ubicacion
    
    return None


def obtener_ocupacion_balda(estanteria, balda):
    """
    Retorna el número de posiciones ocupadas en una balda
    """
    ocupadas = Stock.query.join(Ubicacion).filter(
        Ubicacion.estanteria == estanteria,
        Ubicacion.balda == balda,
        Stock.cantidad > 0
    ).count()
    return ocupadas


def buscar_posicion_libre_en_balda(estanteria, balda):
    """
    Busca una posición libre en una balda específica
    """
    ubicacion_libre = Ubicacion.query.outerjoin(Stock).filter(
        Ubicacion.estanteria == estanteria,
        Ubicacion.balda == balda,
        Stock.id == None
    ).order_by(Ubicacion.posicion).first()
    
    return ubicacion_libre


def hay_espacio_disponible(codigo_fisico, cantidad=1):
    """
    Verifica si hay espacio disponible para un código físico
    
    Returns:
        bool: True si hay espacio, False si no
    """
    ubicacion = buscar_ubicacion_optima(codigo_fisico, cantidad)
    return ubicacion is not None
