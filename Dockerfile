FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
ENV VIRTUAL_ENV=/home/appuser/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG WAVE_VERSION="1.1.1"

# Install OS dependencies
RUN apt-get update && apt-get -y upgrade \
    && apt-get -y install --no-install-recommends curl

RUN curl -L https://github.com/h2oai/wave/releases/download/v${WAVE_VERSION}/wave-${WAVE_VERSION}-linux-amd64.tar.gz -o wave-${WAVE_VERSION}-linux-amd64.tar.gz \
    && tar -xzf wave-${WAVE_VERSION}-linux-amd64.tar.gz \
    && mv wave-${WAVE_VERSION}-linux-amd64 /usr/wave

# Set permissions for the Entrypoint script
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT [ "./docker-entrypoint.sh" ]
