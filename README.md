# angel-ai

Tareas programadas de Claude (Cowork) para el día a día en **humand-mobile**. Cada tarea es un prompt corto que le dice a Claude qué archivo de instrucciones seguir, más los scripts que necesita. Todo corre en tu Mac.

| Herramienta | Qué hace | Cuándo | Salida |
| --- | --- | --- | --- |
| [`pr-report/`](pr-report/) | Reporte de los PRs creados o mergeados el día anterior, por tribu y módulo. Las tribus que elijas llevan análisis de riesgo leyendo el diff. | L–V 4:56 AM | `pr-report/reports/AAAA-MM-DD.md` |
| [`sentry-digest/`](sentry-digest/) | Triage de Sentry (issues nuevos y con pico). Para cada issue nuevo: causa raíz, spec y fix con TDD en un worktree local. | L–V 5:55 AM | `sentry-digest/reports/AAAA-MM-DD.md` + ramas locales `sentry/*` en humand-mobile |

> **El repo es público.** Los reportes, los datos intermedios y el token quedan en tu copia local y están en `.gitignore`. No los commitees ni los fuerces con `git add -f`.

## Requisitos

- Mac con la **app de escritorio de Claude** (Cowork), con tu cuenta de Humand.
- Acceso a `HumandDev/humand-mobile` y el [GitHub CLI](https://cli.github.com) logueado (`brew install gh && gh auth login`).
- `humand-mobile` clonado con `node_modules` instalados (el Sentry digest corre tests de Jest).
- Para el Sentry digest: el conector de **Sentry** habilitado en Claude (Settings → Connectors).
- Python 3.8 o más nuevo (viene con las Command Line Tools de Xcode).

## Setup (unos 10 minutos)

### 1. Clonar al lado de humand-mobile

```bash
cd ~/Desktop/projects            # o donde tengas humand-mobile
git clone https://github.com/atrinidad-hu/angel-ai.git
```

Las carpetas tienen que llamarse **`angel-ai`** y **`humand-mobile`**: las tareas las buscan con esos nombres.

### 2. Correr el chequeo

```bash
cd angel-ai
./setup/check.sh ../humand-mobile
```

Revisa python, crea `.github-token` con `gh auth token` si todavía no existe, confirma que el token puede leer el repo y que está ignorado por git, y encuentra humand-mobile. Seguí lo que marque con ❌.

> Si el check dice que el token no puede leer el repo, tu token de `gh` probablemente no está autorizado para el SSO de HumandDev. Corré `gh auth refresh -h github.com` o autorizalo en github.com/settings/tokens.

### 3. (Opcional) Personalizar el reporte de PRs

```bash
cp pr-report/config.example.json pr-report/config.json
```

En `config.json` podés cambiar `detail_tribes`, las tribus que llevan análisis a fondo (por defecto `["Communication"]`), y `utc_offset_hours`. El archivo no se versiona.

### 4. Probar el recolector a mano

```bash
python3 pr-report/scripts/pr_report_fetch.py
```

Debería terminar con algo como `28 PRs: Communication=16, Tech=6, …` y dejar el JSON en `pr-report/.work/`. Para probar otro día: `--date 2026-09-30`.

### 5. Crear las tareas programadas en Claude

1. En la app de escritorio, abrí una tarea nueva con **tu computadora** seleccionada.
2. Conectá las dos carpetas con **Add folder**: `angel-ai` y `humand-mobile`.
3. Pedile a Claude:

   > Creá dos tareas programadas que requieran esta computadora y usen las carpetas angel-ai y humand-mobile:
   > - "Reporte diario de PRs": lunes a viernes 4:56 AM, prompt = el contenido de `angel-ai/pr-report/PROMPT.md` debajo de la línea.
   > - "Sentry morning digest": lunes a viernes 5:55 AM, prompt = el contenido de `angel-ai/sentry-digest/PROMPT.md` debajo de la línea.

4. Para probar sin esperar a mañana, pedile que las corra ahora: *"Corré ahora la tarea Reporte diario de PRs"*.

Si preferís hacerlo a mano: en la sección de tareas programadas de la app, creá cada tarea, pegá el prompt del `PROMPT.md` correspondiente y agregá las dos carpetas.

## Uso diario

- Los reportes aparecen en `pr-report/reports/` y `sentry-digest/reports/`, uno por día.
- **La Mac tiene que estar prendida y sin dormir, con la app de Claude abierta**, a la hora de cada tarea. Si no, esa corrida falla. Podés programar el despertar en Configuración del Sistema → Batería → Opciones, o con `pmset`.
- Los lunes, las dos tareas cubren desde el viernes.
- Las ramas `sentry/*` que crea el digest son **solo locales**: revisalas, pushealas y abrí el PR vos.

## Actualizar

```bash
cd angel-ai && git pull
```

Las tareas leen `INSTRUCCIONES.md` y los scripts en cada corrida, así que no hace falta recrearlas. Solo hay que volver a pegar el prompt si cambia algún `PROMPT.md`.

## Cambiar el comportamiento

- **Formato o criterio de un reporte:** editá el `INSTRUCCIONES.md` de esa herramienta. Si el cambio le sirve a todo el team, abrí un PR acá.
- **Clasificación por tribu, señales de riesgo o archivos "core":** `pr-report/scripts/pr_report_fetch.py` (`TRIBES`, `CORE_PATTERNS`). Refleja la tabla de tribus del `CLAUDE.md` de humand-mobile: si esa tabla cambia, actualizala acá también.

## Estructura

```
angel-ai/
├── README.md
├── .gitignore
├── .github-token            ← local, ignorado (gh auth token)
├── setup/
│   └── check.sh             ← verificación del setup
├── pr-report/
│   ├── PROMPT.md            ← prompt de la tarea programada
│   ├── INSTRUCCIONES.md     ← lo que sigue Claude en cada corrida
│   ├── config.example.json  ← copiá a config.json para personalizar
│   ├── scripts/
│   │   └── pr_report_fetch.py
│   ├── reports/             ← salida, ignorada
│   └── .work/               ← JSON y diffs intermedios, ignorado
└── sentry-digest/
    ├── PROMPT.md
    ├── INSTRUCCIONES.md
    └── reports/             ← salida, ignorada
```

## Problemas comunes

| Síntoma | Causa probable | Arreglo |
| --- | --- | --- |
| El reporte dice "token vencido" o `GitHub 401` | Cerraste sesión o se renovó el token de `gh` | `gh auth token > .github-token` |
| `GitHub 404` sobre humand-mobile | El token no está autorizado para el SSO de HumandDev | `gh auth refresh -h github.com`, o autorizalo en github.com/settings/tokens |
| La tarea no corrió | La Mac estaba dormida o la app de Claude cerrada | Programá el despertar de la Mac un poco antes de la tarea |
| El Sentry digest no encuentra issues | El conector de Sentry no está habilitado para la tarea | Habilitalo en Settings → Connectors |
| Claude no encuentra las carpetas | Las carpetas no se llaman `angel-ai` / `humand-mobile`, o no están conectadas a la tarea | Renombralas o reconectalas en la configuración de la tarea |
