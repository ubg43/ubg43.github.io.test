from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from pathlib import Path
import json
import re
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError

NAMESPACE = "ubg43-global-trending-v1"
SOURCE = Path("legacy-index.html")
OUTPUT = Path("global-trending.json")
MAX_WORKERS = 24
REQUEST_TIMEOUT = 6

CARD_RE = re.compile(r'<div\s+class="game-card"[^>]*>.*?</div>', re.I | re.S)
TITLE_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.I | re.S)
URL_PATTERNS = [
    re.compile(r"openGame\(\s*['\"]([^'\"]+)", re.I),
    re.compile(r"window\.open\(\s*['\"]([^'\"]+)", re.I),
    re.compile(r"href=['\"]([^'\"]+)", re.I),
]

def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", value))).strip()

def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def global_key(title: str, url: str) -> str:
    raw = normalize(title) + "|" + url.split("#", 1)[0]
    h = 2166136261
    for ch in raw:
        h ^= ord(ch)
        h = ((h << 0) ^ 0) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    return "g_" + np_to_base36(h)

def np_to_base36(number: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number == 0:
        return "0"
    out = []
    while number:
        number, rem = divmod(number, 36)
        out.append(chars[rem])
    return "".join(reversed(out))

def extract_games() -> list[dict]:
    if not SOURCE.exists():
        raise SystemExit("legacy-index.html missing")
    text = SOURCE.read_text(encoding="utf-8")
    out, seen = [], set()
    for card in CARD_RE.findall(text):
        tm = TITLE_RE.search(card)
        if not tm:
            continue
        title = clean_text(tm.group(1))
        if not title or title.casefold().startswith("[!"):
            continue
        url = ""
        for pat in URL_PATTERNS:
            m = pat.search(card)
            if m:
                url = unescape(m.group(1)).strip()
                break
        if not url:
            continue
        key = global_key(title, url)
        if key in seen:
            continue
        seen.add(key)
        out.append({"key": key, "title": title, "url": url})
    if len(out) < 300:
        raise SystemExit(f"Only {len(out)} games found in legacy-index.html; refusing to overwrite global trending with an incomplete list.")
    return out

ERROR_CODES = {}
def fetch_count(key: str) -> tuple[str, int | None]:
    url = f"https://api.counterapi.dev/v1/{urllib.parse.quote(NAMESPACE, safe='')}/{urllib.parse.quote(key, safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": "UBG43-global-trending/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        value = data.get("count", data.get("value", data.get("data", {}).get("count") if isinstance(data.get("data"), dict) else None))
        value = int(value)
        return key, max(0, value)
    except HTTPError as exc:
        ERROR_CODES[exc.code] = ERROR_CODES.get(exc.code, 0) + 1
        return key, None
    except Exception:
        ERROR_CODES["other"] = ERROR_CODES.get("other", 0) + 1
        return key, None

def main() -> None:
    games = extract_games()
    old = {}
    if OUTPUT.exists():
        try:
            payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
            old = {str(x.get("key")): int(x.get("count", 0)) for x in payload.get("games", []) if x.get("key")}
        except Exception:
            old = {}

    counts = old.copy()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_count, game["key"]): game for game in games}
        ok = 0
        for future in as_completed(futures):
            key, count = future.result()
            if count is not None:
                counts[key] = count
                ok += 1

    rows = [
        {"key": game["key"], "title": game["title"], "url": game["url"], "count": int(counts.get(game["key"], 0))}
        for game in games
        if int(counts.get(game["key"], 0)) > 0
    ]
    rows.sort(key=lambda x: (-x["count"], x["title"].casefold()))
    snapshot = {
        "version": 1,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "games": rows[:100],
        "scannedGames": len(games),
        "successfulReads": ok,
    }
    OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"GLOBAL TRENDING SNAPSHOT: scanned={len(games)} successful_reads={ok} nonzero={len(rows)} top={len(snapshot['games'])} errors={ERROR_CODES}")

if __name__ == "__main__":
    main()
