ARG PYTHON_VER=3.11.0

FROM python:${PYTHON_VER}-slim-buster as builder

COPY requirements.lock .
RUN pip3 install -r requirements.lock

FROM python:${PYTHON_VER}-slim-buster as runner

ARG PYTHON_VER=3.11

RUN addgroup --gid 65532 nonroot && adduser --uid 65532 --ingroup nonroot nonroot
USER nonroot

COPY --from=builder /usr/local/lib/python${PYTHON_VER}/site-packages /usr/local/lib/python${PYTHON_VER}/site-packages
COPY --chown=nonroot:nonroot ./dgmtx.py /app/

ENTRYPOINT ["/app/dgmtx.py","-s","/state/laststate.json","-c","/conf/config.ini"]
