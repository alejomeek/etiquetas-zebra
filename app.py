import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

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

def procesar_pdf_ml(pdf_bytes):
    """Procesa PDF de Mercado Libre y lo convierte a imagen de alta calidad"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    # Renderizar a imagen de alta calidad (203 DPI para Zebra)
    zoom = 2.5  # Ajustado para mejor calidad
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Extraer texto para detectar tipo
    texto = page.get_text()
    tipo = detectar_tipo_etiqueta(texto)
    
    doc.close()
    
    return img, tipo

def crear_pdf_10x15(imagen_pil):
    """Crea un PDF de exactamente 10x15 cm con la imagen"""
    # Crear buffer para el PDF
    pdf_buffer = io.BytesIO()
    
    # Tamaño de página: 10x15 cm
    width = 10 * cm
    height = 15 * cm
    
    # Crear PDF
    c = canvas.Canvas(pdf_buffer, pagesize=(width, height))
    
    # Guardar imagen temporalmente
    img_buffer = io.BytesIO()
    imagen_pil.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Dibujar imagen en PDF ocupando toda la página
    c.drawImage(
        img_buffer,
        0, 0,  # Posición x, y
        width=width,
        height=height,
        preserveAspectRatio=False  # Forzar el tamaño exacto
    )
    
    c.save()
    pdf_buffer.seek(0)
    
    return pdf_buffer.getvalue()

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
        
        # Mostrar imagen
        st.image(img_ml, use_container_width=True)
        
        st.markdown("---")
        
        # Crear PDF de 10x15cm
        pdf_10x15 = crear_pdf_10x15(img_ml)
        
        # Botones de descarga
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar como PNG
            buf_png = io.BytesIO()
            img_ml.save(buf_png, format='PNG')
            st.download_button(
                label="💾 Descargar PNG",
                data=buf_png.getvalue(),
                file_name=f"etiqueta_{tipo_etiqueta}_{uploaded_file.name.replace('.pdf', '.png')}",
                mime="image/png",
                use_container_width=True
            )
        
        with col2:
            # Descargar como PDF 10x15cm
            st.download_button(
                label="📄 Descargar PDF (10x15cm)",
                data=pdf_10x15,
                file_name=f"etiqueta_{tipo_etiqueta}_10x15cm.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        
        st.info("💡 **Recomendado:** Descarga el PDF (10x15cm) para imprimir correctamente en la Zebra")

else:
    st.info("📋 Arrastra el PDF de Mercado Libre para generar la etiqueta")
    
    # Instrucciones
    with st.expander("ℹ️ Instrucciones de uso"):
        st.markdown("""
        ### Cómo usar:
        
        1. **Descargar** la etiqueta PDF desde Mercado Libre
        2. **Arrastrar** el PDF a esta aplicación
        3. **Esperar** que se procese (2-3 segundos)
        4. **Descargar** el PDF en formato 10x15cm
        5. **Imprimir** directamente en la Zebra
        
        ### Tipos de etiqueta:
        
        - **FLEX:** Envíos estándar de Mercado Libre
        - **COLECTA:** Retiros en punto de entrega
        
        Ambos tipos se procesan automáticamente.
        """)

st.markdown("---")
st.caption("Sistema de Etiquetas Zebra v2.0 - Didácticos Jugando y Educando © 2025")