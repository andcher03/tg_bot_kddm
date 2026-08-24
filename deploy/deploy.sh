#!/usr/bin/env bash

set -Eeuo pipefail
umask 027

APP_DIR="/opt/kddm/app"
VENV_DIR="/opt/kddm/venv"
BACKUP_DIR="/var/lib/kddm/backups"
HEALTH_URL="https://admin.kznmol.ru/login"
LOCK_FILE="/run/lock/kddm-deploy.lock"
SERVICES=(
    "kddm-web.service"
    "kddm-bot.service"
    "kddm-mailing-worker.service"
)

log() {
    printf '[deploy] %s\n' "$*"
}

fail() {
    log "ОШИБКА: $*"
    return 1
}

restart_services() {
    local service

    for service in "${SERVICES[@]}"; do
        if systemctl cat "$service" >/dev/null 2>&1; then
            log "Перезапуск $service"
            systemctl restart "$service"
        fi
    done
}

if [[ $# -ne 1 ]]; then
    fail "Ожидался SHA commit в единственном аргументе."
fi

TARGET_SHA="${1,,}"

if [[ ! "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]]; then
    fail "Некорректный SHA commit."
fi

if [[ "${EUID}" -ne 0 ]]; then
    fail "Скрипт должен запускаться через sudo."
fi

for command in curl flock git pg_dump pg_restore runuser systemctl; do
    command -v "$command" >/dev/null || fail "Не найдена команда: $command"
done

[[ -d "$APP_DIR/.git" ]] || fail "Репозиторий не найден: $APP_DIR"
[[ -x "$VENV_DIR/bin/python" ]] || fail "Python-окружение не найдено: $VENV_DIR"

exec 9>"$LOCK_FILE"
flock -n 9 || fail "Другой deployment уже выполняется."

CURRENT_SHA="$(runuser -u kddm -- git -C "$APP_DIR" rev-parse HEAD)"
CODE_CHANGED=0
BACKUP_FILE=""

rollback_code() {
    local exit_code=$?
    trap - ERR

    if [[ "$CODE_CHANGED" -eq 1 ]]; then
        log "Возврат к предыдущему commit $CURRENT_SHA"
        runuser -u kddm -- git -C "$APP_DIR" checkout --detach --force "$CURRENT_SHA" || true
        runuser -u kddm -- "$VENV_DIR/bin/python" -m pip install \
            --disable-pip-version-check \
            -r "$APP_DIR/requirements.txt" || true
        restart_services || true
    fi

    if [[ -n "$BACKUP_FILE" ]]; then
        log "Резервная копия перед deployment: $BACKUP_FILE"
    fi

    exit "$exit_code"
}

trap rollback_code ERR

if [[ -n "$(runuser -u kddm -- git -C "$APP_DIR" status --porcelain --untracked-files=no)" ]]; then
    fail "На сервере есть незакоммиченные изменения отслеживаемых файлов."
fi

log "Получение commit $TARGET_SHA"
runuser -u kddm -- git -C "$APP_DIR" fetch --prune origin main
runuser -u kddm -- git -C "$APP_DIR" cat-file -e "${TARGET_SHA}^{commit}"
runuser -u kddm -- git -C "$APP_DIR" merge-base --is-ancestor "$TARGET_SHA" origin/main

install -d -o root -g kddm -m 750 "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/predeploy_$(date -u +%Y%m%dT%H%M%SZ)_${TARGET_SHA:0:12}.dump"

log "Создание резервной копии PostgreSQL"
runuser -u postgres -- pg_dump --format=custom --dbname=kddm >"$BACKUP_FILE"
chown root:kddm "$BACKUP_FILE"
chmod 640 "$BACKUP_FILE"
pg_restore --list "$BACKUP_FILE" >/dev/null

log "Переключение к commit $TARGET_SHA"
runuser -u kddm -- git -C "$APP_DIR" checkout --detach --force "$TARGET_SHA"
CODE_CHANGED=1

log "Установка Python-зависимостей"
runuser -u kddm -- "$VENV_DIR/bin/python" -m pip install \
    --disable-pip-version-check \
    -r "$APP_DIR/requirements.txt"

log "Применение миграций"
runuser -u kddm -- bash -c \
    "cd '$APP_DIR' && '$VENV_DIR/bin/python' -m alembic upgrade head"
runuser -u kddm -- bash -c \
    "cd '$APP_DIR' && '$VENV_DIR/bin/python' -m alembic check"

restart_services

log "Проверка Web Admin"
for attempt in {1..12}; do
    if curl --fail --silent --show-error --location \
        --max-time 15 "$HEALTH_URL" >/dev/null; then
        trap - ERR
        log "Deployment успешно завершён: $TARGET_SHA"
        log "Backup: $BACKUP_FILE"
        exit 0
    fi

    if [[ "$attempt" -lt 12 ]]; then
        sleep 5
    fi
done

fail "Web Admin не прошёл проверку после deployment."
