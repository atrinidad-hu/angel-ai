# Reporte diario de PRs — instrucciones para Claude

Esto es lo que sigue la tarea programada en cada corrida. Si lo editás, el cambio aplica desde la próxima.

Rutas (dentro de la tarea, con `device_bash`):
- `ANGEL_AI` = `$HOME/mnt/angel-ai` (este repo)
- `HUMAND_MOBILE` = `$HOME/mnt/humand-mobile` (solo lectura, para contexto)

## Pasos

1. Correr el recolector:
   `python3 $ANGEL_AI/pr-report/scripts/pr_report_fetch.py`
   Deja `pr-report/.work/prs-<fecha>.json` y, para las tribus de `detail_tribes` del JSON, el diff de cada PR en `pr-report/.work/diffs/<n>.diff`.
   Si falla (token vencido, sin red, error de GitHub), escribir igual `pr-report/reports/<fecha>.md` con el error y cómo arreglarlo (ej. `gh auth token > <ruta del repo>/.github-token`), y terminar.
2. Leer el JSON. Para cada PR usar título, body, lista de archivos y `risk_signals`.
   Para las tribus de `detail_tribes`, leer además el diff de los PRs que no sean triviales antes de opinar.
   Si hace falta más contexto, se puede leer código en `$HUMAND_MOBILE` (solo lectura: no cambiar archivos, no hacer checkout/pull/commit).
3. Escribir `$ANGEL_AI/pr-report/reports/<report_date>.md` (en español). Si ya existe, sobrescribirlo. Tomar como referencia de tono y detalle el reporte más reciente de esa carpeta, si hay.
4. No commitear nada: `reports/` y `.work/` están en `.gitignore` porque tienen información interna.

## Formato

```
# PRs humand-mobile — <ventana, ej. "martes 29/09" o "viernes 25/09 a domingo 27/09">

**N PRs** · X creados (siguen abiertos/draft) · Y mergeados (abiertos antes) · Z creados y mergeados en el día
⚠️ **A tener en cuenta (<tribus en detalle>):** lista corta de links a los PRs marcados como importantes, o "nada crítico".

## <Tribu>   (primero las de detail_tribes; después Time & People, Talent & Data, Operations & Finance, Communication, Tech, Sin tribu asignada — saltando las ya listadas)
### <módulo>  (ordenados por cantidad de PRs, desc)
- [#1234](url) **Título** — @autor · 🟢 mergeado / 🔵 abierto / 📝 draft / ⚪ cerrado sin merge · +add/-del
  Una o dos líneas: qué es y qué problema resuelve o qué agrega (del body/diff, no repetir el título).
```

- Módulo: usar `title_module` (el prefijo `<Module> |` del título, ej. "Chats 2.0", "Calls") cuando exista; si no, `module` (derivado de los archivos). Unificar nombres equivalentes ("Group"/"Groups", "Post"/"Posts"). Si el prefijo contradice claramente los archivos (ej. "Calls |" en un PR que solo toca livestream), agrupar por los archivos y aclararlo entre paréntesis.
- Tribu: usar `tribe` tal cual (sale del label del PR, o de los archivos si no tiene label).
- Un PR aparece una sola vez aunque se haya creado y mergeado en la ventana.
- Tribus o módulos sin PRs no se listan.
- Si `tribe_source` es `archivos` y el PR toca varios módulos, mencionar los otros módulos entre paréntesis.
- Los PRs de backport automático (`[vX.Y.Z] …`) se agrupan en una sola línea al final de su módulo: "Backports: #a, #b → vX.Y.Z".

## Tribus en detalle (`detail_tribes`, por defecto Communication)

**Trivial** (copy, estilos, rename, bump menor, test/e2e aislado, fix chico y acotado): una línea, igual que el resto.

**Importante** — marcar con ⚠️ y dar todo lo relevante — si cumple alguno:
- PR grande o que cambia un flujo central (envío/recepción de mensajes, sockets, push, llamadas, sesión de audio, feed, livestream, marcaciones, pagos…).
- Toca config core, navegación raíz, Redux/stores globales, DB local, dependencias o patches, código nativo, entrypoint.
- Cambia lógica sin tests (hooks, utils, services, stores, sagas, schemas) — las reglas de humand-mobile dicen que eso sí se testea; los componentes no.
- Hotfix/Bugfix, base en una rama de release, o mergeado muy rápido para su tamaño.
- Puede afectar el arranque de la app, performance, o romper otros módulos.

Para los importantes, debajo de la línea del PR:
```
  ⚠️ **Por qué importa:** …
  - Qué cambia concretamente (archivos/flujos clave).
  - Riesgos: ej. "Cambia una configuración core y no tiene unit tests", "Puede afectar el arranque de la app porque …".
  - Qué revisar o probar si lo vas a tocar / QA sugerido.
```
Ser concreto y basarse en el diff; no inventar riesgos. Si `risk_signals` marca algo que en el diff resulta inofensivo, decirlo.

## Resto de tribus

Solo qué se hizo: una línea por PR. Sin análisis de riesgo.
