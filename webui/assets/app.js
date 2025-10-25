
let POW_DIFFICULTY = 0;
async function fetchPowCfg(){
  try{
    const r = await fetch('/api/security/status'); const j = await r.json();
    POW_DIFFICULTY = (j && j.config && j.config.pow_difficulty) ? j.config.pow_difficulty : 0;
  }catch{POW_DIFFICULTY=0;}
}
function hex(n){ return n.toString(16).padStart(2,'0'); }
async function powHeader(path){
  if(POW_DIFFICULTY<=0) return null;
  const secret = (new Date()).toISOString().slice(0,16); // minute-ish marker; not used on server, just to vary nonce
  let nonce = 0, target = '0'.repeat(POW_DIFFICULTY);
  while(true){
    const msg = new TextEncoder().encode(secret+'|'+path+'|'+nonce);
    const buf = await crypto.subtle.digest('SHA-256', msg);
    const h = Array.from(new Uint8Array(buf)).map(hex).join('');
    if(h.startsWith(target)) return String(nonce);
    nonce++;
    if(nonce % 5000 === 0) await new Promise(r=>setTimeout(r,0));
  }
}
window.addEventListener('load', fetchPowCfg);

/* INTUICYJNY JEDEN CHAT – auto-routing po intencji + STREAM + COPY */
const $ = (q)=>document.querySelector(q);
const msgs = $('#msgs');
const input = $('#input');

function token(){ return localStorage.getItem('AUTH_TOKEN') || ''; }
function tenantId(){ return localStorage.getItem('TENANT_ID') || 'default'; }
function autoToolsOn(){ return (localStorage.getItem('AUTO_TOOLS')||'1') !== '0'; }
function setToken(v){ localStorage.setItem('AUTH_TOKEN', v); }
$('#authToken').value = token();

$('#autoToolsToggle').checked = autoToolsOn();
$('#autoToolsToggle').addEventListener('change', ()=>{ localStorage.setItem('AUTO_TOOLS', $('#autoToolsToggle').checked ? '1' : '0'); });
$('#tenantIdInput').value = tenantId();
$('#tenantIdInput').addEventListener('change', ()=>{ localStorage.setItem('TENANT_ID', $('#tenantIdInput').value.trim()||'default'); });
$('#saveToken').addEventListener('click', ()=>{
  setToken($('#authToken').value.trim());
  addSys('Token zapisany.');
});

// Autoresize
input.addEventListener('input', ()=>{
  input.style.height='auto';
  input.style.height = Math.min(input.scrollHeight, 220)+'px';
});

// Drag & drop
const drop = $('#drop');
document.addEventListener('dragover', e=>{ e.preventDefault(); drop.classList.remove('hidden'); });
document.addEventListener('dragleave', e=>{ if(e.target===drop) drop.classList.add('hidden'); });
document.addEventListener('drop', e=>{
  e.preventDefault();
  drop.classList.add('hidden');
  const f = e.dataTransfer.files?.[0];
  if(f) uploadFile(f);
});

$('#btnUpload').addEventListener('click', ()=>$('#fileInput').click());
$('#fileInput').addEventListener('change', e=>{
  const f = e.target.files?.[0];
  if(f) uploadFile(f);
});

// Mic (STT)
let mediaRec=null, chunks=[];
$('#btnMic').addEventListener('click', async ()=>{
  try{
    if(!mediaRec){
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      mediaRec = new MediaRecorder(stream);
      chunks = [];
      mediaRec.ondataavailable = e=>chunks.push(e.data);
      mediaRec.onstop = async ()=>{
        const blob = new Blob(chunks, {type: 'audio/webm'});
        await sttFile(blob, 'audio.webm');
      };
      mediaRec.start();
      addSys('🎙️ Nagrywanie... kliknij ponownie, aby zakończyć.');
    }else{
      mediaRec.stop(); mediaRec=null;
    }
  }catch(e){ addSys('Błąd mikrofonu: '+e); }
});

