from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, ProductoMaquina, CodigoFisico, Ubicacion, Stock, Movimiento, TareaReorganizacion, codigo_maquina_association
from sqlalchemy import func
from config import Config
from utils.optimizer import (
    calcular_reorganizacion_optima, 
    buscar_ubicacion_optima, 
    hay_espacio_disponible
)
from datetime import datetime
from collections import defaultdict
import pandas as pd
from io import BytesIO
from flask import send_file

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Utilidad: extraer nombre de proyecto limpiando prefijos comunes
def extraer_proyecto(descripcion: str) -> str:
    if not descripcion:
        return ''
    texto = descripcion.strip().upper()
    stopwords = {
        'CABINA', 'CAB', 'SALA', 'HVAH', 'HVAC', 'HVAHU', 'SMART',
        'PANEL', 'PANELS', 'PANELES', 'MAZO', 'MAZOS', 'ARMARIO', 'CUADRO'
    }
    tokens = [t for t in texto.split() if t]
    # eliminar prefijos que sean stopwords
    while tokens and tokens[0] in stopwords:
        tokens.pop(0)
    # eliminar artículos iniciales comunes
    articulos = {'DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS'}
    while tokens and tokens[0] in articulos:
        tokens.pop(0)
    # si quedó vacío, devolver la original
    proyecto = ' '.join(tokens).strip()
    return proyecto if proyecto else texto


@app.route('/')
def index():
    """Dashboard principal con vista de estanterías"""
    # Obtener todas las ubicaciones con su stock
    ubicaciones_stock = {}
    stock_items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(Stock.cantidad > 0).all()
    
    for stock_item in stock_items:
        ubicacion_key = stock_item.ubicacion.formato_display
        codigo = stock_item.codigo_fisico
        ubicaciones_stock[ubicacion_key] = {
            'codigo': codigo.codigo,
            'denominacion': codigo.descripcion or codigo.tipo_display,
            'cantidad': stock_item.cantidad,
            'tipo_icono': '📦' if codigo.tipo == 'mazo' else '🔲',
            'tipo_clase': codigo.tipo.replace('_', '-'),
            'dias': stock_item.dias_almacenado
        }
    
    # Calcular ocupación de baldas y agrupar productos por balda
    baldas_ocupacion = {}
    baldas_productos = {}  # Nueva estructura: {E1-B1: [{producto1}, {producto2}, ...]}
    
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        for balda in range(1, Config.NUM_BALDAS + 1):
            key = f"E{est}-B{balda}"
            # Obtener todos los items en esta balda, ORDENADOS por posición
            items_balda = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == balda,
                Stock.cantidad > 0
            ).order_by(Ubicacion.posicion).all()
            
            # Crear un mapa de posiciones ocupadas (P1 a P6 o P5)
            # Cambio: usar lista en lugar de diccionario para permitir múltiples items por posición
            posiciones_ocupadas = {}  # {posicion: [items...]}
            huecos_ocupados = 0
            
            for item in items_balda:
                huecos_item = 0
                if item.codigo_fisico.tipo == 'mazo':
                    # Mazos: 1 mazo = 1 hueco, balda de 5 huecos (20%)
                    huecos_item = item.cantidad * 1
                elif item.codigo_fisico.tipo == 'panel_grande':
                    # Panel grande: 3 posiciones de 6 = 50%
                    huecos_item = item.cantidad * 3
                elif item.codigo_fisico.tipo == 'panel_mediano':
                    # Panel mediano: 2 posiciones de 6 = 33.33%
                    huecos_item = item.cantidad * 2
                elif item.codigo_fisico.tipo == 'panel_pequeño':
                    # Panel pequeño: 1 posición de 6 = 16.67%
                    huecos_item = item.cantidad * 1
                
                huecos_ocupados += huecos_item
                
                producto_data = {
                    'ubicacion': item.ubicacion.formato_display,
                    'codigo': item.codigo_fisico.codigo,
                    'descripcion': item.codigo_fisico.descripcion or item.codigo_fisico.tipo_display,
                    'descripcion_proyecto': extraer_proyecto(item.codigo_fisico.descripcion or ''),
                    'cantidad': item.cantidad,
                    'tipo': item.codigo_fisico.tipo,
                    'tipo_clase': item.codigo_fisico.tipo.replace('_', '-'),
                    'tipo_icono': (
                        '📦' if item.codigo_fisico.tipo == 'mazo'
                        else '🔲' if item.codigo_fisico.tipo == 'panel_grande'
                        else '◻️' if item.codigo_fisico.tipo == 'panel_mediano'
                        else '▫️'
                    ),
                    'huecos': huecos_item,
                    'porcentaje_balda': (huecos_item / (5 if item.codigo_fisico.tipo == 'mazo' else 6)) * 100,
                    'posicion': item.ubicacion.posicion
                }
                
                # Guardar en la lista de esta posición
                if item.ubicacion.posicion not in posiciones_ocupadas:
                    posiciones_ocupadas[item.ubicacion.posicion] = []
                posiciones_ocupadas[item.ubicacion.posicion].append(producto_data)
            
            # Construir lista ordenada con productos y espacios vacíos en sus posiciones
            productos_balda = []
            posiciones_procesadas = set()  # Posiciones ya procesadas
            
            # Determinar cuántas posiciones tiene esta balda (5 para mazos, 6 para paneles)
            es_balda_mazos = any(any(p.get('tipo') == 'mazo' for p in items) for items in posiciones_ocupadas.values())
            max_posiciones = 5 if es_balda_mazos else 6
            porcentaje_por_posicion = 20 if es_balda_mazos else 16.67
            
            for pos in range(1, max_posiciones + 1):
                if pos in posiciones_procesadas:
                    continue
                    
                if pos in posiciones_ocupadas:
                    # Hay uno o más productos en esta posición
                    for producto in posiciones_ocupadas[pos]:
                        productos_balda.append(producto)
                        posiciones_procesadas.add(pos)
                        
                        # Marcar las posiciones que ocupa visualmente este producto
                        if producto['tipo'] == 'panel_grande':
                            # Panel grande ocupa 3 posiciones: P# + P#+1 + P#+2
                            posiciones_procesadas.add(pos + 1)
                            posiciones_procesadas.add(pos + 2)
                        elif producto['tipo'] == 'panel_mediano':
                            # Panel mediano ocupa 2 posiciones: P# + P#+1
                            posiciones_procesadas.add(pos + 1)
                else:
                    # Posición vacía
                    productos_balda.append({
                        'vacio': True,
                        'posicion': pos,
                        'porcentaje_balda': porcentaje_por_posicion,
                        'estanteria': est,
                        'balda': balda,
                        'tipo_balda': 'mazos' if es_balda_mazos else 'paneles'
                    })
            
            # Porcentaje basado en 5 huecos (mazos) o 6 huecos (paneles)
            # Si hay mazos en la balda, usar 5 huecos como base
            total_huecos = 5 if any(any(p.get('tipo') == 'mazo' for p in items) for items in posiciones_ocupadas.values()) else 6
            baldas_ocupacion[key] = (huecos_ocupados / total_huecos) * 100
            baldas_productos[key] = productos_balda
    
    # Calcular métricas generales
    total_baldas = Config.NUM_ESTANTERIAS * Config.NUM_BALDAS
    
    # Contar baldas según su ocupación real
    baldas_ocupadas = 0  # Baldas con más del 90% de ocupación
    baldas_parcialmente_ocupadas = 0  # Baldas con 10-90% de ocupación
    baldas_libres = 0  # Baldas con menos del 10% de ocupación
    
    for key, ocupacion in baldas_ocupacion.items():
        if ocupacion >= 90:
            baldas_ocupadas += 1
        elif ocupacion > 10:
            baldas_parcialmente_ocupadas += 1
        else:
            baldas_libres += 1
    
    # Contar baldas vacías (sin ningún producto)
    baldas_con_stock = set((item.ubicacion.estanteria, item.ubicacion.balda) for item in stock_items)
    baldas_vacias = total_baldas - len(baldas_con_stock)
    baldas_libres += baldas_vacias  # Sumar las baldas completamente vacías
    
    # Ocupación general basada en baldas llenas vs total
    ocupacion_porcentaje = round((baldas_ocupadas / total_baldas) * 100, 1)
    
    # Info por estantería
    estanterias_info = {}
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        baldas_est = set()
        for stock_item in stock_items:
            if stock_item.ubicacion.estanteria == est:
                baldas_est.add(stock_item.ubicacion.balda)
        estanterias_info[est] = {
            'total': Config.NUM_BALDAS,
            'ocupadas': len(baldas_est)
        }
    
    # Verificar si hay que resaltar alguna ubicación (desde salida)
    resaltar = request.args.get('resaltar')
    
    return render_template('dashboard.html',
                         ubicaciones_stock=ubicaciones_stock,
                         baldas_ocupacion=baldas_ocupacion,
                         baldas_productos=baldas_productos,
                         total_baldas=total_baldas,
                         baldas_ocupadas=baldas_ocupadas,
                         baldas_parcialmente_ocupadas=baldas_parcialmente_ocupadas,
                         baldas_libres=baldas_libres,
                         ocupacion_porcentaje=ocupacion_porcentaje,
                         estanterias_info=estanterias_info,
                         resaltar_ubicacion=resaltar)


