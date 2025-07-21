FROM python:3.9

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /server/requirements.txt
RUN pip install --no-cache-dir -r /server/requirements.txt

COPY server /server

ENV PYTHONPATH=/server

WORKDIR /server

CMD ["sh", "-c", "gunicorn api.wsgi:app --bind 0.0.0.0:5000 --log-level debug"]