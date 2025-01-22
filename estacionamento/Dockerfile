FROM python:3.10-alpine

WORKDIR /estacionamento

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY src/ src/

ENV PYTHONPATH="/estacionamento/src"

CMD ["python", "src/app.py"]