@app.route('/estanteria/<int:num>/imprimir')
def imprimir_estanteria(num):
    """Vista dedicada para imprimir una estantería en A4 horizontal"""
    # Reutilizar el cálculo del dashboard, pero filtrar por estantería
    stock_items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
        Stock.cantidad > 0,
        Ubicacion.estanteria == num
    ).all()
    
    # Ocupación y productos por balda de esta estantería
    baldas_ocupacion = {}
    baldas_productos = {}
    for balda in range(1, Config.NUM_BALDAS + 1):
        key = f"E{num}-B{balda}"
        items_balda = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
            Ubicacion.estanteria == num,
            Ubicacion.balda == balda,
            Stock.cantidad > 0
        ).order_by(Ubicacion.posicion).all()
        
        # Crear un mapa de posiciones ocupadas (P1 a P6 o P5)
        posiciones_ocupadas = {}  # {posicion: [items...]}
        huecos_ocupados = 0
        
        for item in items_balda:
            if item.codigo_fisico.tipo == 'mazo':
                huecos_item = item.cantidad * 1
            elif item.codigo_fisico.tipo == 'panel_grande':
                huecos_item = item.cantidad * 3
            elif item.codigo_fisico.tipo == 'panel_mediano':
                huecos_item = item.cantidad * 2
            else:
                huecos_item = item.cantidad * 1
            huecos_ocupados += huecos_item
            
            producto_data = {
                'ubicacion': item.ubicacion.formato_display,
                'codigo': item.codigo_fisico.codigo,
                'descripcion': item.codigo_fisico.descripcion or item.codigo_fisico.tipo_display,
                'descripcion_proyecto': extraer_proyecto(item.codigo_fisico.descripcion or ''),
                'cantidad': item.cantidad,
                'tipo': item.codigo_fisico.tipo,
                'tipo_clase': item.codigo_fisico.tipo.replace('_', '-'),
                'tipo_icono': (
                    '📦' if item.codigo_fisico.tipo == 'mazo'
                    else '🔲' if item.codigo_fisico.tipo == 'panel_grande'
                    else '◻️' if item.codigo_fisico.tipo == 'panel_mediano'
                    else '▫️'
                ),
                'huecos': huecos_item,
                'porcentaje_balda': (huecos_item / (5 if item.codigo_fisico.tipo == 'mazo' else 6)) * 100,
                'posicion': item.ubicacion.posicion
            }
            
            if item.ubicacion.posicion not in posiciones_ocupadas:
                posiciones_ocupadas[item.ubicacion.posicion] = []
            posiciones_ocupadas[item.ubicacion.posicion].append(producto_data)
        
        # Construir lista ordenada con productos y espacios vacíos
        productos_balda = []
        posiciones_procesadas = set()
        
        es_balda_mazos = any(any(p.get('tipo') == 'mazo' for p in items) for items in posiciones_ocupadas.values())
        max_posiciones = 5 if es_balda_mazos else 6
        porcentaje_por_posicion = 20 if es_balda_mazos else 16.67
        
        for pos in range(1, max_posiciones + 1):
            if pos in posiciones_procesadas:
                continue
                
            if pos in posiciones_ocupadas:
                for producto in posiciones_ocupadas[pos]:
                    productos_balda.append(producto)
                    posiciones_procesadas.add(pos)
                    
                    # Marcar las posiciones que ocupa visualmente
                    if producto['tipo'] == 'panel_grande':
                        posiciones_procesadas.add(pos + 1)
                        posiciones_procesadas.add(pos + 2)
                    elif producto['tipo'] == 'panel_mediano':
                        posiciones_procesadas.add(pos + 1)
            else:
                productos_balda.append({
                    'vacio': True,
                    'posicion': pos,
                    'porcentaje_balda': porcentaje_por_posicion,
                    'estanteria': num,
                    'balda': balda,
                    'tipo_balda': 'mazos' if es_balda_mazos else 'paneles'
                })
        
        total_huecos = 5 if es_balda_mazos else 6
        baldas_ocupacion[key] = (huecos_ocupados / total_huecos) * 100
        baldas_productos[key] = productos_balda
    
    # Métricas
    total_baldas = Config.NUM_BALDAS
    baldas_con_stock = set()
    for item in stock_items:
        baldas_con_stock.add(item.ubicacion.balda)
    baldas_ocupadas = len(baldas_con_stock)
    baldas_libres = total_baldas - baldas_ocupadas
    ocupacion_porcentaje = round((baldas_ocupadas / total_baldas) * 100, 1)
    
    return render_template('dashboard_print.html',
                           estanteria_num=num,
                           baldas_ocupacion=baldas_ocupacion,
                           baldas_productos=baldas_productos,
                           total_baldas=total_baldas,
                           baldas_ocupadas=baldas_ocupadas,
                           baldas_libres=baldas_libres,
                           ocupacion_porcentaje=ocupacion_porcentaje)


