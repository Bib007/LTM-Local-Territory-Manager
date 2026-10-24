FROM ghcr.io/home-assistant/base:3.22
ARG BUILD_VERSION
ARG BUILD_ARCH
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="app" io.hass.arch="${BUILD_ARCH}"
RUN apk add --no-cache python3 tesseract-ocr tesseract-ocr-data-dan tesseract-ocr-data-eng
WORKDIR /opt/distrikt
COPY app ./app
COPY templates ./templates
COPY run.sh /run.sh
RUN chmod a+x /run.sh
CMD ["/run.sh"]
