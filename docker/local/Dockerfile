FROM python:3.12.11-slim AS builder

ARG CACHEBUST=1
ARG PROJECT_DIR=/opt/app
ARG REQUIREMENTS_FILE=requirements.dev.txt
ARG PYTHON_VENV=/opt/.venv
ARG SERVICE_PORT=8080
ARG NEXUS_PIP_IS_ENABLE=false
ARG NEXUS_PIP_USER
ARG NEXUS_PIP_PASSWORD
ARG NEXUS_PIP_URL

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PROJECT_DIR="${PROJECT_DIR}" \
    SERVICE_PORT="${SERVICE_PORT}" \
    REQUIREMENTS_FILE="${REQUIREMENTS_FILE}" \
    PYTHON_VENV="${PYTHON_VENV}" \
    NEXUS_PIP_IS_ENABLE="${NEXUS_PIP_IS_ENABLE}" \
    NEXUS_PIP_USER="${NEXUS_PIP_USER}" \
    NEXUS_PIP_PASSWORD="${NEXUS_PIP_PASSWORD}" \
    NEXUS_PIP_URL="${NEXUS_PIP_URL}" \
    DEBIAN_FRONTEND=noninteractive \
    APT_PROXY_IS_ENABLE=${APT_PROXY_IS_ENABLE} \
    APT_PROXY_URL=${APT_PROXY_URL} \
    APT_PROXY_SECURITY_URL=${APT_PROXY_SECURITY_URL}

RUN set -exu && \
    if [ "${APT_PROXY_IS_ENABLE}" = "true" ]; then \
        if [ -z "${APT_PROXY_URL}" ] || [ -z "${APT_PROXY_SECURITY_URL}" ]; then \
            echo "APT proxy enabled, but APT_PROXY_URL or APT_PROXY_SECURITY_URL is not set!" >&2; \
            exit 1; \
        fi && \
        echo "Configuring APT to use Nexus mirror (classic format)..." && \
        echo > /etc/apt/sources.list && \
        rm /etc/apt/sources.list.d/debian.sources && \
        echo "deb ${APT_PROXY_URL} trixie main" > /etc/apt/sources.list.d/nexus.list && \
        echo "deb ${APT_PROXY_URL} trixie-updates main" >> /etc/apt/sources.list.d/nexus.list && \
        echo "deb ${APT_PROXY_SECURITY_URL} trixie-security main" >> /etc/apt/sources.list.d/nexus.list; \
    fi && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl wget net-tools tcpdump atop strace telnet vim \
    git=1:2.47.3-0+deb13u1 \
    build-essential=12.12 \
    gcc=4:14.2.0-1 \
    libffi-dev=3.4.8-2 \
    netcat-traditional=1.10-50 \
    tzdata=2025b-4+deb13u1 \
    gettext=0.23.1-2 \
    libpq-dev=17.9-0+deb13u1 \
    libmagic1=1:5.46-5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM builder AS python-env

RUN python -m venv "${PYTHON_VENV}" && \
    "${PYTHON_VENV}/bin/python" -m pip install --no-cache-dir --upgrade pip setuptools wheel

RUN if [ "$NEXUS_PIP_IS_ENABLE" = "true" ]; then \
    echo "Using PyPI repository - ${NEXUS_PIP_URL}"; \
    "${PYTHON_VENV}/bin/pip" config set global.index-url "https://${NEXUS_PIP_URL}" && \
    "${PYTHON_VENV}/bin/pip" config set global.trusted-host "${NEXUS_PIP_URL}"; \
    else \
    echo "Using default PyPI repository"; \
    fi

COPY "${REQUIREMENTS_FILE}" /
RUN "${PYTHON_VENV}/bin/pip" install \
    --no-cache-dir \
    --trusted-host nexus3.gosuslugi.local \
    -r "/${REQUIREMENTS_FILE:?}" && \
    rm -rf "/${REQUIREMENTS_FILE:?}"

COPY ./libs /libs
RUN "${PYTHON_VENV}/bin/pip" install /libs/kronoslab_filter-0.4.5-py3-none-any.whl

FROM builder AS application

ARG SERVICE_PORT=8080

EXPOSE ${SERVICE_PORT}

COPY --from=python-env "${PYTHON_VENV}" "${PYTHON_VENV}"
ENV PATH="${PYTHON_VENV}/bin:${PATH}"

COPY ./src/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

FROM application AS server

RUN groupadd -r kronoslab && useradd -r -g kronoslab kronoslab

WORKDIR "${PROJECT_DIR}"
COPY ./src "${PROJECT_DIR}"

RUN chown -R kronoslab:kronoslab "${PROJECT_DIR}"
USER kronoslab

FROM server AS local