@app.route('/entrada', methods=['GET'])
def entrada():
    """Mostrar grid de catálogo de productos activos"""
    # Obtener todos los códigos físicos activos
    codigos_catalogo = CodigoFisico.query.filter_by(activo=True).order_by(CodigoFisico.codigo).all()
    
    # Preparar datos para el template
    productos_catalogo = []
    for codigo in codigos_catalogo:
        # Obtener máquinas asociadas
        maquinas = [pm.codigo for pm in codigo.productos_maquina]
        maquinas_str = ', '.join(maquinas) if maquinas else ''
        
        # Calcular stock total
        stock_total = db.session.query(func.sum(Stock.cantidad)).filter(
            Stock.codigo_fisico_id == codigo.id,
            Stock.cantidad > 0
        ).scalar() or 0
        
        # Determinar badge color según tipo
        tipo_badges = {
            'mazo': 'warning',
            'panel_grande': 'primary',
            'panel_mediano': 'info',
            'panel_pequeño': 'secondary'
        }
        
        tipo_displays = {
            'mazo': 'Mazo',
            'panel_grande': 'Panel Grande',
            'panel_mediano': 'Panel Mediano',
            'panel_pequeño': 'Panel Pequeño'
        }
        
        # Preparar texto completo para búsqueda
        descripcion_completa = codigo.descripcion or tipo_displays.get(codigo.tipo, codigo.tipo)
        descripcion_proyecto = extraer_proyecto(codigo.descripcion or '')
        busqueda_texto = f"{codigo.codigo} {descripcion_completa} {descripcion_proyecto} {maquinas_str}".lower()
        
        productos_catalogo.append({
            'id': codigo.id,
            'codigo': codigo.codigo,
            'descripcion': descripcion_completa,
            'descripcion_proyecto': descripcion_proyecto,
            'maquinas': maquinas_str,
            'busqueda_texto': busqueda_texto,
            'tipo': codigo.tipo,
            'tipo_display': tipo_displays.get(codigo.tipo, codigo.tipo),
            'tipo_badge': tipo_badges.get(codigo.tipo, 'secondary'),
            'stock_actual': int(stock_total)
        })
    
    return render_template('entrada.html', productos_catalogo=productos_catalogo)


@app.route('/entrada/procesar', methods=['POST'])
def entrada_procesar():
    """Procesar entrada de material desde el grid"""
    codigo_fisico_id = request.form.get('codigo_fisico_id')
    cantidad_total = int(request.form.get('cantidad', 1))
    
    codigo_fisico = CodigoFisico.query.get(codigo_fisico_id)
    
    if not codigo_fisico:
        return jsonify({'success': False, 'error': 'Producto no encontrado'})
    
    # Procesar cada unidad individualmente
    ubicaciones_asignadas = []
    
    for i in range(cantidad_total):
        # Buscar ubicación óptima para esta unidad (cantidad=1)
        ubicacion = buscar_ubicacion_optima(codigo_fisico, 1)
        
        if not ubicacion:
            # Si no hay más espacio, hacer rollback de lo realizado
            db.session.rollback()
            return jsonify({
                'success': False, 
                'error': f'No hay espacio suficiente. Solo se pudieron almacenar {i} de {cantidad_total} unidades.'
            })
        
        # Crear registro de stock unitario
        stock_nuevo = Stock(
            codigo_fisico_id=codigo_fisico.id,
            ubicacion_id=ubicacion.id,
            cantidad=1,
            fecha_entrada=datetime.now()
        )
        db.session.add(stock_nuevo)
        
        # Registrar movimiento unitario
        movimiento = Movimiento(
            tipo='entrada',
            producto_codigo=codigo_fisico.codigo,
            ubicacion_destino=ubicacion.formato_display,
            cantidad=1,
            observaciones=f'Entrada automática - {codigo_fisico.tipo_display}'
        )
        db.session.add(movimiento)
        
        ubicaciones_asignadas.append(ubicacion.formato_display)
    
    db.session.commit()
    
    # Generar mensaje con todas las ubicaciones
    if len(ubicaciones_asignadas) == 1:
        mensaje = f'1 unidad de {codigo_fisico.codigo} almacenada en {ubicaciones_asignadas[0]}'
    else:
        ubicaciones_str = ', '.join(ubicaciones_asignadas)
        mensaje = f'{cantidad_total} unidades de {codigo_fisico.codigo} almacenadas en: {ubicaciones_str}'
    
    return jsonify({
        'success': True,
        'ubicaciones': ubicaciones_asignadas,
        'mensaje': mensaje
    })


@app.route('/salida', methods=['GET'])
def salida():
    """Mostrar grid de productos disponibles en stock"""
    # Obtener todos los productos con stock
    codigos_con_stock = db.session.query(CodigoFisico.id).join(
        Stock, Stock.codigo_fisico_id == CodigoFisico.id
    ).filter(Stock.cantidad > 0).distinct().all()
    
    codigos_ids = [c.id for c in codigos_con_stock]
    
    # Obtener información completa de cada código físico con stock
    productos_stock = []
    for codigo_id in codigos_ids:
        codigo_fisico = CodigoFisico.query.get(codigo_id)
        
        # Calcular totales de stock
        total_cantidad = db.session.query(func.sum(Stock.cantidad)).filter(
            Stock.codigo_fisico_id == codigo_id,
            Stock.cantidad > 0
        ).scalar() or 0
        
        ubicaciones_count = db.session.query(func.count(Stock.id)).filter(
            Stock.codigo_fisico_id == codigo_id,
            Stock.cantidad > 0
        ).scalar() or 0
        
        fecha_mas_antigua = db.session.query(func.min(Stock.fecha_entrada)).filter(
            Stock.codigo_fisico_id == codigo_id,
            Stock.cantidad > 0
        ).scalar()
        
        dias_antiguo = (datetime.now() - fecha_mas_antigua).days if fecha_mas_antigua else 0
        
        # Obtener máquinas asociadas
        maquinas = [pm.codigo for pm in codigo_fisico.productos_maquina]
        maquinas_str = ', '.join(maquinas) if maquinas else ''
        
        # Determinar badge color según tipo
        tipo_badges = {
            'mazo': 'warning',
            'panel_grande': 'primary',
            'panel_mediano': 'info',
            'panel_pequeño': 'secondary'
        }
        
        tipo_displays = {
            'mazo': 'Mazo',
            'panel_grande': 'Panel Grande',
            'panel_mediano': 'Panel Mediano',
            'panel_pequeño': 'Panel Pequeño'
        }
        
        # Preparar texto completo para búsqueda
        descripcion_completa = codigo_fisico.descripcion or tipo_displays.get(codigo_fisico.tipo, codigo_fisico.tipo)
        descripcion_proyecto = extraer_proyecto(codigo_fisico.descripcion or '')
        busqueda_texto = f"{codigo_fisico.codigo} {descripcion_completa} {descripcion_proyecto} {maquinas_str}".lower()
        
        productos_stock.append({
            'codigo': codigo_fisico.codigo,
            'descripcion': descripcion_completa,
            'descripcion_proyecto': descripcion_proyecto,
            'maquinas': maquinas_str,
            'busqueda_texto': busqueda_texto,
            'tipo': codigo_fisico.tipo,
            'tipo_display': tipo_displays.get(codigo_fisico.tipo, codigo_fisico.tipo),
            'tipo_badge': tipo_badges.get(codigo_fisico.tipo, 'secondary'),
            'cantidad_total': int(total_cantidad),
            'ubicaciones_count': ubicaciones_count,
            'dias_antiguo': dias_antiguo
        })
    
    # Ordenar por código
    productos_stock.sort(key=lambda x: x['codigo'])
    
    return render_template('salida.html', productos_stock=productos_stock)


