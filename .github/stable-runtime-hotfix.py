from pathlib import Path
import re
# Canonical runtime trigger: this script is the single final browser controller for the homepage.

p = Path('index.html')
if not p.exists():
    raise SystemExit('index.html missing')

s = p.read_text(encoding='utf-8')
if '<!-- UBG43 verified library source: zones.json -->' not in s:
    s = s.replace('</head>', '<!-- UBG43 verified library source: zones.json -->\n</head>', 1)

# Preserve the site's single JSON-LD block, then remove every other inline controller.
m = re.search(r"""<script\b[^>]*type=["']application/ld\+json["'][^>]*>.*?</script>""", s, flags=re.I | re.S)
jsonld = m.group(0) if m else ''
s = re.sub(r"""<script\b[^>]*>.*?</script>""", '', s, flags=re.I | re.S)
if jsonld:
    s = s.replace('</head>', jsonld + '\n</head>', 1)

# Remove old runtime style blocks before installing the canonical style.
s = re.sub(r"""<style[^>]*id=["'](?:ubg43-final-runtime-style|smart-game-ui|expanded-category-runtime-style)["'][^>]*>.*?</style>""", '', s, flags=re.I | re.S)

# Keep the main runtime from rebuilding the grid destructively as late game data arrives.
old = "function renderGrid(){if(!state.cards.size){grid.innerHTML='';state.games.forEach(g=>{const c=cardFor(g);state.cards.set(gameKey(g),c);grid.append(c)})}applyFilters()}"
new = "function renderGrid(){const frag=document.createDocumentFragment();state.games.forEach(g=>{const k=gameKey(g);if(!state.cards.has(k))state.cards.set(k,cardFor(g));frag.appendChild(state.cards.get(k))});grid.append(frag);applyFilters()}"
if old in s:
    s = s.replace(old, new, 1)

# Store each game's URL on its card so the final click handler never loses it.
old = "c.className='game-card';c.tabIndex=0;c.dataset.category="
new = "c.className='game-card';c.tabIndex=0;c.dataset.url=g.url;c.dataset.category="
if old in s:
    s = s.replace(old, new, 1)

# Always use lazy images in the large dynamically-built library.
old = "img.loading=mini?'lazy':'eager'"
if old in s:
    s = s.replace(old, "img.loading='lazy'", 1)

# Avoid re-running category construction on every card filter operation.
old = "function applyFilters(){const q=normalize(state.query);let visible=0;state.games.forEach(g=>{const c=state.cards.get(gameKey(g));if(!c)return;const ok=matches(g)&&(!q||normalize(g.title).includes(q));c.style.display=ok?'':'none';if(ok)visible++;decorate(c,g)});status.textContent=`${visible} of ${state.games.length} games shown`;renderCategories()}"
new = "function applyFilters(){const q=normalize(state.query);let visible=0;state.games.forEach(g=>{const c=state.cards.get(gameKey(g));if(!c)return;const ok=matches(g)&&(!q||normalize(g.title).includes(q));c.style.display=ok?'':'none';if(ok)visible++});status.textContent=`${visible} of ${state.games.length} games shown`}"
if old in s:
    s = s.replace(old, new, 1)

# Repair the report link typo from older hotfix revisions.
s = s.replace('https://forms.gle/zXYtnxwHgvXmBrq9', 'https://forms.gle/zXYtnxwXhGvXmBrq9')

# Remove a previous copy of the safety runtime before inserting the current one.
s = re.sub(r'<style id="ubg43-final-runtime-style">.*?</style>\s*<script id="ubg43-final-runtime">.*?</script>', '', s, count=1, flags=re.I | re.S)

