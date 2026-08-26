# syntax=docker/dockerfile:1.7
# Candidate AWS runtime. This image is not approved for biological execution
# until its CPU and GPU smoke tests pass and its derived digest is recorded.

FROM --platform=linux/amd64 mambaorg/micromamba:2.5.0@sha256:07f1a5db3a545a0b1b0b1c8835ba654b67a8479ec77513f2a236f45e6687629b AS micromamba

FROM --platform=linux/amd64 nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04@sha256:1da6cf17f9c651323905c8cf5fd63a781a9a2fc0d28a477ca21df80a7bfaa00c

ARG TARGETARCH
ARG ALPHAPULLDOWN_WHEEL_URL="https://files.pythonhosted.org/packages/f0/9f/bc5f28a5d5317d438a17a67224fbe3c35ac0b6c223f2c425cc5ab409a395/alphapulldown-2.5.0-py3-none-any.whl"
ARG ALPHAPULLDOWN_WHEEL_SHA256="67a8496560fddf9c9570015bf88545e48502fad7cc12f995dc69a5999a0ad75a"
ARG ALPHAPULLDOWN_SOURCE_REVISION="1c99b15ce3fef42374c24a5bd83ce8241117d5f6"

LABEL org.opencontainers.image.title="AlphaPulldown DNAAF screen AWS candidate runtime" \
      org.opencontainers.image.description="AlphaFold2 runtime for the isolated Milestone 2 benchmark" \
      org.opencontainers.image.source="https://github.com/REPLACE_WITH_OWNER/REPLACE_WITH_REPOSITORY" \
      org.opencontainers.image.base.name="docker.io/nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04" \
      org.opencontainers.image.base.digest="sha256:1da6cf17f9c651323905c8cf5fd63a781a9a2fc0d28a477ca21df80a7bfaa00c" \
      org.opencontainers.image.alphapulldown.version="2.5.0" \
      org.opencontainers.image.alphapulldown.revision="${ALPHAPULLDOWN_SOURCE_REVISION}" \
      org.opencontainers.image.alphapulldown.wheel.sha256="${ALPHAPULLDOWN_WHEEL_SHA256}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
USER root
ENV MAMBA_ROOT_PREFIX=/opt/mamba \
    CONDA_PREFIX=/opt/conda \
    PATH=/opt/conda/bin:${PATH} \
    PYTHONUNBUFFERED=1 \
    ALPHAPULLDOWN_SOURCE_REVISION=${ALPHAPULLDOWN_SOURCE_REVISION}

# The pinned mambaorg/micromamba 2.5.0 image exposes its static binary at
# /bin/micromamba (not /usr/local/bin/micromamba).
COPY --from=micromamba /bin/micromamba /usr/local/bin/micromamba
RUN test "${TARGETARCH:-amd64}" = "amd64" \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

COPY deployment/aws/environment-af2.yml /tmp/environment-af2.yml
RUN micromamba create -y -p /opt/conda -f /tmp/environment-af2.yml \
    && micromamba clean --all --yes

COPY deployment/aws/requirements-af2.txt /tmp/requirements-af2.txt
RUN curl --fail --location --silent --show-error \
      --output /tmp/alphapulldown-2.5.0-py3-none-any.whl "${ALPHAPULLDOWN_WHEEL_URL}" \
    && echo "${ALPHAPULLDOWN_WHEEL_SHA256}  /tmp/alphapulldown-2.5.0-py3-none-any.whl" | sha256sum --check \
    && python -m pip install --no-cache-dir -r /tmp/requirements-af2.txt \
    && python -m pip install --no-cache-dir /tmp/alphapulldown-2.5.0-py3-none-any.whl \
    && python -m pip check

WORKDIR /opt/alphapulldown-project
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps . \
    && mkdir -p /opt/alphapulldown-runtime \
    && micromamba list --explicit -p /opt/conda > /opt/alphapulldown-runtime/conda-explicit.txt \
    && python -m pip freeze --all > /opt/alphapulldown-runtime/pip-freeze.txt

COPY deployment/aws/smoke_cpu.py /opt/alphapulldown-runtime/smoke_cpu.py
COPY deployment/aws/smoke_gpu.py /opt/alphapulldown-runtime/smoke_gpu.py
RUN python /opt/alphapulldown-runtime/smoke_cpu.py

WORKDIR /workspace
CMD ["sleep", "infinity"]
