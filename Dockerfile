FROM ubuntu

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt-get -y install python3-dev libopus0 ffmpeg make python3-pip git
COPY . /app
ENV PAFY_BACKEND=internal
RUN make install
ENV PAFY_BACKEND=



CMD ["python3", "-m", "riffbot", "-c", "config.ini"]
