#!/usr/bin/env bash
# تشغيل التطوير بدون إعادة تحميل لا نهائية بسبب مجلد .pyuserbase داخل المشروع
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
# المجلد كمسار (ليس glob) حتى يُستثنى بالكامل من إعادة التحميل
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload \
  --reload-exclude ".pyuserbase"
