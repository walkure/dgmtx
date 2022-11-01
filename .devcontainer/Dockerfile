ARG PYTHON_VER=3.11.0

FROM python:${PYTHON_VER}-slim-buster
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get -y update && apt-get upgrade -qqy && apt-get -y install \
    bash curl git
    
RUN pip install -U setuptools flake8 black
ENV PATH /root/.local/bin:$PATH
