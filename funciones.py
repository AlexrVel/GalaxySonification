import numpy as np
import pandas as pd
from midiutil import MIDIFile
from scipy.ndimage import uniform_filter1d
import os
from midi2audio import FluidSynth
import subprocess
from pydub import AudioSegment
import matplotlib.pyplot as plt
import os
from src.data_loader import load_galaxy_data
import music21 as m21

def cargar_datos(archivo):
        # Cargar datos
    with open(archivo, 'r') as f:
        primera_linea = f.readline().strip()
    # Detectar si hay encabezado
    try:
        [float(x) for x in primera_linea.split()]
        skip = 0  # No es encabezado
    except ValueError:
        skip = 1  # Es encabezado
    # Intentar leer con diferentes separadores
    try:
        datos = pd.read_csv(archivo, sep=r"\s+", comment='#', header=None, skiprows=skip, dtype={0: float, 1: float})
    except:
        datos = pd.read_csv(archivo, sep=';', comment='#', header=None, skiprows=skip, dtype={0: float, 1: float})
    return (datos)

def detectar_region_plana(archivo, ventana=100, suavizado=10, rango_central=(0.95, 1.05)):
    
    # Cargar datos
    datos = cargar_datos(archivo)
    
    longitudes_onda = datos.iloc[:, 0].values
    intensidades = datos.iloc[:, 1].values
    
    # Aplicar suavizado si es necesario
    if suavizado > 1:
        intensidades_suavizadas = uniform_filter1d(intensidades, size=suavizado)
    else:
        intensidades_suavizadas = intensities
    
    # Calcular la media y desviación estándar en ventanas móviles
    medias = np.array([np.mean(intensidades_suavizadas[i:i+ventana]) for i in range(len(intensidades_suavizadas) - ventana)])
    stds = np.array([np.std(intensidades_suavizadas[i:i+ventana]) for i in range(len(intensidades_suavizadas) - ventana)])
    
    # Filtrar regiones que estén dentro del rango dado
    indices_planos = np.where((medias >= rango_central[0]) & (medias <= rango_central[1]) & (stds < np.median(stds) * 0.5))[0]
    
    if len(indices_planos) == 0:
        print("No se encontró una región plana con los criterios dados.")
        return None
    
    # Seleccionar la primera región plana detectada
    idx_mejor_region = indices_planos[0]
    mejor_media = medias[idx_mejor_region]
    mejor_std = stds[idx_mejor_region]
    region_x = longitudes_onda[idx_mejor_region:idx_mejor_region+ventana]
    region_y = intensidades[idx_mejor_region:idx_mejor_region+ventana]
    
    return mejor_media, mejor_std


