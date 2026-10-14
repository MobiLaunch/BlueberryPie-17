/* PrismOS design review. Local, offline, simulated controls only. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const apps = [
    {id:'browser',name:'Browser',icon:'browser',color:'peach'},
    {id:'files',name:'Files',icon:'folder',color:'mint'},
    {id:'terminal',name:'Terminal',icon:'terminal',color:'lilac'},
    {id:'settings',name:'Settings',icon:'settings',color:'butter'},
    {id:'music',name:'Music',icon:'music',color:'rose'},
    {id:'calendar',name:'Calendar',icon:'calendar',color:'mint'},
    {id:'photos',name:'Photos',icon:'photo',color:'peach'},
    {id:'mail',name:'Mail',icon:'mail',color:'lilac'},
    {id:'style',name:'Wallpaper & style',icon:'spark',color:'rose'},
  ];
  const icon = name => window.PRISM_ICONS[name] || window.PRISM_ICONS.spark;
  const state = {palette:'Lilac',dark:false,reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,wifi:true,bluetooth:true,dnd:false,sound:true};
  try { const saved = JSON.parse(localStorage.getItem('prismos-preview') || '{}');
    for (const key of ['palette','dark','reduced']) if (typeof saved[key] === typeof state[key]) state[key] = saved[key];
  } catch { /* Storage is optional, including in restricted file previews. */ }
  if (!window.PRISM_TOKENS.palettes[state.palette]) state.palette = 'Lilac';
  let panel = 'shade';
  let restoreFocus = null;
  let launchToken = 0;
  let toastTimeout;
  let playing = false;
  const panels = ['shade','drawer','appearance'];

  function hydrate(root = document) {
    $$('[data-icon]',root).forEach(el => { el.innerHTML = icon(el.dataset.icon); });
  }
  function persist() {
    try { localStorage.setItem('prismos-preview',JSON.stringify({palette:state.palette,dark:state.dark,reduced:state.reduced})); } catch {}
  }
  function applyTheme() {
    const roles = window.PRISM_TOKENS.palettes[state.palette][state.dark ? 'dark' : 'light'];
    for (const [name,value] of Object.entries(roles)) if (typeof value === 'string') document.documentElement.style.setProperty('--'+name,value);
    document.documentElement.style.colorScheme = state.dark ? 'dark' : 'light';
    document.body.classList.toggle('dark',state.dark);
    document.body.classList.toggle('reduced-motion',state.reduced);
    document.body.classList.add('motion-override');
    $$('[data-palette]').forEach(el => { el.classList.toggle('selected',el.dataset.palette === state.palette); el.setAttribute('aria-pressed',String(el.dataset.palette === state.palette)); });
    for (const key of ['dark','reduced']) {
      $$('[data-setting="'+key+'"]').forEach(el => { el.classList.toggle('on',state[key]); el.setAttribute('aria-checked',String(state[key])); });
    }
    syncTiles(); persist();
  }
  function syncTiles() {
    $$('[data-toggle]').forEach(button => {
      const key = button.dataset.toggle, active = state[key];
      button.classList.toggle('active',active);
      button.setAttribute('aria-pressed',String(active));
      const text = key === 'wifi' ? (active ? 'Prism Network' : 'Off') : key === 'bluetooth' ? (active ? 'Connected' : 'Off') : key === 'sound' ? (active ? 'On' : 'Muted') : (active ? 'On' : 'Off');
      $('.tile-status',button).textContent = text;
    });
  }
  function toast(message) {
    $('#toast').textContent = message; $('#toast').hidden = false;
    clearTimeout(toastTimeout); toastTimeout = setTimeout(() => $('#toast').hidden = true,3800);
  }
  function closePanels(restore = true) {
    panels.forEach(id => { const el = $('#'+id); if (id === 'shade') {el.classList.remove('open');el.inert = true;el.setAttribute('aria-modal','false');el.setAttribute('aria-hidden','true');} else el.hidden = true; });
    $('#modal-backdrop').hidden = true; $('#shade-backdrop').hidden = true;
    document.body.classList.remove('shade-visible');
    $('[data-open="shade"]').setAttribute('aria-expanded','false');
    panel = null;
    if (restore && restoreFocus?.isConnected) restoreFocus.focus();
  }
  function openPanel(id) {
    if (!panels.includes(id)) return;
    if (panel === id && !$('#'+id).hidden && (id !== 'shade' || $('#shade').classList.contains('open'))) { closePanels(); return; }
    restoreFocus = document.activeElement;
    closePanels(false);
    panel = id;
    const el = $('#'+id);
    if (id === 'shade') {
      el.classList.add('open');el.inert = false;el.setAttribute('aria-modal','true');el.setAttribute('aria-hidden','false');
      $('#shade-backdrop').hidden = false;document.body.classList.add('shade-visible');
      $('[data-open="shade"]').setAttribute('aria-expanded','true');
      el.focus();
    } else {
      el.hidden = false; $('#modal-backdrop').hidden = false;
      if (id === 'drawer') { $('#app-search').value = ''; renderApps(''); $('#app-search').focus(); }
      else el.focus();
    }
  }
  function renderApps(query) {
    const filtered = apps.filter(app => app.name.toLowerCase().includes(query.trim().toLowerCase()));
    $('#app-grid').replaceChildren();
    filtered.forEach(app => {
      const button = document.createElement('button');
      button.className = 'app-choice';button.dataset.app = app.id;
      button.setAttribute('aria-label',app.name);
      button.innerHTML = '<span class="app-icon '+app.color+'">'+icon(app.icon)+'</span><span>'+app.name+'</span>';
      $('#app-grid').append(button);
    });
    $('#no-apps').hidden = filtered.length > 0;
  }
  function buildPalettes() {
    for (const [name,data] of Object.entries(window.PRISM_TOKENS.palettes)) {
      const dot = document.createElement('button');dot.className = 'palette-dot';dot.dataset.palette = name;
      dot.style.background = data.light.primary;dot.setAttribute('aria-label','Use '+name+' palette');
      $('.palette-dots').append(dot);
      const option = document.createElement('button');option.className = 'palette-option';option.dataset.palette = name;
      option.innerHTML = '<span class="palette-swatch"><i style="background:'+data.light.primary+'"></i><i style="background:'+data.light.tertiary+'"></i></span>'+name;
      $('.palette-options').append(option);
    }
  }
  function updateClock() {
    const now = new Date();
    const time = new Intl.DateTimeFormat('en-US',{hour:'2-digit',minute:'2-digit',hour12:false}).format(now);
    $('.status-clock').textContent = time;$('.shade-clock').textContent = time;$('.style-clock').textContent = time;
    $('.giant-clock').textContent = time;
    $('.date').textContent = new Intl.DateTimeFormat('en-US',{weekday:'long',month:'long',day:'numeric'}).format(now);
    $('.shade-date').textContent = new Intl.DateTimeFormat('en-US',{weekday:'short',month:'short',day:'numeric'}).format(now);
  }
  function syncSlider(input) {
    input.parentElement.style.setProperty('--value',input.value+'%');
    $('output',input.parentElement).textContent = input.value+'%';
    if (input.id === 'brightness') $('.wallpaper-art').style.opacity = .5 + Number(input.value)/200;
  }
  function clearNotifications() {
    $('#notifications').innerHTML = '<div class="caught-up">You’re all caught up.</div>';
    $('#clear-notifications').disabled = true;
  }
  function closeApp() {
    launchToken++;
    $('#launch-splash').hidden = true;
    const el = $('#app-window');
    if (el.hidden) return;
    if (state.reduced) {el.hidden = true;return;}
    el.classList.add('closing');
    setTimeout(() => {el.hidden = true;el.classList.remove('closing');if(restoreFocus?.isConnected)restoreFocus.focus();},160);
  }
  async function launchApp(id, source) {
    const app = apps.find(item => item.id === id);
    if (!app) return;
    const token = ++launchToken;
    const origin = source.getBoundingClientRect();
    restoreFocus = source;
    closePanels(false);
    $('#app-window').hidden = true;
    const splash = $('#launch-splash');
    splash.getAnimations().forEach(animation => animation.cancel());
    $('#splash-icon').innerHTML = icon(app.icon);
    const width = Math.min(850,innerWidth-44), height = Math.min(580,innerHeight-130);
    const target = {left:(innerWidth-width)/2,top:(innerHeight-height)/2,width,height};
    Object.assign(splash.style,{left:target.left+'px',top:target.top+'px',width:width+'px',height:height+'px'});
    if (!state.reduced) {
      splash.hidden = false;
      const animation = splash.animate([{left:origin.left+'px',top:origin.top+'px',width:origin.width+'px',height:origin.height+'px',borderRadius:'24px',opacity:1},{left:target.left+'px',top:target.top+'px',width:width+'px',height:height+'px',borderRadius:'32px',opacity:1}],{duration:320,easing:'cubic-bezier(.22,1.15,.34,1)'});
      try {await animation.finished;} catch {return;}
    }
    if (token !== launchToken) return;
    splash.hidden = true;
    if (id === 'settings' || id === 'style') {openPanel('appearance');return;}
    $('#window-title').textContent = app.name;$('#window-icon').innerHTML = icon(app.icon);
    $('#app-window').classList.remove('closing');
    buildApp(app);$('#app-window').hidden = false;$('#app-window').focus();
  }
  function buildApp(app) {
    const target = $('#app-content');
    if (app.id === 'files') {
      target.innerHTML = '<div class="files-app"><nav class="files-sidebar" aria-label="Folders">'+['Home','Documents','Downloads','Pictures'].map((name,i)=>'<button data-folder="'+name+'" class="'+(i===0?'selected':'')+'">'+icon('folder')+name+'</button>').join('')+'</nav><div class="files-main"><h2 id="folder-name">Home</h2><div class="file-grid"></div></div></div>';
      showFolder('Home');
    } else if (app.id === 'browser') {
      target.innerHTML = '<div class="browser-app"><div class="browser-address">prismos://welcome</div><div class="browser-home">'+icon('browser')+'<h2>A colorful start.</h2><p>This is a browser layout preview.</p><p>The native session launches your installed browser.</p><button class="pill-button" style="margin:25px auto 0" data-open="appearance">Find your color</button></div></div>';
    } else if (app.id === 'terminal') {
      target.innerHTML = '<div class="terminal-app"><div id="terminal-output"><b>PrismOS</b> 0.1 · design preview\nArch at heart. A little more you.\n\nType help for demo commands.\n</div><form id="terminal-form" class="terminal-line"><b>prism ~ ❯</b><input aria-label="Terminal command" autocomplete="off" spellcheck="false"></form></div>';
      $('#terminal-form').addEventListener('submit',event => {
        event.preventDefault();const input=$('input',event.currentTarget),command=input.value.trim();input.value='';
        const output=$('#terminal-output');
        if(command==='clear'){output.textContent='';return;}
        const line=document.createElement('div');line.textContent='prism ~ ❯ '+command;output.append(line);
        const result=document.createElement('div');
        result.textContent = command==='help'?'Demo commands: help, clear, uname, neofetch, echo <text>':command==='uname'?'Linux PrismOS (simulated preview)':command==='neofetch'?'✦ PrismOS\nDesktop: Material-inspired Quickshell\nBase: Arch Linux\nPalette: '+state.palette:command.startsWith('echo ')?command.slice(5):command?'Command unavailable in this design preview.':'';
        output.append(result);target.scrollTop=target.scrollHeight;
      });
    } else {
      target.innerHTML='<div class="generic-app">'+icon(app.icon)+'<h2>'+app.name+', with personality.</h2><p>This is an application design preview.<br>The native shell opens installed Linux applications.</p><button class="pill-button" style="margin:30px auto 0" data-open="appearance">Make it yours</button></div>';
    }
  }
  function showFolder(name) {
    const folders={Home:['Documents','Downloads','Pictures','Projects','Music','Videos'],Documents:['Getting started.md','Roadmap.md','Design notes.md'],Downloads:['PrismOS-source.zip','Wallpaper.svg'],Pictures:['Lilac skies','Mint morning','Peach sunset']};
    $('#folder-name').textContent=name;
    $$('[data-folder]').forEach(el=>el.classList.toggle('selected',el.dataset.folder===name));
    $('.file-grid').innerHTML=(folders[name]||[]).map(item=>'<button class="file-card" data-file="'+item+'"><span>'+icon(item.includes('.')?'mail':'folder')+'</span>'+item+'<small>Demo content</small></button>').join('');
  }
  document.addEventListener('click',event => {
    const open=event.target.closest('[data-open]'),close=event.target.closest('[data-close]'),toggle=event.target.closest('[data-toggle]'),setting=event.target.closest('[data-setting]'),palette=event.target.closest('[data-palette]'),app=event.target.closest('[data-app]'),folder=event.target.closest('[data-folder]'),file=event.target.closest('[data-file]');
    if(open){openPanel(open.dataset.open);return;}
    if(close){closePanels();return;}
    if(toggle){const key=toggle.dataset.toggle;state[key]=!state[key];applyTheme();if(key==='dnd')toast(state.dnd?'Notifications will be quiet.':'Notifications are back on.');return;}
    if(setting){const key=setting.dataset.setting;state[key]=!state[key];applyTheme();return;}
    if(palette){state.palette=palette.dataset.palette;applyTheme();return;}
    if(app){launchApp(app.dataset.app,app);return;}
    if(folder){showFolder(folder.dataset.folder);return;}
    if(file){toast(file.dataset.file+' · sample content');return;}
    if(event.target.closest('.dismiss-notification'))clearNotifications();
  });
  $('#app-search').addEventListener('input',event=>renderApps(event.target.value));
  $('#app-search').addEventListener('keydown',event=>{if(event.key==='Enter'){$('#app-grid button')?.click();}});
  $('#clear-notifications').addEventListener('click',clearNotifications);
  $('#modal-backdrop').addEventListener('click',()=>closePanels());
  $('#shade-backdrop').addEventListener('click',()=>closePanels());
  $('#close-app').addEventListener('click',closeApp);
  $('#power').addEventListener('click',()=>toast('Power actions are not available in this preview.'));
  $('#play-media').addEventListener('click',()=>{playing=!playing;$('.wave').classList.toggle('playing',playing);$('#play-media').textContent=playing?'Ⅱ':'▶';$('#play-media').setAttribute('aria-label',playing?'Pause demo track':'Play demo track');});
  $$('input[type="range"]').forEach(input=>{syncSlider(input);input.addEventListener('input',()=>syncSlider(input));});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'){if(panel)closePanels();else closeApp();return;}
    const typing = ['INPUT','TEXTAREA'].includes(document.activeElement.tagName);
    if(event.key==='/'&&!typing){event.preventDefault();openPanel('drawer');return;}
    if(event.key==='Tab'){
      const scope=panel?$('#'+panel):!$('#app-window').hidden?$('#app-window'):null;
      if(!scope)return;
      const focusable=$$('button:not(:disabled),input,a[href],[tabindex="0"]',scope).filter(el=>el.getClientRects().length);
      if(!focusable.length)return;
      const first=focusable[0],last=focusable.at(-1);
      if(event.shiftKey&&(document.activeElement===first||document.activeElement===scope)){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&(document.activeElement===last||document.activeElement===scope)){event.preventDefault();first.focus();}
    }
  });
  let gestureStart=null;
  $('.status-bar').addEventListener('pointerdown',event=>{if(event.pointerType==='touch'&&event.clientX>innerWidth*.6)gestureStart={x:event.clientX,y:event.clientY};});
  document.addEventListener('pointerup',event=>{if(gestureStart&&event.clientY-gestureStart.y>45){if(panel!=='shade')openPanel('shade');}gestureStart=null;});
  for(let i=0;i<23;i++){const bar=document.createElement('i');bar.style.height=(5+Math.sin(i*.9)*5+Math.cos(i*2)*3+6)+'px';bar.style.setProperty('--index',i);$('.wave').append(bar);}
  buildPalettes();hydrate();renderApps('');applyTheme();updateClock();setInterval(updateClock,15000);
  $('.wallpaper-art').style.backgroundImage='url("assets/wallpaper.svg")';
  $('#shade-backdrop').hidden=false;document.body.classList.add('shade-visible');$('#shade').focus();
  window.PRISM_PREVIEW={state,openPanel,closePanels,launchApp};
})();
