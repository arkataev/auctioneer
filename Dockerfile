FROM python:3-onbuild

COPY . /app
WORKDIR /app
RUN python manage.py collectstatic --noinput