def sonificar_galaxia(
    archivo,
    tipo_galaxia,
    rango_onda=(6500, 6700),
    tempo=200,
    duracion_nota=0.5,
    salida_midi_emision=None,
    salida_midi_absorcion=None,
    salida_midi_completo=None,
    ventana=100,
    suavizado=10,
    rango_central=(0.95, 1.05),
    instrumento_emision=0,
    instrumento_absorcion=24,
    nombre_archivo=None,
    escala="pentatonica_am",  # <-- Nuevo parámetro
    num_octavas=5, # Nueva variable
    notas_escala=None
):
    # Cargar datos
    datos = cargar_datos(archivo)
    todas_wavelengths = datos.iloc[:, 0].values
    todas_intensities = datos.iloc[:, 1].values
    mask = (datos.iloc[:, 0] >= rango_onda[0]) & (datos.iloc[:, 0] <= rango_onda[1])
    wavelengths = datos.iloc[:, 0][mask].values
    intensities = datos.iloc[:, 1][mask].values
    mean_intensity, std_intensity = detectar_region_plana(archivo, ventana, suavizado, rango_central)

    if mean_intensity is None or std_intensity is None:
        print("No se puede continuar con la sonificación sin una región plana válida.")
        return

    min_intensity = np.min(todas_intensities)
    max_intensity = np.max(todas_intensities)
    archivo_nombre = os.path.splitext(os.path.basename(archivo))[0]

    # Definir nombres de salida personalizados si no se pasan explícitamente
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if salida_midi_emision is None:
        salida_midi_emision = os.path.join(output_dir, f"{archivo_nombre}_emisión.mid")
    if salida_midi_absorcion is None:
        salida_midi_absorcion = os.path.join(output_dir, f"{archivo_nombre}_absorción.mid")
    if salida_midi_completo is None:
        salida_midi_completo = os.path.join(output_dir, f"{archivo_nombre}.mid")


    # Definir la escala pentatónica con nombres de notas
    # Definir las escalas
    escalas = {
        "pentatonica_am": [("A", 69), ("C", 72), ("D", 74), ("E", 76), ("G", 79)],
        "armonica_am": [("A", 69), ("B", 71), ("C", 72), ("D", 74), ("E", 76), ("F", 77), ("G#", 80)],
        "mayor_a": [("A", 69), ("B", 71), ("C#", 73), ("D", 74), ("E", 76), ("F#", 78), ("G#", 80)],
        "menor_a": [("A", 69), ("B", 71), ("C", 72), ("D", 74), ("E", 76), ("F", 77), ("G", 79)]
    }
    pentatonic_scale = escalas.get(escala, escalas["pentatonica_am"])
    
    # Ajustar el rango de octavas basado en num_octavas
    # Ajustar el rango de octavas basado en num_octavas y el instrumento
    # Instrumentos con registro más agudo (ej. Flauta, Violín) pueden necesitar un C4 (MIDI 48)
    # Otros instrumentos pueden comenzar en C3 (MIDI 36)
    if instrumento_emision in [73, 40] or instrumento_absorcion in [73, 40]: # 73 es Flauta, 40 es Violín
        min_midi_note = 48 # C4
    else:
        min_midi_note = 36 # C3
    max_midi_note = min_midi_note + (num_octavas * 12) - 1
    
    notas_cromaticas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    full_chromatic_scale = []
    for midi_val in range(min_midi_note, max_midi_note + 1):
        octave_num = (midi_val // 12) - 1 # MIDI octave number
        note_name_idx = midi_val % 12
        full_chromatic_scale.append((notas_cromaticas_base[note_name_idx] + str(octave_num), midi_val))
    num_notes = len(full_chromatic_scale)

    # Aquí el step_size depende del tipo de galaxia
    if tipo_galaxia.lower() == "espiral":
        step_size = 8 / num_notes  # Rango máximo de espirales es 8
    elif tipo_galaxia.lower() == "elíptica":
        step_size = 2 / num_notes # Rango máximo de elípticas es 2
    else:
        step_size = (max_intensity - min_intensity) / num_notes  # por defecto

    midi_emision = MIDIFile(1)
    midi_absorcion = MIDIFile(1)
    midi_emision.addTempo(0, 0, tempo)
    midi_absorcion.addTempo(0, 0, tempo)
    midi_completo = MIDIFile(2)
    midi_completo.addTempo(0, 0, tempo)
    midi_completo.addTempo(1, 0, tempo)
    # --- AÑADE ESTAS LÍNEAS PARA ASIGNAR INSTRUMENTOS ---
    midi_emision.addProgramChange(0, 0, 0, instrumento_emision)
    midi_absorcion.addProgramChange(0, 0, 0, instrumento_absorcion)
    midi_completo.addProgramChange(0, 0, 0, instrumento_emision)      # Canal 0: emisión
    midi_completo.addProgramChange(1, 1, 0, instrumento_absorcion)    # Canal 1: absorción
    puntos_sonificados = []
    # Escala seleccionada por el usuario
    # notas_escala contains the intervals (0-11) for the selected scale
    notas_escala_set = set(notas_escala)

    # Aquí filtras o coloreas según la escala seleccionada por el usuario
    for i, intensity in enumerate(intensities):
        index = int((intensity - min_intensity) / step_size)
        index = max(0, min(index, num_notes - 1)) # Usar num_notes de la escala cromática
        note_name_full, note = full_chromatic_scale[index]
        # Find the nearest note in the selected scale
        final_note = note
        if (note % 12) not in notas_escala_set:
            # Search for the nearest note in the scale, both upwards and downwards
            found_nearest = False
            for j in range(1, max(num_notes, 12)): # Search up to an octave or full range
                # Check upwards
                if note + j <= max_midi_note and ((note + j) % 12) in notas_escala_set:
                    final_note = note + j
                    found_nearest = True
                    break
                # Check downwards
                if note - j >= min_midi_note and ((note - j) % 12) in notas_escala_set:
                    final_note = note - j
                    found_nearest = True
                    break
            if not found_nearest:
                # If no nearest note found within reasonable range, default to original note
                # or handle as an error/skip, for now, we'll use the original note
                final_note = note
        tiempo = i * duracion_nota
        if intensity >= mean_intensity: # Emisión
            midi_emision.addNote(0, 0, final_note, tiempo, duracion_nota, 100)
            midi_completo.addNote(0, 0, final_note, tiempo, duracion_nota, 100)
            midi_absorcion.addNote(0, 0, 0, tiempo, duracion_nota, 0)
        else:  # Absorción
            midi_absorcion.addNote(0, 0, final_note, tiempo, duracion_nota, 100)
            midi_completo.addNote(1, 1, final_note, tiempo, duracion_nota, 100)
            midi_emision.addNote(0, 0, 0, tiempo, duracion_nota, 0)
            puntos_sonificados.append((wavelengths[i], intensity))

    # Guardar los archivos MIDI
    with open(salida_midi_emision, "wb") as f:
        midi_emision.writeFile(f)
    with open(salida_midi_absorcion, "wb") as f:
        midi_absorcion.writeFile(f)
    with open(salida_midi_completo, "wb") as f:
        midi_completo.writeFile(f)

    print(f"DEBUG: MIDI Emision Path: {salida_midi_emision}")
    print(f"DEBUG: MIDI Absorcion Path: {salida_midi_absorcion}")
    print(f"DEBUG: MIDI Completo Path: {salida_midi_completo}")
    return salida_midi_emision, salida_midi_absorcion, salida_midi_completo

def tipo(archivo, rango_onda=(3800, 4200)): 
    # Cargar datos
    datos = pd.read_csv(archivo, sep=';')
    
    # Filtrar datos dentro del rango de longitud de onda
    mask = (datos.iloc[:, 0] >= rango_onda[0]) & (datos.iloc[:, 0] <= rango_onda[1])
    wavelengths = datos.iloc[:, 0][mask].values
    intensities = datos.iloc[:, 1][mask].values

    media = np.mean(intensities)

    if media>2:
        tipo = "Irregular"
    if media <2 and media>1:
        tipo = "Espiral"
    if media<1:
        tipo = "Eliptica"


    print(f"Galaxia es {tipo}, con media {media}")
    return(tipo)


def convertir_midi_a_wav(nombre_midi, nombre_wav):
    sf2 = "default.sf2"  # soundfont (asegúrate de tenerlo)
    FluidSynth(sound_font=sf2).midi_to_audio(nombre_midi, nombre_wav)
    
def convertir_midi_a_wav_musescore(midi_file, wav_file, musescore_path="C:/Program Files/MuseScore 4/bin/MuseScore4.exe"):
    """
    Convierte un archivo MIDI a WAV usando MuseScore 4.
    """
    if not os.path.isfile(musescore_path):
        raise FileNotFoundError("MuseScore no se encontró en la ruta indicada.")

    subprocess.run([musescore_path, midi_file, "-o", wav_file], check=True)
    
def mezclar_wavs(wav1, wav2, salida="mezcla.wav"):
    audio1 = AudioSegment.from_wav(wav1)
    audio2 = AudioSegment.from_wav(wav2)
    mezcla = audio1.overlay(audio2)
    mezcla.export(salida, format="wav")


def graficar_galaxia_plotly(
    archivo,
    tipo_galaxia,
    rango_onda=(6500, 6700),
    ventana=100,
    suavizado=10,
    rango_central=(0.95, 1.05),
    escala="pentatonica_am",
    cantidad_de_octavas=5,
    nombre_archivo=None,
    num_octavas=5,
    notas_escala=None
):
    # Ensure notas_escala is a list, default to chromatic scale if None
    if notas_escala is None:
        notas_escala = list(range(12)) # Default to chromatic scale (0-11)
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Cargar datos
    datos = cargar_datos(archivo)
    todas_wavelengths = datos.iloc[:, 0].values
    todas_intensities = datos.iloc[:, 1].values
    mask = (datos.iloc[:, 0] >= rango_onda[0]) & (datos.iloc[:, 0] <= rango_onda[1])
    wavelengths = datos.iloc[:, 0][mask].values
    intensities = datos.iloc[:, 1][mask].values
    mean_intensity, std_intensity = detectar_region_plana(archivo, ventana, suavizado, rango_central)

    if mean_intensity is None or std_intensity is None:
        print("No se puede graficar sin una región plana válida.")
        return

    min_intensity = np.min(todas_intensities)
    max_intensity = np.max(todas_intensities)
    archivo_nombre_base = os.path.splitext(os.path.basename(archivo))[0]

    # Definir las escalas
    escalas = {
        "pentatonica_am": [("A", 69), ("C", 72), ("D", 74), ("E", 76), ("G", 79)],
        "armonica_am": [("A", 69), ("B", 71), ("C", 72), ("D", 74), ("E", 76), ("F", 77), ("G#", 80)],
        "mayor_a": [("A", 69), ("B", 71), ("C#", 73), ("D", 74), ("E", 76), ("F#", 78), ("G#", 80)],
        "menor_a": [("A", 69), ("B", 71), ("C", 72), ("D", 74), ("E", 76), ("F", 77), ("G", 79)]
    }
    pentatonic_scale = escalas.get(escala, escalas["pentatonica_am"])
    octavas = [-24, -12, 0, 12, 24, 36, 48]
    full_scale = [(name, note + octave) for octave in octavas for name, note in pentatonic_scale]
    num_notes = cantidad_de_octavas * 12

    # Aquí el step_size depende del tipo de galaxia
    if tipo_galaxia.lower() == "espiral":
        step_size = 8 / num_notes  # Rango máximo de espirales es 8
    elif tipo_galaxia.lower() == "elíptica":
        step_size = 2 / num_notes # Rango máximo de elípticas es 2
    else:
        step_size = (max_intensity - min_intensity) / num_notes  # por defecto

    # Escala cromática completa (por ejemplo, C1-B6)
    notas_cromaticas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    full_chromatic_scale = []
    for octava in range(num_octavas):
        for i, name in enumerate(notas_cromaticas):
            # MIDI notes for C4 (middle C) is 60. C1 is 36. C-2 is 0.
            # We want to start from C2 (MIDI 48) for better audibility/visualization
            full_chromatic_scale.append((name, 48 + (12 * octava) + i))
    
    # Filter full_chromatic_scale based on notas_escala (MIDI values)
    # notas_escala contains the intervals (0-11) for the selected scale
    # We need to check if the MIDI note's pitch class is in notas_escala
    notas_escala_set = set(notas_escala)

    # Mapeo de colores para cada nota (similar a sonificar_galaxia)
    note_colors = {
        "C": "green",
        "C#": "yellowgreen",
        "D": "orange",
        "D#": "gold",
        "E": "purple",
        "F": "cyan",
        "F#": "deepskyblue",
        "G": "red",
        "G#": "indigo",
        "A": "blue",
        "A#": "magenta",
        "B": "pink"
    }

    # Mapeo de colores para cada nota (similar a sonificar_galaxia)
    note_colors = {
        "C": "green",
        "C#": "yellowgreen",
        "D": "orange",
        "D#": "gold",
        "E": "purple",
        "F": "cyan",
        "F#": "deepskyblue",
        "G": "red",
        "G#": "indigo",
        "A": "blue",
        "A#": "magenta",
        "B": "pink"
    }

    fig = go.Figure()

    # --- GRÁFICO COMBINADO ---
    # Espectro completo
    fig.add_trace(go.Scatter(
        x=todas_wavelengths, 
        y=todas_intensities, 
        mode='lines', 
        name='Espectro completo', 
        line=dict(color='gray', width=1), 
        showlegend=True
     ))

    # Región sonificada (axvspan equivalente)
    fig.add_shape(type="rect",
        x0=rango_onda[0], y0=0, x1=rango_onda[1], y1=1.05 * max_intensity, # Ajustar y1 si es necesario
        line=dict(width=0),
        fillcolor="yellow",
        opacity=0.3,
        layer="below"
    )
    fig.add_annotation(x=(rango_onda[0] + rango_onda[1]) / 2, y=1.02 * max_intensity, text="Región sonificada", showarrow=False)

    # Separar puntos de absorción y emisión en la región sonificada
    absorcion_mask = intensities < mean_intensity
    emision_mask = intensities >= mean_intensity

    fig.add_trace(go.Scatter(
        x=wavelengths[absorcion_mask], 
        y=intensities[absorcion_mask], 
        mode='markers', 
        marker=dict(color='blue', size=5), 
        name='Absorción (Azul)', 
        showlegend=True
     ))
    fig.add_trace(go.Scatter(
        x=wavelengths[emision_mask], 
        y=intensities[emision_mask], 
        mode='markers', 
        marker=dict(color='red', size=5), 
        name='Emisión (Roja)', 
        showlegend=True
     ))

    # Líneas horizontales para las notas
    for i, note_info in enumerate(full_chromatic_scale):
        note_name_full = note_info[0]
        note_midi = note_info[1]
        note_base_name = ''.join([i for i in note_name_full if not i.isdigit()]) # Extract C, C#, D, etc.

        # Calcular la posición Y de la línea
        # Asegurarse de que la intensidad mapeada esté dentro del rango de la gráfica
        y_pos = min_intensity + (note_midi - min(n[1] for n in full_chromatic_scale)) * (max_intensity - min_intensity) / (max(n[1] for n in full_chromatic_scale) - min(n[1] for n in full_chromatic_scale))

        # Asignar color y nombre de la nota
        color = note_colors.get(note_base_name, "lightgray") # Usar get para evitar KeyError
        
        # Solo graficar si la nota está en la escala seleccionada
        # Check if the pitch class of the current note_midi is in notas_escala_set
        if (note_midi % 12) in notas_escala_set:
            fig.add_hline(y=y_pos, line_dash="dot", line_color=color, line_width=1,
                          annotation_text=note_name_full, annotation_position="right",
                          annotation_font_color=color)

    fig.update_layout(
        title_text=f"Espectro Galáctico y Sonificación de {nombre_archivo if nombre_archivo else archivo_nombre_base}",
        xaxis_title="Longitud de onda (Å)",
        yaxis_title="Intensidad normalizada",
        height=700, # Ajustar altura para una sola gráfica
        showlegend=True,
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
        yaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
        legend=dict(font=dict(color='black'))
    )

    return fig

