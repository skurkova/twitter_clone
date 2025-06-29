FROM python:3.9

RUN apt-get update && apt-get install -y python3-dev && rm -rf /var/lib/apt/lists/*

COPY /server/requirements.txt /server/requirements.txt
RUN pip install -r /server/requirements.txt

COPY /server /server

WORKDIR /server

CMD ["sh", "-c", "gunicorn api.main:app --bind 0.0.0.0:5000 --workers 3 --log-level debug"]