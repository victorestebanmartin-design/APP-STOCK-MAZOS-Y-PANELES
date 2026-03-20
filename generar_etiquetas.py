#!/usr/bin/env python3
"""
Generador de etiquetas para estantería
======================================
Etiquetas: 80mm x 25mm | Fondo amarillo | Letras azul
Hoja:      A4 (210mm x 297mm) | 2 columnas x 10 filas = 20 etiquetas/página

Est. 1-3 (PANELES): 6 posiciones = 3 columnas × 2 profundidades
  - Posición impar  (1,3,5) → DELANTE  ▶
  - Posición par    (2,4,6) → DETRÁS   ◀
Est. 4   (MAZOS):   5 posiciones en batería (sin profundidad)
"""

import os
import webbrowser

# ── Configuración ──────────────────────────────────────────────────────────────
NUM_ESTANTERIAS       = 4
NUM_BALDAS            = 4
NUM_POSICIONES_PANEL  = 6   # estanterías 1, 2 y 3
NUM_POSICIONES_MAZO   = 5   # estantería 4 (mazos)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "etiquetas_estanteria.html")

# ── Generar ubicaciones ────────────────────────────────────────────────────────
ubicaciones = []
for est in range(1, NUM_ESTANTERIAS + 1):
    num_pos = NUM_POSICIONES_MAZO if est == 4 else NUM_POSICIONES_PANEL
    for balda in range(1, NUM_BALDAS + 1):
        for pos in range(1, num_pos + 1):
            ubicaciones.append((est, balda, pos))

print(f"Total de ubicaciones: {len(ubicaciones)}")

# ── Construir HTML de cada etiqueta ───────────────────────────────────────────
def etiqueta_html(est, balda, pos):
    codigo = f"E{est}-B{balda}-P{pos}"

    if est == 4:
        # Mazos: sin indicador de profundidad, código centrado grande
        return f"""
      <div class="label label-mazo">
        <div class="content-col content-full">
          <div class="codigo">{codigo}</div>
          <div class="sub">MAZOS</div>
        </div>
      </div>"""
    else:
        # Paneles: posición impar = DELANTE ▲, par = DETRÁS ▼
        if pos % 2 == 1:   # impar → DELANTE
            flecha = "&#9650;"   # ▲
            dir_txt = "DELANTE"
            cls_dir = "dir-delante"
        else:               # par   → DETRÁS
            flecha = "&#9660;"   # ▼
            dir_txt = "DETR&Aacute;S"
            cls_dir = "dir-detras"
        return f"""
      <div class="label label-panel">
        <div class="arrow-col {cls_dir}">
          <span class="flecha">{flecha}</span>
          <span class="dir-label">{dir_txt}</span>
        </div>
        <div class="divider"></div>
        <div class="content-col">
          <div class="codigo">{codigo}</div>
          <div class="sub">PANELES</div>
        </div>
      </div>"""

etiquetas_html = "\n".join(etiqueta_html(e, b, p) for e, b, p in ubicaciones)