@app.route('/buscar_fifo')
def buscar_fifo():
    """API para buscar ubicación FIFO de un producto"""
    codigo = request.args.get('codigo', '').strip().upper()
    
    # Buscar código físico
    codigo_fisico = CodigoFisico.query.filter_by(codigo=codigo).first()
    
    if not codigo_fisico:
        return jsonify({'success': False, 'error': 'Código no encontrado'})
    
    # Buscar stock más antiguo (FIFO)
    stock_fifo = Stock.query.filter(
        Stock.codigo_fisico_id == codigo_fisico.id,
        Stock.cantidad > 0
    ).order_by(Stock.fecha_entrada.asc()).first()
    
    if not stock_fifo:
        return jsonify({'success': False, 'error': 'Sin stock disponible'})
    
    # Retornar información FIFO
    ubicacion = stock_fifo.ubicacion
    return jsonify({
        'success': True,
        'stock_id': stock_fifo.id,
        'ubicacion': ubicacion.formato_display,
        'cantidad': stock_fifo.cantidad,
        'fecha_entrada': stock_fifo.fecha_entrada.strftime('%d/%m/%Y %H:%M'),
        'dias_almacenado': stock_fifo.dias_almacenado
    })


@app.route('/confirmar_salida', methods=['POST'])
def confirmar_salida():
    """Confirmar y registrar salida de material"""
    stock_id = request.form.get('stock_id')
    cantidad = int(request.form.get('cantidad', 1))
    
    stock_item = Stock.query.get(stock_id)
    
    if not stock_item:
        flash('Error: Stock no encontrado', 'danger')
        return redirect(url_for('salida'))
    
    if cantidad > stock_item.cantidad:
        flash('Error: Cantidad solicitada mayor que disponible', 'danger')
        return redirect(url_for('salida'))
    
    # Registrar movimiento
    movimiento = Movimiento(
        tipo='salida',
        producto_codigo=stock_item.codigo_fisico.codigo,
        ubicacion_origen=stock_item.ubicacion.formato_display,
        cantidad=cantidad,
        observaciones=f'Salida FIFO - {stock_item.dias_almacenado} días almacenado'
    )
    db.session.add(movimiento)
    
    # Actualizar stock
    if cantidad == stock_item.cantidad:
        # Salida total - eliminar registro
        db.session.delete(stock_item)
    else:
        # Salida parcial - actualizar cantidad
        stock_item.cantidad -= cantidad
    
    db.session.commit()
    
    salida_info = {
        'codigo': stock_item.codigo_fisico.codigo,
        'cantidad': cantidad,
        'ubicacion': stock_item.ubicacion.formato_display
    }
    
    flash(f'Salida registrada: {cantidad} unidades de {stock_item.codigo_fisico.codigo}', 'success')
    return render_template('salida.html', salida_confirmada=salida_info)


@app.route('/reorganizar')
def reorganizar():
    """Reorganizar balda sobresaturada"""
    balda_key = request.args.get('balda')  # Formato: E1-B2
    
    if not balda_key:
        flash('No se especificó balda a reorganizar', 'danger')
        return redirect(url_for('index'))
    
    # Parsear estantería y balda
    partes = balda_key.split('-')
    if len(partes) != 2:
        flash('Formato de balda inválido', 'danger')
        return redirect(url_for('index'))
    
    estanteria = int(partes[0][1:])  # E1 -> 1
    balda = int(partes[1][1:])  # B2 -> 2
    
    # Obtener todos los productos de esta balda
    items_balda = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
        Ubicacion.estanteria == estanteria,
        Ubicacion.balda == balda,
        Stock.cantidad > 0
    ).order_by(Stock.fecha_entrada).all()
    
    if not items_balda:
        flash('La balda está vacía', 'info')
        return redirect(url_for('index'))
    
    # Calcular ocupación actual
    huecos_ocupados = 0
    for item in items_balda:
        if item.codigo_fisico.tipo == 'mazo':
            huecos_ocupados += item.cantidad * 1
        elif item.codigo_fisico.tipo == 'panel_grande':
            huecos_ocupados += item.cantidad * 2.5
        elif item.codigo_fisico.tipo == 'panel_mediano':
            huecos_ocupados += item.cantidad * (5/3)
        elif item.codigo_fisico.tipo == 'panel_pequeño':
            huecos_ocupados += item.cantidad * (5/6)
    
    if huecos_ocupados <= 5:
        flash(f'La balda {balda_key} no está sobresaturada ({huecos_ocupados:.1f}/5 huecos)', 'info')
        return redirect(url_for('index'))
    
    # Intentar mover productos a otras baldas para liberar espacio
    movimientos_realizados = []
    
    # Ordenar por más recientes primero (intentar mover los que entraron último)
    for producto_mover in reversed(items_balda):
        if huecos_ocupados <= 5:
            break  # Ya está dentro del límite
        
        # Buscar ubicación en OTRA balda (no la actual)
        ubicacion_nueva = buscar_ubicacion_en_otra_balda(
            producto_mover.codigo_fisico, 
            producto_mover.cantidad,
            estanteria_excluir=estanteria,
            balda_excluir=balda
        )
        
        if ubicacion_nueva:
            # Calcular huecos que libera este producto
            huecos_liberar = 0
            if producto_mover.codigo_fisico.tipo == 'mazo':
                huecos_liberar = producto_mover.cantidad * 1
            elif producto_mover.codigo_fisico.tipo == 'panel_grande':
                huecos_liberar = producto_mover.cantidad * 2.5
            elif producto_mover.codigo_fisico.tipo == 'panel_pequeño':
                huecos_liberar = producto_mover.cantidad * (5/6)
            
            # Mover el producto
            ubicacion_anterior = producto_mover.ubicacion.formato_display
            producto_mover.ubicacion_id = ubicacion_nueva.id
            
            # Registrar movimiento
            movimiento = Movimiento(
                tipo='reorganizacion',
                producto_codigo=producto_mover.codigo_fisico.codigo,
                ubicacion_origen=ubicacion_anterior,
                ubicacion_destino=ubicacion_nueva.formato_display,
                cantidad=producto_mover.cantidad,
                observaciones=f'Reorganización automática - balda {balda_key} sobresaturada ({huecos_ocupados:.1f}/5 huecos)'
            )
            db.session.add(movimiento)
            
            huecos_ocupados -= huecos_liberar
            movimientos_realizados.append(f'{producto_mover.codigo_fisico.codigo} de {ubicacion_anterior} a {ubicacion_nueva.formato_display}')
    
    if movimientos_realizados:
        db.session.commit()
        flash(f'Reorganización exitosa: {"; ".join(movimientos_realizados)}. Balda {balda_key} ahora al {huecos_ocupados/5*100:.0f}%', 'success')
    else:
        flash('No se encontró espacio en otras baldas. Considere hacer salida de productos antiguos o aumentar capacidad.', 'warning')
    
    return redirect(url_for('index'))


