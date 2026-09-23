from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path('index.html')
REPORT_URL = 'https://forms.gle/zXYtnxwXhGvXmBrq9'

if not INDEX.exists():
    raise SystemExit('index.html missing')

text = INDEX.read_text(encoding='utf-8')
text = text.replace('https://forms.gle/zXYtnxwHgvXmBrq9', REPORT_URL)
text = text.replace('https://forms.gle/zXYtnxwGvXmBrq9', REPORT_URL)
text = re.sub(r'<title>[^<]*</title>', '<title>Google Docs</title>', text, count=1, flags=re.I)

# Homepage rails are visible on the normal homepage and hidden only while search mode is active.
text = text.replace('.ubg43-home-secondary{display:none}', '.ubg43-home-secondary{display:block}')
text = text.replace('.ubg43-searching #trendingSection,.ubg43-searching #newSection{display:block!important}', '.ubg43-searching #trendingSection,.ubg43-searching #newSection{display:none!important}')
text = text.replace('.ubg43-category-view #trendingSection,.ubg43-category-view #newSection{display:block!important}', '.ubg43-category-view #trendingSection,.ubg43-category-view #newSection{display:none!important}')

required = [
    'id="gameGrid"', 'id="searchBar"', 'id="categoryToggle"',
    'id="randomGameButton"', 'id="reportGameButton"',
    'window.openGame=openGame', 'function setSearchMode', 'about:blank', 'ubg43-final-runtime',
    'function isTrending', '.ubg43-badge.new', '.ubg43-badge.trending', "window.open(REPORT_URL,'_blank','noopener,noreferrer')",
    REPORT_URL, 'legacy-index.html', 'zones.json', '<title>Google Docs</title>',
    'wewynhmybroxzynaxnrx.supabase.co', 'SUPABASE_TRENDING_URL', 'function loadGlobalTrending', 'Popular picks based on play activity',
    '.ubg43-home-secondary{display:block}', '.ubg43-searching #trendingSection,.ubg43-searching #newSection{display:none!important}'
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit('Stable runtime missing: ' + ', '.join(missing))

forbidden = [
    'Building your game library…', 'Building your game library...',
    'ubg43-site-protection-runtime', 'ubg43-hotfix-runtime', 'window.location.href=REPORT_URL',
    'ubg43-direct-launch-runtime'
]
bad = [x for x in forbidden if x in text]

# Verify the canonical game player is the automatic ad-filter path for every hosted game.
ad_required = [
    'const isRawGame=u=>/^https:\\/\\/raw\\.githubusercontent\\.com\\//i.test(u);',
    'const AD_HOST_PATTERNS=',
    'function stripKnownAds(html){',
    'let html=stripKnownAds(await r.text());',
    'new MutationObserver(clean)',
    'doubleclick.net',
    'googlesyndication.com',
    'adsterra.com',
    'propellerads.com',
    'monetag.com',
    'popads.net',
    'popcash.net'
]
bad += ['automatic ad-filter wiring missing: '+x for x in ad_required if x not in text]
raw_game_urls = re.findall(r'https://raw\\.githubusercontent\\.com/[^\'\"\\s<>]+', text, flags=re.I)
if not raw_game_urls:
    bad.append('no hosted raw game URLs found to validate the ad-filter launch path')

# All current automated game-library builders must reapply the canonical runtime,
# so newly added cards inherit the same ad filtering automatically.
builder_workflows = [
    '.github/workflows/extra-games.yml',
    '.github/workflows/undertale-games.yml',
    '.github/workflows/auto-categories.yml',
    '.github/workflows/fix-live-site.yml'
]
for wf in builder_workflows:
    wp = Path(wf)
    if not wp.exists():
        bad.append('game builder workflow missing: '+wf)
    else:
        ws = wp.read_text(encoding='utf-8')
        if 'python3 .github/stable-runtime-hotfix.py' not in ws:
            bad.append('game builder does not reapply stable runtime: '+wf)

runtime_start = text.find('<script id="ubg43-final-runtime">')
runtime_end = text.find('</script>', runtime_start)
if runtime_start >= 0 and runtime_end >= 0:
    runtime = text[runtime_start:runtime_end]
    for marker in ('Open directly', 'Open game directly', 'w.location.href=u', 'window.location.href=u'):
        if marker in runtime:
            bad.append('forbidden direct-launch marker in game runtime: ' + marker)
    if "window.open('about:blank'" not in runtime and 'window.open("about:blank"' not in runtime:
        bad.append('game runtime does not open games in about:blank')
else:
    bad.append('canonical game runtime missing')

if bad:
    raise SystemExit('Forbidden legacy runtime remains: ' + ', '.join(bad))

scripts = re.findall(r'<script([^>]*)>(.*?)</script>', text, re.I | re.S)
with tempfile.TemporaryDirectory() as td:
    for i, (attrs, body) in enumerate(scripts):
        if 'application/ld+json' in attrs.lower() or not body.strip():
            continue
        path = Path(td) / f'script{i}.js'
        path.write_text(body, encoding='utf-8')
        check = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True)
        if check.returncode:
            detail = check.stderr.strip().splitlines()[-1] if check.stderr.strip() else 'unknown JavaScript syntax error'
            raise SystemExit(detail)

INDEX.write_text(text, encoding='utf-8')
print('FINAL SITE SANITY PASSED: search hides homepage rails, clearing search restores them, about:blank game player, NEW/TRENDING badges, report link, and JavaScript syntax are valid.')
