# src/sound_mapper.py
def map_values_to_midi_notes(data, scale=(60, 72)):
    """
    Convierte valores Y en notas MIDI dentro de un rango dado.
    Retorna una lista de notas.
    """
    y_values = data[:, 1]
    min_val, max_val = y_values.min(), y_values.max()
    midi_min, midi_max = scale

    # Normaliza y escala a notas
    notes = ((y_values - min_val) / (max_val - min_val)) * (midi_max - midi_min) + midi_min
    return notes.astype(int)

def map_to_velocity(data, min_vel=40, max_vel=100):
    """
    Escala el eje Y como velocidad (intensidad).
    """
    y = data[:, 1]
    return ((y - y.min()) / (y.max() - y.min()) * (max_vel - min_vel) + min_vel).astype(int)
