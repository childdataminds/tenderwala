#!/bin/bash
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/tenderwala}"
APP_SERVICE_NAME="${APP_SERVICE_NAME:-tenderwala}"
DEPLOY_RUN_AS="${DEPLOY_RUN_AS:-$(stat -c '%U' "$APP_DIR")}"
DEPLOY_LOG_PATH="${DEPLOY_LOG_PATH:-/var/log/tenderwala-deploy.log}"

mkdir -p "$(dirname "$DEPLOY_LOG_PATH")"

{
  echo "==== $(date -Iseconds) deploy start ===="
  echo "app_dir=$APP_DIR"
  echo "service=$APP_SERVICE_NAME"
  echo "run_as=$DEPLOY_RUN_AS"

  cd "$APP_DIR"

  if [ "$(id -u)" -eq 0 ] && [ "$DEPLOY_RUN_AS" != "root" ]; then
    runuser -u "$DEPLOY_RUN_AS" -- git pull origin main
  else
    git pull origin main
  fi

  systemctl restart "$APP_SERVICE_NAME"
  echo "==== $(date -Iseconds) deploy success ===="
} >>"$DEPLOY_LOG_PATH" 2>&1
