# I observed some odd characters being displayed when soundcurses is run from
# a Docker container. Not sure if an artifact from Docker terminal or from the
# python:3 image C.UTF-8 locale.

FROM python:3-slim

WORKDIR /usr/src/app

COPY . .

RUN ["pip", "install", "-r", "requirements.txt"]

CMD ["python", "./soundcurses.py"]
