# Stage 1: Builder
FROM python:3.13-alpine AS builder

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
        ca-certificates gcc postgresql-dev linux-headers musl-dev \
        libffi-dev jpeg-dev zlib-dev && \
    pip install --no-cache -r requirements.txt && \
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
    PIP_NO_CACHE_DIR=1

# Copia pacotes e binários do builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Criar usuário
RUN adduser -h /app -s /bin/sh -D userapp

WORKDIR /app

# Copiar o código
COPY . .

# Instalar curl e dependências básicas (somente se necessário)
RUN apk add --no-cache curl

# Permissões e diretórios
RUN chown -R userapp:userapp /app && \
    mkdir -p /app/static /app/staticfiles && \
    chmod -R 755 /app/static /app/staticfiles

# Porta exposta
EXPOSE 8000

# Rodar como usuário não-root
USER userapp
