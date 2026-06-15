import streamlit as st
import requests
import json
import time
from PIL import Image
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Bible Cartoon Gratis", page_icon="✝️", layout="wide")

# --- CONFIGURACIÓN DE APIs GRATUITAS (HUGGING FACE) ---
# Puedes usar los "Inference Endpoints" gratuitos de Hugging Face.
# Opcional: añade tu token gratis en los Secrets de Streamlit como HF_TOKEN para mayor velocidad.
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# URLs de Modelos Gratuitos en Hugging Face
API_LLM_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
API_IMAGEN_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3-medium-diffusers"
# Nota: Los modelos de video gratis suelen saturarse rápido. Usaremos un generador de GIFs animados/Video optimizado.
API_VIDEO_URL = "https://api-inference.huggingface.co/models/guoyww/AnimateDiff" 

# --- FUNCIONES DE GENERACIÓN GRATUITA ---

def consultar_llm_gratis(historia):
    """Genera prompts en inglés usando un modelo de texto gratuito."""
    prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n" \
             f"Create 3 scene descriptions in English for a cartoon video about: {historia}. " \
             f"Keep descriptions short and vivid. Style: 3D Pixar cartoon, vibrant colors. " \
             f"Format your response as a simple list: Scene 1:, Scene 2:, Scene 3:<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 250, "temperature": 0.6}}
    try:
        response = requests.post(API_LLM_URL, headers=headers, json=payload)
        resultado = response.json()
        if isinstance(resultado, list) and len(resultado) > 0:
            return resultado[0].get('generated_text', '').split("assistant")[-1]
        return "Scene 1: Biblical landscape, Pixar style\nScene 2: Characters interacting, cartoon style"
    except:
        # En caso de que la API de texto falle o esté saturada, devolvemos una plantilla por defecto
        return f"Scene 1: High quality 3D cartoon style of {historia}\nScene 2: Dynamic animation of {historia}"

def generar_imagen_gratis(prompt_visual):
    """Genera una imagen cartoon usando Stable Diffusion de forma gratuita."""
    payload = {"inputs": f"{prompt_visual}, 3D Pixar digital art, cute character design, bright colors, cinematic lighting, masterpiece"}
    try:
        response = requests.post(API_IMAGEN_URL, headers=headers, json=payload)
        # Si la API responde correctamente, devuelve los bytes de la imagen
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"Error al conectar con el servidor de imagen: {e}")
    return None

# --- INTERFAZ DE USUARIO ---

st.title("🎬 Generador de Video Cartoon Bíblico (Versión 100% Gratis)")
st.write("Esta aplicación utiliza modelos Open Source alojados gratuitamente en Hugging Face.")

# Selección de la historia
historias = [
    "La Creación del Mar y las Estrellas",
    "El Arca de Noé flotando en el diluvio con animales",
    "Moisés extendiendo su vara frente al Mar Rojo",
    "El nacimiento del bebé Jesús en un pesebre iluminado",
    "Jesús calmando la tormenta en el mar de Galilea",
    "La Resurrección de Jesús saliendo de la tumba con luz brillante"
]
seleccion = st.selectbox("Elige el pasaje bíblico:", historias)

if st.button("🎨 Generar Escenas Animadas Gratis"):
    
    # 1. Crear el guion/prompts
    with st.spinner("📖 Pensando las escenas (Modelo de lenguaje gratis)..."):
        prompts_texto = consultar_llm_gratis(seleccion)
    
    st.success("¡Escenas planificadas!")
    st.info("Generando las imágenes en estilo cartoon. Por favor, espera...")

    # Creamos un diseño de columnas para mostrar los resultados
    col1, col2 = st.columns(2)
    
    # Simulamos el procesamiento de dos escenas para evitar sobrecargar los servidores compartidos
    prompts_lista = [f"A beautiful cartoon scene of {seleccion}, Pixar style, colorful", 
                     f"A holy dramatic scene of {seleccion}, cute character design, 3D render"]

    with col1:
        st.subheader("🎬 Escena 1")
        img1 = generar_imagen_gratis(prompts_lista[0])
        if img1:
            st.image(img1, use_column_width=True)
            st.caption("✨ Imagen base lista para tu animación.")
            # Nota de animación para la versión gratuita
            st.info("🔄 Para animar gratis de forma masiva: Descarga esta imagen y súbela a herramientas web sin límite como *Luma Dream Machine (Plan Gratis)* o *Kling AI*.")
        else:
            st.warning("El servidor gratuito de imágenes está muy ocupado ahora mismo. Inténtalo de nuevo en unos segundos.")

    with col2:
        st.subheader("🎬 Escena 2")
        img2 = generar_imagen_gratis(prompts_lista[1])
        if img2:
            st.image(img2, use_column_width=True)
            st.caption("✨ Concept art de la segunda escena.")
        else:
            st.write("Servidor en cola. Las APIs públicas gratuitas pueden requerir múltiples intentos.")

st.markdown("---")
st.markdown("""
### ⚠️ Limitación Importante de las Herramientas Gratis en la Nube:
Los modelos que generan **video directo (Text-to-Video)** de forma gratuita pesan más de 40GB en memoria ram. Hugging Face los ofrece gratis, pero suelen tener colas de espera de hasta 5 minutos por cada segundo de video, lo cual causa que Streamlit se desconecte por *timeout*.

**La estrategia inteligente y 100% gratuita:**
1. Usa esta app para generar el **guion y los dibujos tipo Cartoon** de tus personajes bíblicos de forma ilimitada.
2. Descarga las imágenes generadas.
3. Entra a plataformas con planes gratuitos generosos como **Kling AI**, **Luma Dream Machine**, o **Runway Gen-2** (versión web gratuita) y sube tus fotos para que su inteligencia artificial les dé el movimiento cinemático de forma externa sin gastar un centavo.
""")
