# Stage 1: Builder
FROM python:3.13-alpine AS builder

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
        ca-certificates gcc postgresql-dev linux-headers musl-dev \
        libffi-dev jpeg-dev zlib-dev && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + && \
    runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
    )" && \
    apk add --virtual .rundeps $runDeps && \
    apk del .build-deps

# Stage 2: Final image
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copiar wheels pré-compiladas
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Criar usuário não-root
RUN adduser -D -h /app -s /bin/sh userapp

WORKDIR /app

# Copiar o código da aplicação
COPY --chown=userapp:userapp . .

# Criar diretórios necessários
RUN mkdir -p /app/staticfiles /app/static /app/logs \
    && chown -R userapp:userapp /app \
    && chmod -R 755 /app/static /app/staticfiles /app/logs

# Instalar curl e ferramentas básicas
RUN apk add --no-cache curl

# Compilar assets estáticos no build (se não for desenvolvimento)
RUN if [ "$DEBUG" != "True" ]; then \
        python manage.py collectstatic --noinput && \
        python manage.py compress --force; \
    fi

# Porta exposta
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/health/ || exit 1

# Rodar como usuário não-root
USER userapp
