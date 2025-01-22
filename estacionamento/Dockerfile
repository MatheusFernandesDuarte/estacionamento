FROM python:3.10-slim

WORKDIR /estacionamento

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
&& rm -rf ~/.cache/pip

COPY src/ src/

ENV PYTHONPATH="/estacionamento/src"

CMD ["python", "src/app.py"]
