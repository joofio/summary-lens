FROM python:3.10-slim

# Install dependencies
RUN mkdir /app
WORKDIR /app


COPY lens_app /app/lens_app

ENV VIRTUAL_ENV=/usr/local
RUN python3 -m pip install pip --upgrade
RUN python3 -m pip install uv

COPY requirements.txt /app
COPY run.py /app
COPY gunicorn.sh /app

RUN uv pip install -r requirements.txt

EXPOSE 80

RUN ["chmod", "+x", "./gunicorn.sh"]

ENTRYPOINT ["./gunicorn.sh"]
