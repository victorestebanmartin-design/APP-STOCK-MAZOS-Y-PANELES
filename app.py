from routes import app, db
from models import ProductoMaquina, CodigoFisico, Ubicacion, Stock, Movimiento, codigo_maquina_association
from config import Config
import pandas as pd
import os


def init_db():
    """Inicializar base de datos y crear ubicaciones"""
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya existen ubicaciones
        if Ubicacion.query.count() == 0:
            print("Creando ubicaciones...")
            # Crear todas las ubicaciones posibles
            for est in range(1, Config.NUM_ESTANTERIAS + 1):
                for balda in range(1, Config.NUM_BALDAS + 1):
                    for pos in range(1, Config.NUM_POSICIONES + 1):
                        ubicacion = Ubicacion(
                            estanteria=est,
                            balda=balda,
                            posicion=pos
                        )
                        db.session.add(ubicacion)
            
            db.session.commit()
            total = Config.NUM_ESTANTERIAS * Config.NUM_BALDAS * Config.NUM_POSICIONES
            print(f"✓ {total} ubicaciones creadas")
        
        # Importar catálogo inicial si existe
        if ProductoMaquina.query.count() == 0:
            print("Importando catálogo inicial...")
            importar_catalogo_inicial()


def importar_catalogo_inicial():
    """Importar productos del catálogo inicial con el nuevo modelo de dos tablas"""
    # Datos del catálogo proporcionado por el usuario
    datos_catalogo = """CODIGO,DENOMINACION,COD.PANEL,COD.MAZO
280D11001,ABRAZADERA DIAM 3/8 Y SILICONA,,
H0362037,CABINA BI-DIVI/ DIS6,H0364867,
H0436602,CABINA ALSTOM IRISH,,KN-280R175388
680A20127,CABINA BELARUS,681A20074,
H0273275,CABINA BEMUZ SH,H0161897,
680A20159,CABINA BELARUS-HOLANDA,681A20100,
H0143816,CABINA CAF MI20,,KN-280R014816
H0175388,CABINA CFL,,KN-280R175388
H0052548,CABINA CIVITY UK 24Vcc (DMU),H0081351,
H0254369,CABINA DESIRO,H0292851,
H0193062,CABINA EAST MIDLANDS,H0235307,
H0404633,CABINA EMU ROMANIA ALSTOM,H0406434,
H0316536,CABINA EMUS IRELAND,,
H0442010,CABINA ETIHAD,H0445307,KN-280R0442010
H0253457,CABINA F073 PROFANO,,
H0206234,CABINA LIFT UK WG8,H0206689,KN-280R0206234
H0376795,CABINA FNM-H ALSTOM,H0380317,
H0158667,CABINA HANNOVER,H0161897,
H0409066,CABINA LLEIDA,H0482136,
H0263648,CABINA LNVG SMART CORADIA,H0361175,
H0084694,CABINA U. BRUSELAS 07,,KN-280R84694
680A20070,CABINA METRO ROMA,,
680A063,CABINA MI09,,280R10033
H0452041,CABINA MOSEL LUX,H0161897,
KN-280A0538163,CABINA NETZ BERLIN STET,H0544190,
H0044661,CABINA NEWAG,H0046172,
H0227004,CABINA NEWAG II,H0230129,
H0441207,CABINA NEWAG POMORSKIE,H0442084,
680A199,CABINA NIR,,
H0156916,CABINA NS EXTENSIÓN,H0162811,
H0262940,CABINA PESA CD,H0325863,
H0389533,CABINA PESA CD 7022,H0389538,
H0005701,CABINA PESA EMU,H0048164,
H0432024,CABINA PORTUGAL,H0472509,
H0230540,CABINA Regio-S-Bahn Bremen,H0161897,
H0186854,CABINA RENFE HC,H0374898,
H0285789,CABINA SBB,,
KN-280A0285789,CABINA SBB,H0411613,
H0403704,CABINA SERBIA,H0416275,
H0058470,CABINA SMART CORADIA,,H0069325
H0078393,CABINA SMART CORADIA ICNG,H0079842,
H0442276,CABINA STA STICON,H0442534,
H0060596,CABINA STADLER FLIRT BW1,H0069930,
H0058068,CABINA STADLER FLIRT UK ANGLIA,H0065927,KN-280R58068
H0287966,CABINA STADLER FLIRT G ADY,H0315046,
H0064325,CABINA STADLER FLIRT SRR,H0098575,
H0183099,CABINA STAF RENFE,H0342588,
H0184512,CABINA TALGO DB,,KN-280R0184512
H0546585,CABINA TALGO DSB F081,,KN-280R0184512
H0084792,CABINA TALGO F070,,H0123327
H0155116,CABINA TGV 2020,H0163693,KN-280R0155116
H0228529,CABINA TRAM TORINO,H0257470,
H0184957,CABINA UZBEKISTAN III F075,,H0123327
H0138878,CABINA WA8,,H0150777
H0118529,CABINA WEST MIDLANDS,H0122429,
H0439208,CABINA ZEFIRO,H0439210,KN-280R0439208
H0262897,CABINA ZEFIRO ESPAÑA V300,H0262894,KN-280R0262897
680A10171,CABINA ZEFIRO ITALIA V300,681A10140,280R10040-9
H0444024,CABINA KINGZITAL,H0463583,
680B10006,COND CABINA VELARO RUSIA,681A10045,
KN-280A0301798,EVAP COMPACTO CABINA BADEN H0301798,H0409389,
680C10006,EVAP CABINA VELARO RUSIA,,KN-280R10006
H0058077,HVAC CABINA CORADIA,,H0082163
680A10083,HVAC RGV2N-N1(R1 2.3,680D13024,
680M10084,HVAC TGV2N-N2,,280R10024
280G10005,KIT MAT ARMARIO MGV/RGV,,
KN-280G10018,KIT MATERIAL ARMARIO SALA MI84,,
H0006549,SALA MI84,,H0088863
680A152,SALA H2 TGV 2N,,680D6022
680A155,SALA TGV 2RANG R8 N2,,
H0251522,TERMINADOR  "CAN2/NODE",,
H0048763,TERMINADOR CAN485 HEMBRA,,
680D22196,TERMINADOR CAN1 DB,,
H0048763,Terminador CAN2 MACHO,,
680D22197,Terminador CAN2 RS-485. MACHO,,
680B20000,UNIDAD COND. PMR UT447-R134A,,
680B20001,UNIDAD COND. APTA R407C,,
680K10151,UNIDAD EXTRACTORA DOBLE -PH-,680C10675,
H0208855,UNIDAD EXTRACTORA HITACHI,,H0E06373
H0208855,UNIDAD EXTRACTORA HITACHI,,H0E06373
H0410725,UNIDAD EXTRACTORA ITE,,H0227674
H0406736,UNIDAD EXTRACTORA KT,,H0227675
H0163303,UNIDAD EXTRACTORA MYCU,,H0184210
H0201606,UNIDAD EXTRACTORA EXHAUST,,H0217495
H0617312,UNIT NEWAG 6016 CALSERIE,,H0548991
H0315146,EXHAUST UNIT,,H0217495
H0601492,CABINA PESA 61WE,H0612756,
680K096,CONJUNTO WA8 EXTRAC,,
H0345180,UNIDAD EXTRACTORA,,
H0551175,CABINA ZEFIRO,H0551174,KN-280R0551175
H0547185,CABINA KOLEJE SLASKIE,H0548991,
H0442721,UNIDAD ARB ACONDICIONADO PESA - CD,H0442710,
H0442825,CABINA PESA CD PILSEN RAL7035,H0442623,
H0508938,DISPOSITIVO DE PURGA. ROOFTOP ERMETE,H0601672,
H0544940,EXTRACTORA. ROOFTOP ERMETE,,H0601673
H0509062,CABINA ERMETE,,H0604934
KN-280A0340751,CABINA CIZE F065 DDNG,,"""

    # Procesar datos
    from io import StringIO
    df = pd.read_csv(StringIO(datos_catalogo))
    
    # Diccionario para almacenar códigos físicos únicos
    codigos_fisicos_dict = {}
    
    count_maquinas = 0
    count_codigos = 0
    count_asociaciones = 0
    
    for _, row in df.iterrows():
        # 1. Crear ProductoMaquina
        codigo_maquina = row['CODIGO'].strip()
        denominacion = row['DENOMINACION'].strip()
        
        maquina = ProductoMaquina.query.filter_by(codigo=codigo_maquina).first()
        if not maquina:
            maquina = ProductoMaquina(
                codigo=codigo_maquina,
                denominacion=denominacion
            )
            db.session.add(maquina)
            count_maquinas += 1
        
        # 2. Procesar COD.PANEL si existe
        cod_panel = row.get('COD.PANEL', '').strip() if pd.notna(row.get('COD.PANEL')) and str(row.get('COD.PANEL', '')).strip() != '' else None
        if cod_panel:
            # Determinar tipo de panel (por ahora panel_grande por defecto, se puede ajustar manualmente)
            if cod_panel not in codigos_fisicos_dict:
                tipo_panel = 'panel_grande'  # Tipo por defecto
                codigo_fisico_panel = CodigoFisico(
                    codigo=cod_panel,
                    tipo=tipo_panel,
                    descripcion=f"Panel de {denominacion}"
                )
                db.session.add(codigo_fisico_panel)
                codigos_fisicos_dict[cod_panel] = codigo_fisico_panel
                count_codigos += 1
            else:
                codigo_fisico_panel = codigos_fisicos_dict[cod_panel]
            
            # Asociar con la máquina
            if codigo_fisico_panel not in maquina.codigos_fisicos:
                maquina.codigos_fisicos.append(codigo_fisico_panel)
                count_asociaciones += 1
        
        # 3. Procesar COD.MAZO si existe
        cod_mazo = row.get('COD.MAZO', '').strip() if pd.notna(row.get('COD.MAZO')) and str(row.get('COD.MAZO', '')).strip() != '' else None
        if cod_mazo:
            if cod_mazo not in codigos_fisicos_dict:
                codigo_fisico_mazo = CodigoFisico(
                    codigo=cod_mazo,
                    tipo='mazo',
                    descripcion=f"Mazo de {denominacion}"
                )
                db.session.add(codigo_fisico_mazo)
                codigos_fisicos_dict[cod_mazo] = codigo_fisico_mazo
                count_codigos += 1
            else:
                codigo_fisico_mazo = codigos_fisicos_dict[cod_mazo]
            
            # Asociar con la máquina
            if codigo_fisico_mazo not in maquina.codigos_fisicos:
                maquina.codigos_fisicos.append(codigo_fisico_mazo)
                count_asociaciones += 1
    
    db.session.commit()
    print(f"✓ {count_maquinas} máquinas importadas")
    print(f"✓ {count_codigos} códigos físicos creados")
    print(f"✓ {count_asociaciones} asociaciones establecidas")


