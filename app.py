# app.py
import streamlit as st
import os
from funciones import (load_galaxy_data, list_available_galaxies, sonificar_galaxia, cargar_datos, 
                      graficar_galaxia_plotly, map_values_to_midi_notes, map_to_velocity, 
                      create_midi_file, convert_midi_to_wav)
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# Inicializar st.session_state para todos los valores que queremos mantener entre recargas
if "midi_generado" not in st.session_state:
    st.session_state["midi_generado"] = False
if "wav_generado" not in st.session_state:
    st.session_state["wav_generado"] = False
# Inicializar variables para selección de galaxia
if "galaxia" not in st.session_state:
    st.session_state["galaxia"] = None
if "file_path" not in st.session_state:
    st.session_state["file_path"] = None
if "nombre_base" not in st.session_state:
    st.session_state["nombre_base"] = None
if "rango_onda" not in st.session_state:
    st.session_state["rango_onda"] = None
if "tipo_galaxia" not in st.session_state:
    st.session_state["tipo_galaxia"] = "Espiral"
if "num_octavas" not in st.session_state:
    st.session_state["num_octavas"] = 5
if "selected_scale_name" not in st.session_state:
    st.session_state["selected_scale_name"] = "Armónica Menor"
if "tempo" not in st.session_state:
    st.session_state["tempo"] = 120
if "duracion_nota" not in st.session_state:
    st.session_state["duracion_nota"] = 1.0
if "instrumento_emision" not in st.session_state:
    st.session_state["instrumento_emision"] = "Piano acústico"
if "instrumento_absorcion" not in st.session_state:
    st.session_state["instrumento_absorcion"] = "Guitarra acústica"
if "figura_index" not in st.session_state:
    st.session_state["figura_index"] = 2

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
    uploaded_file = st.file_uploader("", type=["txt"], key="uploaded_file", on_change=lambda: update_uploaded_file())
    
    # Función para actualizar cuando se sube un archivo
    def update_uploaded_file():
        if st.session_state.uploaded_file is not None:
            # Guardar el archivo subido temporalmente
            temp_path = os.path.join(DATA_DIR, "espectro_usuario.txt")
            with open(temp_path, "wb") as f:
                f.write(st.session_state.uploaded_file.read())
            st.session_state["file_path"] = temp_path
            st.session_state["galaxia"] = "espectro_usuario.txt"
            # Asegurarse de usar el nombre original del archivo para nombre_base
            st.session_state["nombre_base"] = os.path.splitext(st.session_state.uploaded_file.name)[0]
            
            # Establecer automáticamente el rango de onda
            data = cargar_datos(temp_path)
            if data is not None:
                min_wavelength = float(data.iloc[:, 0].min())
                max_wavelength = float(data.iloc[:, 0].max())
                st.session_state["rango_onda"] = (min_wavelength, max_wavelength)

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

    galaxia = st.selectbox(
        "Selecciona una galaxia:", 
        galaxias, 
        index=galaxias.index(galaxia_default) if galaxia_default in galaxias else 0,
        key="galaxia_selectbox",
        on_change=lambda: update_galaxia()
    )
    
    # Función para actualizar la galaxia seleccionada
    def update_galaxia():
        selected_galaxia = st.session_state.galaxia_selectbox
        st.session_state["galaxia"] = selected_galaxia
        if uploaded_file is None or selected_galaxia != uploaded_file.name:
            file_path = os.path.join(DATA_DIR, selected_galaxia)
            st.session_state["file_path"] = file_path
            st.session_state["nombre_base"] = os.path.splitext(selected_galaxia)[0]
            
            # Establecer automáticamente el rango de onda
            data = cargar_datos(file_path)
            if data is not None:
                min_wavelength = float(data.iloc[:, 0].min())
                max_wavelength = float(data.iloc[:, 0].max())
                st.session_state["rango_onda"] = (min_wavelength, max_wavelength)

