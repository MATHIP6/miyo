FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/


COPY ./src /app/src
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV HOST_ADDRESS="127.0.0.1"

CMD ["python", "src/main.py"]
