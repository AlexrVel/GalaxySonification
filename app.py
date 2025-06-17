# app.py
import streamlit as st
import os
from src.data_loader import load_galaxy_data, list_available_galaxies
from src.sound_mapper import map_values_to_midi_notes, map_to_velocity
from src.midi_generator import create_midi_file
import plotly.graph_objects as go
from src.midi_generator import convert_midi_to_wav
from funciones import sonificar_galaxia, cargar_datos
from funciones import graficar_galaxia_plotly
import matplotlib.pyplot as plt

# Inicializar st.session_state
if "midi_generado" not in st.session_state:
    st.session_state["midi_generado"] = False
if "wav_generado" not in st.session_state:
    st.session_state["wav_generado"] = False

# Constantes locales
DATA_DIR = "data"
MIDI_OUTPUT = "output.mid"
WAV_OUTPUT = "output.wav"
SOUNDFONT_PATH = "FluidR3_GM.sf2"
#SOUNDFONT_PATH = "GeneralUser-GS.sf2"

# Streamlit le crea webs sin complique y las llama desde python
st.set_page_config(page_title="Sonificación Galáctica", layout="wide")
st.title("🌌 Sonificación de Galaxias")
st.write("Convierte datos astronómicos en música 🎶 usando MIDI")
st.markdown(
    """
    ¿Alguna vez te has preguntado cómo sería escuchar una galaxia? Gracias a las tecnologías de sonificación, hoy es posible traducir datos astronómicos en sonidos y explorar el cosmos a través del sentido de la audición.
    
    Galaxy Sonification es una aplicación interactiva que transforma los espectros electromagnéticos de las galaxias en paisajes sonoros, permitiendo identificar características distintivas según su tipo morfológico. Aunque existen tres tipos principales de galaxias —elípticas, espirales e irregulares—, la aplicación ofrece actualmente dos modos específicos de sonificación: uno para galaxias elípticas y otro para espirales. Sin embargo, también puedes cargar espectros de galaxias irregulares y experimentar con ambos modos para descubrir nuevas formas de representación sonora.
    """
)
st.info("Para una generación más rápida del audio, te recomendamos utilizar tempos altos o seleccionar duraciones cortas para las notas, como corcheas o semicorcheas. Esto no solo agiliza el procesamiento, sino que también permite una exploración más fluida del contenido espectral.")
# Paso 1: Selección de galaxia y carga de archivo en columnas
col_galaxia, col_upload = st.columns([2, 1])

with col_upload:
    st.markdown('O sube tu propio espectro (.txt) [formato NED, ver más en [NED](https://ned.ipac.caltech.edu/)]')
    uploaded_file = st.file_uploader("", type=["txt"])

with col_galaxia:
    galaxias = list_available_galaxies(DATA_DIR)
    # Si hay archivo subido, agregar su nombre a la lista de galaxias (si no está)
    if uploaded_file is not None:
        nombre_txt_usuario = uploaded_file.name
        if nombre_txt_usuario not in galaxias:
            galaxias = [nombre_txt_usuario] + galaxias  # Lo pone al inicio
        galaxia_default = nombre_txt_usuario
    else:
        galaxia_default = galaxias[0] if galaxias else None

    galaxia = st.selectbox("Selecciona una galaxia:", galaxias, index=galaxias.index(galaxia_default) if galaxia_default in galaxias else 0)