@app.route('/catalogo/importar', methods=['POST'])
def catalogo_importar():
    """Importar productos desde CSV"""
    from flask import request, jsonify
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se recibió archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Archivo vacío'}), 400
    
    try:
        df = pd.read_csv(file)
        
        # Validar columnas requeridas
        required_cols = ['CODIGO', 'DENOMINACION']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'success': False, 'error': f'El CSV debe contener: {", ".join(required_cols)}'}), 400
        
        count_maquinas = 0
        count_codigos = 0
        codigos_fisicos_dict = {}
        
        for _, row in df.iterrows():
            codigo = str(row['CODIGO']).strip().upper()
            denominacion = str(row['DENOMINACION']).strip()
            
            # Verificar si ya existe la máquina
            if not ProductoMaquina.query.filter_by(codigo=codigo).first():
                maquina = ProductoMaquina(
                    codigo=codigo,
                    denominacion=denominacion
                )
                db.session.add(maquina)
                count_maquinas += 1
                
                # Procesar panel y mazo si existen
                cod_panel = str(row.get('COD.PANEL', '')).strip() if pd.notna(row.get('COD.PANEL')) else ''
                cod_mazo = str(row.get('COD.MAZO', '')).strip() if pd.notna(row.get('COD.MAZO')) else ''
                
                if cod_panel and cod_panel not in codigos_fisicos_dict:
                    codigo_fisico_panel = CodigoFisico(
                        codigo=cod_panel,
                        tipo='panel_grande',
                        descripcion=f"Panel de {denominacion}"
                    )
                    db.session.add(codigo_fisico_panel)
                    codigos_fisicos_dict[cod_panel] = codigo_fisico_panel
                    maquina.codigos_fisicos.append(codigo_fisico_panel)
                    count_codigos += 1
                
                if cod_mazo and cod_mazo not in codigos_fisicos_dict:
                    codigo_fisico_mazo = CodigoFisico(
                        codigo=cod_mazo,
                        tipo='mazo',
                        descripcion=f"Mazo de {denominacion}"
                    )
                    db.session.add(codigo_fisico_mazo)
                    codigos_fisicos_dict[cod_mazo] = codigo_fisico_mazo
                    maquina.codigos_fisicos.append(codigo_fisico_mazo)
                    count_codigos += 1
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{count_maquinas} máquinas y {count_codigos} códigos físicos importados'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    
    # Ejecutar aplicación
    print("\n" + "="*50)
    print("🚀 Iniciando aplicación Stock Mazos y Paneles")
    print("="*50)
    print(f"📍 URL: http://localhost:5001")
    print(f"🗄️  Base de datos: {Config.SQLALCHEMY_DATABASE_URI}")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
