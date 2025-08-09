FROM nvidia/cuda:12.9.1-runtime-ubuntu22.04

LABEL maintainer="RuVl"

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Set enviroment variables
ENV TZ="Europe/Moscow"
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONUNBUFFERED=1

# Project directory
WORKDIR /usr/src/app

# Copy and install requirements
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir tensorflow[and-cuda]==2.19.0

# Copy project to directory
COPY . ./

ENTRYPOINT ["python3", "run.py"]