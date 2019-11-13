FROM python:3.7-alpine

ARG FFMPEG_VERSION=4.2.1

ARG PREFIX=/opt/ffmpeg
ARG LD_LIBRARY_PATH=/opt/ffmpeg/lib
ARG MAKEFLAGS="-j4"

# FFmpeg build dependencies.
RUN apk add --update --no-cache \
  build-base \
  coreutils \
#  freetype-dev \
  gcc \
  lame-dev \
  libressl \
  libxcb \
  libxcb-dev \
  libressl-dev \
#  libogg-dev \
#  libass \
#  libass-dev \
#  libvpx-dev \
#  libvorbis-dev \
#  libwebp-dev \
#  libtheora-dev \
  opus-dev \
  pkgconf \
  pkgconfig \
  rtmpdump-dev \
  wget \
  x264-dev \
  x265-dev \
  yasm \
  supervisor \
  docker \
  git \
  bash \
  python-dev \
  py-pip \
  jpeg-dev \
  zlib-dev \
  musl-dev \
  linux-headers \
  libc-dev

# Get fdk-aac from testing.
RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories && \
  apk add --update fdk-aac-dev

# Get ffmpeg source.
RUN cd /tmp/ && \
  wget http://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.gz && \
  tar zxf ffmpeg-${FFMPEG_VERSION}.tar.gz && rm ffmpeg-${FFMPEG_VERSION}.tar.gz

# Compile ffmpeg.
RUN cd /tmp/ffmpeg-${FFMPEG_VERSION} && \
  ./configure \
  --enable-version3 \
  --enable-gpl \
  --enable-nonfree \
  --enable-small \
  --enable-libxcb \
#  --enable-libmp3lame \
#  --enable-libx264 \
#  --enable-libx265 \
#  --enable-libvpx \
#  --enable-libtheora \
#  --enable-libvorbis \
#  --enable-libopus \
#  --enable-libfdk-aac \
#  --enable-libass \
#  --enable-libwebp \
#  --enable-librtmp \
#  --enable-postproc \
#  --enable-avresample \
#  --enable-libfreetype \
  --enable-openssl \
  --disable-debug \
  --disable-doc \
  --disable-ffplay \
  --extra-cflags="-I${PREFIX}/include" \
  --extra-ldflags="-L${PREFIX}/lib" \
  --extra-libs="-lpthread -lm" \
  --prefix="${PREFIX}" && \
  make && make install && make distclean

ENV LIBRARY_PATH=/lib:/usr/lib
ENV PATH=/opt/ffmpeg/bin:$PATH

RUN apk add --update \
  ca-certificates \
#  openssl \
#  pcre \
#  lame \
#  libogg \
#  libass \
#  libvpx \
#  libvorbis \
#  libwebp \
#  libtheora \
  opus \
  rtmpdump \
  x264-dev \
  x265-dev

RUN rm -rf /var/cache/apk/* /tmp/*

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

ADD setup.py /tmp/setup.py
ADD MANIFEST.in /tmp/MANIFEST.in
ADD requirements.txt /tmp/requirements.txt
COPY galloper /tmp/galloper

RUN cd /tmp && python setup.py install && rm -rf /tmp/*
RUN mkdir /tmp/tasks
ADD start.sh /tmp/start.sh
RUN chmod +x /tmp/start.sh
WORKDIR /tmp
RUN pip install celery==4.3.0
RUN pip install kombu==4.5.0
RUN pip install selenium==3.141.0
RUN pip install git+https://github.com/carrier-io/control_tower.git
RUN echo "Starting point" > /var/log/worker.log

SHELL ["/bin/bash", "-c"]
EXPOSE 5000
ENTRYPOINT ["/tmp/start.sh"]