# No cargar automáticamente una galaxia por defecto al iniciar la aplicación
# Esto evita que se muestre el error cuando no se ha seleccionado ninguna galaxia

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
if "galaxia" in st.session_state and st.session_state["galaxia"] is not None:
    galaxia = st.session_state["galaxia"]
    col_desc, col_img = st.columns([2, 1])  # 2:1 para que el texto sea más ancho que la imagen
    descripcion = descripciones_galaxias.get(galaxia, "Sin descripción disponible para esta galaxia.")
    with col_desc:
        st.markdown(f"**Descripción:** {descripcion}")
    # Buscar imagen en .png o .jpg
    if galaxia is not None:  # Verificar que galaxia no sea None antes de usar replace
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
    # Si galaxia es None, no mostrar nada en la columna de imagen

# Solo mostrar la selección del tipo de galaxia si hay una galaxia seleccionada
if "galaxia" in st.session_state and st.session_state["galaxia"] is not None:
    # Selección del tipo de galaxia (sin formulario para aplicación automática)
    st.subheader("🎼 Selecciona el tipo de galaxia para la sonificación:")
    # Determinar el índice basado en el valor actual en session_state
    if st.session_state["tipo_galaxia"] == "Espiral":
        index = 0
    elif st.session_state["tipo_galaxia"] == "Elíptica":
        index = 1
    elif st.session_state["tipo_galaxia"] == "Irregular":
        index = 2
    else:
        index = 0  # Por defecto, usar Espiral
        
    tipo_galaxia = st.radio(
        "", 
        ("Espiral", "Elíptica", "Irregular"), 
        index=index,
        key="tipo_galaxia_radio",
        on_change=lambda: update_tipo_galaxia()
    )

# Función para actualizar el tipo de galaxia
def update_tipo_galaxia():
    st.session_state["tipo_galaxia"] = st.session_state.tipo_galaxia_radio

