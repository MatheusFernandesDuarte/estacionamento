FROM python:3.10

WORKDIR /estacionamento

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH="/estacionamento/src"

CMD ["python", "src/app.py"]