# Diccionario de descripciones (puedes ampliarlo con tus propias descripciones)
descripciones_galaxias = {
    "NGC_6643.txt": "NGC 6643 es una galaxia espiral ubicada en la constelación de Draco.",
    "NGC_1300.txt": "NGC 1300 es una galaxia espiral barrada situada en la constelación de Eridanus.",
    "NGC_3370.txt": "NGC 3370 es una galaxia espiral en la constelación de Leo.",
    "NGC_4881.txt": "NGC 4881 es una galaxia elíptica en el cúmulo de Coma.",
    "NGC_1569.txt": (
        "NGC 1569 es una galaxia irregular enana ubicada en la constelación de la Jirafa a 11 millones años luz.\n"
        "La galaxia llamada NGC 1569 brilla intensamente gracias a la luz de millones de estrellas jóvenes que se han formado recientemente.\n"
        "NGC 1569 está formando estrellas a un ritmo 100 veces más rápido que el observado en nuestra propia galaxia, la Vía Láctea.\n"
        "Este ritmo frenético de formación estelar ha continuado casi sin pausa durante los últimos 100 millones de años.\n"
        "En el centro de la galaxia se encuentra un grupo de tres cúmulos estelares gigantes, cada uno con más de un millón de estrellas. "
        "(Dos de estos cúmulos están tan cerca entre sí que parecen uno solo). Estos cúmulos están ubicados en una gran cavidad central, "
        "cuyo gas ha sido expulsado por la acción de muchas estrellas masivas y jóvenes que ya explotaron como supernovas.\n"
        "Estas explosiones también provocaron un flujo violento de gas y partículas que ha esculpido enormes estructuras de gas. "
        "Una de estas estructuras, visible en la parte inferior derecha, mide unos 3,700 años luz de longitud.\n"
        "Información y figura tomadas de https://science.nasa.gov/asset/hubble/starburst-galaxy-ngc-1569/"
    ),
    "NGC_2276.txt": (
        "NGC 2276 es una galaxia espiral en interacción. En la mayoría de las galaxias espirales, el centro suele mostrar un núcleo brillante compuesto por estrellas más viejas de color amarillento. "
        "Sin embargo, en el caso de NGC 2276, ese núcleo parece estar desplazado hacia la parte superior izquierda. "
        "Esto se debe a que una galaxia vecina situada a la derecha de NGC 2276 (NGC 2300, que no aparece en la imagen) la está atrayendo gravitacionalmente. "
        "Esa fuerza está tirando del disco de estrellas azules en un lado, distorsionando la forma típica de 'huevo frito' que suelen tener estas galaxias. "
        "Este tipo de “tira y afloja” entre galaxias cercanas no es raro en el universo. Sin embargo, al igual que los copos de nieve, ningún encuentro cercano entre galaxias es exactamente igual a otro. "
        "Además, en el borde superior izquierdo de NGC 2276 se forma un brazo azul brillante, compuesto por estrellas jóvenes y masivas de corta vida. "
        "Estas estrellas marcan una región de intensa formación estelar, que pudo haber sido provocada por una colisión anterior con una galaxia enana. "
        "También es posible que se deba a que NGC 2276 se esté desplazando a través del gas sobrecalentado que se encuentra entre galaxias en los cúmulos galácticos. "
        "Al atravesar este gas, se comprime y colapsa, dando lugar al nacimiento masivo de nuevas estrellas. "
        "La galaxia espiral NGC 2276 se encuentra a unos 120 millones de años luz, en la constelación boreal de Cefeo. "
        "Información y figura tomadas de https://science.nasa.gov/asset/hubble/ngc-2276/"
    ),
    "NGC_3379.txt": (
        "M105 (también conocida como NGC 3379) es una galaxia elíptica que se encuentra a unos 32 millones de años luz de distancia, en la constelación de Leo. Es la galaxia elíptica más grande del catálogo de Messier que no forma parte del cúmulo de Virgo. Sin embargo, M105 sí pertenece al Grupo de M96 (o Leo I), junto con sus vecinas M95, M96 y varias otras galaxias más débiles.\n"
        "La galaxia fue descubierta en 1781 por Pierre Méchain, colega de Charles Messier, pocos días después de haber localizado M95 y M96. Curiosamente, M105 no fue incluida originalmente en el catálogo de Messier. Fue añadida en 1947, cuando la astrónoma Helen S. Hogg encontró una carta escrita por Méchain en la que describía esta galaxia.\n"
        "El telescopio espacial Hubble observó el núcleo de M105 y midió el movimiento de las estrellas que giran alrededor de su centro. Estas observaciones confirmaron la presencia de un agujero negro supermasivo en el corazón de la galaxia. Según estimaciones recientes, este agujero negro podría tener una masa hasta 200 millones de veces mayor que la del Sol. Información y figura tomadas de https://science.nasa.gov/mission/hubble/science/explore-the-night-sky/hubble-messier-catalog/messier-105/"
    ),
    "NGC_4485.txt": (
        "La galaxia irregular NGC 4485 muestra claras señales de haber estado involucrada en una especie de “choque y fuga” cósmico con otra galaxia que pasó muy cerca. Pero en lugar de destruirla, este encuentro fortuito ha dado lugar al nacimiento de una nueva generación de estrellas, y posiblemente, también de planetas.\n"
        "En el lado derecho de la galaxia se observa una intensa actividad de formación estelar, visible en la abundancia de estrellas jóvenes azules y nebulosas rosadas donde se están gestando nuevas estrellas. En contraste, el lado izquierdo parece más intacto, conservando algunos indicios de lo que alguna vez fue una estructura espiral, que entonces evolucionaba de manera más tranquila.\n"
        "La responsable de este encuentro es la galaxia más grande NGC 4490, que no aparece en la imagen, ubicada fuera del encuadre, en la parte inferior. Estas dos galaxias rozaron sus bordes hace millones de años y actualmente están separadas por unos 24,000 años luz. La interacción gravitacional entre ambas creó ondas de gas y polvo más densas, lo que disparó la intensa formación de estrellas en ambas galaxias.\n"
        "NGC 4485 es un ejemplo cercano del tipo de colisiones cósmicas que eran mucho más comunes hace miles de millones de años, cuando el universo era más pequeño y las galaxias estaban mucho más juntas.\n"
        "Esta galaxia se encuentra a unos 25 millones de años luz, en la constelación boreal de Canes Venatici (Los Perros de Caza). Información y figura tomadas de https://science.nasa.gov/asset/hubble/ngc-4485/"
    ),
    # Agrega aquí más descripciones según tus galaxias
}

