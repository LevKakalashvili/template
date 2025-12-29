``./requirements.local.txt`` - для локальной разработки, там прописан урл для качания с нексуса
В ```docker-compose.local.yml``` Прописываем
```
    env_file:
      - ./src/.env
    build:
        args:
            REQUIREMENTS_FILE: ./requirements.local.txt
```
# Проблема с миграцией
```logs
Attaching to publishing_api publishing_api
Apply migrations publishing_api

FAILED: No config file 'alembic.ini' found, or file has no '[alembic]' section publishing_api exited with code 1
```

## Dockerfile
1. Перед строчкой в ``Dockerfile``
```dockerfile
COPY ./src/entrypoint.sh /entrypoint.sh
```

2. Нужно прописать дополнительное копирование. Обычно в `Dockerfile` - 84 - 85 строчки
```dockerfile
WORKDIR "${PROJECT_DIR}"
COPY ./src "${PROJECT_DIR}"

COPY ./src/entrypoint.sh /entrypoint.sh
```
3. Из-за моего парля это нужно заменить. 
```dockerfile
RUN if [ "$NEXUS_PIP_IS_ENABLE" = "true" ]; then \
    echo "Using PyPI repository - ${NEXUS_PIP_URL}"; \
    "${PYTHON_VENV}/bin/pip" config set global.index-url "https://${NEXUS_PIP_USER}:${NEXUS_PIP_PASSWORD}@${NEXUS_PIP_URL}" && \
    "${PYTHON_VENV}/bin/pip" config set global.trusted-host "${NEXUS_PIP_URL}"; \
    else \
    echo "Using default PyPI repository"; \
    fi
```