def buscar_ubicacion_en_otra_balda(codigo_fisico, cantidad, estanteria_excluir, balda_excluir):
    """Busca ubicación óptima excluyendo una balda específica y priorizando baldas del mismo tipo"""
    from models import Ubicacion, Stock, CodigoFisico
    
    # Calcular huecos necesarios
    if codigo_fisico.tipo == 'mazo':
        huecos_necesarios = cantidad * 1
    elif codigo_fisico.tipo == 'panel_grande':
        huecos_necesarios = cantidad * 2.5
    elif codigo_fisico.tipo == 'panel_mediano':
        huecos_necesarios = cantidad * (5/3)
    elif codigo_fisico.tipo == 'panel_pequeño':
        huecos_necesarios = cantidad * (5/6)
    else:
        huecos_necesarios = cantidad * 1
    
    # PRIORIDAD 1: Buscar baldas que YA tienen productos del mismo tipo
    baldas_mismo_tipo = db.session.query(
        Ubicacion.estanteria, Ubicacion.balda
    ).join(Stock).join(CodigoFisico).filter(
        CodigoFisico.tipo == codigo_fisico.tipo,
        Stock.cantidad > 0
    ).distinct().all()
    
    for est, bald in baldas_mismo_tipo:
        # Saltar la balda que queremos descongestionar
        if est == estanteria_excluir and bald == balda_excluir:
            continue
        
        # Calcular ocupación de esta balda
        items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
            Ubicacion.estanteria == est,
            Ubicacion.balda == bald,
            Stock.cantidad > 0
        ).all()
        
        huecos_ocupados = 0
        for item in items:
            if item.codigo_fisico.tipo == 'mazo':
                huecos_ocupados += item.cantidad * 1
            elif item.codigo_fisico.tipo == 'panel_grande':
                huecos_ocupados += item.cantidad * 2.5
            elif item.codigo_fisico.tipo == 'panel_mediano':
                huecos_ocupados += item.cantidad * (5/3)
            elif item.codigo_fisico.tipo == 'panel_pequeño':
                huecos_ocupados += item.cantidad * (5/6)
        
        # Verificar si hay espacio suficiente
        if huecos_ocupados + huecos_necesarios <= 5:
            # Buscar posición libre en esta balda
            ubicacion = Ubicacion.query.outerjoin(Stock).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == bald,
                Stock.id == None
            ).order_by(Ubicacion.posicion).first()
            
            if ubicacion:
                return ubicacion
    
    # PRIORIDAD 2: Buscar baldas completamente vacías
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        for bald in range(1, Config.NUM_BALDAS + 1):
            # Saltar la balda que queremos descongestionar
            if est == estanteria_excluir and bald == balda_excluir:
                continue
            
            # Verificar si está completamente vacía
            items_count = Stock.query.join(Ubicacion).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == bald,
                Stock.cantidad > 0
            ).count()
            
            if items_count == 0:
                # Buscar primera posición de esta balda vacía
                ubicacion = Ubicacion.query.filter(
                    Ubicacion.estanteria == est,
                    Ubicacion.balda == bald
                ).order_by(Ubicacion.posicion).first()
                
                if ubicacion:
                    return ubicacion
    
    # PRIORIDAD 3: Buscar baldas con espacio suficiente (aunque tengan otros tipos)
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        for bald in range(1, Config.NUM_BALDAS + 1):
            # Saltar la balda que queremos descongestionar
            if est == estanteria_excluir and bald == balda_excluir:
                continue
            
            # Calcular ocupación de esta balda
            items = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
                Ubicacion.estanteria == est,
                Ubicacion.balda == bald,
                Stock.cantidad > 0
            ).all()
            
            huecos_ocupados = 0
            for item in items:
                if item.codigo_fisico.tipo == 'mazo':
                    huecos_ocupados += item.cantidad * 1
                elif item.codigo_fisico.tipo == 'panel_grande':
                    huecos_ocupados += item.cantidad * 2.5
                elif item.codigo_fisico.tipo == 'panel_mediano':
                    huecos_ocupados += item.cantidad * (5/3)
                elif item.codigo_fisico.tipo == 'panel_pequeño':
                    huecos_ocupados += item.cantidad * (5/6)
            
            # Verificar si hay espacio suficiente
            if huecos_ocupados + huecos_necesarios <= 5:
                # Buscar posición libre en esta balda
                ubicacion = Ubicacion.query.outerjoin(Stock).filter(
                    Ubicacion.estanteria == est,
                    Ubicacion.balda == bald,
                    Stock.id == None
                ).order_by(Ubicacion.posicion).first()
                
                if ubicacion:
                    return ubicacion
    
    return None


@app.route('/catalogo')
def catalogo():
    """Vista de catálogo con dos pestañas: Códigos Físicos y Máquinas"""
    codigos = CodigoFisico.query.order_by(CodigoFisico.codigo).all()
    maquinas = ProductoMaquina.query.order_by(ProductoMaquina.codigo).all()
    return render_template('catalogo.html', codigos=codigos, maquinas=maquinas)


