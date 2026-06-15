import streamlit as st
import requests
import os
import time
from gtts import gTTS

# Importaciones clásicas de MoviePy (Estables y garantizadas con la versión 1.0.3 en requirements.txt)
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

from PIL import Image
from io import BytesIO

# Configuración de la página de Streamlit
st.set_page_config(page_title="Creador de Videos Bíblicos", page_icon="📖", layout="wide")

# ----------------------------------------------------------------------
# CONFIGURACIÓN Y CONTENIDO BÍBLICO
# ----------------------------------------------------------------------
st.sidebar.title("Configuración de IA")

if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    st.sidebar.success("🔒 Token cargado desde los Secrets de Streamlit.")
else:
    HF_TOKEN = st.sidebar.text_input("Introduce tu Hugging Face Token (HF_...)", type="password")

# Diccionario de traducción básico para optimizar los prompts enviados a la IA en inglés
DICCIONARIO_TRADUCCION = {
    "En el principio, Dios creó los cielos y la tierra, y todo estaba en oscuridad.": "In the beginning, God created the heavens and the earth, dramatic dark cosmic void, biblical art",
    "Entonces Dios dijo: Sea la luz, y la luz separó el día de la noche.": "God saying let there be light, holy light splitting the dark night, cosmic creation",
    "Dios creó los mares, la tierra firme y la llenó de vegetación y árboles frutales.": "God creating beautiful oceans, rich lands, lush vegetation and fruit trees, paradise",
    "Finalmente, Dios creó al hombre y a la mujer a su imagen y semejanza para cuidar de la creación.": "Creation of Adam and Eve in the beautiful garden of Eden, biblical illustration",
    "La tierra se llenó de maldad, pero Noé halló gracia ante los ojos de Dios.": "Noah praying under dramatic dark storm clouds, biblical times, cinematic lighting",
    "Dios le ordenó a Noé construir un gran arca para salvar a su familia y a los animales.": "Noah building a massive wooden ark, ancient tools, majestic structure",
    "Comenzó a llover por cuarenta días y cuarenta noches, cubriendo toda la tierra.": "The great flood, giant ark floating on huge ocean waves, heavy rain and storms",
    "Al final, el arca reposó y un arcoíris apareció en el cielo como promesa de Dios.": "Noah's ark resting on Mount Ararat, a beautiful bright rainbow spanning across the sky",
    "Un ángel visitó a María para anunciarle que daría a luz al Salvador del mundo.": "The Annunciation, angel Gabriel appearing to Virgin Mary, holy light, divine painting",
    "Jesús nació en un humilde pesebre en Belén, porque no había lugar en el mesón.": "The Nativity, baby Jesus in a humble manger, Mary and Joseph, cozy warm light",
    "Pastores en el campo vieron ángeles cantar en los cielos celebrando su nacimiento.": "Shepherds in the field looking up at a choir of angels singing in the starry night sky",
    "Sabios del oriente siguieron una estrella brillante para adorar al nuevo Rey.": "Three wise men, magi riding camels in the desert following a bright shining star",
    "Jesús recorrió Galilea enseñando y sanando a toda clase de enfermos.": "Jesus Christ healing people in ancient Galilee village, compassionate savior, detailed painting",
    "En una tormenta en el mar, Jesús se levantó y le ordenó al viento y al agua que se calmaran.": "Jesus calming the storm on a wooden boat, rough sea waves, dramatic cinematic lighting",
    "Con solo cinco panes y dos peces, Jesús alimentó a más de cinco mil personas.": "Miracle of the multiplication of loaves and fishes, Jesus feeding a large crowd",
    "Jesús demostró su poder sobre la muerte al resucitar a su amigo Lázaro.": "Resurrection of Lazarus, Jesus standing outside an ancient stone tomb, Lazarus coming out wrapped in cloths"
}

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

def query_hugging_face(prompt_es, token):
    # Usamos un endpoint de RealVisXL por ser sumamente estable, rápido y excelente para pasajes históricos
    API_URL = "https://api-inference.huggingface.co/models/SG161222/RealVisXL_V4.0"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Traducimos usando nuestro diccionario o dejamos una base descriptiva por defecto
    prompt_en = DICCIONARIO_TRADUCCION.get(prompt_es, f"Biblical illustration of: {prompt_es}")
    style_prompt = f"Cinematic biblical art, dramatic lighting, detailed oil painting, highly realistic, masterwork, 8k, {prompt_en}"
    
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"inputs": style_prompt}, 
                timeout=60  # Incrementamos el tiempo límite en la nube
            )
            
            if response.status_code == 503:
                # Si el modelo se está iniciando, esperamos un poco y reintentamos
                time.sleep(12)
                continue
                
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                st.error(f"Error de API Hugging Face (Código {response.status_code}): {response.text}")
                return None
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if intento < max_intentos - 1:
                st.warning(f"⚠️ Dificultad momentánea de red en la nube. Reintentando ({intento + 1}/{max_intentos})...")
                time.sleep(6)
            else:
                st.error("❌ Error de red persistente. Por favor, realiza un 'Reboot App' desde el menú de la esquina inferior derecha para limpiar los DNS del servidor.")
                return None
        except Exception as e:
            st.error(f"Error inesperado: {e}")
            return None
    return None

def crear_video_biblico(escenas, token, nombre_salida):
    clips_de_video = []
    progreso = st.progress(0)
    total_escenas = len(escenas)
    
    # Directorio temporal Linux
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
        imagen = query_hugging_face(texto, token)
        if imagen is None:
            status_text.error("⛔ Proceso interrumpido debido a fallos con el proveedor de imágenes.")
            return None
            
        img_path = f"{temp_dir}/image_{idx}.png"
        imagen.save(img_path)
        
        # 3. Ensamblar Clip Individual
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration
        
        video_clip = ImageClip(img_path).set_duration(duracion)
        video_clip = video_clip.with_audio(audio_clip) if hasattr(video_clip, 'with_audio') else video_clip.set_audio(audio_clip)
        
        clips_de_video.append(video_clip)
        progreso.progress(int((idx + 1) / total_escenas * 100))
        time.sleep(1.5)  # Margen de seguridad anti-saturación

    status_text.write("🎥 Concatenando y renderizando el MP4 final...")
    
    # Concatenación robusta
    video_final = concatenate_videoclips(clips_de_video, method="compose")
    path_final = f"{temp_dir}/{nombre_salida}"
    
    # Renderizado optimizado para la nube
    video_final.write_videofile(
        path_final, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        logger=None
    )
    
    # Liberar memoria física
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
    with st.spinner("La IA está renderizando tus imágenes y locuciones. Esto tomará unos minutos..."):
        
        # Multiplicamos la lista para alcanzar la meta de los 2-3 minutos en el video final
        escenas_extendidas = escenas_seleccionadas * 3  
        nombre_archivo = f"{categoria.replace(' ', '_').replace(':', '')}.mp4"
        
        video_resultado = crear_video_biblico(escenas_extendidas, HF_TOKEN, nombre_archivo)
        
        if video_resultado and os.path.exists(video_resultado):
            st.success("¡Tu video está listo! 🎉")
            
            # Reproductor integrado en pantalla
            st.video(video_resultado)
            
            # Botón de descarga
            with open(video_resultado, "rb") as file:
                st.download_button(
                    label="⬇️ Descargar Video MP4",
                    data=file,
                    file_name=nombre_archivo,
                    mime="video/mp4"
                )
