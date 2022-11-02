ARG PYTHON_VER=3.11.0

FROM python:${PYTHON_VER}-slim-buster as builder

COPY requirements.lock .
RUN pip3 install -r requirements.lock

FROM python:${PYTHON_VER}-slim-buster as runner

ARG PYTHON_VER=3.11
COPY --from=builder /usr/local/lib/python${PYTHON_VER}/site-packages /usr/local/lib/python${PYTHON_VER}/site-packages

COPY ./dgmtx.py .

ENTRYPOINT ["./dgmtx.py","-s","/state/laststate.json","-c","/conf/config.ini"]
