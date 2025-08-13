#!/bin/sh
set -e

echo ">> Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
# nc в Debian/Ubuntu пакете называется netcat-openbsd; в slim обычно есть
until nc -z "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"; do
  sleep 0.5
done
echo ">> Postgres is up"

# Применим миграции, если есть Alembic
if [ -f "alembic.ini" ]; then
  echo ">> Running Alembic migrations"
  alembic upgrade head
fi

echo ">> Starting app: $@"
exec "$@"
