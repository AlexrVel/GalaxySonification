# src/midi_generator.py
from midiutil import MIDIFile
from midi2audio import FluidSynth
import os
import subprocess

def create_midi_file(notes, velocities, output_file="output.mid", tempo=120):
    """
    Genera un archivo MIDI dado un conjunto de notas y velocidades.
    """
    track = 0
    channel = 0
    time = 0  # inicio
    duration = 1  # 1 beat por nota

    midi = MIDIFile(1)  # 1 track
    midi.addTempo(track, time, tempo)

    for i, pitch in enumerate(notes):
        midi.addNote(track, channel, pitch, time + i, duration, int(velocities[i]))

    with open(output_file, "wb") as f:
        midi.writeFile(f)

def convert_midi_to_wav(midi_path, wav_path, soundfont_path="FluidR3_GM.sf2", fluidsynth_path="fluidsynth"):
    """
    Convierte un archivo MIDI a WAV sin consola negra (Windows) y con rutas absolutas seguras.
    """
    midi_path = os.path.abspath(midi_path)
    wav_path = os.path.abspath(wav_path)
    # soundfont_path = os.path.abspath(soundfont_path)  # Línea original
    # soundfont_path = os.path.abspath("FluidR3_GM.sf2")  # Línea original comentada
    soundfont_path = os.path.abspath("GeneralUser-GS.sf2")  # Usar el nuevo SoundFont

    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"MIDI no encontrado: {midi_path}")
    if not os.path.exists(soundfont_path):
        raise FileNotFoundError(f"SoundFont no encontrado: {soundfont_path}")

    command = [
        fluidsynth_path,
        "-ni",
        "-F", wav_path,
        "-r", "44100",
        soundfont_path,
        midi_path
    ]

    print("🔧 Ejecutando comando:", " ".join(command))

    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        subprocess.run(command, check=True, startupinfo=startupinfo)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al ejecutar FluidSynth: {e}")

