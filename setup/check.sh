#!/usr/bin/env bash
# Verifica (y en lo posible arregla) lo que necesitan las tareas de angel-ai.
# Uso: ./setup/check.sh [ruta a humand-mobile]   (por defecto: ../humand-mobile)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HM="${1:-$ROOT/../humand-mobile}"
ok=0; warn=0; fail=0
pass() { echo "  ✅ $*"; ok=$((ok+1)); }
note() { echo "  ⚠️  $*"; warn=$((warn+1)); }
bad()  { echo "  ❌ $*"; fail=$((fail+1)); }

echo "angel-ai en: $ROOT"

echo "1. Herramientas"
if command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
  pass "python3 $(python3 -c 'import platform; print(platform.python_version())')"
else
  bad "falta python3 >= 3.8 (brew install python)"
fi
if command -v gh >/dev/null; then pass "gh instalado"; else note "gh no está instalado (brew install gh) — solo hace falta para crear el token"; fi

echo "2. Token de GitHub ($ROOT/.github-token)"
TOKEN_FILE="$ROOT/.github-token"
if [ ! -s "$TOKEN_FILE" ] && command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  gh auth token > "$TOKEN_FILE" && echo "  → creado desde 'gh auth token'"
fi
if [ -s "$TOKEN_FILE" ]; then
  chmod 600 "$TOKEN_FILE"
  pass "token presente (permisos 600)"
else
  bad "falta el token: corré 'gh auth login' y después 'gh auth token > $TOKEN_FILE'"
fi
if git -C "$ROOT" check-ignore -q .github-token; then pass ".github-token está ignorado por git"; else bad ".github-token NO está en .gitignore"; fi

echo "3. Acceso al repo a reportar"
if [ -s "$TOKEN_FILE" ] && python3 "$ROOT/pr-report/scripts/pr_report_fetch.py" --check; then
  pass "el token puede leer el repo"
else
  bad "el token no puede leer el repo (¿SSO de HumandDev sin autorizar? github.com/settings/tokens → Configure SSO)"
fi

echo "4. humand-mobile ($HM)"
if [ -f "$HM/CLAUDE.md" ]; then
  pass "encontrado"
  [ "$(basename "$(cd "$HM" && pwd)")" = "humand-mobile" ] || note "la carpeta no se llama 'humand-mobile': las tareas la buscan en \$HOME/mnt/humand-mobile"
  [ -d "$HM/node_modules" ] || note "sin node_modules: el Sentry digest no va a poder correr tests (yarn install)"
else
  bad "no encontré humand-mobile; pasá la ruta: ./setup/check.sh /ruta/a/humand-mobile"
fi
[ "$(basename "$ROOT")" = "angel-ai" ] || note "este clon no se llama 'angel-ai': las tareas lo buscan en \$HOME/mnt/angel-ai"

echo
echo "Resultado: $ok ok · $warn avisos · $fail errores"
[ "$fail" -eq 0 ]
