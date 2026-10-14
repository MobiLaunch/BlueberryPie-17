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
  const state = {palette:'Lilac',dark:false,reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,wifi:true,bluetooth:true,dnd:false,sound:true,microphone:true,favorites:['browser','files','terminal','music']};
  try { const saved = JSON.parse(localStorage.getItem('prismos-preview') || '{}');
    for (const key of ['palette','dark','reduced']) if (typeof saved[key] === typeof state[key]) state[key] = saved[key];
    if(Array.isArray(saved.favorites))state.favorites=[...new Set(saved.favorites)].filter(id=>apps.some(app=>app.id===id)).slice(0,8);
  } catch { /* Storage is optional, including in restricted file previews. */ }
  if (!window.PRISM_TOKENS.palettes[state.palette]) state.palette = 'Lilac';
  let panel = 'shade';
  let restoreFocus = null;
  let launchToken = 0;
  let toastTimeout;
  let playing = false;
  const panels = ['shade','drawer','appearance','power-panel','connections','sound-panel'];
  let contextApp=null,contextSource=null,powerChoice=null,holdTimer=null,heldSource=null;
  let connectionKind='wifi',selectedNetwork=null,connectionToken=0,connectionBusy=false;
  const networks=[{id:'prism',name:'Prism Network',signal:96,secured:true,connected:true,saved:true},
    {id:'blueberry',name:'Blueberry Studio',signal:82,secured:true,connected:false,saved:false},
    {id:'cafe',name:'Cafe: Open',signal:54,secured:false,connected:false,saved:false}];
  const devices=[{id:'buds',name:'Blue buds',paired:true,connected:true},{id:'keyboard',name:'Studio keyboard',paired:true,connected:false},{id:'speaker',name:'New speaker',paired:false,connected:false}];
  const soundDevices={outputs:[{id:'speakers',label:'Built-in speakers',value:64,muted:false},{id:'buds',label:'Blue buds',value:45,muted:false},{id:'hdmi',label:'HDMI display',value:80,muted:false}],
    inputs:[{id:'internal',label:'Internal microphone',value:48,muted:false},{id:'usb',label:'USB microphone',value:62,muted:false}]};
  let selectedOutput='speakers',selectedInput='internal';
  let soundTab='output';
  const currentOutput=()=>soundDevices.outputs.find(d=>d.id===selectedOutput);
  const currentInput=()=>soundDevices.inputs.find(d=>d.id===selectedInput);

  function hydrate(root = document) {
    $$('[data-icon]',root).forEach(el => { el.innerHTML = icon(el.dataset.icon); });
  }
  function persist() {
    try { localStorage.setItem('prismos-preview',JSON.stringify({palette:state.palette,dark:state.dark,reduced:state.reduced,favorites:state.favorites})); } catch {}
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
      const tile=button.closest('.quick-tile');
      tile.classList.toggle('active',active);
      button.setAttribute('aria-pressed',String(active));
      const text = key === 'wifi' ? (active ? networks.find(n=>n.connected)?.name || 'Not connected' : 'Off') : key === 'bluetooth' ? (active ? devices.some(d=>d.connected)?'Connected':'On' : 'Off') : key === 'sound' ? (active ? 'On' : 'Muted') : (active ? 'On' : 'Off');
      $('.tile-status',tile).textContent = text;
    });
  }
  function toast(message) {
    $('#toast').textContent = message; $('#toast').hidden = false;
    clearTimeout(toastTimeout); toastTimeout = setTimeout(() => $('#toast').hidden = true,3800);
  }
  function closePanels(restore = true) {
    connectionToken++;connectionBusy=false;selectedNetwork=null;
    $('#connection-list').replaceChildren();
    $('#app-context').hidden=true;
    panels.forEach(id => { const el = $('#'+id); if (id === 'shade') {el.classList.remove('open');el.inert = true;el.setAttribute('aria-modal','false');el.setAttribute('aria-hidden','true');} else el.hidden = true; });
    $('#modal-backdrop').hidden = true; $('#shade-backdrop').hidden = true;
    document.body.classList.remove('shade-visible');
    $('[data-open="shade"]').setAttribute('aria-expanded','false');
    panel = null;
    if (restore && restoreFocus?.isConnected) restoreFocus.focus();
  }
  function openConnections(kind){
    connectionKind=kind;openPanel('connections');renderConnections();
  }
  function renderConnections(){
    $('#connection-title').textContent=connectionKind==='wifi'?'Wi-Fi':'Bluetooth';
    $('#connection-radio').textContent=state[connectionKind]?'Turn off':'Turn on';
    $('#connection-radio').disabled=connectionBusy;$('#scan-connections').disabled=connectionBusy||!state[connectionKind];
    $('#connection-status').textContent=connectionBusy?'Just a moment…':state[connectionKind]?'Choose what you want to connect.':'Turn on '+(connectionKind==='wifi'?'Wi-Fi':'Bluetooth')+' to find connections.';
    const list=$('#connection-list');list.replaceChildren();if(!state[connectionKind])return;
    const items=connectionKind==='wifi'?networks:devices;
    items.forEach(item=>{
      const row=document.createElement('article');row.className='connection-row';row.dataset.connection=item.id;
      const choice=document.createElement('button');choice.className='connection-choice'+(item.connected||selectedNetwork===item.id?' selected':'');
      choice.disabled=connectionBusy;choice.innerHTML=icon(connectionKind==='wifi'?'wifi':'bluetooth');
      const label=document.createElement('span'),name=document.createElement('b'),status=document.createElement('small');
      name.textContent=item.name;status.textContent=connectionKind==='wifi'?item.signal+'% · '+(item.connected?'Connected':item.saved?'Saved':item.secured?'WPA2':'Open network'):(item.connected?'Connected':item.paired?'Paired':'Ready to pair');
      label.append(name,status);choice.append(label);row.append(choice);list.append(row);
      if(connectionKind==='bluetooth'){
        choice.setAttribute('aria-label',(item.connected?'Disconnect ':item.paired?'Connect ':'Pair ')+item.name);
        choice.addEventListener('click',()=>{if(!item.paired){toast('Pairing codes are handled by Bluetooth settings in the native session.');return;}simulateConnection(()=>item.connected=!item.connected);});return;
      }
      choice.setAttribute('aria-label','Select '+item.name);
      choice.addEventListener('click',()=>{selectedNetwork=selectedNetwork===item.id?null:item.id;renderConnections();const input=$('[data-connection="'+item.id+'"] input');input?.focus();});
      if(selectedNetwork!==item.id)return;
      const form=document.createElement('form'),error=document.createElement('p');error.className='connection-error';error.setAttribute('role','alert');
      if(item.secured&&!item.connected){const field=document.createElement('label');field.textContent='Password for '+item.name;const input=document.createElement('input');input.type='password';input.maxLength=64;input.autocomplete='off';input.setAttribute('aria-label','Password for '+item.name);input.placeholder=item.saved?'Leave empty to use saved password':'Network password';field.append(input);form.append(field);}
      const submit=document.createElement('button');submit.className='pill-button';submit.type='submit';submit.textContent=item.connected?'Disconnect':'Connect';submit.disabled=connectionBusy;
      form.append(error,submit);row.append(form);
      form.addEventListener('submit',event=>{event.preventDefault();if(connectionBusy)return;const input=$('input',form);const length=input?.value.length||0;
        if(item.secured&&!item.connected&&((!item.saved&&length<8)||(length>0&&length<8))){error.textContent='Use at least 8 characters.';input.focus();return;}
        form.reset();const disconnect=item.connected;
        simulateConnection(()=>{if(disconnect)item.connected=false;else{networks.forEach(n=>n.connected=false);item.connected=true;item.saved=true;}});
      });
    });
  }
  function simulateConnection(change){
    const token=++connectionToken;connectionBusy=true;renderConnections();
    setTimeout(()=>{if(token!==connectionToken)return;change();connectionBusy=false;selectedNetwork=null;renderConnections();syncTiles();$('#connection-status').textContent='Connection updated · preview';},state.reduced?0:450);
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
      if(id==='power-panel')resetPower();
      if(id==='sound-panel'){setSoundTab('output');renderSound();}
      if (id === 'drawer') { $('#app-search').value = ''; renderApps(''); $('#app-search').focus(); }
      else el.focus();
    }
  }
  function syncSound(){
    const output=currentOutput(),input=currentInput();
    state.sound=!output.muted;state.microphone=!input.muted;
    for(const [id,device] of [['volume',output],['output-level',output],['input-level',input]]){
      const slider=$('#'+id);slider.value=device.value;syncSlider(slider);
    }
    $('#selected-output').textContent=output.label+' · '+(output.muted?'Muted':output.value+'%');
    $('#selected-input').textContent=input.label+' · '+(input.muted?'Muted':input.value+'%');
    $('#mute-output').textContent=output.muted?'Unmute output':'Mute output';$('#mute-output').setAttribute('aria-pressed',String(output.muted));
    $('#mute-input').textContent=input.muted?'Unmute microphone':'Mute microphone';$('#mute-input').setAttribute('aria-pressed',String(input.muted));
    syncTiles();
  }
  function setSoundTab(tab){
    soundTab=tab;
    for(const kind of ['output','input']){
      const selected=kind===tab,button=$('#sound-'+kind+'-tab');button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;
      $('#sound-'+kind+'-section').hidden=!selected;
    }
  }
  function renderSound(){
    for(const kind of ['outputs','inputs']){
      const list=$('#sound-'+kind);list.replaceChildren();
      soundDevices[kind].forEach(device=>{
        const selected=kind==='outputs'?selectedOutput===device.id:selectedInput===device.id;
        const button=document.createElement('button');button.className='sound-choice'+(selected?' selected':'');button.setAttribute('aria-pressed',String(selected));
        button.setAttribute('aria-label',(kind==='outputs'?'Play through ':'Use microphone ')+device.label);
        const symbol=document.createElement('span');symbol.innerHTML=icon(kind==='outputs'?'headphones':'microphone');
        const label=document.createElement('span');label.textContent=device.label;
        const check=document.createElement('b');check.textContent=selected?'✓':'';check.setAttribute('aria-hidden','true');
        button.append(symbol,label,check);list.append(button);
        button.addEventListener('click',()=>{if(kind==='outputs')selectedOutput=device.id;else selectedInput=device.id;renderSound();$('#sound-status').textContent=device.label+' selected · preview';
          [...list.querySelectorAll('button')].find(el=>el.getAttribute('aria-pressed')==='true')?.focus();});
      });
    }
    syncSound();
  }
  function renderApps(query) {
    const filtered = apps.filter(app => app.name.toLowerCase().includes(query.trim().toLowerCase()));
    $('#app-grid').replaceChildren();
    filtered.forEach(app => {
      const button = document.createElement('button');
      button.className = 'app-choice';button.dataset.app = app.id;
      button.setAttribute('aria-label',app.name);
      button.innerHTML = '<span class="app-icon '+app.color+'">'+icon(app.icon)+'</span><span>'+app.name+'</span>'+(state.favorites.includes(app.id)?'<i class="pin-mark" aria-label="Pinned"></i>':'');
      $('#app-grid').append(button);
    });
    $('#no-apps').hidden = filtered.length > 0;
  }
  function renderDock(){
    const dock=$('.dock');
    dock.querySelectorAll('[data-app]').forEach(el=>el.remove());
    [...state.favorites,'settings'].filter((id,index,array)=>array.indexOf(id)===index).forEach(id=>{
      const app=apps.find(item=>item.id===id);if(!app)return;
      const button=document.createElement('button');button.className='dock-app';button.dataset.app=id;button.setAttribute('aria-label',app.name);
      button.innerHTML='<span class="app-icon '+app.color+'">'+icon(app.icon)+'</span><span class="dock-tip">'+app.name+'</span>';dock.append(button);
    });
  }
  function showContext(source,x,y){
    contextApp=apps.find(app=>app.id===source.dataset.app);contextSource=source;if(!contextApp)return;
    $('#context-pin').textContent=state.favorites.includes(contextApp.id)?'Unpin from dock':'Pin to dock';
    $('#app-context').hidden=false;$('#app-context').style.left=Math.max(10,Math.min(x,innerWidth-190))+'px';$('#app-context').style.top=Math.max(50,Math.min(y,innerHeight-110))+'px';$('#context-open').focus();
  }
  function resetPower(){powerChoice=null;$('#power-heading').textContent='Take a moment.';$('#power-description').textContent='Choose what happens next.';$('.power-choices').hidden=false;$('#confirm-power').hidden=true;}
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
      target.innerHTML = '<div class="terminal-app"><div id="terminal-output"><b>PrismOS</b> 0.4 · design preview\nArch at heart. A little more you.\n\nType help for demo commands.\n</div><form id="terminal-form" class="terminal-line"><b>prism ~ ❯</b><input aria-label="Terminal command" autocomplete="off" spellcheck="false"></form></div>';
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
    if(heldSource&&heldSource.contains(event.target)){event.preventDefault();heldSource=null;return;}
    if(event.target.closest('#context-pin')){
      const id=contextApp.id;
      if(state.favorites.includes(id))state.favorites=state.favorites.filter(item=>item!==id);
      else if(state.favorites.length>=8){toast('Unpin an app before adding another.');return;}
      else state.favorites.push(id);
      persist();renderDock();renderApps($('#app-search').value);$('#app-context').hidden=true;return;
    }
    if(event.target.closest('#context-open')){const app=contextApp,source=contextSource;$('#app-context').hidden=true;launchApp(app.id,source);return;}
    $('#app-context').hidden=true;
    const soundTabButton=event.target.closest('[data-sound-tab]');
    if(soundTabButton){setSoundTab(soundTabButton.dataset.soundTab);return;}
    const soundOpen=event.target.closest('[data-sound-open]');
    if(soundOpen){openPanel('sound-panel');setSoundTab(soundOpen.dataset.soundOpen);return;}
    const connections=event.target.closest('[data-connections]');
    if(connections){openConnections(connections.dataset.connections);return;}
    const power=event.target.closest('[data-power-choice]');
    if(power){powerChoice=power.dataset.powerChoice;$('#power-heading').textContent=powerChoice+' your session?';$('#power-description').textContent=['Restart','Power off','Sign out'].includes(powerChoice)?'Save your work before continuing.':'Ready when you are.';$('.power-choices').hidden=true;$('#confirm-power').textContent='Confirm '+powerChoice;$('#confirm-power').hidden=false;$('#confirm-power').focus();return;}
    const open=event.target.closest('[data-open]'),close=event.target.closest('[data-close]'),toggle=event.target.closest('[data-toggle]'),setting=event.target.closest('[data-setting]'),palette=event.target.closest('[data-palette]'),app=event.target.closest('[data-app]'),folder=event.target.closest('[data-folder]'),file=event.target.closest('[data-file]');
    if(open){openPanel(open.dataset.open);return;}
    if(close){closePanels();return;}
    if(toggle){const key=toggle.dataset.toggle;state[key]=!state[key];if(key==='sound')currentOutput().muted=!state.sound;if(key==='microphone')currentInput().muted=!state.microphone;syncSound();applyTheme();if(key==='dnd')toast(state.dnd?'Notifications will be quiet.':'Notifications are back on.');return;}
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
  $('#power').addEventListener('click',()=>openPanel('power-panel'));
  $('#confirm-power').addEventListener('click',()=>{const choice=powerChoice;closePanels();toast(choice+' is simulated in this design preview.');});
  $('#cancel-power').addEventListener('click',()=>{if(powerChoice)resetPower();else closePanels();});
  $('#connection-radio').addEventListener('click',()=>{state[connectionKind]=!state[connectionKind];if(!state[connectionKind]){(connectionKind==='wifi'?networks:devices).forEach(item=>item.connected=false);}selectedNetwork=null;syncTiles();renderConnections();});
  $('#scan-connections').addEventListener('click',()=>simulateConnection(()=>{}));
  $('#mute-output').addEventListener('click',()=>{currentOutput().muted=!currentOutput().muted;syncSound();});
  $('#mute-input').addEventListener('click',()=>{currentInput().muted=!currentInput().muted;syncSound();});
  $('.sound-tabs').addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();setSoundTab(event.key==='Home'?'output':event.key==='End'?'input':soundTab==='output'?'input':'output');$('#sound-'+soundTab+'-tab').focus();}});
  $('#play-media').addEventListener('click',()=>{playing=!playing;$('.wave').classList.toggle('playing',playing);$('#play-media').textContent=playing?'Ⅱ':'▶';$('#play-media').setAttribute('aria-label',playing?'Pause demo track':'Play demo track');});
  $$('input[type="range"]').forEach(input=>{syncSlider(input);input.addEventListener('input',()=>{syncSlider(input);
    if(input.id==='volume'||input.id==='output-level'){currentOutput().value=Number(input.value);syncSound();}
    if(input.id==='input-level'){currentInput().value=Number(input.value);syncSound();}
  });});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&!$('#app-context').hidden){$('#app-context').hidden=true;contextSource?.focus();return;}
    if(event.key==='ContextMenu'||(event.shiftKey&&event.key==='F10')){const source=document.activeElement.closest('[data-app]');if(source){event.preventDefault();const box=source.getBoundingClientRect();showContext(source,box.left,box.bottom);}return;}
    if(event.key==='Escape'){if(panel)closePanels();else closeApp();return;}
    const typing = ['INPUT','TEXTAREA'].includes(document.activeElement.tagName);
    if(event.key==='/'&&!typing){event.preventDefault();openPanel('drawer');return;}
    if(event.key==='Tab'){
      const scope=!$('#app-context').hidden?$('#app-context'):panel?$('#'+panel):!$('#app-window').hidden?$('#app-window'):null;
      if(!scope)return;
      const focusable=$$('button:not(:disabled),input,a[href],[tabindex="0"]',scope).filter(el=>el.getClientRects().length);
      if(!focusable.length)return;
      const first=focusable[0],last=focusable.at(-1);
      if(event.shiftKey&&(document.activeElement===first||document.activeElement===scope)){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&(document.activeElement===last||document.activeElement===scope)){event.preventDefault();first.focus();}
    }
  });
  document.addEventListener('contextmenu',event=>{const source=event.target.closest('[data-app]');if(source){event.preventDefault();showContext(source,event.clientX,event.clientY);}});
  document.addEventListener('pointerdown',event=>{const source=event.target.closest('[data-app]');if(source&&event.pointerType==='touch'){clearTimeout(holdTimer);holdTimer=setTimeout(()=>{heldSource=source;showContext(source,event.clientX,event.clientY);},550);}});
  document.addEventListener('pointerup',()=>clearTimeout(holdTimer));
  document.addEventListener('pointercancel',()=>{clearTimeout(holdTimer);heldSource=null;});
  let gestureStart=null;
  $('.status-bar').addEventListener('pointerdown',event=>{if(event.pointerType==='touch'&&event.clientX>innerWidth*.6)gestureStart={x:event.clientX,y:event.clientY};});
  document.addEventListener('pointerup',event=>{if(gestureStart&&event.clientY-gestureStart.y>45){if(panel!=='shade')openPanel('shade');}gestureStart=null;});
  for(let i=0;i<23;i++){const bar=document.createElement('i');bar.style.height=(5+Math.sin(i*.9)*5+Math.cos(i*2)*3+6)+'px';bar.style.setProperty('--index',i);$('.wave').append(bar);}
  buildPalettes();hydrate();renderDock();renderApps('');applyTheme();updateClock();setInterval(updateClock,15000);
  $('.wallpaper-art').style.backgroundImage='url("assets/wallpaper.svg")';
  $('#shade-backdrop').hidden=false;document.body.classList.add('shade-visible');$('#shade').focus();
  window.PRISM_PREVIEW={state,openPanel,closePanels,launchApp};
})();
