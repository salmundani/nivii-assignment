FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    apt-get clean

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .

EXPOSE 5000

CMD ["flask", "run", "--host", "0.0.0.0"]
