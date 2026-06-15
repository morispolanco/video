import streamlit as st
import requests
import os
import time
import urllib.parse
from gtts import gTTS

# Importaciones clásicas de MoviePy (Estables con versión 1.0.3 en requirements.txt)
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

from PIL import Image
from io import BytesIO

# Configuración de la página de Streamlit
st.set_page_config(page_title="Creador de Videos Bíblicos", page_icon="📖", layout="wide")

# ----------------------------------------------------------------------
# CONTENIDO BÍBLICO Y TRADUCCIONES
# ----------------------------------------------------------------------

# Mapeo en inglés para que los servidores de Pollinations generen arte espectacular
DICCIONARIO_TRADUCCION = {
    "En el principio, Dios creó los cielos y la tierra, y todo estaba en oscuridad.": "In the beginning, God created the heavens and the earth, deep space cosmic dark void, cinematic biblical art",
    "Entonces Dios dijo: Sea la luz, y la luz separó el día de la noche.": "God saying let there be light, holy divine light splitting the dark night, creation of universe",
    "Dios creó los mares, la tierra firme y la llenó de vegetación y árboles frutales.": "God creating beautiful oceans, solid lands, lush green forests and fruit trees, paradise landscape",
    "Finalmente, Dios creó al hombre y a la mujer a su imagen y semejanza para cuidar de la creación.": "Adam and Eve standing in the beautiful garden of Eden, biblical illustration, masterwork painting",
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
# FUNCIONES DE GENERACIÓN (POLLINATIONS API)
# ----------------------------------------------------------------------

def query_pollinations(prompt_es):
    """Genera imágenes usando la infraestructura ilimitada de Pollinations.ai"""
    prompt_en = DICCIONARIO_TRADUCCION.get(prompt_es, f"Biblical illustration of: {prompt_es}")
    
    # Inyectamos parámetros de calidad artística e indicamos relación de aspecto 16:9 para video (1024x576)
    style_prompt = f"Cinematic biblical art, dramatic lighting, epic historical oil painting, highly detailed, masterwork, {prompt_en}"
    
    # Codificar el texto para URL de forma segura
    prompt_encoded = urllib.parse.quote(style_prompt)
    
    # Endpoint público de Pollinations usando el modelo estable de Flux
    url = f"https://image.pollinations.ai/p/{prompt_encoded}?width=1024&height=576&model=flux&nologo=true"
    
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)
            
    return None

def crear_video_biblico(escenas, nombre_salida):
    clips_de_video = []
    progreso = st.progress(0)
    total_escenas = len(escenas)
    
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
        
        # 2. Generar Imagen (Pollinations - Rápido y Estable)
        imagen = query_pollinations(texto)
        if imagen is None:
            status_text.error(f"⛔ Error crítico al obtener la imagen de la Escena {idx+1}. Interrumpiendo.")
            return None
            
        img_path = f"{temp_dir}/image_{idx}.png"
        imagen.save(img_path)
        
        # 3. Ensamblar Clip
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration
        
        video_clip = ImageClip(img_path).set_duration(duracion)
        video_clip = video_clip.set_audio(audio_clip)
        
        clips_de_video.append(video_clip)
        progreso.progress(int((idx + 1) / total_escenas * 100))
        
        # Un pequeño respiro técnico de un segundo es suficiente para Pollinations
        time.sleep(1)

    status_text.write("🎥 Ensamblando todos los clips en el archivo MP4 final (2-3 minutos)...")
    
    video_final = concatenate_videoclips(clips_de_video, method="compose")
    path_final = f"{temp_dir}/{nombre_salida}"
    
    video_final.write_videofile(
        path_final, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        logger=None
    )
    
    for clip in clips_de_video:
        clip.close()
    video_final.close()
    
    return path_final

# ----------------------------------------------------------------------
# INTERFAZ DE USUARIO
# ----------------------------------------------------------------------

st.title("📖 Creador Automático de Videos Bíblicos")
st.subheader("Versión estable e ilimitada de alto rendimiento (Sin Tokens).")

st.info("💡 Esta versión utiliza servidores alternativos optimizados. No necesitas configurar claves ni tokens en la barra lateral.")

categoria = st.selectbox("Selecciona la historia bíblica para el video largo:", list(HISTORIAS.keys()))
escenas_seleccionadas = HISTORIAS[categoria]

with st.expander("Ver pasajes cronológicos que compondrán el video"):
    for i, escena in enumerate(escenas_seleccionadas):
        st.markdown(f"**Escena {i+1}:** {escena}")

if st.button("🚀 Iniciar Generación de Video"):
    with st.spinner("La IA está renderizando las imágenes y locuciones simultáneamente. Por favor, espera..."):
        
        # Multiplicamos la secuencia x3 para alcanzar cómodamente la meta de 2 a 3 minutos
        escenas_extendidas = escenas_seleccionadas * 3  
        nombre_archivo = f"{categoria.replace(' ', '_').replace(':', '')}.mp4"
        
        video_resultado = crear_video_biblico(escenas_extendidas, nombre_archivo)
        
        if video_resultado and os.path.exists(video_resultado):
            st.success("¡Tu video completo en MP4 ha sido generado exitosamente! 🎉")
            st.video(video_resultado)
            
            with open(video_resultado, "rb") as file:
                st.download_button(
                    label="⬇️ Descargar Video MP4",
                    data=file,
                    file_name=nombre_archivo,
                    mime="video/mp4"
                )
