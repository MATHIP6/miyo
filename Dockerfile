FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/


COPY ./src /app/src
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV HOST_ADDRESS="127.0.0.1"
ENV UPSTREAM_DNS="1.1.1.1"
ENV UPSTREAM_PORT=53

CMD ["python", "src/main.py"]
