FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y apt-transport-https ca-certificates gnupg curl
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update &&  apt-get install -y google-cloud-sdk

RUN mkdir -p /app
WORKDIR /app
COPY ./src/* .
COPY ./vm/scl-orchestration-vm.jinja .
COPY ./vm/run.sh .