# Mostrar descripción e imagen si existe una galaxia seleccionada
if galaxia:
    col_desc, col_img = st.columns([2, 1])  # 2:1 para que el texto sea más ancho que la imagen
    descripcion = descripciones_galaxias.get(galaxia, "Sin descripción disponible para esta galaxia.")
    with col_desc:
        st.markdown(f"**Descripción:** {descripcion}")
    # Buscar imagen en .png o .jpg
    imagen_path = os.path.join(DATA_DIR, galaxia.replace('.txt', '.png'))
    if not os.path.exists(imagen_path):
        imagen_path = os.path.join(DATA_DIR, galaxia.replace('.txt', '.jpg'))
    if not os.path.exists(imagen_path):
        imagen_path = os.path.join(DATA_DIR, galaxia.replace('.txt', '.jpeg'))
    with col_img:
        if os.path.exists(imagen_path):
            st.image(imagen_path, caption=f"Imagen de {galaxia}", use_container_width=True)
        else:
            st.info("No hay imagen disponible para esta galaxia.")

# Nuevo: Menú para elegir el tipo de galaxia
st.subheader("🎼 Selecciona el tipo de galaxia para la sonificación:")
tipo_galaxia = st.radio("", ("Espiral", "Elíptica"), key="tipo_galaxia_radio")

if uploaded_file is not None:
    # Guardar el archivo subido temporalmente
    temp_path = os.path.join(DATA_DIR, "espectro_usuario.txt")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())
    file_path = temp_path
    galaxia = "espectro_usuario.txt"
    nombre_base = os.path.splitext(uploaded_file.name)[0]  # Usar nombre real del archivo subido
elif galaxia:
    file_path = os.path.join(DATA_DIR, galaxia)
    nombre_base = os.path.splitext(galaxia)[0]  # Usar nombre de la galaxia