// Rendering
function addBubble(role){
  const el = document.createElement('div');
  el.className = 'msg '+role;
  const b = document.createElement('div');
  b.className = 'bubble';
  el.appendChild(b);
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
  return b;
}
function addUser(t){
  const b = addBubble('user');
  b.textContent = t;
}
function addSys(t){
  const b = addBubble('asst');
  b.textContent = t;
}
function renderMarkdownish(text){
  // very small parser for ``` fences
  const container = document.createElement('div');
  const parts = text.split(/```/);
  for (let i=0;i<parts.length;i++){
    const seg = parts[i];
    if(i % 2 === 1){ // code block
      const codeblock = document.createElement('div');
      codeblock.className = 'codeblock';
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Kopiuj';
      btn.addEventListener('click', ()=>navigator.clipboard.writeText(seg.trim()));
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = seg.replace(/^\w+\n/,''); // strip language hint if present
      pre.appendChild(code);
      codeblock.appendChild(btn);
      codeblock.appendChild(pre);
      container.appendChild(codeblock);
    } else {
      const p = document.createElement('div');
      p.textContent = seg;
      container.appendChild(p);
    }
  }
  return container;
}
function addBanner(bubble, html){ const d=document.createElement('div'); d.className='banner'; d.innerHTML=html; bubble.parentElement.insertBefore(d, bubble); }
function renderAttachments(items){
  const wrap = document.createElement('div'); wrap.className='attach-grid';
  (items||[]).forEach(async it=>{
    const box = document.createElement('div'); box.className='attach';
    const title = document.createElement('div'); title.className='meta'; title.textContent = it.name + ' • ' + (it.mime||'') + ' • ' + (Math.round((it.size||0)/1024))+' KB';
    const dl = document.createElement('a'); dl.className='dl'; dl.href = it.url; dl.download = it.name; dl.textContent = 'Pobierz';
    if((it.kind||'').startsWith('image')){
      const img = document.createElement('img'); img.src = it.thumb_url || it.url; img.alt = it.name;
      box.appendChild(img);
    } else if((it.kind||'').startsWith('video')){
      const vid = document.createElement('video'); vid.src = it.url; vid.controls = true; vid.preload='metadata';
      vid.onloadeddata = ()=>{ try{ const c=document.createElement('canvas'); c.width=240; c.height=Math.floor(240*(vid.videoHeight/vid.videoWidth)); const ctx=c.getContext('2d'); ctx.drawImage(vid,0,0,c.width,c.height); }catch{} };
      box.appendChild(vid);
    } else if((it.kind||'').startsWith('audio')){
      const au = document.createElement('audio'); au.src = it.url; au.controls = true;
      box.appendChild(au);
    } else {
      const icon = document.createElement('div'); icon.className='meta'; icon.textContent='📎 plik';
      box.appendChild(icon);
    }
    box.appendChild(title); box.appendChild(dl);
    // auto-describe images
    if((it.kind||'').startsWith('image') && it.url){ const d = await describeImage(it.url); if(d && d.text){ const desc = document.createElement('div'); desc.className='meta'; desc.textContent = 'Opis AI: '+d.text; box.appendChild(desc);} try{ const headers={'Content-Type':'application/json'}; if(token()) headers['Authorization']='Bearer '+token(); headers['X-Tenant-ID']=tenantId(); headers['X-Form-Start']=String(FORM_START_TS); headers['X-Honeypot']=HONEYPOT; const rr = await fetch('/api/vision/ocr',{method:'POST',headers,body: JSON.stringify({image_url: it.url})}); if(rr.ok){ const jj = await rr.json(); if(jj && jj.text){ const o = document.createElement('div'); o.className='meta'; o.textContent = 'OCR: '+jj.text; box.appendChild(o); } } }catch(e){} }
    wrap.appendChild(box);
  });
  return wrap;
}
function finalizeBubble(bubble, text, rawObj){
  const rendered = renderMarkdownish(text);
  bubble.innerHTML = '';
  bubble.appendChild(rendered);
  bubble.appendChild(bubbleToolbar(text));
  try{ renderSources(bubble, rawObj||{}); }catch{}
  smoothScrollToBottom();
}

// API
async function api(path, {method='POST', json=null, form=null}={}){
  const headers = {};
  if(token()) headers['Authorization'] = 'Bearer '+token();
  headers['X-Tenant-ID'] = tenantId();
  headers['X-Form-Start'] = String(FORM_START_TS);
  headers['X-Honeypot'] = HONEYPOT;
  headers['X-Auto-Tools'] = autoToolsOn() ? '1' : '0';
  if(form){ /* form data */ }
  else headers['Content-Type']='application/json';
  const res = await fetch(path, {method, headers, body: form?form:(json?JSON.stringify(json):undefined)});
  const ct = res.headers.get('content-type')||'';
  const data = ct.includes('application/json')? await res.json() : await res.text();
  return { status:res.status, data, headers:res.headers };
}

// SSE/stream for chat
async function streamChat(path, body, onToken, onDone, onMeta){ onMeta = onMeta || function(){};
  const headers = {'Content-Type':'application/json'};
  if(token()) headers['Authorization'] = 'Bearer '+token();
  const pow = await powHeader(path); if(pow) headers['X-PoW']=pow; const res = await fetch(path, {method:'POST', headers, body: JSON.stringify(body)});
  const ct = res.headers.get('content-type')||'';
  onMeta({headers:res.headers});
  if(!res.body || !ct.includes('text/event-stream')){
    // fallback: non-streaming
    let data;
    try{ data = ct.includes('application/json') ? await res.json() : await res.text(); }
    catch(e){ data = await res.text(); }
    onToken(typeof data==='string'? data : JSON.stringify(data,null,2), true);
    onDone();
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while(true){
    const {value, done} = await reader.read();
    if(done) break;
    buffer += decoder.decode(value, {stream:true});
    const chunks = buffer.split('\n\n');
    buffer = chunks.pop();
    for(const chunk of chunks){
      const lines = chunk.split('\n');
      for(const line of lines){
        if(line.startsWith('data:')){
          const data = line.slice(5).trim();
          if(data === '[DONE]') { onDone(); return; }
          onToken(data, false);
        }
      }
    }
  }
  // flush tail
  if(buffer.trim()){
    buffer.split('\n').forEach(line=>{
      if(line.startsWith('data:')) onToken(line.slice(5).trim(), false);
    });
  }
  onDone();
}

// Router
function parseCmd(text){
  const t = text.trim();
  if(/^\/(r|research)\b/i.test(t)) return {kind:'research', args:t.replace(/^\/(r|research)\b/i,'').trim()||t};
  if(/^\/psy\b/i.test(t)) return {kind:'psy', args:t.replace(/^\/psy\b/i,'').trim()};
  if(/^\/code\b/i.test(t)) return {kind:'code', args:t.replace(/^\/code\b/i,'').trim()};
  if(/^\/admin\s+clear\b/i.test(t)) return {kind:'admin_clear'};
  if(/^\/metrics\b/i.test(t)) return {kind:'open', url:'/metrics'};
  if(/^\/docs\b/i.test(t)) return {kind:'open', url:'/docs'};
  return {kind:'chat', args:t};
}

$('#btnSend').addEventListener('click', send);
input.addEventListener('keydown', e=>{
  if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }
});

async function send(){
  const text = input.value.trim();
  if(!text) return;
  addUser(text);
  input.value=''; input.dispatchEvent(new Event('input'));

  const cmd = parseCmd(text);
  let bubble = addBubble('asst');
  bubble.classList.add('streaming');
  let buffer = '';

  let lastStatus = 200; let lastRaw = null;
function onToken(tok, isFinal){
    // Heuristic: if JSON payloads, try to unwrap {text: "..."} etc.
    try{
      const obj = JSON.parse(tok);
      if(typeof obj === 'string'){ buffer += obj; }
      else if (obj && typeof obj.text === 'string') { buffer += obj.text; }
      else if (obj && typeof obj.delta === 'string') { buffer += obj.delta; }
      else { buffer += tok; }
    }catch{ buffer += tok; }
    bubble.textContent = buffer;
    msgs.scrollTop = msgs.scrollHeight;
    if(isFinal){ bubble.classList.remove('streaming'); finalizeBubble(bubble, buffer); }
  }
  function onDone(){ bubble.classList.remove('streaming'); finalizeBubble(bubble, buffer, lastRaw); }

  try{
    if(cmd.kind==='open'){
      window.open(cmd.url, '_blank'); onToken('Otworzono: '+cmd.url, true); return;
    }
    if(cmd.kind==='research'){
      const r = await api('/api/research', { json: { query: cmd.args, mode:'fast' } });
      lastStatus = r.status; lastRaw = r.data;
      if(r.status>=400){ renderError(bubble, r.data, r.status); return; }
      onToken(typeof r.data==='string'? r.data : JSON.stringify(r.data,null,2), true);
    }else if(cmd.kind==='psy'){
      const r = await api('/api/psyche', { json: { message: cmd.args, user_id:'default' } });
      lastStatus = r.status; lastRaw = r.data;
      if(r.status>=400){ renderError(bubble, r.data, r.status); return; }
      onToken(typeof r.data==='string'? r.data : JSON.stringify(r.data,null,2), true);
    }else if(cmd.kind==='code'){
      const r = await api('/api/programista', { json: { code: cmd.args || 'print(42)', tool:'ruff' } });
      lastStatus = r.status; lastRaw = r.data;
      if(r.status>=400){ renderError(bubble, r.data, r.status); return; }
      onToken(typeof r.data==='string'? r.data : JSON.stringify(r.data,null,2), true);
    }else if(cmd.kind==='admin_clear'){
      const r = await api('/api/admin/cache/clear', { json: { cache_type:'all' } });
      lastStatus = r.status; lastRaw = r.data;
      if(r.status>=400){ renderError(bubble, r.data, r.status); return; }
      onToken(typeof r.data==='string'? r.data : JSON.stringify(r.data,null,2), true);
    }else{
      // chat – stream if server supports SSE, fallback to non-stream
      await streamChat('/api/chat/assistant/stream', { messages:[{role:'user', content: cmd.args}] }, onToken, onDone, (meta)=>{ try{ if(meta.headers.get('X-Used-Tool')==='research'){ addBanner(bubble, 'Użyto <b>research</b> 🔎 (auto)'); } }catch{} });
    }
  }catch(e){
    onToken('Błąd: '+e, true);
  }
}

async function uploadFile(file){
  addUser(`📎 ${file.name}`);
  const fd = new FormData();
  fd.append('file', file);
  try{
    const r = await api('/api/files/upload', { form: fd });
    const text = typeof r.data==='string'? r.data : JSON.stringify(r.data,null,2);
    const bubble = addBubble('asst'); finalizeBubble(bubble, text, r.data);
  }catch(e){
    const bubble = addBubble('asst'); finalizeBubble(bubble, 'Upload error: '+e);
  }
}

async function sttFile(blob, name){
  addUser('🎤 nagranie');
  const fd = new FormData();
  fd.append('file', blob, name);
  try{
    const r = await api('/api/stt/transcribe', { form: fd });
    const text = typeof r.data==='string' ? r.data : (r.data.text || JSON.stringify(r.data,null,2));
    const bubble = addBubble('asst'); finalizeBubble(bubble, text, r.data);
  }catch(e){
    const bubble = addBubble('asst'); finalizeBubble(bubble, 'STT error: '+e);
  }
}

function smoothScrollToBottom(){ msgs.classList.add('smooth'); msgs.scrollTop = msgs.scrollHeight; setTimeout(()=>msgs.classList.remove('smooth'), 200); }
function bubbleToolbar(text){
  const bar = document.createElement('div');
  bar.className = 'toolbar';
  const btn = document.createElement('button');
  btn.textContent = 'Kopiuj całość';
  btn.addEventListener('click', ()=>navigator.clipboard.writeText(text));
  bar.appendChild(btn);
  return bar;
}
function renderSources(bubble, data){
  const list = data?.sources || data?.citations || data?.refs;
  if(!list || !Array.isArray(list) || list.length===0) return;
  const box = document.createElement('div');
  box.className = 'sources';
  const h = document.createElement('h4'); h.textContent = 'Źródła'; box.appendChild(h);
  list.slice(0,8).forEach((s,i)=>{
    const a = document.createElement('a');
    a.target = '_blank';
    try{
      if(typeof s === 'string'){ a.href = s; a.textContent = `#${i+1}`; }
      else if (s.url){ a.href = s.url; a.textContent = s.title || s.url; }
      else { a.textContent = s.title || `#${i+1}`; a.href = s.href || '#'; }
    }catch{ a.textContent = `#${i+1}`; a.href = '#'; }
    box.appendChild(a);
  });
  bubble.appendChild(box);
}
function renderError(bubble, payload, status){
  bubble.classList.add('err');
  const title = document.createElement('div');
  title.className = 'title';
  const code = (payload && (payload.code || payload.error || payload.detail)) || 'Błąd';
  title.textContent = `Błąd ${status || ''} – ${typeof code==='string'?code:JSON.stringify(code)}`;
  const pre = document.createElement('pre');
  pre.textContent = typeof payload==='string'? payload : JSON.stringify(payload, null, 2);
  bubble.innerHTML = '';
  bubble.appendChild(title);
  bubble.appendChild(pre);
}
// Prefill token if exists
async function uploadFiles(files){
  const fd = new FormData();
  [...files].forEach(f=>fd.append('files', f, f.name));
  const headers = {}; if(token()) headers['Authorization'] = 'Bearer '+token(); headers['X-Auto-Tools'] = autoToolsOn() ? '1':'0'; headers['X-Tenant-ID'] = tenantId();
  const res = await fetch('/api/files/upload', { method:'POST', headers, body: fd });
  const ct = res.headers.get('content-type')||'';
  if(!res.ok) throw new Error('upload_failed');
  if(ct.includes('application/json')) return await res.json();
  return {text:'Wgrano', items: []};
}


