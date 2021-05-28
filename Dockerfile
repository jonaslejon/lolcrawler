FROM alpine:latest

RUN apk update && apk add --no-cache bash \
        alsa-lib \
        at-spi2-atk \
        atk \
        cairo \
        cups-libs \
        dbus-libs \
        eudev-libs \
        expat \
        flac \
        gdk-pixbuf \
        glib \
        libgcc \
        libjpeg-turbo \
        libpng \
        libwebp \
        libx11 \
        libxcomposite \
        libxdamage \
        libxext \
        libxfixes \
        tzdata \
        libexif \
        udev \
        xvfb \
        zlib-dev \
        chromium \
        chromium-chromedriver
RUN apk add --no-cache python3 py3-pip py3-lxml
RUN pip3 install selenium

ADD crawl.py crawl.py
ADD linkfinder.py linkfinder.py
ADD browser_crawl.py browser_crawl.py
ADD requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

RUN adduser -D -g '' basicuser
USER basicuser
ENTRYPOINT ["python3",  "/crawl.py"]