# ── Plantilla HTML completa ────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Etiquetas Estantería</title>
  <style>
    /* ── Ajuste de página ───────────────────────────────────────── */
    @page {{
      size: A4 portrait;
      margin: 8mm;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: Arial, Helvetica, sans-serif;
      background: #fff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    /* ── Rejilla de etiquetas ───────────────────────────────────── */
    /*
       A4 con margen 8mm → 210 - 16 = 194mm de ancho útil
       2 columnas de 80mm + 1 hueco de (194 - 160) = 34mm → gap 17mm
       10 filas de 25mm + gap de 3mm → encaja en 277mm (297-20)
    */
    .labels-grid {{
      display: grid;
      grid-template-columns: 80mm 80mm;
      grid-template-rows: repeat(auto-fill, 25mm);
      gap: 3mm 17mm;
      width: 194mm;
      margin: 0 auto;
    }}

    /* ── Etiqueta base ───────────────────────────────────────────── */
    .label {{
      width: 80mm;
      height: 25mm;
      background-color: #FFE500;
      border: 2pt solid #0033A0;
      border-radius: 2mm;
      display: flex;
      flex-direction: row;
      align-items: stretch;
      overflow: hidden;
      page-break-inside: avoid;
    }}

    /* ── Columna izquierda: flecha vertical ─────────────────────── */
    .arrow-col {{
      width: 16mm;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5mm;
      padding: 1.5mm 0;
      flex-shrink: 0;
    }}

    .flecha {{
      font-size: 18pt;
      font-weight: 900;
      line-height: 1;
    }}

    .dir-label {{
      font-size: 5pt;
      font-weight: 800;
      letter-spacing: 0.3pt;
      text-transform: uppercase;
      text-align: center;
      line-height: 1.1;
    }}

    .dir-delante {{
      color: #001F6B;
    }}

    .dir-detras {{
      color: #0044BB;
    }}

    /* ── Divisor vertical ───────────────────────────────────────── */
    .divider {{
      width: 1pt;
      background-color: #0033A0;
      opacity: 0.35;
      margin: 3mm 0;
      flex-shrink: 0;
    }}

    /* ── Columna derecha: código + tipo ─────────────────────────── */
    .content-col {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1mm 3mm;
      gap: 0.8mm;
    }}

    /* Mazos: sin flecha, ocupa todo el ancho */
    .content-full {{
      padding: 1mm 5mm;
    }}

    .codigo {{
      color: #0033A0;
      font-size: 21pt;
      font-weight: 900;
      letter-spacing: 1.5pt;
      line-height: 1;
      text-align: center;
      white-space: nowrap;
    }}

    /* Mazos: código más grande al no tener flecha */
    .label-mazo .codigo {{
      font-size: 23pt;
      letter-spacing: 2pt;
    }}

    .sub {{
      color: #0033A0;
      font-size: 6.5pt;
      font-weight: 700;
      letter-spacing: 1.2pt;
      text-transform: uppercase;
      opacity: 0.8;
      text-align: center;
    }}

    /* ── Corte de página ────────────────────────────────────────── */
    .page-break {{
      page-break-after: always;
      height: 0;
    }}

    /* ── Instrucción en pantalla (no se imprime) ────────────────── */
    .instructions {{
      font-family: Arial, sans-serif;
      font-size: 12px;
      color: #333;
      background: #f0f4ff;
      border: 1px solid #0033A0;
      border-radius: 6px;
      padding: 12px 16px;
      margin-bottom: 12mm;
      max-width: 194mm;
      margin-left: auto;
      margin-right: auto;
    }}
    .instructions b {{ color: #0033A0; }}
    @media print {{
      .instructions {{ display: none; }}
    }}
  </style>
</head>
<body>

  <div class="instructions">
    <b>Instrucciones de impresión:</b><br>
    1. Pulsa <b>Ctrl+P</b> (o Archivo → Imprimir).<br>
    2. Selecciona papel <b>A4</b>, orientación <b>Vertical</b>.<br>
    3. Activa <b>"Gráficos de fondo" / "Imprimir fondos"</b> para que salga el color amarillo.<br>
    4. Márgenes: <b>Mínimo</b> o <b>Ninguno</b> (el HTML ya los gestiona).<br>
    5. Guarda como PDF o imprime directamente.<br>
    <br>
    <b>Total:</b> {len(ubicaciones)} etiquetas &nbsp;·&nbsp;
    <b>Tamaño:</b> 80 × 25 mm &nbsp;·&nbsp;
    <b>Páginas aprox.:</b> {-(-len(ubicaciones) // 20)}
  </div>

  <div class="labels-grid">
{etiquetas_html}
  </div>

</body>
</html>
"""

# ── Guardar y abrir ────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Archivo generado: {OUTPUT_FILE}")
print(f"  {len(ubicaciones)} etiquetas  |  {-(-len(ubicaciones) // 20)} páginas A4")
print()
print("Abriendo en el navegador...")
webbrowser.open(f"file:///{OUTPUT_FILE.replace(os.sep, '/')}")
print("Usa Ctrl+P en el navegador → 'Imprimir fondos' activo → Guardar como PDF")
