"""
monitor.py
lang: Python 3.11, file: monitor.py
GitHub Actions forum monitor — scrapea foros de hacking, manda hits al webhook
storage: GitHub Gist (sin Gist token corre igual pero sin memoria entre runs)
"""

import json, hashlib, time, os, sys
from datetime import datetime
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] pip install requests beautifulsoup4"); sys.exit(1)

# ── ENV ────────────────────────────────────────────────────────────────────────
WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "")
GIST_TOKEN   = os.getenv("GIST_TOKEN", "")
GIST_ID      = os.getenv("GIST_ID", "")
GIST_FILE    = "seen_posts.json"

# ── KEYWORDS ───────────────────────────────────────────────────────────────────
KEYWORDS = [
    "database","db leak","db dump","combo","combolist","leak","dump","sqli",
    "credentials","stealer","infostealer","logs","hash","breach","wordlist",
    "config","grabber","user:pass","email:pass","login:pass",
    "soulhemteam","chronus","157","141",
    "bypass","cheat","exploit","0day","rce","lfi",
    "free download","gratis","descarga gratuita","free db",
]

# ── SOURCES ────────────────────────────────────────────────────────────────────
SOURCES = [
    {
        "name": "BreachForums",
        "urls": [
            "https://breachforums.st/Forum-Databases",
            "https://breachforums.st/Forum-Leaks",
            "https://breachforums.st/Forum-Combolists",
        ],
        "sel": ".thread-title a, .threadlist a[href*='Thread-'], h3 a",
        "json": False,
    },
    {
        "name": "Nulled",
        "urls": [
            "https://www.nulled.to/forum/196-databases/",
            "https://www.nulled.to/forum/5-leaks/",
            "https://www.nulled.to/forum/50-tools-programs/",
        ],
        "sel": ".topic_title a, h3.ipsType_break a, .ipsDataItem_title a",
        "json": False,
    },
    {
        "name": "Cracked",
        "urls": [
            "https://cracked.to/Forum-Databases",
            "https://cracked.to/Forum-Leaks",
            "https://cracked.to/Forum-Configs",
        ],
        "sel": ".thread-title a, [class*='thread'] a, .subject a",
        "json": False,
    },
    {
        "name": "XSS.is",
        "urls": ["https://xss.is/forums/leaks.44/"],
        "sel": "h3.structItem-title a",
        "json": False,
    },
    {
        "name": "Hackforums",
        "urls": [
            "https://hackforums.net/forumdisplay.php?fid=68",
            "https://hackforums.net/forumdisplay.php?fid=197",
        ],
        "sel": "span.subject a, .threadlist a",
        "json": False,
    },
    {
        "name": "GitHub",
        "urls": [
            "https://api.github.com/search/repositories?q=database+dump+leak+free&sort=updated&per_page=10",
            "https://api.github.com/search/repositories?q=stealer+logs+combo+list&sort=updated&per_page=10",
            "https://api.github.com/search/repositories?q=infostealer+credentials+free&sort=updated&per_page=10",
            "https://api.github.com/search/repositories?q=soulhemteam+OR+chronusteam+OR+hack157&sort=updated&per_page=10",
        ],
        "sel": None,
        "json": True,
    },
    {
        "name": "LeakIX",
        "urls": [
            "https://leakix.net/search?scope=leak&q=database",
            "https://leakix.net/search?scope=leak&q=mysql+dump",
            "https://leakix.net/search?scope=leak&q=credentials",
        ],
        "sel": "h3, .event-title, [class*='leak-title'], [class*='result'] h4",
        "json": False,
    },
]

# ── HEADERS ────────────────────────────────────────────────────────────────────
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

session = requests.Session()
session.headers.update({
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
})

# ── GIST STORAGE ───────────────────────────────────────────────────────────────
def gist_load() -> set:
    if not (GIST_TOKEN and GIST_ID):
        log("⚠  sin Gist token — sin memoria entre runs")
        return set()
    try:
        r = requests.get(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={"Authorization": f"Bearer {GIST_TOKEN}",
                     "Accept": "application/vnd.github+json"},
            timeout=15,
        )
        r.raise_for_status()
        content = r.json()["files"][GIST_FILE]["content"]
        return set(json.loads(content))
    except Exception as e:
        log(f"[gist-load-err] {e}")
        return set()

