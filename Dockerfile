FROM python:3.8.6-buster

ENV PROJECT_ID=wagon-bootcamp-633

COPY api /api
COPY MRIsegmentation /MRIsegmentation
COPY requirements.txt /requirements.txt
COPY vgg19_final.h5 /vgg19_final.h5

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD uvicorn api.simple:app --host 0.0.0.0 --port $PORT