if galaxia and file_path:
    data = cargar_datos(file_path)

    if data is not None:
        # Paso 3: Generar MIDI (move this block up if needed)
        # Elimina o comenta esta línea:
        # st.subheader("🎼 Generar sonido")
        # Ahora el slider es el título principal:
        st.subheader("🎼 Rango de longitudes de onda a sonificar")
        min_wavelength = float(data.iloc[:, 0].min())
        max_wavelength = float(data.iloc[:, 0].max())
        rango_onda = st.slider(
            "",
            min_value=min_wavelength,
            max_value=max_wavelength,
            value=(min_wavelength, max_wavelength),
            step=0.1
        )











        # Distribución en columnas: gráfica a la izquierda, opciones a la derecha
        col_grafica, col_opciones = st.columns([2, 1])
        with col_grafica:
            st.subheader("🔭 Visualización de datos")
            num_octavas = st.slider("Número de octavas", 1, 7, 5, key="num_octavas_slider")
            st.info("🎧 Consejo: Para una mejor identificación de las líneas espectrales se recomienda utilizar entre 5 y 7 octavas.")
            # Define scale options and selection BEFORE plotting
            scale_options = {
                "Armónica Menor": [0, 2, 3, 5, 7, 8, 11],
                "Pentatónica Menor": [0, 3, 5, 7, 10],
                "Mayor": [0, 2, 4, 5, 7, 9, 11],
                "Menor Natural": [0, 2, 3, 5, 7, 8, 10],
                "Cromática": list(range(12))
            }
            selected_scale_name = st.selectbox("Selecciona una escala musical", list(scale_options.keys()))
            notas_escala = scale_options.get(selected_scale_name, scale_options["Armónica Menor"])
            
            # Ensure notas_escala is always a list
            if not isinstance(notas_escala, list):
                notas_escala = scale_options["Armónica Menor"] # Default to Armónica Menor

            fig = graficar_galaxia_plotly(
                archivo=file_path,
                tipo_galaxia=tipo_galaxia,
                rango_onda=rango_onda,
                nombre_archivo=nombre_base,
                num_octavas=num_octavas,
                notas_escala=notas_escala
            )
            min_intensity = float(data.iloc[:, 1].min())
            max_intensity = float(data.iloc[:, 1].max())
            num_notes_range = (24, 24 + (num_octavas * 12))

            # Paleta de colores cíclica para las notas
            note_colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "7f7f7f", "#bcbd22", "#17becf", "#a93226", "#229954"
            ]

            # Graficar la curva general encima (opcional)
            fig.add_trace(go.Scatter(
                x=data.iloc[:, 0],
                y=data.iloc[:, 1],
                mode='lines',
                line=dict(color='gray', width=1),
                name=galaxia,
                opacity=1.0
            ))
            fig.add_vrect(
                x0=rango_onda[0], x1=rango_onda[1],
                fillcolor="orange", opacity=0.3,
                layer="below", line_width=0,
                annotation_text="Región sonificada", annotation_position="top left"
            )

            fig.update_layout(
                title=f"Datos de {nombre_base}",
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=60, r=10, t=40, b=40),
                xaxis=dict(
                    color="black",
                    showline=True,
                    linewidth=2,
                    linecolor="black",
                    mirror=True,
                    showgrid=False,
                    zeroline=False,
                    title=dict(text="Longitud de onda (ángstrom)", font=dict(color="black")),
                    tickfont=dict(color="black")  # <-- Esto hace visibles los números del eje X
                ),
                yaxis=dict(
                    color="black",
                    showline=True,
                    linewidth=2,
                    linecolor="black",
                    mirror=True,
                    showgrid=False,
                    zeroline=False,
                    title=dict(text="Flujo normalizado", font=dict(color="black")),
                    tickfont=dict(color="black")  # <-- Esto hace visibles los números del eje Y
                )
            )
            fig = graficar_galaxia_plotly(
                archivo=file_path,
                tipo_galaxia=tipo_galaxia,
                rango_onda=rango_onda,
                nombre_archivo=nombre_base,
                num_octavas=num_octavas,
                notas_escala=notas_escala
            )
            st.plotly_chart(fig)

        with col_opciones:
            st.subheader("🎼 Opciones de Sonificación")
            tempo = st.slider("Tempo (BPM)", min_value=40, max_value=240, value=120, step=1)
            figura = st.selectbox(
                "Duración de la nota",
                [
                    ("𝅝 Redonda", 4.0),
                    ("𝅗𝅥 Blanca", 2.0),
                    ("𝅘𝅥 Negra", 1.0),
                    ("𝅘𝅥𝅮 Corchea", 0.5),
                    ("𝅘𝅥𝅯 Semicorchea", 0.25)
                ],
                index=2
            )
            duracion_nota = figura[1]
            instrumentos_midi = {
                "Piano acústico": 0,
                "Guitarra acústica": 24,
                "Violín": 40,
                "Trompeta": 56,
                "Flauta": 73,
                "Órgano": 19,
                "Saxofón": 65,
                "Sintetizador": 81
            }
            instrumento_emision = st.selectbox(
                "Instrumento para Emisión",
                list(instrumentos_midi.keys()),
                index=0
            )
            instrumento_absorcion = st.selectbox(
                "Instrumento para Absorción",
                list(instrumentos_midi.keys()),
                index=1
            )
            # Botón grande y más alto
            st.markdown(
                """
                <style>
                div.stButton > button {
                    font-size: 1.5em;
                    height: 4.5em; /* Más alto aún */
                    width: 100%;
                    background-color: #6c63ff;
                    color: white;
                    border-radius: 10px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            if st.button("🎹 Sonificar", use_container_width=True):
                # Lógica unificada usando la función nueva
                nombre_base = os.path.splitext(galaxia)[0]
                salida_midi_emision = f"{nombre_base}_emision.mid"
                salida_midi_absorcion = f"{nombre_base}_absorcion.mid"
                salida_midi_completo = f"{nombre_base}_completo.mid"
                salida_wav_emision = f"{nombre_base}_emision.wav"
                salida_wav_absorcion = f"{nombre_base}_absorcion.wav"
                salida_wav_completo = f"{nombre_base}_completo.wav"

                salida_midi_emision_path, salida_midi_absorcion_path, salida_midi_completo_path = sonificar_galaxia(
                    archivo=file_path,
                    rango_onda=rango_onda,
                    tipo_galaxia=tipo_galaxia,
                    num_octavas=num_octavas,
                    tempo=tempo,
                    duracion_nota=duracion_nota,
                    instrumento_emision=instrumentos_midi[instrumento_emision],
                    instrumento_absorcion=instrumentos_midi[instrumento_absorcion],
                    notas_escala=notas_escala
                )
                # Convertir los MIDIs a WAV para previsualización
                try:
                    convert_midi_to_wav(salida_midi_emision_path, salida_wav_emision, SOUNDFONT_PATH)
                except Exception as e:
                    st.warning(f"No se pudo convertir {salida_midi_emision_path} a WAV: {e}")
                try:
                    convert_midi_to_wav(salida_midi_absorcion_path, salida_wav_absorcion, SOUNDFONT_PATH)
                except Exception as e:
                    st.warning(f"No se pudo convertir {salida_midi_absorcion_path} a WAV: {e}")
                try:
                    convert_midi_to_wav(salida_midi_completo_path, salida_wav_completo, SOUNDFONT_PATH)
                except Exception as e:
                    st.warning(f"No se pudo convertir {salida_midi_completo_path} a WAV: {e}")

                st.success("✅ Archivos MIDI generados correctamente.")
                st.session_state["midi_generado"] = True
                st.session_state["wav_generado"] = True

        # Opciones de descarga horizontales
        if st.session_state["midi_generado"]:
            from pydub import AudioSegment
            wav_emision = f"{os.path.splitext(galaxia)[0]}_emision.wav"
            wav_absorcion = f"{os.path.splitext(galaxia)[0]}_absorcion.wav"
            wav_mix = f"{os.path.splitext(galaxia)[0]}_mix_preview.wav"
            if os.path.exists(wav_emision) and os.path.exists(wav_absorcion):
                audio_emision = AudioSegment.from_wav(wav_emision)
                audio_absorcion = AudioSegment.from_wav(wav_absorcion)
                min_len = min(len(audio_emision), len(audio_absorcion))
                audio_emision = audio_emision[:min_len]
                audio_absorcion = audio_absorcion[:min_len]
                audio_mix = audio_emision.overlay(audio_absorcion)
                audio_mix.export(wav_mix, format="wav")
                st.subheader("🔊 Previsualizar sonido")
                st.audio(wav_mix, format="audio/wav")
                # Botones de descarga en horizontal
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                archivos = [
                    (f"{os.path.splitext(galaxia)[0]}_emision.mid", "⬇️ MIDI Emisión"),
                    (f"{os.path.splitext(galaxia)[0]}_emision.wav", "⬇️ WAV Emisión"),
                    (f"{os.path.splitext(galaxia)[0]}_absorcion.mid", "⬇️ MIDI Absorción"),
                    (f"{os.path.splitext(galaxia)[0]}_absorcion.wav", "⬇️ WAV Absorción"),
                    (f"{os.path.splitext(galaxia)[0]}_completo.mid", "⬇️ MIDI Completo"),
                    (f"{os.path.splitext(galaxia)[0]}_completo.wav", "⬇️ WAV Completo"),
                ]
                cols = [col1, col2, col3, col4, col5, col6]
                for (archivo, label), col in zip(archivos, cols):
                    with col:
                        if os.path.exists(archivo):
                            with open(archivo, "rb") as f:
                                st.download_button(label, f, file_name=archivo, key=f"{archivo}_descarga1")
        