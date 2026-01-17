import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import sys

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Etiquetas Zebra",
    page_icon="🏷️",
    layout="centered"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        font-weight: bold;
    }
    div[data-testid="stFileUploader"] {
        border: 2px dashed #3483fa;
        border-radius: 10px;
        padding: 20px;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def detectar_tipo_etiqueta(texto):
    """Detecta si la etiqueta es FLEX o Colecta"""
    texto_lower = texto.lower()
    if 'colecta' in texto_lower or 'punto de' in texto_lower:
        return 'colecta'
    else:
        return 'flex'

def detectar_bounding_box_etiqueta(page):
    """
    Detecta automáticamente el bounding box de la etiqueta en el PDF
    Busca el área con contenido (texto, imágenes, gráficos) ignorando espacios blancos
    """
    # Obtener el bbox de todos los elementos de la página
    # Esto incluye texto, imágenes y gráficos

    # Método 1: Usar el bbox del contenido de la página
    # Obtener todos los bloques de texto e imágenes
    blocks = page.get_text("dict")["blocks"]

    if not blocks:
        # Si no hay bloques, usar toda la página
        return page.rect

    # Calcular el bounding box que contiene todo el contenido
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for block in blocks:
        bbox = block.get("bbox")
        if bbox:
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

    # Si no encontramos nada, usar toda la página
    if min_x == float('inf'):
        return page.rect

    # Agregar un margen pequeño (5 puntos = ~1.76mm)
    margin = 5
    min_x = max(0, min_x - margin)
    min_y = max(0, min_y - margin)
    max_x = min(page.rect.width, max_x + margin)
    max_y = min(page.rect.height, max_y + margin)

    return fitz.Rect(min_x, min_y, max_x, max_y)

def generar_pdf_10x15cm(pdf_bytes):
    """
    Genera un PDF de exactamente 10x15cm con la etiqueta recortada
    - Detecta automáticamente el bounding box de la etiqueta
    - Recorta solo esa área
    - Crea un PDF nuevo de 10x15cm (283.46 x 425.20 puntos)
    - Escala proporcionalmente sin distorsión
    """
    # Dimensiones del PDF destino: 10x15cm = 283.46 x 425.20 puntos (a 72 DPI)
    TARGET_WIDTH = 283.46  # 10 cm
    TARGET_HEIGHT = 425.20  # 15 cm

    # Abrir el PDF original
    doc_original = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_original = doc_original[0]

    # Detectar el bounding box de la etiqueta
    label_bbox = detectar_bounding_box_etiqueta(page_original)

    # Calcular dimensiones de la etiqueta detectada
    label_width = label_bbox.width
    label_height = label_bbox.height

    # Calcular escala para ajustar al tamaño objetivo manteniendo proporción
    scale_x = TARGET_WIDTH / label_width
    scale_y = TARGET_HEIGHT / label_height
    scale = min(scale_x, scale_y)  # Usar la escala menor para mantener proporción

    # Crear un nuevo documento PDF con dimensiones exactas de 10x15cm
    doc_nuevo = fitz.open()
    page_nueva = doc_nuevo.new_page(width=TARGET_WIDTH, height=TARGET_HEIGHT)

    # Calcular las dimensiones escaladas
    scaled_width = label_width * scale
    scaled_height = label_height * scale

    # Centrar la etiqueta en la página (si es necesario)
    offset_x = (TARGET_WIDTH - scaled_width) / 2
    offset_y = (TARGET_HEIGHT - scaled_height) / 2

    # Crear un rectángulo destino en la página nueva
    target_rect = fitz.Rect(offset_x, offset_y, offset_x + scaled_width, offset_y + scaled_height)

    # Insertar la página original recortada en la nueva página
    # show_pdf_page permite recortar (clip) y escalar
    page_nueva.show_pdf_page(
        target_rect,  # Dónde colocar en la página nueva
        doc_original,  # Documento fuente
        0,  # Número de página fuente
        clip=label_bbox  # Área a recortar del original
    )

    # Convertir el documento nuevo a bytes
    pdf_output = doc_nuevo.tobytes(garbage=4, deflate=True)

    # Cerrar documentos
    doc_original.close()
    doc_nuevo.close()

    return pdf_output, label_bbox

def procesar_pdf_ml(pdf_bytes):
    """Procesa PDF de Mercado Libre para mostrar preview"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    # Renderizar a imagen solo para preview
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Extraer texto para detectar tipo
    texto = page.get_text()
    tipo = detectar_tipo_etiqueta(texto)
    
    doc.close()
    
    return img, tipo

# ============== INTERFAZ PRINCIPAL ==============
st.title("🏷️ Sistema de Etiquetas Zebra")
st.markdown("**Didácticos Jugando y Educando**")
st.markdown("---")

st.header("📦 Etiquetas Mercado Libre")

uploaded_file = st.file_uploader(
    "Arrastra o selecciona el PDF de Mercado Libre",
    type=['pdf'],
    help="Sube la etiqueta PDF descargada de Mercado Libre"
)

if uploaded_file:
    with st.spinner("Procesando etiqueta..."):
        pdf_bytes = uploaded_file.read()
        img_ml, tipo_etiqueta = procesar_pdf_ml(pdf_bytes)

        st.subheader("Vista Previa")

        # Mostrar tipo de etiqueta
        if tipo_etiqueta == 'flex':
            st.success("✅ Etiqueta FLEX detectada")
        else:
            st.info("ℹ️ Etiqueta COLECTA detectada")

        # Mostrar imagen preview
        st.image(img_ml, use_container_width=True)

        st.markdown("---")

        # Generar PDF de 10x15cm
        try:
            pdf_10x15cm, label_bbox = generar_pdf_10x15cm(pdf_bytes)

            # Mostrar información de detección
            with st.expander("ℹ️ Información de procesamiento"):
                st.write(f"**Bounding box detectado:**")
                st.write(f"- Posición: ({label_bbox.x0:.1f}, {label_bbox.y0:.1f}) - ({label_bbox.x1:.1f}, {label_bbox.y1:.1f}) puntos")
                st.write(f"- Dimensiones: {label_bbox.width:.1f} x {label_bbox.height:.1f} puntos")
                st.write(f"- Equivalente: {label_bbox.width/28.35:.1f} x {label_bbox.height/28.35:.1f} cm")
                st.write(f"**PDF generado:** 10 x 15 cm (283.46 x 425.20 puntos)")
                st.write(f"**Resolución:** 203 DPI para impresora térmica Zebra")
        except Exception as e:
            st.error(f"Error al generar PDF 10x15cm: {str(e)}")
            pdf_10x15cm = None

        # Botones de descarga
        col1, col2, col3 = st.columns(3)

        with col1:
            # Descargar como PNG (preview)
            buf_png = io.BytesIO()
            img_ml.save(buf_png, format='PNG')
            st.download_button(
                label="💾 PNG Preview",
                data=buf_png.getvalue(),
                file_name=f"etiqueta_{tipo_etiqueta}_{uploaded_file.name.replace('.pdf', '.png')}",
                mime="image/png",
                use_container_width=True
            )

        with col2:
            # Descargar PDF 10x15cm procesado
            if pdf_10x15cm:
                st.download_button(
                    label="🏷️ PDF 10x15cm",
                    data=pdf_10x15cm,
                    file_name=f"etiqueta_{tipo_etiqueta}_10x15cm.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

        with col3:
            # Descargar PDF ORIGINAL de ML
            st.download_button(
                label="📄 PDF Original",
                data=pdf_bytes,
                file_name=f"etiqueta_{tipo_etiqueta}_ML_original.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.success("✅ **Recomendado:** Descarga el **PDF 10x15cm** para imprimir en la Zebra GC420t")
        st.info("💡 El PDF ha sido recortado y ajustado automáticamente al tamaño de 10x15cm")

else:
    st.info("📋 Arrastra el PDF de Mercado Libre para procesarlo")
    
    # Instrucciones
    with st.expander("ℹ️ Instrucciones de uso"):
        st.markdown("""
        ### Cómo usar:

        1. **Descargar** la etiqueta PDF desde Mercado Libre
        2. **Arrastrar** el PDF a esta aplicación
        3. **Ver preview** de la etiqueta detectada
        4. **Descargar PDF 10x15cm** (recomendado para Zebra)
        5. **Imprimir** en la impresora térmica Zebra GC420t

        ### Tipos de etiqueta:

        - **FLEX:** Envíos estándar de Mercado Libre
        - **COLECTA:** Retiros en punto de entrega

        Ambos tipos se procesan automáticamente.

        ### ¿Qué hace el procesamiento automático?

        - **Detecta** automáticamente dónde está la etiqueta en el PDF
        - **Recorta** solo el área útil (sin espacios blancos)
        - **Genera** un PDF de exactamente 10x15cm
        - **Mantiene** la calidad a 203 DPI para impresión térmica
        - **Preserva** códigos de barras y QR codes escaneables

        ### ¿Cuál PDF descargar?

        - **PDF 10x15cm** (recomendado): Procesado automáticamente para Zebra GC420t
        - **PDF Original**: PDF sin procesar de Mercado Libre (tamaño carta)
        - **PNG Preview**: Solo para visualización, no para imprimir
        """)

st.markdown("---")
st.caption("Sistema de Etiquetas Zebra v3.0 - Didácticos Jugando y Educando © 2025")