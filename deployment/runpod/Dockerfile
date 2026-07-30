# syntax=docker/dockerfile:1.7
FROM --platform=linux/amd64 kosinskilab/alphafold2:2.5.0@sha256:434704a18e24d59de7cbfd6f7cdc310d5dce03ded6cf91c4927b6e2c9e87110c

ARG TARGETARCH
ARG ALPHAPULLDOWN_INPUT_PARSER_VERSION=0.5.1

LABEL org.opencontainers.image.title="AlphaPulldown DNAAF screen RunPod runtime" \
      org.opencontainers.image.description="Docker-native AlphaFold2 runtime for the isolated Milestone 2 benchmark" \
      org.opencontainers.image.source="https://github.com/REPLACE_WITH_OWNER/REPLACE_WITH_REPOSITORY" \
      org.opencontainers.image.base.name="docker.io/kosinskilab/alphafold2:2.5.0" \
      org.opencontainers.image.base.digest="sha256:434704a18e24d59de7cbfd6f7cdc310d5dce03ded6cf91c4927b6e2c9e87110c"

RUN test "${TARGETARCH:-amd64}" = "amd64" \
    && python -m pip install --no-cache-dir \
        "alphapulldown-input-parser==${ALPHAPULLDOWN_INPUT_PARSER_VERSION}"

WORKDIR /opt/alphapulldown-project
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps .

ENV ALPHAPULLDOWN_BASE_IMAGE_DIGEST="sha256:434704a18e24d59de7cbfd6f7cdc310d5dce03ded6cf91c4927b6e2c9e87110c" \
    ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST="UNBUILT" \
    PYTHONUNBUFFERED="1"

WORKDIR /workspace
CMD ["sleep", "infinity"]
