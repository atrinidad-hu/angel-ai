#!/usr/bin/env python3
"""Config efectiva del Sentry morning digest.

config.json (personal, ignorado por git) pisa a config.example.json (versionado), clave por clave.

Uso:
  python3 config.py          # imprime la config efectiva como JSON (la lee la tarea en cada corrida)
  python3 config.py --cron   # imprime la expresión cron de schedule (para crear/actualizar la tarea)
"""
import json
import os
import re
import sys

TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def merge(base, override):
    out = dict(base)
    for k, v in override.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load():
    cfg = {}
    for name in ("config.example.json", "config.json"):
        path = os.path.join(TOOL_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                try:
                    cfg = merge(cfg, json.load(f))
                except json.JSONDecodeError as e:
                    sys.exit(f"ERROR: {path} no es JSON válido: {e}")
    return cfg


def validate(cfg):
    errors = []
    sched = cfg.get("schedule", {})
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", str(sched.get("time", "")))
    if not m:
        errors.append('schedule.time debe ser "HH:MM" (24 h), ej. "05:55"')
    if not re.fullmatch(r"[0-6](-[0-6])?(,[0-6](-[0-6])?)*|\*", str(sched.get("weekdays", ""))):
        errors.append('schedule.weekdays debe ser formato cron de días (0=domingo), ej. "1-5" o "1,3,5"')
    if not sched.get("timezone"):
        errors.append('schedule.timezone es obligatorio (IANA), ej. "America/Asuncion"')
    analysis = cfg.get("analysis", {})
    if not isinstance(analysis.get("enabled"), bool):
        errors.append("analysis.enabled debe ser true o false")
    mx = analysis.get("max_issues")
    if not isinstance(mx, int) or isinstance(mx, bool) or mx < 1:
        errors.append("analysis.max_issues debe ser un entero >= 1")
    if errors:
        sys.exit("ERROR en la config del Sentry digest:\n- " + "\n- ".join(errors))
    return int(m.group(1)), int(m.group(2))


def main():
    cfg = load()
    hour, minute = validate(cfg)
    s = cfg["schedule"]
    cron = f"CRON_TZ={s['timezone']} {minute} {hour} * * {s['weekdays']}"
    if "--cron" in sys.argv:
        print(cron)
    else:
        print(json.dumps({**cfg, "cron": cron}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
