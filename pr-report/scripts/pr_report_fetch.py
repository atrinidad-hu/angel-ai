#!/usr/bin/env python3
"""Recolecta los PRs de HumandDev/humand-mobile creados o mergeados en la ventana del
reporte diario y los deja clasificados por tribu/módulo en un JSON.

Uso: python3 pr_report_fetch.py [--date YYYY-MM-DD] [--out DIR] [--check]
  --date   fecha del reporte (el día en que se lee). Por defecto: hoy (America/Asuncion).
           Lunes -> cubre viernes a domingo; resto -> el día anterior.
  --out    carpeta de trabajo (JSON + diffs). Por defecto: pr-report/.work/ (ignorada por git).
  --check  solo verifica que el token pueda leer el repo y termina.
Token: variable GITHUB_TOKEN / GH_TOKEN, o primera línea de <raíz del repo>/.github-token.
Repo a reportar: variable PR_REPORT_REPO (por defecto HumandDev/humand-mobile).
Solo usa la biblioteca estándar.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL_DIR = os.path.dirname(HERE)          # angel-ai/pr-report
REPO_ROOT = os.path.dirname(TOOL_DIR)     # angel-ai


def load_config():
    """config.json (personal, ignorado por git) pisa a config.example.json (versionado)."""
    cfg = {}
    for name in ("config.example.json", "config.json"):
        path = os.path.join(TOOL_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                cfg.update(json.load(f))
    return cfg


CONFIG = load_config()
REPO = os.environ.get("PR_REPORT_REPO") or CONFIG.get("repo", "HumandDev/humand-mobile")
API = "https://api.github.com"
# Offset fijo en horas (Paraguay: UTC-3 todo el año; Argentina/Uruguay también -3).
TZ = timezone(timedelta(hours=CONFIG.get("utc_offset_hours", -3)))
DETAIL_TRIBES = set(CONFIG.get("detail_tribes", ["Communication"]))

TRIBES = {
    "Communication": ["article", "calls", "callsLegacy", "celebrations", "chat", "chats", "drafts",
                      "events", "group", "home", "keyUpdates", "livestream", "livestreamLegacy",
                      "marketplace", "post", "universalSearch"],
    "Operations & Finance": ["form", "serviceManagement", "surveys", "loans"],
    "Talent & Data": ["acknowledgement", "employeeLifecycle", "jobsPortal", "recruiting", "goals",
                      "learning", "libraries", "notificationsCenter", "onboarding",
                      "peopleExperience", "performance", "prode", "trainings", "widgets"],
    "Time & People": ["auth", "documents", "files", "login", "shifts", "profile", "settings",
                      "timeOff", "timeTracking"],
    "Tech": ["app", "commons", "search"],
}
MODULE_TO_TRIBE = {m: t for t, ms in TRIBES.items() for m in ms}
# Carpetas compartidas que en CLAUDE.md pertenecen a un módulo de producto.
SHARED_TO_MODULE = {"calls": "calls", "livestreams": "livestream"}
TRIBE_LABELS = set(TRIBES)

# Archivos cuyo cambio afecta arranque, build o config global de la app.
CORE_PATTERNS = [
    (r"^package\.json$", "dependencias (package.json)"),
    (r"^yarn\.lock$", "lockfile"),
    (r"^\.yarn/patches/", "patches de dependencias"),
    (r"^(app\.config\.ts|app\.json|eas\.json|index\.js|global\.ts)$", "config/entrypoint de la app"),
    (r"^(metro|babel)\.config\.js$", "config de Metro/Babel"),
    (r"^(tsconfig\.json|declarations\.d\.ts|\.eslintrc\.js)$", "config de TS/lint"),
    (r"^android/", "código nativo Android"),
    (r"^ios/", "código nativo iOS"),
    (r"^modules/", "módulos nativos locales"),
    (r"^cpp/", "código nativo C++"),
    (r"^app/navigation/", "navegación raíz"),
    (r"^app/config/", "config global (API, tokens, i18n, Sentry)"),
    (r"^app/redux/", "store/sagas raíz de Redux"),
    (r"^app/db/|^drizzle/", "base de datos local / migraciones"),
    (r"^app/stores/", "stores globales de Zustand"),
    (r"^app/shared/calls/audio|HumandAudioSession", "sesión de audio (HumandAudioSession)"),
    (r"^\.github/", "CI/CD"),
    (r"^app/shared/components/_HuGo/", "design system HuGo"),
]
TEST_RE = re.compile(r"(\.test\.|\.spec\.|__tests__/|\.harness\.|^e2e/)")
# Lógica que el repo espera testeada (los componentes no se testean por regla del CLAUDE.md).
CODE_RE = re.compile(r"^(app|modules)/.*(/hooks/|/utils|/redux/|/store/|/stores/|services|schemas|"
                     r"sockets|Controller|Service|/instances/|/db/|/core/).*\.(ts|tsx|js)$")


def load_token():
    env = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env:
        return env.strip()
    path = os.path.join(REPO_ROOT, ".github-token")
    try:
        with open(path) as f:
            tok = f.readline().strip()
    except FileNotFoundError:
        sys.exit(f"ERROR: falta el token en {path}. Crealo con: gh auth token > {path}")
    if not tok:
        sys.exit(f"ERROR: {path} está vacío")
    return tok


def gh(path, token, params=None, accept="application/vnd.github+json"):
    url = path if path.startswith("http") else API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}", "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "humand-pr-report"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode()
                return json.loads(body) if "json" in accept else body
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (403, 429) and "rate limit" in msg.lower() and attempt < 3:
                time.sleep(20 * (attempt + 1))
                continue
            if e.code >= 500 and attempt < 3:
                time.sleep(5)
                continue
            sys.exit(f"ERROR GitHub {e.code} en {url}: {msg}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(5)
                continue
            sys.exit(f"ERROR de red en {url}: {e}")


def window(report_date):
    days_back = 3 if report_date.weekday() == 0 else 1
    start = datetime(report_date.year, report_date.month, report_date.day, tzinfo=TZ) - timedelta(days=days_back)
    end = datetime(report_date.year, report_date.month, report_date.day, tzinfo=TZ) - timedelta(seconds=1)
    return start, end


def search(query, token):
    items, page = [], 1
    while True:
        d = gh("/search/issues", token, {"q": query, "per_page": 100, "page": page})
        items += d.get("items", [])
        if len(items) >= d.get("total_count", 0) or not d.get("items") or page >= 10:
            return items
        page += 1


def list_files(num, token):
    files, page = [], 1
    while page <= 30:
        batch = gh(f"/repos/{REPO}/pulls/{num}/files", token, {"per_page": 100, "page": page})
        files += batch
        if len(batch) < 100:
            break
        page += 1
    return files


def module_of(path):
    m = re.match(r"^app/modules/employeeLifecycle/", path)
    if m:
        return "employeeLifecycle"
    m = re.match(r"^app/modules/([^/]+)/", path)
    if m:
        return m.group(1)
    m = re.match(r"^app/shared/([^/]+)/", path)
    if m and m.group(1) in SHARED_TO_MODULE:
        return SHARED_TO_MODULE[m.group(1)]
    m = re.match(r"^e2e/flows/([^/]+)/", path)
    if m:
        return m.group(1)
    return None


def classify(files, labels):
    counts = Counter(filter(None, (module_of(f["filename"]) for f in files)))
    modules = [m for m, _ in counts.most_common()]
    main_module = modules[0] if modules else None
    label_tribe = next((l for l in labels if l in TRIBE_LABELS), None)
    if label_tribe:
        tribe, source = label_tribe, "label"
    elif main_module in MODULE_TO_TRIBE:
        tribe, source = MODULE_TO_TRIBE[main_module], "archivos"
    elif main_module:
        tribe, source = "Sin tribu asignada", "archivos"
    else:
        tribe, source = "Tech", "archivos"
    return tribe, source, main_module or "shared / infra", modules


def risk_signals(pr, files, labels):
    sig = []
    names = [f["filename"] for f in files]
    core = sorted({desc for n in names for pat, desc in CORE_PATTERNS if re.search(pat, n)})
    if core:
        sig.append("toca: " + ", ".join(core))
    code = [n for n in names if CODE_RE.search(n) and not TEST_RE.search(n)]
    tests = [n for n in names if TEST_RE.search(n)]
    if code and not tests:
        sig.append(f"{len(code)} archivos de lógica (hooks/utils/stores/services/sockets) sin tests en el PR")
    size = pr["additions"] + pr["deletions"]
    if size >= 800 or pr["changed_files"] >= 30:
        sig.append(f"PR grande: +{pr['additions']}/-{pr['deletions']} en {pr['changed_files']} archivos")
    hot = [l for l in labels if "Hotfix" in l or "Bugfix" in l]
    if hot:
        sig.append("etiqueta: " + ", ".join(hot))
    if pr["base"]["ref"] not in ("develop", "main", "master"):
        sig.append(f"base: {pr['base']['ref']}")
    if pr.get("merged_at") and pr.get("created_at"):
        mins = (datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")) -
                datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))).total_seconds() / 60
        if mins < 60 and size > 150:
            sig.append(f"mergeado {int(mins)} min después de abrirse")
    return sig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--out", default=os.path.join(TOOL_DIR, ".work"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    token = load_token()
    if args.check:
        d = gh(f"/repos/{REPO}", token)
        print(f"OK: el token puede leer {d['full_name']} (default branch: {d['default_branch']})")
        return
    rd = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else datetime.now(TZ).date()
    start, end = window(rd)
    rng = f"{start.isoformat()}..{end.isoformat()}"

    created = search(f"repo:{REPO} is:pr created:{rng}", token)
    merged = search(f"repo:{REPO} is:pr is:merged merged:{rng}", token)
    nums = {}
    for it in created:
        nums.setdefault(it["number"], set()).add("creado")
    for it in merged:
        nums.setdefault(it["number"], set()).add("mergeado")

    os.makedirs(os.path.join(args.out, "diffs"), exist_ok=True)
    prs = []
    for num in sorted(nums):
        pr = gh(f"/repos/{REPO}/pulls/{num}", token)
        files = list_files(num, token)
        labels = [l["name"] for l in pr.get("labels", [])]
        tribe, source, module, modules = classify(files, labels)
        state = "mergeado" if pr.get("merged_at") else ("cerrado sin merge" if pr["state"] == "closed" else
                                                         ("draft" if pr.get("draft") else "abierto"))
        prefix = re.match(r"^(?:\[[^\]]+\]\s*)?([^|]{2,40}?)\s*\|", pr["title"])
        entry = {
            "number": num, "title": pr["title"],
            "title_module": prefix.group(1).strip() if prefix else None, "url": pr["html_url"], "author": pr["user"]["login"],
            "events": sorted(nums[num]), "state": state, "base": pr["base"]["ref"],
            "created_at": pr["created_at"], "merged_at": pr.get("merged_at"),
            "labels": labels, "tribe": tribe, "tribe_source": source, "module": module,
            "modules": modules, "additions": pr["additions"], "deletions": pr["deletions"],
            "changed_files": pr["changed_files"], "body": (pr.get("body") or "")[:4000],
            "files": [{"f": f["filename"], "s": f["status"], "+": f["additions"], "-": f["deletions"]}
                      for f in files[:300]],
            "risk_signals": risk_signals(pr, files, labels),
        }
        if tribe in DETAIL_TRIBES:
            # Diff completo sólo para las tribus con análisis en detalle (config: detail_tribes).
            diff_path = os.path.join(args.out, "diffs", f"{num}.diff")
            with open(diff_path, "w") as f:
                for fl in files:
                    f.write(f"--- {fl['filename']} ({fl['status']} +{fl['additions']}/-{fl['deletions']})\n")
                    f.write((fl.get("patch") or "[sin patch: binario o demasiado grande]") + "\n\n")
            entry["diff_path"] = diff_path
        prs.append(entry)

    out = {"report_date": rd.isoformat(), "repo": REPO, "detail_tribes": sorted(DETAIL_TRIBES), "window_start": start.isoformat(),
           "window_end": end.isoformat(), "total": len(prs), "prs": prs}
    out_path = os.path.join(args.out, f"prs-{rd.isoformat()}.json")
    with open(out_path, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    by_tribe = Counter(p["tribe"] for p in prs)
    print(f"OK {out_path}\nventana {start:%a %d/%m %H:%M} → {end:%a %d/%m %H:%M} (UTC-3)")
    print(f"{len(prs)} PRs: " + ", ".join(f"{t}={n}" for t, n in by_tribe.most_common()))


if __name__ == "__main__":
    main()
