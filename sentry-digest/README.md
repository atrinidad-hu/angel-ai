# sentry-digest

Triage matutino de Sentry (org `humand`, proyecto `humand-app`) para humand-mobile. Cubre las últimas 24 h, o 72 h los lunes.

1. **Digest:** issues nuevos y con pico (≥3x su promedio, o regresiones), marcando los urgentes (crash, muchos usuarios, flujos core).
2. **Análisis de cada issue nuevo** (hasta 5 por corrida): causa raíz con nivel de confianza. Después, en un git worktree aislado de humand-mobile (`.claude/worktrees/sentry-<ID>`, rama `sentry/<ID>-…`): un test que reproduce el bug (rojo), el fix mínimo (verde) y `specs/sentry-<ID>/spec.md` con una sección "⚠️ Requiere validación humana".
3. **Reporte** en español en `reports/AAAA-MM-DD.md`. También queda como respuesta de la corrida, así que llega por push o mail si tenés las notificaciones activadas.

Qué **no** hace nunca: tocar Sentry (resolver, asignar, comentar), tocar tu checkout principal de humand-mobile, ni pushear o abrir PRs. Las ramas quedan locales para que las revises.

Requiere el conector de Sentry en Claude y `node_modules` instalados en humand-mobile.

Tarea programada: ver [`PROMPT.md`](PROMPT.md). Instrucciones completas: [`INSTRUCCIONES.md`](INSTRUCCIONES.md).
