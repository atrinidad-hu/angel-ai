# pr-report

Reporte diario de los PRs de `HumandDev/humand-mobile` creados o mergeados el día anterior (los lunes, de viernes a domingo), agrupados por **tribu** y **módulo**.

- **Tribus en detalle** (`detail_tribes`, por defecto Communication): Claude lee el diff de cada PR no trivial y marca con ⚠️ los que requieren atención (config core, nativo, dependencias, arranque de la app, lógica sin tests, hotfixes, PRs grandes), explicando qué cambia, los riesgos y qué probar.
- **Resto de tribus:** una línea por PR con lo que se hizo.

## Cómo funciona

1. `scripts/pr_report_fetch.py` (solo biblioteca estándar de Python) consulta la API de GitHub con tu token. Clasifica cada PR por tribu (primero por el label del PR, si no por los archivos tocados, según la tabla del `CLAUDE.md` de humand-mobile), calcula señales de riesgo y guarda un JSON y los diffs en `.work/`.
2. Claude lee ese JSON, siguiendo [`INSTRUCCIONES.md`](INSTRUCCIONES.md), y escribe `reports/AAAA-MM-DD.md`.

```bash
python3 scripts/pr_report_fetch.py                 # ventana de hoy
python3 scripts/pr_report_fetch.py --date 2026-09-28  # reporte de un lunes (vie–dom)
python3 scripts/pr_report_fetch.py --check         # solo valida el token
```

Tarea programada: ver [`PROMPT.md`](PROMPT.md). Setup completo: ver el [README principal](../README.md).