def gist_save(seen: set):
    if not (GIST_TOKEN and GIST_ID):
        return
    # mantener lista ordenada — trim a 8000 desde el final de inserción no aplica
    # a sets; convertimos a lista estable y guardamos todo (Gist soporta 5MB+)
    payload = json.dumps(sorted(seen)[-8000:])
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={"Authorization": f"Bearer {GIST_TOKEN}",
                     "Accept": "application/vnd.github+json"},
            json={"files": {GIST_FILE: {"content": payload}}},
            timeout=15,
        )
        r.raise_for_status()
        log(f"✓ gist guardado — {len(seen)} entries")
    except Exception as e:
        log(f"[gist-save-err] {e}")

# ── UTILS ──────────────────────────────────────────────────────────────────────
def uid(src: str, text: str) -> str:
    return hashlib.md5(f"{src}:{text.strip().lower()}".encode()).hexdigest()[:14]

def has_kw(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in KEYWORDS)

def log(msg: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}", flush=True)

def fetch(url: str) -> requests.Response | None:
    try:
        r = session.get(url, timeout=20, allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception as e:
        log(f"  [err] {url[:55]} → {e}")
        return None

# ── WEBHOOK ────────────────────────────────────────────────────────────────────
def webhook(source: str, title: str, link: str = ""):
    if not WEBHOOK_URL:
        return
    body = (
        f"🔴 **{source}**\n"
        f"📌 `{title[:250]}`\n"
        f"{f'🔗 <{link}>' if link else ''}\n"
        f"⏱ `{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}`"
    )
    try:
        requests.post(WEBHOOK_URL,
                      json={"content": body, "username": "ForumMonitor"},
                      timeout=10)
    except Exception as e:
        log(f"  [webhook-err] {e}")

# ── SCRAPERS ───────────────────────────────────────────────────────────────────
def scrape_html(src: dict, url: str, seen: set) -> int:
    r = fetch(url)
    if not r:
        return 0
    soup = BeautifulSoup(r.text, "html.parser")
    hits = 0
    for el in soup.select(src["sel"]):
        title = el.get_text(strip=True)
        href  = urljoin(url, el.get("href", ""))   # URL absoluta
        if not title or len(title) < 6:
            continue
        pid = uid(src["name"], title)
        if pid in seen:
            continue
        seen.add(pid)
        kw = has_kw(title)
        log(f"  {'🔴' if kw else '⚪'} [{src['name']}] {title[:90]}")
        if kw:
            hits += 1
            webhook(src["name"], title, href)
    return hits

def scrape_github(src: dict, url: str, seen: set) -> int:
    r = fetch(url)
    if not r:
        return 0
    try:
        data = r.json()
    except Exception:
        return 0
    hits = 0
    for repo in data.get("items", []):
        pid = f"gh:{repo['id']}"
        if pid in seen:
            continue
        seen.add(pid)
        name  = repo.get("full_name", "")
        desc  = (repo.get("description") or "")[:80]
        stars = repo.get("stargazers_count", 0)
        link  = repo.get("html_url", "")
        title = f"{name} — {desc}"
        if not has_kw(title):                       # mismo filtro que HTML
            log(f"  ⚪ [GitHub] {title[:90]}")
            continue
        log(f"  🔴 [GitHub] {title[:90]} [⭐{stars}]")
        hits += 1
        webhook("GitHub", f"{title} [⭐{stars}]", link)
    return hits

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    log("=== forum-monitor start ===")
    seen = gist_load()
    log(f"seen cargado: {len(seen)} entries")
    total = 0

    for src in SOURCES:
        for url in src["urls"]:
            log(f"→ {src['name']} | {url[:65]}")
            if src["json"]:
                total += scrape_github(src, url, seen)
            else:
                total += scrape_html(src, url, seen)
            time.sleep(1.5)   # era 3 — baja worst-case a ~5.5min

    gist_save(seen)
    log(f"=== done — {total} hits nuevos ===")

if __name__ == "__main__":
    main()