# Verificar si tenemos una galaxia y un archivo cargados en session_state
if "galaxia" in st.session_state and "file_path" in st.session_state and st.session_state["galaxia"] is not None and st.session_state["file_path"] is not None:
    galaxia = st.session_state["galaxia"]
    file_path = st.session_state["file_path"]
    nombre_base = st.session_state["nombre_base"]
    
    # Intentar cargar los datos solo si tenemos un archivo válido
    try:
        data = cargar_datos(file_path)
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        data = None

    if data is not None:
        # Distribución en columnas: gráfica a la izquierda, opciones a la derecha
        col_grafica, col_opciones = st.columns([2, 1])
        
        with col_grafica:
            # Visualización de datos (sin formulario para aplicación automática)
            st.subheader("🔭 Visualización de datos")
            
            # Selección del rango de longitudes de onda (sin formulario para aplicación automática)
            st.subheader("🎼 Rango de longitudes de onda a sonificar")
            min_wavelength = float(data.iloc[:, 0].min())
            max_wavelength = float(data.iloc[:, 0].max())
            
            # Usar valores previos si existen
            default_value = st.session_state["rango_onda"] if st.session_state["rango_onda"] is not None else (min_wavelength, max_wavelength)
            
            rango_onda = st.slider(
                "",
                min_value=min_wavelength,
                max_value=max_wavelength,
                value=default_value,
                step=0.1,
                key="rango_onda_slider",
                on_change=lambda: update_rango_onda(),
                help="Arrastra para seleccionar el rango de longitudes de onda a sonificar"
            )
            
            # Función para actualizar el rango de onda
            def update_rango_onda():
                st.session_state["rango_onda"] = st.session_state.rango_onda_slider
            
            # Define scale options and selection BEFORE plotting
            scale_options = {
                "Armónica Menor": [0, 2, 3, 5, 7, 8, 11],
                "Pentatónica Menor": [0, 3, 5, 7, 10],
                "Mayor": [0, 2, 4, 5, 7, 9, 11],
                "Menor Natural": [0, 2, 3, 5, 7, 8, 10],
                "Cromática": list(range(12))
            }
            
            selected_scale_name = st.selectbox(
                "Selecciona una escala musical", 
                list(scale_options.keys()),
                index=list(scale_options.keys()).index(st.session_state["selected_scale_name"]) if st.session_state["selected_scale_name"] in scale_options else 0,
                key="scale_selectbox",
                on_change=lambda: update_scale()
            )
            
            # Función para actualizar la escala seleccionada
            def update_scale():
                st.session_state["selected_scale_name"] = st.session_state.scale_selectbox
            
            # Obtener notas de la escala seleccionada
            notas_escala = scale_options.get(st.session_state["selected_scale_name"], scale_options["Armónica Menor"])
            
            # Ensure notas_escala is always a list
            if not isinstance(notas_escala, list):
                notas_escala = scale_options["Armónica Menor"] # Default to Armónica Menor

            # Si tenemos todos los datos necesarios, mostrar la gráfica
            if "rango_onda" in st.session_state and st.session_state["rango_onda"] is not None:
                fig = graficar_galaxia_plotly(
                    archivo=file_path,
                    tipo_galaxia=st.session_state["tipo_galaxia"],
                    rango_onda=st.session_state["rango_onda"],
                    nombre_archivo=nombre_base,
                    num_octavas=st.session_state["num_octavas"],
                    notas_escala=notas_escala
                )
                min_intensity = float(data.iloc[:, 1].min())
                max_intensity = float(data.iloc[:, 1].max())
                num_notes_range = (24, 24 + (st.session_state["num_octavas"] * 12))

                # Paleta de colores cíclica para las notas
                note_colors = [
                    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "7f7f7f", "#bcbd22", "#17becf", "#a93226", "#229954"
                ]

            # Si tenemos todos los datos necesarios, mostrar la gráfica
            if "rango_onda" in st.session_state and st.session_state["rango_onda"] is not None:
                # Graficar la curva general encima (opcional)
                fig.add_trace(go.Scatter(
                    x=data.iloc[:, 0],
                    y=data.iloc[:, 1],
                    mode='lines',
                    line=dict(color='gray', width=1),
                    name=galaxia,
                    opacity=1.0
                ))
                
                # Añadir rectángulo para la región sonificada
                fig.add_vrect(
                    x0=st.session_state["rango_onda"][0], 
                    x1=st.session_state["rango_onda"][1],
                    fillcolor="orange", 
                    opacity=0.3,
                    layer="below", 
                    line_width=0,
                    annotation_text="Región sonificada", 
                    annotation_position="top left"
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
                
                # Mostrar la gráfica
                st.plotly_chart(fig)

        with col_opciones:
            # Opciones de sonificación (sin formulario para aplicación automática)
            st.subheader("🎼 Opciones de Sonificación")
            
            # Número de octavas
            num_octavas = st.slider(
                "Número de octavas", 
                1, 7, 
                st.session_state["num_octavas"],
                key="num_octavas_slider",
                on_change=lambda: update_num_octavas()
            )
            
            # Función para actualizar el número de octavas
            def update_num_octavas():
                st.session_state["num_octavas"] = st.session_state.num_octavas_slider
            
            st.info("🎧 Consejo: Para una mejor identificación de las líneas espectrales se recomienda utilizar entre 5 y 7 octavas.")
            
            # Usar valores previos si existen
            tempo = st.slider(
                "Tempo (BPM)", 
                min_value=40, 
                max_value=240, 
                value=st.session_state["tempo"],
                step=1,
                key="tempo_slider",
                on_change=lambda: update_tempo()
            )
            
            # Función para actualizar el tempo
            def update_tempo():
                st.session_state["tempo"] = st.session_state.tempo_slider
            
            figuras = [
                ("𝅝 Redonda", 4.0),
                ("𝅗𝅥 Blanca", 2.0),
                ("𝅘𝅥 Negra", 1.0),
                ("𝅘𝅥𝅮 Corchea", 0.5),
                ("𝅘𝅥𝅯 Semicorchea", 0.25)
            ]
            
            figura = st.selectbox(
                "Duración de la nota",
                figuras,
                index=st.session_state["figura_index"],
                key="figura_selectbox",
                on_change=lambda: update_figura()
            )
            
            # Función para actualizar la figura y duración de nota
            def update_figura():
                selected_figura = st.session_state.figura_selectbox
                st.session_state["figura_index"] = figuras.index(selected_figura)
                st.session_state["duracion_nota"] = selected_figura[1]
            
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
                index=list(instrumentos_midi.keys()).index(st.session_state["instrumento_emision"]) if st.session_state["instrumento_emision"] in instrumentos_midi else 0,
                key="instrumento_emision_selectbox",
                on_change=lambda: update_instrumento_emision()
            )
            
            # Función para actualizar el instrumento de emisión
            def update_instrumento_emision():
                st.session_state["instrumento_emision"] = st.session_state.instrumento_emision_selectbox
            
            instrumento_absorcion = st.selectbox(
                "Instrumento para Absorción",
                list(instrumentos_midi.keys()),
                index=list(instrumentos_midi.keys()).index(st.session_state["instrumento_absorcion"]) if st.session_state["instrumento_absorcion"] in instrumentos_midi else 1,
                key="instrumento_absorcion_selectbox",
                on_change=lambda: update_instrumento_absorcion()
            )
            
            # Función para actualizar el instrumento de absorción
            def update_instrumento_absorcion():
                st.session_state["instrumento_absorcion"] = st.session_state.instrumento_absorcion_selectbox
                
                # Estilo para el botón de sonificación
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
            # Formulario para el botón de sonificación
            with st.form(key="sonificar_form"):
                if st.form_submit_button("🎹 Sonificar", use_container_width=True):
                    # Verificar que tenemos todos los datos necesarios
                    if ("galaxia" in st.session_state and 
                        "file_path" in st.session_state and 
                        "rango_onda" in st.session_state and 
                        st.session_state["rango_onda"] is not None):
                        
                        # Obtener valores de session_state
                        galaxia = st.session_state["galaxia"]
                        file_path = st.session_state["file_path"]
                        nombre_base = st.session_state["nombre_base"]
                        rango_onda = st.session_state["rango_onda"]
                        tipo_galaxia = st.session_state["tipo_galaxia"]
                        num_octavas = st.session_state["num_octavas"]
                        tempo = st.session_state["tempo"]
                        duracion_nota = st.session_state["duracion_nota"]
                        instrumento_emision = st.session_state["instrumento_emision"]
                        instrumento_absorcion = st.session_state["instrumento_absorcion"]
                        
                        # Configurar nombres de archivos de salida
                        salida_midi_emision = f"{nombre_base}_emision.mid"
                        salida_midi_absorcion = f"{nombre_base}_absorcion.mid"
                        salida_midi_completo = f"{nombre_base}_completo.mid"
                        salida_wav_emision = f"{nombre_base}_emision.wav"
                        salida_wav_absorcion = f"{nombre_base}_absorcion.wav"
                        salida_wav_completo = f"{nombre_base}_completo.wav"
                        
                        # Obtener notas de la escala seleccionada
                        scale_options = {
                            "Armónica Menor": [0, 2, 3, 5, 7, 8, 11],
                            "Pentatónica Menor": [0, 3, 5, 7, 10],
                            "Mayor": [0, 2, 4, 5, 7, 9, 11],
                            "Menor Natural": [0, 2, 3, 5, 7, 8, 10],
                            "Cromática": list(range(12))
                        }
                        notas_escala = scale_options.get(st.session_state["selected_scale_name"], scale_options["Armónica Menor"])
                        
                        # Obtener valores de instrumentos MIDI
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

                        # Generar archivos MIDI
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
                    else:
                        st.error("Por favor, asegúrate de haber seleccionado una galaxia y configurado todos los parámetros necesarios.")
                        st.session_state["midi_generado"] = False
                        st.session_state["wav_generado"] = False

        # Opciones de descarga horizontales
        if st.session_state["midi_generado"]:
            from pydub import AudioSegment
            # Usar nombre_base de session_state para consistencia
            nombre_base = st.session_state["nombre_base"]
            wav_emision = f"{nombre_base}_emision.wav"
            wav_absorcion = f"{nombre_base}_absorcion.wav"
            wav_mix = f"{nombre_base}_mix_preview.wav"
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
                    (f"{nombre_base}_emision.mid", "⬇️ MIDI Emisión"),
                    (f"{nombre_base}_emision.wav", "⬇️ WAV Emisión"),
                    (f"{nombre_base}_absorcion.mid", "⬇️ MIDI Absorción"),
                    (f"{nombre_base}_absorcion.wav", "⬇️ WAV Absorción"),
                    (f"{nombre_base}_completo.mid", "⬇️ MIDI Completo"),
                    (f"{nombre_base}_completo.wav", "⬇️ WAV Completo"),
                ]
                cols = [col1, col2, col3, col4, col5, col6]
                for (archivo, label), col in zip(archivos, cols):
                    with col:
                        if os.path.exists(archivo):
                            with open(archivo, "rb") as f:
                                st.download_button(label, f, file_name=archivo, key=f"{archivo}_descarga1")
        