// Drag & drop upload
const dropzoneHint = $('#dropzoneHint');
document.addEventListener('dragover', (e)=>{ e.preventDefault(); dropzoneHint.style.display='block'; });
document.addEventListener('dragleave', (e)=>{ dropzoneHint.style.display='none'; });
document.addEventListener('drop', async (e)=>{
  e.preventDefault(); dropzoneHint.style.display='none';
  const files = e.dataTransfer.files; if(!files || !files.length) return;
  const res = await uploadFiles(files);
  // render user bubble with attachments
  const bubble = addMessage('user',''); 
  if(res.items && res.items.length){ bubble.appendChild(renderAttachments(res.items)); }
  // keep a hint text for caption
  addMessage('user', 'Proszę opisz powyższy załącznik.');
});

// PWA Service Worker register (scope /webui/)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', ()=>{
    try{ navigator.serviceWorker.register('/webui/sw.js', {scope:'/webui/'}); }catch(e){}
  });
}
// iOS: block pinch/double-tap zoom (per request)
let lastTouchEnd = 0;
document.addEventListener('gesturestart', function (e) { e.preventDefault(); }, {passive:false});
document.addEventListener('touchend', function (e) {
  const now = (new Date()).getTime();
  if (now - lastTouchEnd <= 300) { e.preventDefault(); }
  lastTouchEnd = now;
}, {passive:false});

