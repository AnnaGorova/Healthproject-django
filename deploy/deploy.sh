#!/usr/bin/env bash
set -euo pipefail

cd /opt/shb
NEW_IMAGE="$1"
PREV_IMAGE="$(cat .current_image 2>/dev/null || true)"

# Compose бере назву образу зі змінної WEB_IMAGE
export WEB_IMAGE="$NEW_IMAGE"
docker compose pull web
docker compose up -d --no-build --remove-orphans
docker compose restart nginx

# Перевірка: до 60 секунд чекаємо, поки сайт відповість
ok=0
for i in $(seq 1 15); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost/ || true)
  if [[ "$code" =~ ^(200|301|302)$ ]]; then ok=1; break; fi
  sleep 4
done

if [ "$ok" = 1 ]; then
  echo "$NEW_IMAGE" > .current_image
  echo "Deploy OK: $NEW_IMAGE"
  exit 0
fi

echo "Health check FAILED" >&2
docker compose logs web --tail 50 >&2 || true
if [ -n "$PREV_IMAGE" ]; then
  echo "Rolling back to $PREV_IMAGE" >&2
  export WEB_IMAGE="$PREV_IMAGE"
  docker compose up -d --no-build
  docker compose restart nginx
fi
exit 1