runtime = r'''<style id="ubg43-final-runtime-style">
.ubg43-badges{position:absolute;left:9px;top:9px;z-index:20;display:flex;flex-direction:column;gap:5px;pointer-events:none}
.ubg43-badge{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:6px 8px 8px 6px;font:900 9px/1 Arial,sans-serif;letter-spacing:.06em;box-shadow:0 4px 10px rgba(0,0,0,.22);white-space:nowrap}
.ubg43-badge.new{background:#e52424;color:#ffe600}.ubg43-badge.trending{background:#ffe600;color:#c31d1d}
.search-shell input[type="search"]{-webkit-appearance:textfield;appearance:textfield}.search-shell input[type="search"]::-webkit-search-cancel-button,.search-shell input[type="search"]::-webkit-search-decoration{-webkit-appearance:none;appearance:none;display:none}.search-clear{display:none;align-items:center;justify-content:center;padding:0;margin:0;line-height:1;text-align:center;box-sizing:border-box}
.ubg43-searching .hero{display:none}.ubg43-searching #searchPage{display:block!important}.ubg43-searching #gameGrid{padding-top:6px}.ubg43-searching #trendingSection,.ubg43-searching #newSection{display:block!important}.ubg43-category-view #trendingSection,.ubg43-category-view #newSection{display:none!important}
@media(max-width:640px){.ubg43-badge{height:20px;padding:0 7px;font-size:8px}}
</style>
<script id="ubg43-final-runtime">
(()=>{
'use strict';
const $=id=>document.getElementById(id),grid=$('gameGrid'),search=$('searchBar'),clear=$('searchClear'),results=$('searchResults'),searchPage=$('searchPage'),searchPageText=$('searchPageText'),recSection=$('recommendSection'),trendRail=$('trendingRail'),newRail=$('newRail'),recRail=$('recommendRail');
const REPORT_URL='https://forms.gle/zXYtnxwXhGvXmBrq9';
const SUPABASE_TRENDING_URL='https://wewynhmybroxzynaxnrx.supabase.co';
const SUPABASE_TRENDING_KEY='sb_publishable_9-0Y5XyyOzpnILu1cb6dHg_j8234P2p';
const SUPABASE_TRENDING_HEADERS={'apikey':SUPABASE_TRENDING_KEY,'Authorization':'Bearer '+SUPABASE_TRENDING_KEY,'Content-Type':'application/json'};
const globalTrending={ready:false,loading:false,failed:false,updatedAt:null,counts:Object.create(null)};
const BLOCKED_TITLE_PATTERNS=['[!] comments','suggest games','d4c9vfywyu','1 date danger'];
const blockedTitle=c=>{const t=String(c?.querySelector('h3')?.textContent||'').trim().toLowerCase();return BLOCKED_TITLE_PATTERNS.some(x=>t.includes(x))||t.startsWith('[!]')};
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const titleOf=c=>(c?.querySelector('h3')?.textContent||'').trim();
const urlOf=c=>{const d=c?.dataset?.url;if(d)return d;const a=c?.getAttribute('onclick')||'',m=a.match(/openGame\(\s*[\'\"]([^\'\"]+)/i);if(m)return m[1];const w=a.match(/window\.open\(\s*[\'\"]([^\'\"]+)/i);if(w)return w[1];return c?.querySelector('a[href]')?.href||''};
const imageOf=c=>c?.querySelector('img')?.getAttribute('src')||'';
const keyOf=c=>norm(titleOf(c))+'|'+urlOf(c).replace(/#.*$/,'');
const read=(k,f)=>{try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(f))||f}catch(_){return f}};
const write=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(_){}};
const playKey=c=>norm(titleOf(c))+'|'+imageOf(c);
const globalKey=c=>{let s=keyOf(c),h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return 'g_'+(h>>>0).toString(36)};
const globalCount=c=>Number(globalTrending.counts[globalKey(c)]||0);
const parseGlobalCount=data=>{const v=data?.count??data?.value??data?.data?.count??data?.data?.value;const n=Number(v);return Number.isFinite(n)?n:null};
const updateTrendRailState=()=>{const sub=document.querySelector('#trendingSection .section-sub');if(!sub)return;const live=Object.keys(globalTrending.counts).length;sub.textContent=live?'Most played across UBG43':globalTrending.loading?'Trending picks • loading global play activity…':globalTrending.failed?'Trending picks • will update automatically':'Popular picks based on play activity'};
async function incrementGlobal(c){
  if(!c||!titleOf(c))return;
  const k=globalKey(c),now=Date.now(),sent=read('ubg43_global_sent',{}),last=Number(sent[k]||0);
  if(now-last<60000)return;
  sent[k]=now;write('ubg43_global_sent',sent);
  globalTrending.counts[k]=(globalTrending.counts[k]||0)+1;
  renderRails();decorate();
  try{
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7000);
    const r=await fetch(SUPABASE_TRENDING_URL+'/rest/v1/rpc/record_game_play',{method:'POST',headers:SUPABASE_TRENDING_HEADERS,body:JSON.stringify({p_game_key:k,p_title:titleOf(c),p_game_url:urlOf(c)}),cache:'no-store',signal:controller.signal});
    clearTimeout(timer);
    if(!r.ok)throw new Error('Supabase play '+r.status);
    const server=Number(await r.json());
    if(Number.isFinite(server))globalTrending.counts[k]=server;
    globalTrending.ready=true;globalTrending.failed=false;updateTrendRailState();renderRails();decorate();
  }catch(_){
    if(!globalTrending.ready)globalTrending.failed=true;
  }
}
const recordPlay=c=>{const h=read('ubg43_final_plays',{}),k=playKey(c),x=h[k]||{title:titleOf(c),plays:0,last:0};x.plays++;x.last=Date.now();h[k]=x;write('ubg43_final_plays',h);incrementGlobal(c)};
const recordSearch=q=>{const n=norm(q);if(n.length<2)return;const h=read('ubg43_final_searches',{}),x=h[n]||{count:0,last:0};x.count++;x.last=Date.now();h[n]=x;write('ubg43_final_searches',h)};
const escapeHtml=s=>String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const isRawGame=u=>/^https:\/\/raw\.githubusercontent\.com\/gn-math\/html\//i.test(u);
const rawBase=u=>{try{return new URL('.',u).href}catch(_){return u}};
function buildGameWindow(w,title){
  const d=w.document;
  d.open();
  d.write(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(title||'UBG43 Game')}</title><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#06142f}#stage{position:fixed;inset:0;width:100%;height:100%}#frame{width:100%;height:100%;border:0;display:block;background:#fff}</style></head><body><div id="stage"></div></body></html>`);
  d.close();
}
async function mountGame(w,u,title){
  if(!w||w.closed)return;
  buildGameWindow(w,title);
  const stage=w.document.getElementById('stage');
  const iframe=w.document.createElement('iframe');
  iframe.id='frame';
  iframe.title=title||'UBG43 game';
  iframe.referrerPolicy='no-referrer';
  iframe.allow='autoplay; fullscreen; gamepad; clipboard-read; clipboard-write';
  iframe.setAttribute('allowfullscreen','');
  stage.appendChild(iframe);
  if(isRawGame(u)){
    try{
      const controller=new AbortController();
      const timer=setTimeout(()=>controller.abort(),10000);
      const r=await fetch(u,{cache:'no-store',mode:'cors',signal:controller.signal});
      clearTimeout(timer);
      if(!r.ok)throw new Error('Game source unavailable');
      let html=await r.text();
      const base=rawBase(u).replace(/&/g,'&amp;').replace(/"/g,'&quot;');
      if(!/<base\b/i.test(html)) html=html.replace(/<head([^>]*)>/i,'<head$1><base href="${base}">');
      const blobUrl=URL.createObjectURL(new Blob([html],{type:'text/html'}));
      iframe.src=blobUrl;
      iframe.addEventListener('load',()=>setTimeout(()=>{try{URL.revokeObjectURL(blobUrl)}catch(_){}},300000),{once:true});
      return true;
    }catch(_){
      stage.innerHTML='<div style="display:grid;place-items:center;height:100%;padding:24px;color:#fff;text-align:center;background:#06142f"><div><h2 style="margin:0 0 8px">This game could not be loaded inside UBG43.</h2><p style="opacity:.72;max-width:520px">This game does not allow in-page embedding, so it cannot be opened in the UBG43 player.</p></div></div>';
      return false;
    }
  }
  iframe.src=u;
  return true;
}
const openGame=(url,title='UBG43 Game')=>{
  const u=String(url||'').trim();
  if(!u)return false;
  let w=null;
  try{w=window.open('about:blank','_blank')}catch(_){}
  if(!w){
    const old=document.getElementById('ubg43-popup-message');if(old)old.remove();
    const n=document.createElement('div');n.id='ubg43-popup-message';n.textContent='Allow pop-ups for UBG43 to open games in a new tab.';n.style.cssText='position:fixed;z-index:3000;right:18px;bottom:18px;background:#06142f;color:#fff;padding:12px 15px;border-radius:11px;box-shadow:0 10px 28px rgba(0,0,0,.35);font-weight:800';
    document.body.append(n);setTimeout(()=>n.remove(),4500);return false;
  }
  mountGame(w,u,title).catch(()=>{});
  return true;
};
window.openGame=openGame;
function cards(){return grid?[...grid.querySelectorAll('.game-card')]:[]}
async function loadLegacyIntoGrid(){
  if(cards().length>=300)return cards().length;
  try{
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),7000);
    const r=await fetch('legacy-index.html?stable=1',{cache:'no-store',signal:controller.signal});
    clearTimeout(timer);
    if(!r.ok)throw new Error('legacy '+r.status);
    const d=new DOMParser().parseFromString(await r.text(),'text/html');
    const source=[...d.querySelectorAll('.game-card')];
    if(source.length<100)throw new Error('legacy game count too low');
    grid.textContent=''; const seen=new Set();
    source.forEach(src=>{
      const h=src.querySelector('h3'),img=src.querySelector('img'); if(!h||!img)return;
      const rawTitle=h.textContent.trim();
      const title=rawTitle.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
      if(!title||BLOCKED_TITLE_PATTERNS.some(x=>rawTitle.toLowerCase().includes(x))||rawTitle.trim().startsWith('[!]')||seen.has(title))return;
      const c=src.cloneNode(true),a=c.getAttribute('onclick')||'',m=a.match(/openGame\(\s*[\'\"]([^\'\"]+)/i);
      if(m)c.dataset.url=m[1]; seen.add(title); grid.append(c);
    });
  }catch(_){}
  return cards().length;
}
function isNew(c){if(c.dataset.new==='1'||c.dataset.new==='true')return true;const d=Date.parse(c.dataset.newSince||c.dataset.date||'');return Number.isFinite(d)&&Date.now()-d<45*86400000}
const fallbackTrendingKeys=new Set();
function isTrending(c){return globalCount(c)>0||fallbackTrendingKeys.has(keyOf(c))}
function badge(c,text,cls){const box=c.querySelector('.ubg43-badges')||(()=>{const x=document.createElement('div');x.className='ubg43-badges';c.append(x);return x})();const b=document.createElement('span');b.className='ubg43-badge '+cls;b.textContent=text;box.append(b)}
function decorate(){const cs=cards();cs.forEach(c=>{c.querySelector('.ribbons')?.remove();c.querySelector('.ubg43-badges')?.remove();if(isNew(c))badge(c,'NEW','new');if(isTrending(c))badge(c,'TRENDING','trending')})}
function wire(c){if(!c)return;c.tabIndex=0;if(!c.dataset.url)c.dataset.url=urlOf(c)}
function applyView(){const q=norm(search?.value||''),cat=window.__ubg43ActiveCategory||'All Games',cs=cards();cs.forEach(c=>{const text=norm(titleOf(c)),catOk=cat==='All Games'||(cat==='New Games'?isNew(c):cat==='Trending'?isTrending(c):(c.dataset.category||'Casual')===cat);c.style.display=catOk&&(!q||text.includes(q))?'':'none'});const shown=cs.filter(c=>c.style.display!=='none').length;if($('status'))$('status').textContent=`${shown} games shown`}
function similarity(a,b){const A=new Set(norm(a).split(' ').filter(x=>x.length>1)),B=new Set(norm(b).split(' ').filter(x=>x.length>1));if(!A.size||!B.size)return 0;let n=0;A.forEach(x=>B.has(x)&&n++);return n/Math.sqrt(A.size*B.size)}
function fillRail(rail,srcs){if(!rail)return;rail.innerHTML='';const used=new Set();srcs.forEach(src=>{if(blockedTitle(src))return;const k=keyOf(src);if(used.has(k))return;used.add(k);const c=src.cloneNode(true);c.dataset.url=urlOf(src);c.style.display='';c.hidden=false;c.querySelector('.ribbons')?.remove();c.querySelector('.ubg43-badges')?.remove();rail.append(c);wire(c);if(isNew(src))badge(c,'NEW','new');if(isTrending(src))badge(c,'TRENDING','trending')});if(srcs.length){const d=document.createElement('div');d.className='done';d.innerHTML='<span>That’s all for now ✨<small>More games are added automatically.</small></span>';rail.append(d)}}
function renderRails(){
  const cs=cards(),fresh=cs.filter(isNew).slice(0,24);
  const live=cs.filter(c=>globalCount(c)>0).sort((a,b)=>(globalCount(b)-globalCount(a))||titleOf(a).localeCompare(titleOf(b)));
  const backup=cs.filter(c=>!isNew(c)&&!live.includes(c)).slice(0,Math.max(0,24-live.length));
  fallbackTrendingKeys.clear();
  if(live.length<24)backup.forEach(c=>fallbackTrendingKeys.add(keyOf(c)));
  fillRail(trendRail,live.concat(backup).slice(0,24));
  fillRail(newRail,fresh.length?fresh:cs.filter(isNew).slice(0,24));
  updateTrendRailState();
  decorate();
}
function recommendations(q){if(!recSection||!recRail)return;const ph=read('ubg43_final_plays',{}),sh=read('ubg43_final_searches',{}),n=norm(q),out=cards().filter(c=>!norm(titleOf(c)).includes(n)).map(c=>{let score=similarity(titleOf(c),q)*.72;score+=(ph[playKey(c)]?.plays||0)*.08;Object.entries(sh).forEach(([k,v])=>score+=similarity(titleOf(c),k)*Math.min(5,v.count||0)*.05);if(isNew(c))score+=.1;return {c,score}}).sort((a,b)=>b.score-a.score||titleOf(a.c).localeCompare(titleOf(b.c))).slice(0,24).map(x=>x.c);fillRail(recRail,out);recSection.classList.toggle('hidden',!out.length)}
function setSearchMode(q){q=q.trim();if(!q){clearSearch();return}window.__ubg43SearchMode=true;document.body.classList.add('ubg43-searching');if(searchPage)searchPage.classList.remove('hidden');if(searchPageText)searchPageText.textContent=`Showing matching games for “${q}”.`;recordSearch(q);applyView();recommendations(q);results?.classList.remove('open');search?.blur()}
function clearSearch(){window.__ubg43SearchMode=false;document.body.classList.remove('ubg43-searching');if(search)search.value='';if(clear)clear.style.display='none';results?.classList.remove('open');searchPage?.classList.add('hidden');recSection?.classList.add('hidden');applyView();window.scrollTo({top:0,behavior:'smooth'})}
function showSuggestions(q){if(!results)return;results.innerHTML='';const n=norm(q);if(!n){results.classList.remove('open');return}const hits=cards().filter(c=>norm(titleOf(c)).includes(n)).slice(0,7);if(!hits.length){const d=document.createElement('div');d.className='search-empty';d.textContent='No matching games yet';results.append(d);results.classList.add('open');return}hits.forEach(c=>{const b=document.createElement('button');b.type='button';b.className='search-result';b.innerHTML='<img alt=""><span class="search-copy"><span class="search-title"></span><span class="search-label">Play game</span></span>';b.querySelector('img').src=imageOf(c);b.querySelector('img').alt=titleOf(c);b.querySelector('.search-title').textContent=titleOf(c);b.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();if(search)search.value=titleOf(c);setSearchMode(titleOf(c))},{capture:true});results.append(b)});results.classList.add('open')}
function openCategories(){const side=$('categorySidebar'),ov=$('categoryOverlay');if(!side)return;side.classList.add('open');ov?.classList.add('open');side.setAttribute('aria-hidden','false');document.body.classList.add('locked');const list=$('categoryList');if(!list)return;list.innerHTML='';const cs=cards(),counts={};cs.forEach(c=>{const cat=c.dataset.category||'Casual';counts[cat]=(counts[cat]||0)+1});['All Games','New Games','Trending','Action','Adventure','Horror','Multiplayer','Fighting','Survival','Platformer','Racing','Sports','Puzzle','Arcade','Strategy','Simulation','Casual','Anime','Rhythm & Music','Card & Board','io'].forEach(cat=>{const b=document.createElement('button');b.type='button';b.className='category'+(window.__ubg43ActiveCategory===cat?' active':'');const n=cat==='All Games'?cs.length:cat==='New Games'?cs.filter(isNew).length:cat==='Trending'?cs.filter(isTrending).length:(counts[cat]||0);b.innerHTML='<span class="category-main"><span class="dot"></span><span class="category-name"></span></span><span class="category-count"></span>';b.querySelector('.category-name').textContent=cat;b.querySelector('.category-count').textContent=String(n);b.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();window.__ubg43ActiveCategory=cat;document.body.classList.toggle('ubg43-category-view',cat!=='All Games');applyView();closeCategories()},{capture:true});list.append(b)})}
function closeCategories(){$('categorySidebar')?.classList.remove('open');$('categoryOverlay')?.classList.remove('open');$('categorySidebar')?.setAttribute('aria-hidden','true');document.body.classList.remove('locked')}
function bind(){
 search?.addEventListener('input',e=>{e.stopImmediatePropagation();const q=search.value.trim();if(clear)clear.style.display=q?'inline-flex':'none';document.body.classList.toggle('ubg43-searching',!!q);showSuggestions(q);if(!q)clearSearch();else applyView()},{capture:true});
 search?.addEventListener('keydown',e=>{e.stopImmediatePropagation();if(e.key==='Enter'){e.preventDefault();setSearchMode(search.value)}else if(e.key==='Escape'){e.preventDefault();clearSearch()}},{capture:true});
 clear?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();clearSearch()},{capture:true});
 $('randomGameButton')?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();const pool=cards().filter(c=>c.style.display!=='none'),list=pool.length?pool:cards(),c=list[Math.floor(Math.random()*list.length)];if(c){recordPlay(c);openGame(urlOf(c),titleOf(c));decorate();renderRails()}},{capture:true});
 $('reportGameButton')?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();window.open(REPORT_URL,'_blank','noopener,noreferrer')},{capture:true});
 $('categoryToggle')?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();openCategories()},{capture:true});
 $('categoryClose')?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();closeCategories()},{capture:true});
 $('categoryOverlay')?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();closeCategories()},{capture:true});
 [['trendPrev','trendingRail'],['trendNext','trendingRail'],['newPrev','newRail'],['newNext','newRail'],['recPrev','recommendRail'],['recNext','recommendRail']].forEach(([id,rid])=>$(id)?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();const r=$(rid);if(r)r.scrollBy({left:Math.max(280,r.clientWidth*.8)*(id.includes('Prev')?-1:1),behavior:'smooth'})},{capture:true}));
 ['trendingRail','newRail','recommendRail'].forEach(id=>$(id)?.addEventListener('wheel',e=>{if(Math.abs(e.deltaY)>Math.abs(e.deltaX)){e.currentTarget.scrollLeft+=e.deltaY}},{passive:true}));
 document.addEventListener('click',e=>{const c=e.target.closest?.('.game-card');if(!c)return;e.preventDefault();e.stopImmediatePropagation();const u=urlOf(c);recordPlay(c);if(u)openGame(u,titleOf(c));renderRails();decorate()},{capture:true});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('categorySidebar')?.classList.contains('open'))closeCategories()},{capture:true});
}
function sync(){cards().forEach(c=>{if(blockedTitle(c))c.remove();else wire(c)});decorate();renderRails();applyView();const s=$('status');if(s&&cards().length)s.textContent=cards().length+' games ready'}
async function loadGlobalTrending(){
  if(globalTrending.loading)return;
  globalTrending.loading=true;updateTrendRailState();
  try{
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7000);
    const r=await fetch(SUPABASE_TRENDING_URL+'/rest/v1/rpc/get_trending_games',{method:'POST',headers:SUPABASE_TRENDING_HEADERS,body:JSON.stringify({p_limit:48}),cache:'no-store',signal:controller.signal});
    clearTimeout(timer);
    if(!r.ok)throw new Error('Supabase trending '+r.status);
    const rows=await r.json(),map=Object.create(null);
    (Array.isArray(rows)?rows:[]).forEach(x=>{const k=String(x?.game_key||'');const n=Number(x?.play_count||0);if(k&&Number.isFinite(n)&&n>0)map[k]=n});
    globalTrending.counts=map;
    globalTrending.updatedAt=new Date().toISOString();
    globalTrending.ready=true;
    globalTrending.failed=false;
  }catch(_){globalTrending.failed=true}
  globalTrending.loading=false;updateTrendRailState();decorate();renderRails();applyView();
}
function start(){
  bind();sync();updateTrendRailState();
  loadGlobalTrending();
  setInterval(loadGlobalTrending,60000);
  loadLegacyIntoGrid().then(()=>{sync();setTimeout(sync,700);setTimeout(sync,1800);setTimeout(sync,3500);loadGlobalTrending()}).catch(()=>{sync();loadGlobalTrending()});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
</script>'''

needle = '</body>'
if needle.lower() not in s.lower():
    raise SystemExit('body end marker not found')
body_pos = s.lower().rfind('</body>')
if body_pos < 0:
    raise SystemExit('body end marker not found')
s = s[:body_pos] + runtime + '\n</body>' + s[body_pos + len('</body>'):]
p.write_text(s, encoding='utf-8')
print('STABLE RUNTIME: about:blank game windows, no direct-launch controls, full legacy feed, working search/buttons/carousels/recommendations, and NEW/TRENDING badges.')
