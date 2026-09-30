# sentry-digest

Triage matutino de Sentry (org `humand`, proyecto `humand-app`) para humand-mobile. Cubre las últimas 24 h, o 72 h los lunes.

1. **Digest:** issues nuevos y con pico (≥3x su promedio, o regresiones), marcando los urgentes (crash, muchos usuarios, flujos core).
2. **Análisis de cada issue nuevo** (hasta 5 por corrida): causa raíz con nivel de confianza. Después, en un git worktree aislado de humand-mobile (`.claude/worktrees/sentry-<ID>`, rama `sentry/<ID>-…`): un test que reproduce el bug (rojo), el fix mínimo (verde) y `specs/sentry-<ID>/spec.md` con una sección "⚠️ Requiere validación humana".
3. **Reporte** en español en `reports/AAAA-MM-DD.md`. También queda como respuesta de la corrida, así que llega por push o mail si tenés las notificaciones activadas.

Qué **no** hace nunca: tocar Sentry (resolver, asignar, comentar), tocar tu checkout principal de humand-mobile, ni pushear o abrir PRs. Las ramas quedan locales para que las revises.

Requiere el conector de Sentry en Claude y `node_modules` instalados en humand-mobile.

## Configuración

Copiá el ejemplo y editá solo lo que quieras cambiar. `config.json` es personal y está ignorado por git, y cada clave pisa a la del ejemplo:

```bash
cp config.example.json config.json
python3 scripts/config.py      # muestra la config efectiva y la valida
```

| Clave | Por defecto | Qué hace |
| --- | --- | --- |
| `schedule.time` | `"05:55"` | Hora de la tarea (HH:MM, 24 h) |
| `schedule.timezone` | `"America/Asuncion"` | Zona horaria IANA |
| `schedule.weekdays` | `"1-5"` | Días en formato cron (0 = domingo) |
| `analysis.enabled` | `true` | `false` = solo el digest, sin causa raíz, worktrees, tests ni specs |
| `analysis.max_issues` | `5` | Issues nuevos analizados por corrida |
| `sentry.org` / `project` / `region_url` | `humand` / `humand-app` / `us.sentry.io` | Qué consultar |

- **`analysis` y `sentry`** se leen en cada corrida: cambialos y listo.
- **`schedule`** define la hora de la tarea programada, que vive en Claude y no en este archivo. Si lo cambiás, pedile a Claude en una tarea con las carpetas conectadas: *"Actualizá el horario de mi tarea Sentry morning digest con `python3 angel-ai/sentry-digest/scripts/config.py --cron`"*.

Tarea programada: ver [`PROMPT.md`](PROMPT.md). Instrucciones completas: [`INSTRUCCIONES.md`](INSTRUCCIONES.md).
