import os

import pandas as pd

def load_galaxy_data(file_path):
    try:
        df = pd.read_csv(file_path, delimiter=';', comment='#')
        return df.values
    except Exception as e:
        print(f"Error cargando archivo {file_path}: {e}")
        return None

def list_available_galaxies(data_dir):
    """
    Lista todos los archivos .txt disponibles en el directorio de datos.
    """
    return [f for f in os.listdir(data_dir) if f.endswith(".txt")]
