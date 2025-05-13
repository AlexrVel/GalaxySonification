FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    apt-utils \
    build-essential \
    fluidsynth \
    libfluidsynth2 \
    soundfont-fluid-gm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
