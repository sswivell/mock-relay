# syntax=docker/dockerfile:1

# Build a wheel from the tagged source, then ship it on a slim runtime image
# so the image carries no compiler and no git.
FROM python:3.12-slim AS build

WORKDIR /src
COPY . /src

RUN python -m pip install --no-cache-dir build \
 && python -m build --wheel --outdir /dist


FROM python:3.12-slim

LABEL org.opencontainers.image.title="MockRelay" \
      org.opencontainers.image.description="Record real HTTP traffic once, replay it offline and deterministically." \
      org.opencontainers.image.source="https://github.com/sswivell/mock-relay" \
      org.opencontainers.image.licenses="MIT"

RUN --mount=type=bind,from=build,source=/dist,target=/dist \
    python -m pip install --no-cache-dir /dist/*.whl

WORKDIR /work
VOLUME ["/work/fixtures"]

# 8080 is the proxy, 8081 is the admin UI and metrics.
EXPOSE 8080 8081

ENTRYPOINT ["mockrelay"]
CMD ["serve"]