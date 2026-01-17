import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Etiquetas Zebra",
    page_icon="🏷️",
    layout="wide"
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

# Cargar credenciales desde Streamlit Secrets
try:
    WIX_API_KEY = st.secrets["wix"]["api_key"]
    WIX_SITE_ID = st.secrets["wix"]["site_id"]
except:
    st.error("⚠️ Configuración de Wix no encontrada. Por favor configura los secrets en Streamlit Cloud.")
    WIX_API_KEY = None
    WIX_SITE_ID = None

# Datos de la empresa
EMPRESA_INFO = {
    "nombre": "DIDÁCTICOS JUGANDO Y EDUCANDO SAS",
    "nit": "NIT 901,144,615-6",
    "direccion": "CC Bulevar - Local S113, Bogotá",
    "celular": "Celular 3134285423",
    "logo_path": "Logo-Rectangular.jpg"
}

# ============== FUNCIONES PARA ETIQUETAS ML ==============
def detectar_tipo_etiqueta(texto):
    """Detecta si la etiqueta es FLEX o Colecta"""
    texto_lower = texto.lower()
    if 'colecta' in texto_lower or 'punto de' in texto_lower:
        return 'colecta'
    else:
        return 'flex'

def procesar_pdf_ml(pdf_bytes):
    """Procesa PDF de Mercado Libre y lo convierte a imagen"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    # Renderizar a imagen de alta calidad
    zoom = 3
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Extraer texto para detectar tipo
    texto = page.get_text()
    tipo = detectar_tipo_etiqueta(texto)
    
    doc.close()
    
    return img, tipo

# ============== FUNCIONES PARA ETIQUETAS WIX ==============
def obtener_pedidos_wix():
    """Obtiene pedidos de Wix usando eCommerce API v1"""
    if not WIX_API_KEY:
        st.error("Credenciales de Wix no configuradas")
        return []
    
    try:
        headers = {
            'Authorization': WIX_API_KEY,
            'wix-site-id': WIX_SITE_ID,
            'Content-Type': 'application/json'
        }
        
        url = "https://www.wixapis.com/ecom/v1/orders/search"
        
        payload = {
            "search": {
                "cursorPaging": {
                    "limit": 100
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            pedidos = data.get('orders', [])
            return pedidos
        else:
            st.error(f"Error al conectar con Wix: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def generar_etiqueta_wix(pedido_data):
    """Genera una etiqueta de Wix con logo grande y textos grandes"""
    # Crear imagen base (10x15 cm a 203 DPI)
    width_px = int(10 * 203 / 2.54)   # ~800 px
    height_px = int(15 * 203 / 2.54)  # ~1200 px
    
    img = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(img)
    
    # PASO 1: Cargar y medir logo
    logo_height = 0
    try:
        if os.path.exists(EMPRESA_INFO['logo_path']):
            logo = Image.open(EMPRESA_INFO['logo_path'])
            # Logo GRANDE: 350px de ancho
            logo_width = 350
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    except:
        pass
    
    # Calcular líneas de dirección
    try:
        direccion = pedido_data['direccion'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['direccion'], str) else str(pedido_data['direccion'])
    except:
        direccion = str(pedido_data['direccion'])
    direccion_lines = direccion.split('\n') if '\n' in direccion else [direccion]
    num_lineas_dir = len([l for l in direccion_lines if l.strip()])
    
    # Calcular si hay observaciones
    tiene_obs = bool(pedido_data.get('observaciones') and str(pedido_data.get('observaciones')).strip())
    
    # Altura total del contenido
    altura_contenido = (
        logo_height +
        30 +
        (34 * 4) +
        30 +
        3 +
        40 +
        50 +
        48 +
        (44 * num_lineas_dir) +
        55 +
        55 +
        (72 if tiene_obs else 0)
    )
    
    # Calcular margen superior para centrar
    margen_superior = (height_px - altura_contenido) // 2
    margen_superior = max(30, margen_superior)
    
    # PASO 2: Pegar logo centrado horizontalmente
    logo_y = margen_superior
    logo_height_final = 0
    try:
        if os.path.exists(EMPRESA_INFO['logo_path']):
            logo = Image.open(EMPRESA_INFO['logo_path'])
            logo_width = 350
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            logo_x = (width_px - logo_width) // 2
            img.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
            logo_height_final = logo_height
    except:
        pass
    
    # Fuentes grandes
    try:
        font_empresa = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        font_destinatario = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
        font_celular = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
        font_direccion = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
        font_ciudad = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
        font_pedido = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
        font_obs = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 32)
        font_obs_label = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32)
    except:
        try:
            font_empresa = ImageFont.truetype("arialbd.ttf", 28)
            font_destinatario = ImageFont.truetype("arialbd.ttf", 40)
            font_celular = ImageFont.truetype("arial.ttf", 36)
            font_direccion = ImageFont.truetype("arial.ttf", 36)
            font_ciudad = ImageFont.truetype("arialbd.ttf", 36)
            font_pedido = ImageFont.truetype("arialbd.ttf", 36)
            font_obs = ImageFont.truetype("arial.ttf", 32)
            font_obs_label = ImageFont.truetype("arialbd.ttf", 32)
        except:
            font_empresa = ImageFont.load_default()
            font_destinatario = ImageFont.load_default()
            font_celular = ImageFont.load_default()
            font_direccion = ImageFont.load_default()
            font_ciudad = ImageFont.load_default()
            font_pedido = ImageFont.load_default()
            font_obs = ImageFont.load_default()
            font_obs_label = ImageFont.load_default()
    
    # Dibujar contenido
    margin_left = 30
    y = logo_y + logo_height_final + 30
    
    # Información de la empresa
    empresa_lines = [
        EMPRESA_INFO['nombre'],
        EMPRESA_INFO['nit'],
        EMPRESA_INFO['direccion'],
        EMPRESA_INFO['celular']
    ]
    
    for line in empresa_lines:
        try:
            line_text = line.encode('latin-1').decode('utf-8') if isinstance(line, str) else str(line)
        except:
            line_text = str(line)
        draw.text((margin_left, y), line_text, font=font_empresa, fill=(0, 0, 0))
        y += 34
    
    # Línea separadora
    y += 30
    draw.line([(margin_left, y), (width_px - 30, y)], fill=(0, 0, 0), width=3)
    y += 40
    
    # Destinatario
    try:
        nombre = pedido_data['nombre'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['nombre'], str) else str(pedido_data['nombre'])
    except:
        nombre = str(pedido_data['nombre'])
    draw.text((margin_left, y), f"Destinatario: {nombre}", font=font_destinatario, fill=(0, 0, 0))
    y += 50
    
    # Celular
    try:
        celular = pedido_data['celular'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['celular'], str) else str(pedido_data['celular'])
    except:
        celular = str(pedido_data['celular'])
    draw.text((margin_left, y), f"Celular: {celular}", font=font_celular, fill=(0, 0, 0))
    y += 48
    
    # Dirección
    direccion_lines = direccion.split('\n') if '\n' in direccion else [direccion]
    
    draw.text((margin_left, y), f"Dirección: {direccion_lines[0].strip()}", font=font_direccion, fill=(0, 0, 0))
    y += 44
    
    for i, line in enumerate(direccion_lines[1:]):
        if line.strip():
            draw.text((margin_left + 140, y), line.strip(), font=font_direccion, fill=(0, 0, 0))
            y += 44
    
    # Ciudad
    try:
        ciudad = pedido_data['ciudad'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['ciudad'], str) else str(pedido_data['ciudad'])
    except:
        ciudad = str(pedido_data['ciudad'])
    draw.text((margin_left, y), f"Ciudad: {ciudad}", font=font_ciudad, fill=(0, 0, 0))
    y += 55
    
    # Número de pedido
    try:
        numero_pedido = pedido_data['numero_pedido'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['numero_pedido'], str) else str(pedido_data['numero_pedido'])
    except:
        numero_pedido = str(pedido_data['numero_pedido'])
    draw.text((margin_left, y), f"Pedido: #{numero_pedido}", font=font_pedido, fill=(0, 0, 0))
    y += 55
    
    # Observaciones
    if pedido_data.get('observaciones'):
        try:
            observaciones = pedido_data['observaciones'].encode('latin-1').decode('utf-8') if isinstance(pedido_data['observaciones'], str) else str(pedido_data['observaciones'])
        except:
            observaciones = str(pedido_data['observaciones'])
            
        if observaciones.strip():
            draw.text((margin_left, y), "Observaciones:", font=font_obs_label, fill=(0, 0, 0))
            y += 38
            
            max_chars = 35
            obs_lines = [observaciones[i:i+max_chars] for i in range(0, len(observaciones), max_chars)]
            for obs_line in obs_lines[:3]:
                draw.text((margin_left, y), obs_line, font=font_obs, fill=(0, 0, 0))
                y += 36
    
    return img

# ============== INTERFAZ PRINCIPAL ==============
st.title("🏷️ Sistema de Etiquetas Zebra")
st.markdown("**Didácticos Jugando y Educando**")

# Tabs principales
tab1, tab2 = st.tabs(["📦 Mercado Libre", "🛒 Wix Commerce"])

# ============== TAB MERCADO LIBRE ==============
with tab1:
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
            
            if tipo_etiqueta == 'flex':
                st.success("✅ Etiqueta FLEX detectada")
            else:
                st.info("ℹ️ Etiqueta COLECTA detectada")
            
            st.image(img_ml, use_container_width=True)
            
            # Botón de descarga
            buf = io.BytesIO()
            img_ml.save(buf, format='PNG')
            st.download_button(
                label="💾 Descargar Etiqueta",
                data=buf.getvalue(),
                file_name=f"etiqueta_{tipo_etiqueta}_{uploaded_file.name.replace('.pdf', '.png')}",
                mime="image/png"
            )
    else:
        st.info("📋 Arrastra el PDF de Mercado Libre para generar la etiqueta")

# ============== TAB WIX ==============
with tab2:
    st.header("🛒 Pedidos Wix Commerce")
    
    if not WIX_API_KEY:
        st.warning("⚠️ Configura las credenciales de Wix en los Secrets de Streamlit Cloud")
    else:
        if st.button("🔄 Actualizar Pedidos", type="primary"):
            with st.spinner("Cargando..."):
                st.session_state.pedidos_wix = obtener_pedidos_wix()
        
        if 'pedidos_wix' in st.session_state and st.session_state.pedidos_wix:
            st.markdown(f"### 📋 {len(st.session_state.pedidos_wix)} pedidos disponibles:")
            
            for idx, pedido in enumerate(st.session_state.pedidos_wix):
                # Extraer información del pedido
                numero_pedido = pedido.get('number', 'N/A')
                billing = pedido.get('billingInfo', {})
                shipping = pedido.get('shippingInfo', {})
                
                # Nombre del cliente
                contact_details = billing.get('contactDetails', {})
                nombre = f"{contact_details.get('firstName', '')} {contact_details.get('lastName', '')}".strip()
                if not nombre:
                    nombre = "Sin nombre"
                
                # Dirección de envío
                shipping_dest = shipping.get('logistics', {}).get('shippingDestination', {})
                address = shipping_dest.get('address', {})
                ciudad = address.get('city', 'N/A')
                
                # Precio total
                price_summary = pedido.get('priceSummary', {})
                total_obj = price_summary.get('total', {})
                
                if isinstance(total_obj, dict):
                    total_amount = total_obj.get('amount', '0')
                else:
                    total_amount = total_obj
                
                try:
                    total_formatted = f"${float(total_amount):,.0f}"
                except:
                    total_formatted = str(total_amount)
                
                # Estado del pedido
                fulfillment_status = pedido.get('fulfillmentStatus', 'N/A')
                
                with st.expander(f"#{numero_pedido} - {nombre} - {ciudad} - {total_formatted} COP | {fulfillment_status}"):
                    # Campo de observaciones
                    observaciones_manual = st.text_input(
                        "📝 Observaciones (opcional):",
                        value="",
                        key=f"obs_{idx}",
                        placeholder="Ej: Contraentrega, Llamar antes, etc."
                    )
                    
                    if st.button(f"🏷️ Generar Etiqueta #{numero_pedido}", key=f"gen_{idx}"):
                        # Preparar datos para la etiqueta
                        shipping_contact = shipping_dest.get('contactDetails', {})
                        
                        pedido_data = {
                            'nombre': nombre,
                            'celular': shipping_contact.get('phone', contact_details.get('phone', 'N/A')),
                            'direccion': f"{address.get('addressLine', '')}\n{address.get('addressLine2', '')}".strip() or "Sin dirección",
                            'ciudad': ciudad,
                            'numero_pedido': numero_pedido,
                            'observaciones': observaciones_manual
                        }
                        
                        # Generar etiqueta
                        img_etiqueta = generar_etiqueta_wix(pedido_data)
                        
                        # Guardar en session_state
                        st.session_state[f'etiqueta_{idx}'] = img_etiqueta
                    
                    # Mostrar preview si existe
                    if f'etiqueta_{idx}' in st.session_state:
                        img_etiqueta = st.session_state[f'etiqueta_{idx}']
                        
                        st.subheader("Vista Previa")
                        st.image(img_etiqueta, use_container_width=True)
                        
                        # Botón de descarga
                        buf = io.BytesIO()
                        img_etiqueta.save(buf, format='PNG')
                        st.download_button(
                            label="💾 Descargar Etiqueta",
                            data=buf.getvalue(),
                            file_name=f"etiqueta_wix_{numero_pedido}.png",
                            mime="image/png",
                            key=f"download_{idx}"
                        )