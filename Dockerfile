FROM python:3.10

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fluidsynth \
    libfluidsynth3 \
    fluid-soundfont-gm \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

