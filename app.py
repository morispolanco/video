import streamlit as st
import requests
import os
import time
from gtts import gTTS

# Importaciones definitivas y corregidas para MoviePy v2.x
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.util import concatenate_videoclips

from PIL import Image
from io import BytesIO

# Configuración de la página de Streamlit
st.set_page_config(page_title="Creador de Videos Bíblicos", page_icon="📖", layout="wide")

# ----------------------------------------------------------------------
# CONFIGURACIÓN Y CONTENIDO BÍBLICO
# ----------------------------------------------------------------------
st.sidebar.title("Configuración de IA")

# Intenta leer desde Secrets, si no existe, muestra el campo en la barra lateral
if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    st.sidebar.success("🔒 Token cargado desde los Secrets de Streamlit.")
else:
    HF_TOKEN = st.sidebar.text_input("Introduce tu Hugging Face Token (HF_...)", type="password")

HISTORIAS = {
    "Génesis: La Creación": [
        "En el principio, Dios creó los cielos y la tierra, y todo estaba en oscuridad.",
        "Entonces Dios dijo: Sea la luz, y la luz separó el día de la noche.",
        "Dios creó los mares, la tierra firme y la llenó de vegetación y árboles frutales.",
        "Finalmente, Dios creó al hombre y a la mujer a su imagen y semejanza para cuidar de la creación."
    ],
    "Génesis: El Arca de Noé": [
        "La tierra se llenó de maldad, pero Noé halló gracia ante los ojos de Dios.",
        "Dios le ordenó a Noé construir un gran arca para salvar a su familia y a los animales.",
        "Comenzó a llover por cuarenta días y cuarenta noches, cubriendo toda la tierra.",
        "Al final, el arca reposó y un arcoíris apareció en el cielo como promesa de Dios."
    ],
    "Evangelios: El Nacimiento de Jesús": [
        "Un ángel visitó a María para anunciarle que daría a luz al Salvador del mundo.",
        "Jesús nació en un humilde pesebre en Belén, porque no había lugar en el mesón.",
        "Pastores en el campo vieron ángeles cantar en los cielos celebrando su nacimiento.",
        "Sabios del oriente siguieron una estrella brillante para adorar al nuevo Rey."
    ],
    "Evangelios: Los Milagros de Jesús": [
        "Jesús recorrió Galilea enseñando y sanando a toda clase de enfermos.",
        "En una tormenta en el mar, Jesús se levantó y le ordenó al viento y al agua que se calmaran.",
        "Con solo cinco panes y dos peces, Jesús alimentó a más de cinco mil personas.",
        "Jesús demostró su poder sobre la muerte al resucitar a su amigo Lázaro."
    ]
}

# ----------------------------------------------------------------------
# FUNCIONES DE GENERACIÓN
# ----------------------------------------------------------------------

def query_hugging_face(prompt, token):
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {token}"}
    style_prompt = f"Cinematic biblical art, dramatic lighting, detailed oil painting, highly realistic, masterwork, {prompt}"
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": style_prompt}, timeout=30)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            st.error(f"Error de API ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión con Hugging Face: {e}")
        return None

def crear_video_biblico(escenas, token, nombre_salida):
    clips_de_video = []
    progreso = st.progress(0)
    total_escenas = len(escenas)
    
    # Directorio temporal seguro para Linux en la nube
    temp_dir = "/tmp/video_gen"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    status_text = st.empty()

    for idx, texto in enumerate(escenas):
        status_text.write(f"🎬 Procesando Escena {idx + 1}/{total_escenas}...")
        
        # 1. Generar Audio (gTTS)
        audio_path = f"{temp_dir}/audio_{idx}.mp3"
        tts = gTTS(text=texto, lang='es', tld='com.mx')
        tts.save(audio_path)
        
        # 2. Generar Imagen (Hugging Face)
        prompt_imagen = f"Biblical scene: {texto}"
        imagen = query_hugging_face(prompt_imagen, token)
        if imagen is None:
            return None
            
        img_path = f"{temp_dir}/image_{idx}.png"
        imagen.save(img_path)
        
        # 3. Ensamblar Clip Individual usando sintaxis v2.x (.with_...)
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration
        
        video_clip = ImageClip(img_path).with_duration(duracion)
        video_clip = video_clip.with_audio(audio_clip)
        
        clips_de_video.append(video_clip)
        progreso.progress(int((idx + 1) / total_escenas * 100))
        time.sleep(1) # Respetar límites de la API gratuita

    status_text.write("🎥 Concatenando y renderizando el MP4 final...")
    
    # Concatenación usando el submódulo .util correctamente importado arriba
    video_final = concatenate_videoclips(clips_de_video, method="compose")
    
    path_final = f"{temp_dir}/{nombre_salida}"
    
    # Exportación optimizada para servidores headless (sin monitor)
    video_final.write_videofile(
        path_final, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        logger=None # Evita saturar la consola de Streamlit Cloud
    )
    
    # Cierre de archivos para liberar memoria del servidor
    for clip in clips_de_video:
        clip.close()
    video_final.close()
    
    return path_final

# ----------------------------------------------------------------------
# INTERFAZ DE USUARIO
# ----------------------------------------------------------------------

st.title("📖 Creador Automático de Videos Bíblicos")
st.subheader("Generación de videos MP4 optimizada para Streamlit Cloud.")

if not HF_TOKEN:
    st.warning("🔑 Introduce tu Token de Hugging Face en la barra lateral para desbloquear la aplicación.")

categoria = st.selectbox("Selecciona la historia bíblica:", list(HISTORIAS.keys()))
escenas_seleccionadas = HISTORIAS[categoria]

with st.expander("Ver pasajes que compondrán el video"):
    for i, escena in enumerate(escenas_seleccionadas):
        st.markdown(f"**Escena {i+1}:** {escena}")

if st.button("🚀 Iniciar Generación de Video", disabled=not HF_TOKEN):
    with st.spinner("La IA está renderizando tus imágenes y locuciones. Esto puede demorar unos minutos..."):
        
        # Multiplicamos por 3 el bloque de texto para alcanzar la meta de los 2-3 minutos
        escenas_extendidas = escenas_seleccionadas * 3  
        nombre_archivo = f"{categoria.replace(' ', '_').replace(':', '')}.mp4"
        
        video_resultado = crear_video_biblico(escenas_extendidas, HF_TOKEN, nombre_archivo)
        
        if video_resultado and os.path.exists(video_resultado):
            st.success("¡Tu video está listo! 🎉")
            
            # Vista previa en la nube
            st.video(video_resultado)
            
            # Botón de descarga directa
            with open(video_resultado, "rb") as file:
                st.download_button(
                    label="⬇️ Descargar Video MP4",
                    data=file,
                    file_name=nombre_archivo,
                    mime="video/mp4"
                )