let mediaRecorder, micChunks=[];
async function startMic(){
  if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){ alert('Brak dostępu do mikrofonu'); return; }
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  mediaRecorder = new MediaRecorder(stream);
  micChunks = [];
  mediaRecorder.ondataavailable = e => { if(e.data.size>0) micChunks.push(e.data); };
  mediaRecorder.onstop = async ()=>{
    const blob = new Blob(micChunks, {type:'audio/webm'});
    const fd = new FormData();
    fd.append('file', blob, 'rec.webm');
    const headers = {}; if(token()) headers['Authorization'] = 'Bearer '+token(); headers['X-Tenant-ID']=tenantId();
    const r = await fetch('/api/stt/transcribe', {method:'POST', headers, body: fd});
    if(!r.ok){ console.error('STT fail'); return; }
    const js = await r.json();
    const t = js && js.text ? js.text : '';
    if(t){ $('#msg').value = t; $('#msg').focus(); }
  };
  mediaRecorder.start();
  $('#micBtn').textContent='⏹️';
}
function stopMic(){
  if(mediaRecorder && mediaRecorder.state!=='inactive'){ mediaRecorder.stop(); $('#micBtn').textContent='🎙️'; }
}
$('#micBtn').addEventListener('click', ()=>{ if(!mediaRecorder || mediaRecorder.state==='inactive'){ startMic(); } else { stopMic(); } });

