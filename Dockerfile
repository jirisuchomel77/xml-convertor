FROM python:3.9-slim-bullseye

ENV PYTHONPATH=/app
WORKDIR /app
RUN pip3 install --upgrade pip

RUN pip3 install 'poetry==1.8.3'
COPY . .

RUN poetry install
