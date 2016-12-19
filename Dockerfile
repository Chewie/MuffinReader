FROM python:2-onbuild
MAINTAINER Kévin Sztern <sztern.kevin@gmail.com>
CMD [ "gunicorn", "-b", "0.0.0.0:8000", "news:app" ]