async function describeImage(url){
  try{
    const headers = {'Content-Type':'application/json'}; if(token()) headers['Authorization']='Bearer '+token(); headers['X-Tenant-ID']=tenantId(); headers['X-Form-Start']=String(FORM_START_TS); headers['X-Honeypot']=HONEYPOT;
    const r = await fetch('/api/vision/describe', {method:'POST', headers, body: JSON.stringify({image_url:url})});
    if(!r.ok) return null;
    return await r.json();
  }catch(e){ return null; }
}

async function handleSlashImage(text){
  const m = text.match(/^\s*\/image\s+(.+)$/i);
  if(!m) return false;
  const prompt = m[1].trim();
  const headers = {'Content-Type':'application/json'}; if(token()) headers['Authorization']='Bearer '+token(); headers['X-Tenant-ID']=tenantId(); headers['X-Form-Start']=String(FORM_START_TS); headers['X-Honeypot']=HONEYPOT;
  const r = await fetch('/api/image/generate', {method:'POST', headers, body: JSON.stringify({prompt})});
  if(!r.ok){ addMessage('assistant','[Błąd generowania obrazu]'); return true; }
  const jsn = await r.json();
  const bubble = addMessage('assistant','Wygenerowano obraz.');
  if(jsn.items && jsn.items.length){ bubble.appendChild(renderAttachments(jsn.items)); }
  return true;
}

