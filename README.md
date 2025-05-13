# 🌌 Sonificación de Galaxias

Este proyecto convierte datos astronómicos (como espectros de galaxias) en música utilizando archivos MIDI y sonido reproducible en la web.

Ideal para divulgación, investigación o simplemente para disfrutar cómo suena el universo 🚀🎶

---

## 📦 Requisitos

### 1. Tener Python 3.8 o superior

Usamos un entorno virtual, creado automáticamente por PyCharm o manualmente con `venv`.

---

### 2. Instalar dependencias de Python

Abre la terminal dentro del proyecto o usa la terminal de PyCharm:

```bash
pip install -r requirements.txt
```

Incluye:
- `streamlit`
- `numpy`
- `matplotlib`
- `midiutil`
- `midi2audio`
- `plotly`

---

### 3. Instalar **FluidSynth**

Este programa convierte archivos MIDI a audio real (.wav).

#### 🔧 En Windows:

1. Descarga desde:  
   [https://github.com/FluidSynth/fluidsynth/wiki/Download#windows](https://github.com/FluidSynth/fluidsynth/wiki/Download#windows)

2. Extrae la carpeta y agrega el subdirectorio `bin/` al **PATH** de tu sistema.

3. Verifica que funcione abriendo una terminal y ejecutando:

```bash
fluidsynth --version
```

---

### 4. Descargar SoundFont 🎵

Este archivo define los instrumentos para generar el audio:

- Recomendado: [FluidR3_GM.sf2](https://member.keymusician.com/Member/FluidR3_GM/index.html)

Guárdalo en la carpeta raíz del proyecto, como:

```
TesisAlex/
├── app.py
├── FluidR3_GM.sf2
```

---

# 🌌 Sonificación de Galaxias
## 🚀 Ejecutar la aplicación

Desde la raíz del proyecto, corre:

```bash
streamlit run app.py
```

Esto abrirá una página web local donde podrás:

✅ Seleccionar galaxias  
✅ Visualizar los datos astronómicos  
✅ Convertirlos en notas musicales (MIDI)  
✅ Escuchar la música directamente  
✅ Descargar el archivo MIDI

---

## 📁 Estructura del proyecto

```
TesisAlex/
├── app.py                 # App principal (Streamlit)
├── FluidR3_GM.sf2         # SoundFont (audio)
├── data/                  # Archivos .txt con datos galácticos
├── src/
│   ├── data_loader.py     # Lectura de datos
│   ├── sound_mapper.py    # Conversión de datos a notas
│   └── midi_generator.py  # Creación de MIDI y conversión a WAV
├── requirements.txt       # Dependencias del proyecto
```

---

## 🎁 Créditos

- Código estructurado por [@raptorf2286](https://github.com/raptorf2286)
- Inspirado por la pasión de un astrónomo que quiere escuchar el universo 💫  [@AlexVel](https://github.com/AlexVel)

🤖 Asistencia técnica brindada por una IA colaborativa, 
con alma de sintetizador y oído cósmico para galaxias en clave de Sol.

![image](https://github.com/user-attachments/assets/6c8b6c94-1e56-4802-b4ad-ea9ef4430b46)

