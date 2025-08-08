FROM python:3.11.13-slim
LABEL authors="RuVl"

# Update packages
RUN apt-get update && apt-get upgrade -y

# Set enviroment variables
ENV TZ="Europe/Moscow"
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONUNBUFFERED=1

# Project directory
WORKDIR /usr/src/app

# Copy and install requirements
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# Copy project to directory
COPY . ./
RUN python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./face.proto

ENTRYPOINT ["python3", "run.py"]