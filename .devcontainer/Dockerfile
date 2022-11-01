ARG PYTHON_VER=3.11.0

FROM python:${PYTHON_VER}-slim-buster
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get -y update && apt-get upgrade -qqy && apt-get -y install \
    bash curl git

RUN bash -c "$(curl -fsSL "https://raw.githubusercontent.com/microsoft/vscode-dev-containers/main/script-library/common-debian.sh")" \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN pip install -U setuptools flake8 black
ENV PATH /root/.local/bin:$PATH