const memBox = document.createElement('div'); memBox.className='mem-hints'; memBox.style.cssText='max-height:120px; overflow:auto; margin:4px 0; font-size:12px; color:#aab; display:none;';
document.querySelector('.input').prepend(memBox);

async function showMemoryHints(q){
  try{
    const headers = {'Content-Type':'application/json'}; if(token()) headers['Authorization']='Bearer '+token(); headers['X-Tenant-ID']=tenantId(); headers['X-Form-Start']=String(FORM_START_TS); headers['X-Honeypot']=HONEYPOT;
    const r = await fetch('/api/memory/search', {method:'POST', headers, body: JSON.stringify({q, topk:5})});
    if(!r.ok){ memBox.style.display='none'; return; }
    const js = await r.json();
    if(!js.items || !js.items.length){ memBox.style.display='none'; return; }
    memBox.innerHTML = '<div style="margin-bottom:4px;color:#9ab">Pamięć (pasujące fakty):</div>' + js.items.map(it=>'<div style="padding:2px 0">• '+(it.text||'')+'</div>').join('');
    memBox.style.display='block';
  }catch{ memBox.style.display='none'; }
}
$('#msg').addEventListener('input', (e)=>{
  const t = e.target.value.trim();
  if(t.length>=8){ showMemoryHints(t); } else { memBox.style.display='none'; }
});
