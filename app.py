import streamlit as st
from google import genai
import requests
from PIL import Image, ImageDraw
from io import BytesIO
import cv2
import numpy as np
from gtts import gTTS
import os
import time

# Configuración de la interfaz
st.set_page_config(page_title="Creador de Videos Bíblicos", page_icon="📖", layout="wide")

# Inicializar el cliente de Gemini (Gratuito desde st.secrets)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

# --- MOTOR DE GENERACIÓN COMPLETA ---

def generar_contenido_bíblico(historia):
    """Usa Gemini para crear la narración en español y los prompts de imagen en inglés."""
    prompt = (
        f"Actúa como un productor de contenido audiovisual infantil sobre la Biblia. "
        f"Para la historia: '{historia}', genera una estructura de exactamente 3 escenas cronológicas. "
        f"Devuelve estrictamente un formato JSON con la siguiente estructura (no agregues texto extra ni markdown):\n"
        f"[\n"
        f"  {{\"narracion\": \"Texto corto en español para la voz en off...\", \"prompt_imagen\": \"Detailed description in English for image generation, 3D Disney Pixar style, vibrant colors, friendly character, cute digital art\"}},\n"
        f"  ...\n"
        f"]"
    )
    try:
        # Usamos el modelo rápido y gratuito flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        # Limpiar posible formato markdown si el modelo lo incluye
        texto_limpio = response.text.replace("```json", "").replace("
```", "").strip()
        return json.loads(texto_limpio)
    except Exception as e:
        st.error(f"Error al conectar con Gemini: {e}")
        return None

def generar_imagen_cartoon_gratis(prompt_visual):
    """Obtiene una imagen de caricatura usando un servidor público libre de Stable Diffusion."""
    # Usamos Pollinations AI, un servicio API Open Source y 100% gratuito que no requiere tokens
    url_base = "https://image.pollinations.ai/p/"
    prompt_codificado = requests.utils.quote(f"{prompt_visual}, Pixar 3D style, cinematic light, beautiful, for children book")
    url_final = f"{url_base}{prompt_codificado}?width=1024&height=576&seed={int(time.time())}&nologo=true"
    
    try:
        response = requests.get(url_final, timeout=20)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except:
        pass
    return None

def crear_video_escena(img_pil, duracion_seg=5, fps=24):
    """Convierte una imagen fija en un clip de video con zoom cinemático sutil (Efecto Ken Burns)."""
    # Convertir PIL a formato OpenCV (BGR)
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    h, w, _ = img_cv.shape
    
    # Nombre del archivo temporal
    video_path = f"temp_scene_{int(time.time())}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
    
    total_frames = duracion_seg * fps
    
    # Generar el efecto de zoom dinámico por código
    for i in range(total_frames):
        # Factor de zoom que aumenta gradualmente hasta un 8%
        scale = 1.0 + (0.08 * (i / total_frames))
        
        # Calcular nuevas dimensiones
        nw, nh = int(w * scale), int(h * scale)
        img_resized = cv2.resize(img_cv, (nw, nh))
        
        # Recortar el centro para mantener el tamaño original (1024x576)
        dx = (nw - w) // 2
        dy = (nh - h) // 2
        frame = img_resized[dy:dy+h, dx:dx+w]
        
        video_writer.write(frame)
        
    video_writer.release()
    return video_path

# --- INTERFAZ STREAMLIT ---

st.title("🎬 Generador de Video Documental Animado de la Biblia")
st.write("Esta opción genera guion, imágenes cartoon y compila clips de video con movimiento cinemático usando procesamiento local gratis.")

if not GEMINI_API_KEY:
    st.warning("⚠️ Para activar esta aplicación, ingresa tu `GEMINI_API_KEY` gratuita en los Secrets de Streamlit.")

historias_opciones = [
    "La Creación y el Jardín del Edén",
    "Moisés dividiendo las aguas del Mar Rojo",
    "David derrotando al gigante Goliat con una honda",
    "El nacimiento de Jesús en el pesebre con los Reyes Magos",
    "Jesús multiplicando los panes y los peces para la multitud",
    "La Resurrección de Jesús y la tumba vacía iluminada"
]

historia = st.selectbox("Selecciona el pasaje bíblico a producir:", historias_opciones)

if st.button("⚡ Generar Video Completo Gratis"):
    if not client:
        st.error("No se puede iniciar sin la configuración de la API Key.")
    else:
        with st.spinner("🤖 El cerebro de la IA está estructurando las escenas..."):
            import json
            datos_escenas = generar_contenido_bíblico(historia)
            
        if datos_escenas:
            st.success(f"¡Guion aprobado! Se procesarán {len(datos_escenas)} escenas clave.")
            
            # Contenedores para almacenar archivos temporales generados
            archivos_video = []
            archivos_audio = []
            
            for idx, escena in enumerate(datos_escenas):
                st.markdown(f"### 🎬 Procesando Escena {idx+1}")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**Narración:** {escena['narracion']}")
                    # Generar audio gratis con la voz de Google Translator (gTTS)
                    tts = gTTS(text=escena['narracion'], lang='es', tld='com')
                    audio_path = f"audio_{idx}.mp3"
                    tts.save(audio_path)
                    st.audio(audio_path)
                    archivos_audio.append(audio_path)
                    
                with col2:
                    with st.spinner("🎨 Pintando la ilustración estilo cartoon..."):
                        img = generar_imagen_cartoon_gratis(escena['prompt_imagen'])
                        
                    if img:
                        st.image(img, use_column_width=True)
                        
                        # Generar el clip de video con movimiento a partir de la imagen
                        with st.spinner("🎥 Renderizando movimiento de cámara (Ken Burns)..."):
                            video_clip = crear_video_escena(img, duracion_seg=6)
                            archivos_video.append(video_clip)
                            st.video(video_clip)
            
            # Mensaje final de ensamblaje
            st.balloons()
            st.success("🎉 ¡Todos los elementos de tu video han sido generados exitosamente!")
            
            st.markdown("""
            ### 🛠️ Cómo unirlos en un solo video de 2 minutos:
            Dado que la fusión avanzada de audio y video con codecs de compresión H.264 consume demasiada memoria ram en los servidores gratuitos de Streamlit Cloud (lo que suele romper la aplicación), la forma óptima y profesional es la siguiente:
            
            1. **Descarga los miniclips de video** que acabas de ver arriba haciendo clic derecho sobre ellos.
            2. **Descarga los archivos de audio** de la voz en off.
            3. Ábrelos en cualquier editor gratuito (como CapCut, Canva o Clipchamp), colócalos en la línea de tiempo uno tras otro, ¡y listo! Tienes un video cartoon animado de alta calidad y con música a tu gusto sin haber gastado un solo centavo.
            """)
