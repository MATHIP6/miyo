FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/


COPY ./src /app/src
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN if [ -n "$HOST_ADDRESS" ]; then \
    echo "HOST_ADDRESS=$HOST_ADDRESS" > .env; \
    fi
CMD ["python", "src/main.py"]