@app.route('/catalogo/codigo/nuevo', methods=['POST'])
def catalogo_codigo_nuevo():
    """Agregar nuevo código físico"""
    codigo = request.form.get('codigo', '').strip().upper()
    tipo = request.form.get('tipo', '').strip()
    descripcion = request.form.get('descripcion', '').strip() or None
    
    # Validar código único
    existe = CodigoFisico.query.filter_by(codigo=codigo).first()
    if existe:
        flash(f'El código {codigo} ya existe', 'danger')
        return redirect(url_for('catalogo'))
    
    codigo_fisico = CodigoFisico(
        codigo=codigo,
        tipo=tipo,
        descripcion=descripcion
    )
    
    db.session.add(codigo_fisico)
    db.session.commit()
    
    flash(f'Código {codigo} agregado correctamente', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/codigo/editar/<int:id>', methods=['POST'])
def catalogo_codigo_editar(id):
    """Editar código físico existente"""
    codigo = CodigoFisico.query.get_or_404(id)
    
    codigo.tipo = request.form.get('tipo', '').strip()
    codigo.descripcion = request.form.get('descripcion', '').strip() or None
    
    db.session.commit()
    
    flash(f'Código {codigo.codigo} actualizado', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/codigo/toggle/<int:id>', methods=['POST'])
def catalogo_codigo_toggle(id):
    """Activar/Desactivar código físico"""
    codigo = CodigoFisico.query.get_or_404(id)
    codigo.activo = not codigo.activo
    db.session.commit()
    
    estado = "activado" if codigo.activo else "desactivado"
    flash(f'Código {codigo.codigo} {estado}', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/codigo/eliminar/<int:id>', methods=['POST'])
def catalogo_codigo_eliminar(id):
    """Eliminar código físico"""
    codigo = CodigoFisico.query.get_or_404(id)
    
    # Verificar que no tenga stock
    if codigo.stock_total > 0:
        flash(f'No se puede eliminar {codigo.codigo}: tiene stock activo', 'danger')
        return redirect(url_for('catalogo'))
    
    codigo_str = codigo.codigo
    db.session.delete(codigo)
    db.session.commit()
    
    flash(f'Código {codigo_str} eliminado', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/maquina/nuevo', methods=['POST'])
def catalogo_maquina_nuevo():
    """Agregar nueva máquina/producto"""
    codigo = request.form.get('codigo', '').strip().upper()
    denominacion = request.form.get('denominacion', '').strip()
    
    # Validar código único
    existe = ProductoMaquina.query.filter_by(codigo=codigo).first()
    if existe:
        flash(f'El código {codigo} ya existe', 'danger')
        return redirect(url_for('catalogo'))
    
    maquina = ProductoMaquina(
        codigo=codigo,
        denominacion=denominacion
    )
    
    db.session.add(maquina)
    db.session.commit()
    
    flash(f'Máquina {codigo} agregada correctamente', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/maquina/editar/<int:id>', methods=['POST'])
def catalogo_maquina_editar(id):
    """Editar máquina/producto existente"""
    maquina = ProductoMaquina.query.get_or_404(id)
    
    maquina.denominacion = request.form.get('denominacion', '').strip()
    
    db.session.commit()
    
    flash(f'Máquina {maquina.codigo} actualizada', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/maquina/eliminar/<int:id>', methods=['POST'])
def catalogo_maquina_eliminar(id):
    """Eliminar máquina/producto"""
    maquina = ProductoMaquina.query.get_or_404(id)
    
    codigo_str = maquina.codigo
    db.session.delete(maquina)
    db.session.commit()
    
    flash(f'Máquina {codigo_str} eliminada', 'success')
    return redirect(url_for('catalogo'))


@app.route('/catalogo/asociar', methods=['POST'])
def catalogo_asociar():
    """Asociar código físico con máquina"""
    codigo_fisico_id = request.form.get('codigo_fisico_id')
    maquina_id = request.form.get('maquina_id')
    
    codigo = CodigoFisico.query.get(codigo_fisico_id)
    maquina = ProductoMaquina.query.get(maquina_id)
    
    if codigo and maquina:
        if maquina not in codigo.productos_maquina:
            codigo.productos_maquina.append(maquina)
            db.session.commit()
            flash(f'Código {codigo.codigo} asociado a {maquina.codigo}', 'success')
        else:
            flash('Ya están asociados', 'info')
    else:
        flash('Error en la asociación', 'danger')
    
    return redirect(url_for('catalogo'))


@app.route('/catalogo/desasociar', methods=['POST'])
def catalogo_desasociar():
    """Desasociar código físico de máquina"""
    codigo_fisico_id = request.form.get('codigo_fisico_id')
    maquina_id = request.form.get('maquina_id')
    
    codigo = CodigoFisico.query.get(codigo_fisico_id)
    maquina = ProductoMaquina.query.get(maquina_id)
    
    if codigo and maquina:
        if maquina in codigo.productos_maquina:
            codigo.productos_maquina.remove(maquina)
            db.session.commit()
            flash(f'Código {codigo.codigo} desasociado de {maquina.codigo}', 'success')
        else:
            flash('No están asociados', 'info')
    else:
        flash('Error en la desasociación', 'danger')
    
    return redirect(url_for('catalogo'))


@app.route('/historial')
def historial():
    """Vista de historial de movimientos"""
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    tipo_movimiento = request.args.get('tipo')
    producto_codigo = request.args.get('producto')
    
    query = Movimiento.query
    
    if fecha_desde:
        query = query.filter(Movimiento.timestamp >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    if fecha_hasta:
        query = query.filter(Movimiento.timestamp <= datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if tipo_movimiento:
        query = query.filter(Movimiento.tipo == tipo_movimiento)
    if producto_codigo:
        query = query.filter(Movimiento.producto_codigo.contains(producto_codigo.upper()))
    
    movimientos = query.order_by(Movimiento.timestamp.desc()).limit(500).all()
    
    return render_template('historial.html', 
                         movimientos=movimientos,
                         filtros={
                             'fecha_desde': fecha_desde,
                             'fecha_hasta': fecha_hasta,
                             'tipo': tipo_movimiento,
                             'producto': producto_codigo
                         })


@app.route('/historial/exportar')
def historial_exportar():
    """Exportar historial a Excel"""
    movimientos = Movimiento.query.order_by(Movimiento.timestamp.desc()).all()
    
    datos = []
    for mov in movimientos:
        datos.append({
            'Fecha': mov.timestamp.strftime('%d/%m/%Y %H:%M'),
            'Tipo': mov.tipo.upper(),
            'Producto': mov.producto_codigo,
            'Origen': mov.ubicacion_origen or '-',
            'Destino': mov.ubicacion_destino or '-',
            'Cantidad': mov.cantidad,
            'Observaciones': mov.observaciones or ''
        })
    
    df = pd.DataFrame(datos)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Historial', index=False)
    output.seek(0)
    
    return send_file(output, 
                    download_name=f'historial_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    as_attachment=True,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/reportes')
def reportes():
    """Vista de reportes y métricas"""
    # Stock actual por código físico
    codigos_stock = []
    codigos = CodigoFisico.query.all()
    
    for codigo in codigos:
        if codigo.stock_total > 0:
            ubicaciones_detalle = []
            for stock_item in codigo.stock_items:
                if stock_item.cantidad > 0:
                    ubicaciones_detalle.append({
                        'ubicacion': stock_item.ubicacion.formato_display,
                        'cantidad': stock_item.cantidad,
                        'dias': stock_item.dias_almacenado
                    })
            
            dias_almacenado = [s.dias_almacenado for s in codigo.stock_items if s.cantidad > 0]
            
            codigos_stock.append({
                'codigo': codigo.codigo,
                'denominacion': codigo.descripcion or codigo.tipo_display,
                'tipo': codigo.tipo_display,
                'cantidad_total': codigo.stock_total,
                'ubicaciones': ubicaciones_detalle,
                'dias_min': min(dias_almacenado) if dias_almacenado else 0,
                'dias_max': max(dias_almacenado) if dias_almacenado else 0,
                'maquinas': ', '.join(codigo.maquinas_info) if codigo.maquinas_info else 'Sin asignar'
            })
    
    # Ocupación por estantería
    ocupacion_estanterias = []
    for est in range(1, Config.NUM_ESTANTERIAS + 1):
        baldas_ocupadas = set()
        for stock_item in Stock.query.join(Ubicacion).filter(
            Ubicacion.estanteria == est,
            Stock.cantidad > 0
        ).all():
            baldas_ocupadas.add(stock_item.ubicacion.balda)
        
        ocupacion_estanterias.append({
            'estanteria': est,
            'baldas_ocupadas': len(baldas_ocupadas),
            'baldas_totales': Config.NUM_BALDAS,
            'porcentaje': round((len(baldas_ocupadas) / Config.NUM_BALDAS) * 100, 1)
        })
    
    # Calcular eficiencia vs óptimo
    reorganizacion = calcular_reorganizacion_optima()
    eficiencia = {
        'baldas_actuales': reorganizacion['baldas_antes'],
        'baldas_optimas': reorganizacion['baldas_despues'],
        'baldas_desperdiciadas': reorganizacion['baldas_liberadas'],
        'porcentaje_eficiencia': 100 - reorganizacion['eficiencia_porcentaje'] if reorganizacion['baldas_antes'] > 0 else 100
    }
    
    return render_template('reportes.html',
                         productos_stock=codigos_stock,
                         ocupacion_estanterias=ocupacion_estanterias,
                         eficiencia=eficiencia,
                         reorganizacion_disponible=reorganizacion)


@app.route('/reportes/optimizar', methods=['POST'])
def reportes_optimizar():
    """Ejecutar optimización global del stock"""
    reorganizacion = calcular_reorganizacion_optima()
    
    if not reorganizacion['lista_movimientos']:
        flash('El stock ya está optimizado', 'info')
        return redirect(url_for('reportes'))
    
    # Guardar tareas de reorganización
    for mov in reorganizacion['lista_movimientos']:
        tarea = TareaReorganizacion(
            producto_codigo=mov['producto_codigo'],
            ubicacion_origen=mov['ubicacion_actual'],
            ubicacion_destino=mov['ubicacion_nueva'],
            cantidad=mov['cantidad'],
            motivo=mov['motivo'],
            orden=mov['id_temp'],
            session_id=reorganizacion['session_id']
        )
        db.session.add(tarea)
    db.session.commit()
    
    flash(f'Plan de optimización creado: {len(reorganizacion["lista_movimientos"])} movimientos', 'success')
    return redirect(url_for('reportes'))


# API endpoints
@app.route('/api/ubicacion/<ubicacion>')
def api_ubicacion_detalle(ubicacion):
    """API: Detalle de una ubicación específica"""
    try:
        partes = Ubicacion.from_formato(ubicacion)
        if not partes:
            return jsonify({'error': 'Formato de ubicación inválido'}), 400
        
        ubicacion_obj = Ubicacion.query.filter_by(
            estanteria=partes['estanteria'],
            balda=partes['balda'],
            posicion=partes['posicion']
        ).first()
        
        if not ubicacion_obj:
            return jsonify({'ubicacion': ubicacion, 'stock': []})
        
        stock_items = Stock.query.filter_by(ubicacion_id=ubicacion_obj.id).filter(Stock.cantidad > 0).all()
        
        stock_info = []
        for item in stock_items:
            stock_info.append({
                'codigo': item.codigo_fisico.codigo,
                'descripcion': item.codigo_fisico.descripcion or item.codigo_fisico.tipo_display,
                'descripcion_proyecto': extraer_proyecto(item.codigo_fisico.descripcion or ''),
                'tipo': item.codigo_fisico.tipo_display,
                'cantidad': item.cantidad,
                'dias_almacenado': item.dias_almacenado,
                'fecha_entrada': item.fecha_entrada.strftime('%d/%m/%Y'),
                'maquinas': item.codigo_fisico.maquinas_info
            })
        
        return jsonify({
            'ubicacion': ubicacion,
            'stock': stock_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/completar_tarea', methods=['POST'])
def api_completar_tarea():
    """API: Marcar tarea de reorganización como completada"""
    data = request.get_json()
    tarea_id = data.get('tarea_id')
    session_id = data.get('session_id')
    
    tarea = TareaReorganizacion.query.filter_by(
        orden=tarea_id,
        session_id=session_id
    ).first()
    
    if not tarea:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    
    # Marcar como completada
    tarea.completada = True
    
    # Ejecutar el movimiento
    # 1. Buscar stock en origen
    ubicacion_origen = Ubicacion.query.filter_by(
        **Ubicacion.from_formato(tarea.ubicacion_origen)
    ).first()
    
    ubicacion_destino = Ubicacion.query.filter_by(
        **Ubicacion.from_formato(tarea.ubicacion_destino)
    ).first()
    
    if ubicacion_origen and ubicacion_destino:
        codigo_fisico = CodigoFisico.query.filter_by(codigo=tarea.producto_codigo).first()
        
        if codigo_fisico:
            # Buscar stock en origen
            stock_origen = Stock.query.filter_by(
                codigo_fisico_id=codigo_fisico.id,
                ubicacion_id=ubicacion_origen.id
            ).first()
            
            if stock_origen and stock_origen.cantidad >= tarea.cantidad:
                # Restar de origen
                if stock_origen.cantidad == tarea.cantidad:
                    db.session.delete(stock_origen)
                else:
                    stock_origen.cantidad -= tarea.cantidad
                
                # Agregar a destino
                stock_destino = Stock.query.filter_by(
                    codigo_fisico_id=codigo_fisico.id,
                    ubicacion_id=ubicacion_destino.id
                ).first()
                
                if stock_destino:
                    stock_destino.cantidad += tarea.cantidad
                else:
                    stock_destino = Stock(
                        codigo_fisico_id=codigo_fisico.id,
                        ubicacion_id=ubicacion_destino.id,
                        cantidad=tarea.cantidad,
                        fecha_entrada=stock_origen.fecha_entrada if stock_origen else datetime.utcnow()
                    )
                    db.session.add(stock_destino)
                
                # Registrar movimiento
                movimiento = Movimiento(
                    tipo='reubicacion',
                    producto_codigo=codigo_fisico.codigo,
                    ubicacion_origen=tarea.ubicacion_origen,
                    ubicacion_destino=tarea.ubicacion_destino,
                    cantidad=tarea.cantidad,
                    observaciones=f'Reorganización automática: {tarea.motivo}'
                )
                db.session.add(movimiento)
    
    db.session.commit()
    
    return jsonify({'success': True, 'tarea_id': tarea_id})


@app.route('/reset_database', methods=['POST'])
def reset_database():
    """Resetear base de datos (vaciar stock y movimientos) con clave de seguridad"""
    clave = request.form.get('clave', '').strip()
    
    if clave != '200985':
        return jsonify({'success': False, 'error': 'Clave incorrecta'})
    
    try:
        # Eliminar todo el stock
        Stock.query.delete()
        
        # Eliminar todos los movimientos
        Movimiento.query.delete()
        
        # Eliminar tareas de reorganización
        TareaReorganizacion.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'mensaje': 'Base de datos reseteada correctamente. Todas las estanterías están vacías.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/reubicar_manual', methods=['POST'])
def reubicar_manual():
    """Reubicar un producto manualmente a una nueva ubicación"""
    ubicacion_origen_str = request.form.get('ubicacion_origen')
    estanteria_destino = int(request.form.get('estanteria_destino'))
    balda_destino = int(request.form.get('balda_destino'))
    
    # Parsear ubicación origen
    partes_origen = Ubicacion.from_formato(ubicacion_origen_str)
    if not partes_origen:
        return jsonify({'success': False, 'error': 'Ubicación origen inválida'})
    
    # Buscar stock en origen
    ubicacion_origen = Ubicacion.query.filter_by(**partes_origen).first()
    if not ubicacion_origen:
        return jsonify({'success': False, 'error': 'Ubicación origen no encontrada'})
    
    stock_origen = Stock.query.filter_by(ubicacion_id=ubicacion_origen.id).first()
    if not stock_origen:
        return jsonify({'success': False, 'error': 'No hay stock en ubicación origen'})
    
    # Buscar ubicación destino óptima en la balda indicada
    codigo_fisico = stock_origen.codigo_fisico
    cantidad = stock_origen.cantidad
    
    # Calcular huecos necesarios según nuevo sistema
    es_balda_mazos = codigo_fisico.tipo == 'mazo'
    if es_balda_mazos:
        huecos_necesarios = cantidad * 1  # 1 hueco por mazo
        total_huecos_balda = 5
    else:
        # Paneles
        if codigo_fisico.tipo == 'panel_grande':
            huecos_necesarios = cantidad * 3  # 3 posiciones
        elif codigo_fisico.tipo == 'panel_mediano':
            huecos_necesarios = cantidad * 2  # 2 posiciones
        else:
            huecos_necesarios = cantidad * 1  # 1 posición
        total_huecos_balda = 6
    
    # Verificar espacio disponible en balda destino
    items_balda_destino = Stock.query.join(Ubicacion).join(CodigoFisico).filter(
        Ubicacion.estanteria == estanteria_destino,
        Ubicacion.balda == balda_destino,
        Stock.cantidad > 0
    ).all()
    
    # Calcular huecos ocupados y crear mapa de posiciones
    posiciones_ocupadas_destino = set()
    huecos_ocupados_destino = 0
    
    for item in items_balda_destino:
        pos = item.ubicacion.posicion
        if item.codigo_fisico.tipo == 'mazo':
            huecos_ocupados_destino += item.cantidad * 1
            posiciones_ocupadas_destino.add(pos)
        elif item.codigo_fisico.tipo == 'panel_grande':
            huecos_ocupados_destino += item.cantidad * 3
            posiciones_ocupadas_destino.update([pos, pos + 1, pos + 2])
        elif item.codigo_fisico.tipo == 'panel_mediano':
            huecos_ocupados_destino += item.cantidad * 2
            posiciones_ocupadas_destino.update([pos, pos + 1])
        else:
            huecos_ocupados_destino += item.cantidad * 1
            posiciones_ocupadas_destino.add(pos)
    
    if huecos_ocupados_destino + huecos_necesarios > total_huecos_balda:
        return jsonify({'success': False, 'error': f'No hay espacio suficiente. Disponible: {total_huecos_balda - huecos_ocupados_destino:.1f} huecos, necesario: {huecos_necesarios:.1f} huecos'})
    
    # Buscar primera posición con espacio consecutivo suficiente
    max_pos = 5 if es_balda_mazos else 6
    posicion_libre = None
    
    for pos in range(1, max_pos + 1):
        # Verificar si hay espacio consecutivo desde esta posición
        espacio_disponible = True
        for offset in range(int(huecos_necesarios)):
            if (pos + offset) > max_pos or (pos + offset) in posiciones_ocupadas_destino:
                espacio_disponible = False
                break
        
        if espacio_disponible:
            posicion_libre = pos
            break
    
    if posicion_libre is None:
        return jsonify({'success': False, 'error': 'No hay posiciones consecutivas libres suficientes'})
    
    # Buscar o crear ubicación destino con la posición encontrada
    ubicacion_destino = Ubicacion.query.filter_by(
        estanteria=estanteria_destino,
        balda=balda_destino,
        posicion=posicion_libre
    ).first()
    
    if not ubicacion_destino:
        return jsonify({'success': False, 'error': 'Error al crear ubicación destino'})
    
    # Realizar reubicación
    ubicacion_origen_display = ubicacion_origen.formato_display
    ubicacion_destino_display = ubicacion_destino.formato_display
    
    # Actualizar stock
    stock_origen.ubicacion_id = ubicacion_destino.id
    
    # Registrar movimiento
    movimiento = Movimiento(
        tipo='reubicacion',
        producto_codigo=codigo_fisico.codigo,
        ubicacion_origen=ubicacion_origen_display,
        ubicacion_destino=ubicacion_destino_display,
        cantidad=cantidad,
        observaciones=f'Reubicación manual'
    )
    db.session.add(movimiento)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': f'{codigo_fisico.codigo} reubicado de {ubicacion_origen_display} a {ubicacion_destino_display}',
        'ubicacion_destino': ubicacion_destino_display
    })


@app.route('/control-stock')
def control_stock():
    """Vista consolidada de control de stock"""
    # Agrupar stock por código físico
    stock_consolidado = db.session.query(
        CodigoFisico.id,
        CodigoFisico.codigo,
        CodigoFisico.descripcion,
        CodigoFisico.tipo,
        func.sum(Stock.cantidad).label('cantidad_total'),
        func.count(Stock.id).label('num_ubicaciones'),
        func.min(Stock.fecha_entrada).label('entrada_mas_antigua'),
        func.max(Stock.fecha_entrada).label('entrada_mas_reciente')
    ).join(Stock).filter(
        Stock.cantidad > 0
    ).group_by(
        CodigoFisico.id
    ).order_by(
        CodigoFisico.tipo, CodigoFisico.codigo
    ).all()
    
    # Preparar datos para la vista
    productos_stock = []
    for item in stock_consolidado:
        # Obtener ubicaciones de este producto
        ubicaciones_query = db.session.query(
            Ubicacion,
            Stock.cantidad
        ).join(Stock).filter(
            Stock.codigo_fisico_id == item.id,
            Stock.cantidad > 0
        ).order_by(Ubicacion.estanteria, Ubicacion.balda, Ubicacion.posicion).all()
        
        ubicaciones_texto = ', '.join([f'{ub[0].formato_display}({ub[1]})' for ub in ubicaciones_query])
        
        # Calcular días desde entrada más antigua
        dias_antiguedad = (datetime.now() - item.entrada_mas_antigua).days if item.entrada_mas_antigua else 0
        
        # Determinar nivel de stock
        if item.tipo == 'mazo':
            nivel = 'alto' if item.cantidad_total >= 10 else 'medio' if item.cantidad_total >= 5 else 'bajo'
        else:  # paneles
            nivel = 'alto' if item.cantidad_total >= 6 else 'medio' if item.cantidad_total >= 3 else 'bajo'
        
        productos_stock.append({
            'codigo': item.codigo,
            'descripcion': item.descripcion or item.tipo,
            'descripcion_proyecto': extraer_proyecto(item.descripcion or ''),
            'tipo': item.tipo,
            'tipo_display': {
                'mazo': 'Mazo',
                'panel_grande': 'Panel Grande',
                'panel_mediano': 'Panel Mediano',
                'panel_pequeño': 'Panel Pequeño'
            }.get(item.tipo, item.tipo),
            'tipo_icono': (
                '📦' if item.tipo == 'mazo'
                else '🔲' if item.tipo == 'panel_grande'
                else '◻️' if item.tipo == 'panel_mediano'
                else '▫️'
            ),
            'cantidad_total': item.cantidad_total,
            'num_ubicaciones': item.num_ubicaciones,
            'ubicaciones': ubicaciones_texto,
            'dias_antiguedad': dias_antiguedad,
            'nivel': nivel
        })
    
    # Calcular resúmenes por tipo
    resumen_tipos = {
        'mazo': {'cantidad': 0, 'productos': 0},
        'panel_grande': {'cantidad': 0, 'productos': 0},
        'panel_mediano': {'cantidad': 0, 'productos': 0},
        'panel_pequeño': {'cantidad': 0, 'productos': 0}
    }
    
    for prod in productos_stock:
        resumen_tipos[prod['tipo']]['cantidad'] += prod['cantidad_total']
        resumen_tipos[prod['tipo']]['productos'] += 1
    
    # Totales generales
    total_productos = len(productos_stock)
    total_unidades = sum(p['cantidad_total'] for p in productos_stock)
    
    return render_template('control_stock.html',
                         productos_stock=productos_stock,
                         resumen_tipos=resumen_tipos,
                         total_productos=total_productos,
                         total_unidades=total_unidades)


@app.route('/control-stock/exportar')
def exportar_stock():
    """Exportar control de stock a Excel"""
    # Obtener datos consolidados
    stock_consolidado = db.session.query(
        CodigoFisico.codigo,
        CodigoFisico.descripcion,
        CodigoFisico.tipo,
        func.sum(Stock.cantidad).label('cantidad_total')
    ).join(Stock).filter(
        Stock.cantidad > 0
    ).group_by(
        CodigoFisico.id
    ).order_by(
        CodigoFisico.tipo, CodigoFisico.codigo
    ).all()
    
    # Crear DataFrame
    datos = []
    for item in stock_consolidado:
        # Obtener ubicaciones
        ubicaciones_query = db.session.query(
            Ubicacion,
            Stock.cantidad
        ).join(Stock).join(CodigoFisico).filter(
            CodigoFisico.codigo == item.codigo,
            Stock.cantidad > 0
        ).all()
        
        ubicaciones_texto = ', '.join([f'{ub[0].formato_display}({ub[1]})' for ub in ubicaciones_query])
        
        datos.append({
            'Código': item.codigo,
            'Descripción': item.descripcion or '',
            'Tipo': {
                'mazo': 'Mazo',
                'panel_grande': 'Panel Grande',
                'panel_mediano': 'Panel Mediano',
                'panel_pequeño': 'Panel Pequeño'
            }.get(item.tipo, item.tipo),
            'Cantidad Total': item.cantidad_total,
            'Ubicaciones': ubicaciones_texto
        })
    
    df = pd.DataFrame(datos)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Stock', index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'control_stock_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


