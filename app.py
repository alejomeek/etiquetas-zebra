import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

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
        
        # Botones de descarga
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar como PNG (preview)
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
            # Descargar PDF ORIGINAL de ML
            st.download_button(
                label="📄 Descargar PDF Original",
                data=pdf_bytes,
                file_name=f"etiqueta_{tipo_etiqueta}_ML.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        
        st.success("✅ **Recomendado:** Descarga el PDF Original para imprimir en la Zebra")
        st.info("💡 El PDF original viene en el formato correcto de Mercado Libre")

else:
    st.info("📋 Arrastra el PDF de Mercado Libre para procesarlo")
    
    # Instrucciones
    with st.expander("ℹ️ Instrucciones de uso"):
        st.markdown("""
        ### Cómo usar:
        
        1. **Descargar** la etiqueta PDF desde Mercado Libre
        2. **Arrastrar** el PDF a esta aplicación
        3. **Ver preview** de la etiqueta
        4. **Descargar PDF Original** 
        5. **Imprimir** directamente en la Zebra desde Windows
        
        ### Tipos de etiqueta:
        
        - **FLEX:** Envíos estándar de Mercado Libre
        - **COLECTA:** Retiros en punto de entrega
        
        Ambos tipos se procesan automáticamente.
        
        ### ¿Por qué descargar el PDF Original?
        
        El PDF de Mercado Libre ya viene en el tamaño correcto.
        La conversión a imagen puede perder calidad o cambiar el tamaño.
        """)

st.markdown("---")
st.caption("Sistema de Etiquetas Zebra v2.0 - Didácticos Jugando y Educando © 2025")