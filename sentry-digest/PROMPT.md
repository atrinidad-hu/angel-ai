# Prompt de la tarea programada — Sentry morning digest

Nombre sugerido: **Sentry morning digest** · Horario: el de `schedule` en la config (por defecto lunes a viernes 5:55, America/Asuncion; `python3 sentry-digest/scripts/config.py --cron` da la expresión exacta) · Requiere tu computadora · Carpetas: `angel-ai` y `humand-mobile` · Necesita el conector de **Sentry** habilitado en Claude.

Copiá todo lo que está debajo de la línea como prompt de la tarea.

---

Morning Sentry triage for humand-mobile. It runs unattended: don't ask questions, make reasonable decisions. Write every user-facing output in Spanish.

Everything on my computer is done with the remote-devices device_bash tool. Mounted folders: `$HOME/mnt/angel-ai` (tools repo) and `$HOME/mnt/humand-mobile` (codebase).

Read and follow exactly `$HOME/mnt/angel-ai/sentry-digest/INSTRUCCIONES.md` — config (`sentry-digest/scripts/config.py`), context, lookback window, digest, deep analysis with TDD in git worktrees, and the final report (saved to `$HOME/mnt/angel-ai/sentry-digest/reports/<today>.md` and returned as your final answer). Never commit anything in angel-ai, and never touch the main checkout of humand-mobile.
