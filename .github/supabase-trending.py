from pathlib import Path
import re

SUPABASE_URL = 'https://wewynhmybroxzynaxnrx.supabase.co'
SUPABASE_KEY = 'sb_publishable_9-0Y5XyyOzpnILu1cb6dHg_j8234P2p'

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_constants = """const GLOBAL_TRENDING_API='https://api.counterapi.dev/v1';
const GLOBAL_TRENDING_NAMESPACE='ubg43-global-trending-v1';
const GLOBAL_TRENDING_SNAPSHOT='global-trending.json';
const globalTrending={ready:false,loading:false,failed:false,updatedAt:null,counts:Object.create(null)};"""
new_constants = f"""const SUPABASE_TRENDING_URL='{SUPABASE_URL}';
const SUPABASE_TRENDING_KEY='{SUPABASE_KEY}';
const SUPABASE_TRENDING_HEADERS={{'apikey':SUPABASE_TRENDING_KEY,'Authorization':'Bearer '+SUPABASE_TRENDING_KEY,'Content-Type':'application/json'}};
const globalTrending={{ready:false,loading:false,failed:false,updatedAt:null,counts:Object.create(null)}};"""
if old_constants not in s:
    raise SystemExit('Supabase patch: old global trending constants not found')
s = s.replace(old_constants, new_constants, 1)

increment_pattern = re.compile(r"async function incrementGlobal\(c\)\{.*?\n\}\nconst recordPlay=", re.S)
new_increment = """async function incrementGlobal(c){
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
const recordPlay="""
if not increment_pattern.search(s):
    raise SystemExit('Supabase patch: incrementGlobal function not found')
s = increment_pattern.sub(new_increment, s, count=1)

loader_pattern = re.compile(r"async function loadGlobalTrending\(\)\{.*?\n\}\nfunction start\(\)", re.S)
new_loader = """async function loadGlobalTrending(){
  if(globalTrending.loading)return;
  globalTrending.loading=true;updateTrendRailState();
  try{
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7000);
    const r=await fetch(SUPABASE_TRENDING_URL+'/rest/v1/rpc/get_trending_games',{method:'POST',headers:SUPABASE_TRENDING_HEADERS,body:JSON.stringify({p_limit:48}),cache:'no-store',signal:controller.signal});
    clearTimeout(timer);
    if(!r.ok)throw new Error('Supabase trending '+r.status);
    const rows=await r.json();
    const map=Object.create(null);
    (Array.isArray(rows)?rows:[]).forEach(x=>{const k=String(x?.game_key||'');const n=Number(x?.play_count||0);if(k&&Number.isFinite(n)&&n>0)map[k]=n});
    globalTrending.counts=map;
    globalTrending.updatedAt=new Date().toISOString();
    globalTrending.ready=true;
    globalTrending.failed=false;
  }catch(_){
    globalTrending.failed=true;
  }
  globalTrending.loading=false;updateTrendRailState();decorate();renderRails();applyView();
}
function start("""
if not loader_pattern.search(s):
    raise SystemExit('Supabase patch: loadGlobalTrending function not found')
s = loader_pattern.sub(new_loader, s, count=1)

for forbidden in ('api.counterapi.dev','ubg43-global-trending-v1','global-trending.json'):
    if forbidden in s:
        raise SystemExit('Supabase patch: old global trending dependency remains: '+forbidden)

p.write_text(s, encoding='utf-8')
print('Supabase global trending runtime applied.')
