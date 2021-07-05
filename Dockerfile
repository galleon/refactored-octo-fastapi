FROM python:3.8.6-buster
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY app /app
COPY requirements.txt /requirements.txt
CMD uvicorn app.simple:app --host 0.0.0.0
