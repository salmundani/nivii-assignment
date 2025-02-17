FROM python:3.12-slim

WORKDIR /code

RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    apt-get clean

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app /code/app/
EXPOSE 80

CMD ["fastapi", "run", "app/main.py", "--port", "80"]