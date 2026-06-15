import streamlit as st
import requests
import os
import time
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
from io import BytesIO

# Configuración de la página de Streamlit
st.set_page_config(page_title="Creador de Videos Bíblicos", page_icon="📖", layout="wide")

# ----------------------------------------------------------------------
# CONFIGURACIÓN Y CONTENIDO BÍBLICO
# ----------------------------------------------------------------------
# Token gratuito de Hugging Face (Se recomienda guardarlo en Streamlit Secrets)
# Consíguelo gratis en: https://huggingface.co/settings/tokens
HF_TOKEN = st.sidebar.text_input("Introduce tu Hugging Face Token (HF_...)", type="password")

# Estructura básica de historias (Génesis y Evangelios)
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
    """Consulta un modelo gratuito de generación de imágenes en Hugging Face."""
    # Usamos SDXL o Flux Schnell por ser rápidos, gratuitos y de alta calidad para las escenas
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Añadimos un estilo artístico para que el video se vea homogéneo y cinematográfico
    style_prompt = f"Cinematic biblical art, dramatic lighting, detailed oil painting, highly realistic, masterwork, {prompt}"
    
    response = requests.post(API_URL, headers=headers, json={"inputs": style_prompt})
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        st.error(f"Error en la API de Hugging Face: {response.status_code} - {response.text}")
        return None

def crear_video_biblico(escenas, token, nombre_salida="video_final.mp4"):
    """Genera el audio, las imágenes y concatena todo en un archivo MP4."""
    clips_de_video = []
    progreso = st.progress(0)
    total_escenas = len(escenas)
    
    # Crear carpeta temporal para los archivos si no existe
    if not os.path.exists("temp"):
        os.makedirs("temp")

    for idx, texto in enumerate(escenas):
        st.write(f"🎬 Procesando Escena {idx + 1}/{total_escenas}...")
        
        # 1. Generar Audio (gTTS - Gratis)
        audio_path = f"temp/audio_{idx}.mp3"
        tts = gTTS(text=texto, lang='es', tld='com.mx')
        tts.save(audio_path)
        
        # Traducir mentalmente o usar palabras clave en inglés para el modelo de imagen (mejora resultados)
        # Aquí puedes usar una librería de traducción, por ahora pasamos el texto con un toque visual
        prompt_imagen = f"Biblical scene depiction of: {texto}"
        
        # 2. Generar Imagen (Hugging Face - Gratis)
        imagen = query_hugging_face(prompt_imagen, token)
        if imagen is None:
            st.error("No se pudo generar la imagen. Abortando proceso.")
            return None
            
        img_path = f"temp/image_{idx}.png"
        imagen.save(img_path)
        
        # 3. Crear Clip de Video para esta escena usando MoviePy
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration # El video durará lo que dure la narración de voz
        
        # Crear clip de imagen con la duración del audio
        video_clip = ImageClip(img_path).set_duration(duracion)
        video_clip = video_clip.set_audio(audio_clip)
        
        clips_de_video.append(video_clip)
        
        # Actualizar barra de progreso
        progreso.progress(int((idx + 1) / total_escenas * 100))
        time.sleep(1) # Pausa de cortesía para la API

    # 4. Concatenar todos los clips en un único video largo
    st.write("🎥 Concatenando todas las escenas en el formato final MP4...")
    video_final = concatenate_videoclips(clips_de_video, method="compose")
    
    path_final = f"temp/{nombre_salida}"
    # fps=24 es estándar para video. Usamos el codec libx264 para máxima compatibilidad MP4
    video_final.write_videofile(path_final, fps=24, codec="libx264", audio_codec="aac")
    
    # Cerrar clips para liberar memoria
    for clip in clips_de_video:
        clip.close()
    video_final.close()
    
    return path_final

# ----------------------------------------------------------------------
# INTERFAZ DE USUARIO (UI)
# ----------------------------------------------------------------------

st.title("📖 Creador Automático de Videos Bíblicos")
st.subheader("Genera videos narrados en MP4 partiendo desde el Génesis hasta los Evangelios.")

st.markdown("""
Esta herramienta utiliza inteligencia artificial gratuita para:
1. Generar la **voz en off** de los pasajes bíblicos.
2. Crear **ilustraciones artísticas** cinemáticas para cada escena.
3. **Concatenar todo** automáticamente en un video final de formato largo.
""")

if not HF_TOKEN:
    st.info("💡 Por favor, introduce tu Token de Hugging Face en la barra lateral para activar la generación de imágenes.")

# Selección de la historia
categoria = st.selectbox("Selecciona la sección de la Biblia:", list(HISTORIAS.keys()))
escenas_seleccionadas = HISTORIAS[categoria]

# Mostrar las escenas que se van a procesar
with st.expander("Ver las escenas que se incluirán en el video"):
    for i, escena in enumerate(escenas_seleccionadas):
        st.markdown(f"**Escena {i+1}:** {escena}")

# Botón de renderizado
if st.button("🚀 Generar Video Completo", disabled=not HF_TOKEN):
    with st.spinner("Generando recursos y renderizando el video MP4... Esto puede tomar unos minutos."):
        
        # Para hacer un video de 2-3 minutos, usualmente se necesitan unas 12-15 escenas.
        # Duplicamos la lista para simular una duración más larga si el usuario elige una corta.
        escenas_extendidas = escenas_seleccionadas * 3 # Ajusta este multiplicador para el largo deseado
        
        nombre_archivo = f"{categoria.replace(' ', '_').replace(':', '')}.mp4"
        video_resultado = crear_video_biblico(escenas_extendidas, HF_TOKEN, nombre_archivo)
        
        if video_resultado and os.path.exists(video_resultado):
            st.success("¡Video generado con éxito! 🎉")
            
            # Mostrar el video en la app
            st.video(video_resultado)
            
            # Botón de descarga
            with open(video_resultado, "rb") as file:
                st.download_button(
                    label="⬇️ Descargar Video MP4",
                    data=file,
                    file_name=nombre_archivo,
                    mime="video/mp4"
                )
