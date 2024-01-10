FROM ghcr.io/binkhq/python:3.10 as build

ENV VENV /app/venv

WORKDIR /src
ADD . .
ARG AZURE_DEVOPS_PAT
ENV VIRTUAL_ENV=$VENV
ENV PATH=$VENV/bin:$PATH

# gcc required for hiredis and git for poetry-dynamic-versioning
RUN apt update && apt -y install git gcc
RUN pip install poetry==1.7.1
RUN poetry config http-basic.azure jeff $AZURE_DEVOPS_PAT
RUN poetry self add poetry-dynamic-versioning[plugin]
RUN python -m venv $VENV
RUN poetry install --without=dev --no-root
RUN poetry build
RUN pip install dist/*.whl

FROM ghcr.io/binkhq/python:3.10

WORKDIR /app
ENV VENV /app/venv
ENV PATH="$VENV/bin:$PATH"
ENV PROMETHEUS_MULTIPROC_DIR=/dev/shm

COPY --from=build $VENV $VENV
COPY --from=build /src/asgi.py .

ENV PROMETHEUS_MULTIPROC_DIR=/dev/shm
CMD [ "gunicorn", "--workers=2", "--threads=2", "--error-logfile=-", \
    "--access-logfile=-", "--bind=0.0.0.0:9000", "wsgi:app" ]
