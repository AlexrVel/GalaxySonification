# app.py
import streamlit as st
import os
from src.data_loader import load_galaxy_data, list_available_galaxies
from src.sound_mapper import map_values_to_midi_notes, map_to_velocity
from src.midi_generator import create_midi_file
import plotly.graph_objects as go
from src.midi_generator import convert_midi_to_wav
from funciones import sonificar_galaxia

# Constantes locales
DATA_DIR = "data"
MIDI_OUTPUT = "output.mid"
WAV_OUTPUT = "output.wav"
SOUNDFONT_PATH = "FluidR3_GM.sf2"
#SOUNDFONT_PATH = "GeneralUser-GS.sf2"

# Streamlit le crea webs sin complique y las llama desde python
st.set_page_config(page_title="Sonificación Galáctica", layout="centered")
st.title("🌌 Sonificación de Galaxias")
st.write("Convierte datos astronómicos en música 🎶 usando MIDI")

# Paso 1: Selección de galaxia
galaxias = list_available_galaxies(DATA_DIR)
galaxia = st.selectbox("Selecciona una galaxia:", galaxias)

# Nuevo: Menú para elegir el tipo de galaxia
tipo_galaxia = st.radio("Selecciona el tipo de galaxia para la sonificación:", ("Espiral", "Elíptica"))

if galaxia:
    file_path = os.path.join(DATA_DIR, galaxia)
    data = load_galaxy_data(file_path)

    if data is not None:
        # Paso 3: Generar MIDI (move this block up if needed)
        st.subheader("🎼 Generar sonido")
        scale_range = st.slider("Rango de notas (C3 a C5)", 36, 84, (60, 72))
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
        min_wavelength = float(data[:, 0].min())
        max_wavelength = float(data[:, 0].max())
        rango_onda = st.slider(
            "Rango de longitudes de onda a sonificar",
            min_value=min_wavelength,
            max_value=max_wavelength,
            value=(min_wavelength, max_wavelength),
            step=0.1
        )

        # Paso 2: Visualización
        st.subheader("🔭 Visualización de datos")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1], mode='lines', name=galaxia))
        fig.add_vrect(
            x0=rango_onda[0], x1=rango_onda[1],
            fillcolor="orange", opacity=0.3,
            layer="below", line_width=0,
            annotation_text="Región sonificada", annotation_position="top left"
        )
        # Agregar líneas horizontales para las notas MIDI seleccionadas
        min_intensity = float(data[:, 1].min())
        max_intensity = float(data[:, 1].max())
        # Determinar el número de notas igual que en la sonificación
        num_notes = scale_range[1] - scale_range[0] + 1
        step_size = (max_intensity - min_intensity) / num_notes
        # Líneas horizontales en los umbrales de intensidad de cada nota
        for i in range(num_notes + 1):
            intensity_value = min_intensity + i * step_size
            fig.add_hline(
                y=intensity_value,
                line=dict(color="gray", width=1, dash="dot"),
                opacity=0.3,
                annotation_text=f"Umbral nota {i+scale_range[0]}",
                annotation_position="right"
            )
        fig.update_layout(title=f"Datos de {galaxia}", xaxis_title="X", yaxis_title="Y")
        st.plotly_chart(fig)

        # Opciones de sonificación e instrumentos (debajo de la gráfica)
        st.subheader("🎼 Opciones de Sonificación")
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

        if st.button("🎹 Generar MIDI"):
            # Lógica unificada usando la función nueva
            nombre_base = os.path.splitext(galaxia)[0]
            salida_midi_emision = f"{nombre_base}_emision.mid"
            salida_midi_absorcion = f"{nombre_base}_absorcion.mid"
            salida_midi_completo = f"{nombre_base}_completo.mid"
            salida_wav_emision = f"{nombre_base}_emision.wav"
            salida_wav_absorcion = f"{nombre_base}_absorcion.wav"
            salida_wav_completo = f"{nombre_base}_completo.wav"

            sonificar_galaxia(
                file_path,
                tipo_galaxia,
                rango_onda=rango_onda,
                tempo=tempo,
                duracion_nota=duracion_nota,
                salida_midi_emision=salida_midi_emision,
                salida_midi_absorcion=salida_midi_absorcion,
                salida_midi_completo=salida_midi_completo,
                instrumento_emision=instrumentos_midi[instrumento_emision],
                instrumento_absorcion=instrumentos_midi[instrumento_absorcion],
                nombre_archivo=nombre_base
            )
            # Convertir los MIDIs a WAV para previsualización
            try:
                convert_midi_to_wav(salida_midi_emision, salida_wav_emision, SOUNDFONT_PATH)
            except Exception as e:
                st.warning(f"No se pudo convertir {salida_midi_emision} a WAV: {e}")
            try:
                convert_midi_to_wav(salida_midi_absorcion, salida_wav_absorcion, SOUNDFONT_PATH)
            except Exception as e:
                st.warning(f"No se pudo convertir {salida_midi_absorcion} a WAV: {e}")
            try:
                convert_midi_to_wav(salida_midi_completo, salida_wav_completo, SOUNDFONT_PATH)
            except Exception as e:
                st.warning(f"No se pudo convertir {salida_midi_completo} a WAV: {e}")

            st.success("✅ Archivos MIDI generados correctamente.")
            midi_generado = True

        # Paso 4: Descargar y reproducir los tres MIDIs y WAVs por separado
        if midi_generado:
            # Mezclar los WAV de emisión y absorción para previsualización
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
                st.subheader("🔊 Previsualizar sonido (Emisión + Absorción)")
                st.audio(wav_mix, format="audio/wav")
                st.caption("La región resaltada en la gráfica corresponde a la sección sonificada. La barra de audio te permite escuchar esa sección.")
            else:
                st.warning("No se encontraron ambos archivos de emisión y absorción para la mezcla.")

            # Botones de descarga para los tres MIDIs y WAVs
            for archivo_midi, archivo_wav, label in [
                (f"{os.path.splitext(galaxia)[0]}_emision.mid", f"{os.path.splitext(galaxia)[0]}_emision.wav", "Emisión"),
                (f"{os.path.splitext(galaxia)[0]}_absorcion.mid", f"{os.path.splitext(galaxia)[0]}_absorcion.wav", "Absorción"),
                (f"{os.path.splitext(galaxia)[0]}_completo.mid", f"{os.path.splitext(galaxia)[0]}_completo.wav", "Completo"),
            ]:
                if os.path.exists(archivo_midi):
                    with open(archivo_midi, "rb") as f:
                        st.download_button(f"⬇️ Descargar MIDI {label}", f, file_name=archivo_midi)
                if os.path.exists(archivo_wav):
                    with open(archivo_wav, "rb") as f:
                        st.download_button(f"⬇️ Descargar WAV {label}", f, file_name=archivo_wav)
            st.info("🎧 Consejo: Si el archivo MIDI te suena raro, intenta bajar el rango de notas o tempo.")
