import { TankMachine } from './engine.js';
import { InputGate } from './input.js';

const $ = id => document.getElementById(id);
const canvas=$('game'), ctx=canvas.getContext('2d');
const game=new TankMachine();
const keyBits={KeyW:1,ArrowUp:1,KeyD:2,ArrowRight:2,KeyS:4,ArrowDown:4,KeyA:8,ArrowLeft:8,Space:128};
const controlBits={up:1,right:2,down:4,left:8,fire:128};
const held=new Map(),inputGate=new InputGate();
const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let pendingMove=0,pendingFire=false,order=0,tickAt=0,lastTime=performance.now();
let previous=game.state(),lastTiles=game.tiles(),lastActors=actors();
let particles=[],rings=[],muzzleUntil=0,toastUntil=0,soundOn=false,audio=null,best=0;
try { best=Number(localStorage.getItem('riscv-tank-best')||0)||0; } catch {}

function setText(id,value){const el=$(id);if(el.textContent!==String(value))el.textContent=String(value);}
function actors(){return [64,80,96,112].map(p=>({pos:game.memory[p>>>2],active:game.memory[(p+8)>>>2],maxHp:p===64?0:game.memory[((p===80?0x92c:p===96?0x930:0x934)>>>2)]}));}
function focusGame(){canvas.focus({preventScroll:true});}
function clearInput(){held.clear();pendingMove=0;pendingFire=false;document.querySelectorAll('[data-control]').forEach(b=>b.classList.remove('held'));}
function note(text){setText('activityText',text);}
function toast(text){setText('toast',text);$('toast').classList.add('visible');toastUntil=performance.now()+1500;note(text);}
function beep(frequency=220,duration=.07,type='square'){
  if(!soundOn)return;
  try {
    audio ||= new (window.AudioContext||window.webkitAudioContext)();audio.resume();
    const o=audio.createOscillator(),g=audio.createGain();o.type=type;o.frequency.setValueAtTime(frequency,audio.currentTime);
    o.frequency.exponentialRampToValueAtTime(Math.max(30,frequency*.45),audio.currentTime+duration);
    g.gain.setValueAtTime(.035,audio.currentTime);g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+duration);
    o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+duration);
  } catch {}
}
function burst(pos,color,count=10){
  if(reducedMotion)return;
  const x=(pos%16)*40+20,y=(pos>>>4)*40+20;
  for(let i=0;i<count;i++){const angle=Math.random()*Math.PI*2,speed=35+Math.random()*90;particles.push({x,y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,life:.3+Math.random()*.22,max:.52,color});}
  rings.push({x,y,life:.25,color});
}

function execute(bits){
  try {
    const before=previous,oldShots=game.memory[10],oldActors=lastActors;
    game.dispatch(bits);const now=game.state(),tiles=game.tiles();
    if(bits&64){particles=[];rings=[];note('新的战斗已准备就绪');}
    if(now.tick!==before.tick){
      let intercepted=false;
      for(let i=0;i<4;i++)if(game.memory[(0xf0>>>2)+i]&&game.memory[(0x80+i*16+12)>>>2]!==0){burst(game.memory[(0xe0>>>2)+i],'#99e3b5',9);intercepted=true;}
      if(intercepted){toast('拦截成功 · 敌弹被抵消');beep(610,.06,'triangle');}
    }
    if(game.memory[10]>oldShots){muzzleUntil=performance.now()+75;beep(170,.055);}
    if(now.items>before.items){toast('拾取升级星 · 按 E 使用');beep(780,.13,'triangle');}
    if(now.uses>before.uses){toast(now.upgrade>before.upgrade?(now.upgrade===1?'强化成功 · 弹药容量提升至 3 发':'强化成功 · 炮弹伤害提升至 2'):'修复成功 · 恢复一条生命');beep(950,.2,'triangle');}
    const newActors=actors();
    if(!(bits&64)&&now.enemies<before.enemies){for(let i=1;i<4;i++)if(oldActors[i].active&&!newActors[i].active)burst(oldActors[i].pos,newActors[i].maxHp===3?'#edb06d':'#a8b2a1',24);toast(newActors.slice(1).some((actor,i)=>oldActors[i+1].active&&!actor.active&&actor.maxHp===3)?'击毁精英怪 +100 · 升级星已掉落':'击毁普通小兵 +100');beep(85,.22,'sawtooth');}
    else if(now.score>before.score){for(let p=0;p<256;p++)if(lastTiles[p]===1&&tiles[p]===0)burst(p,'#bd895a',8);toast('击碎砖墙 +10');beep(95,.09,'triangle');}
    if(now.lives<before.lives){burst(oldActors[0].pos,'#dd9878',20);toast(now.lives?'受到攻击 · 已返回出生点':'生命耗尽');beep(65,.25,'sawtooth');}
    if(now.status===4&&before.status!==4){note('任务完成！全部敌军已消灭');beep(650,.2,'triangle');clearInput();}
    if(now.status===3&&before.status!==3){note(now.cause===2?'基地被毁 · 留意炮口，避免误伤':'本次战斗结束');beep(60,.3,'sawtooth');clearInput();}
    previous=now;lastTiles=tiles;lastActors=newActors;
    if(now.best>best){best=now.best;try{localStorage.setItem('riscv-tank-best',String(best));}catch{}}
    updateUI();
  } catch(error){
    clearInput();note('运行出现异常，请刷新后重试。');console.error(error);
    $('overlay').hidden=false;setText('overlayTitle','运行暂停');setText('overlayCopy','请刷新页面后重新进入战场。');
  }
}

function updateUI(){
  const s=previous;
  setText('score',String(s.score).padStart(3,'0'));setText('enemies',s.enemies);setText('best',String(Math.max(best,s.best)).padStart(3,'0'));
  const lifeMarkup=Array.from({length:3},(_,i)=>i<s.lives?'♥':'<span class="heart-empty">♥</span>').join(' ');
  if($('lives').innerHTML!==lifeMarkup)$('lives').innerHTML=lifeMarkup;
  $('lives').setAttribute('aria-label',`${s.lives} 条生命`);
  setText('base',s.base?'完好':'失守');$('base').className=s.base?'base-good':'base-lost';
  const total=s.total||2,levelNames=['训练','进阶','困难'];
  setText('enemyTotal',` / ${total}`);
  setText('progressLabel',`${total-s.enemies} / ${total}`);$('progress').style.width=`${(total-s.enemies)*100/total}%`;
  setText('levelTitle',`0${s.level+1} · ${levelNames[s.level]}防守`);
  setText('levelDetail',`${total} 辆敌军分批进攻，最多同时 ${s.level?'3':'2'} 辆。普通小兵 1 格生命，精英怪 3 格生命；仅精英掉落升级星。屋顶护墙需两次命中 · 每 ${4-s.level} 拍行动。`);
  setText('upgradeName',['基础坦克','一级 · 扩容坦克','二级 · 强攻坦克'][s.upgrade]||'基础坦克');
  setText('upgradeDetail',`弹药 ${s.upgrade?3:2} 发 · 伤害 ${s.upgrade===2?2:1}${s.pickup!==0xffffffff?' · ★ 战场上有升级星':''}`);
  setText('itemCount',s.items);
  $('useItem').disabled=s.status!==1||s.items===0||(s.upgrade===2&&s.lives===3);
  $('useItem').title=s.upgrade===2?'消耗一枚升级星恢复一条生命':'消耗一枚升级星强化坦克';
  const status=['待命','交战中','已暂停','失守','任务完成'][s.status]||'待命';
  setText('statusBadge',status);$('statusBadge').classList.toggle('lost',s.status===3);
  $('battleStatus').innerHTML=`<i class="status-dot"></i>${status}`;
  setText('frameNote',s.status===1?'主动拦截，也是一种防守':'保护金色基地');
  $('start').disabled=s.status===1;
  $('start').innerHTML=s.status===1?'战斗中':s.status===2?'继续战斗 <kbd>Enter</kbd>':s.status>=3?'再次出击 <kbd>Enter</kbd>':'开始战斗 <kbd>Enter</kbd>';
  $('pause').disabled=s.status!==1&&s.status!==2;
  $('pause').innerHTML=s.status===2?'继续 <kbd>P</kbd>':'暂停 <kbd>P</kbd>';
  $('overlay').hidden=s.status===1;
  const content=s.status===0?[`基地防守 · ${levelNames[s.level]}战场`,'守住你的基地',`击碎砖墙，消灭 ${total} 辆敌军。<br>${s.level?'后续敌军会持续补入。':'对射可以抵消敌弹。'}`,'开始战斗']:
    s.status===2?['战斗已暂停','稍作休整','战场已经暂停。<br>准备好后，继续保护基地。','继续战斗']:
    s.status===4?['任务完成','战场已经清空',`最终得分 <strong>${s.score}</strong> · 剩余生命 ${s.lives}<br>你的基地成功守住了。`,'再来一局']:
    ['任务结束',s.cause===2?'基地失守':'生命耗尽',s.cause===2?'基地被命中，本次战斗结束。<br>留意炮口方向，避免误伤。':`最终得分 <strong>${s.score}</strong><br>调整路线，再次出击。`,'重新出击'];
  if(s.status!==1){setText('overlayTag',content[0]);setText('overlayTitle',content[1]);$('overlayCopy').innerHTML=content[2];$('overlayAction').innerHTML=content[3]+' <kbd>Enter</kbd>';}
  const p=game.memory[64>>>2];canvas.setAttribute('aria-label',`坦克战场。${status}。玩家位置 ${p&15},${p>>>4}，生命 ${s.lives}，敌军 ${s.enemies}。强化 ${s.upgrade} 级，升级星 ${s.items} 枚。方向键或 WASD 移动，空格射击，E 使用道具。`);
  canvas.dataset.status=String(s.status);
}

function startOrResume(){
  clearInput();
  if(previous.status>=3)execute(64);
  if(previous.status===0)execute(16);else if(previous.status===2)execute(32);
  inputGate.reset();tickAt=performance.now()+Number($('speed').value);note('战斗开始 · 保护基地');focusGame();
}
function pause(){if(previous.status===1||previous.status===2){clearInput();execute(32);tickAt=performance.now()+Number($('speed').value);focusGame();}}
function restart(){clearInput();execute(64);tickAt=performance.now()+Number($('speed').value);focusGame();}
$('start').addEventListener('click',startOrResume);$('overlayAction').addEventListener('click',startOrResume);
$('pause').addEventListener('click',pause);$('restart').addEventListener('click',restart);
$('level').addEventListener('change',()=>{game.setLevel($('level').value);restart();toast('关卡已切换 · 点击开始战斗');});
$('useItem').addEventListener('click',()=>{if(previous.status===1){execute(512);focusGame();}});
$('bulletSpeed').addEventListener('change',()=>{game.setBulletPeriod($('bulletSpeed').value);toast('子弹速度已调整');focusGame();});
$('speed').addEventListener('change',()=>{tickAt=performance.now()+Number($('speed').value);note('战斗节奏已调整');});
$('sound').addEventListener('click',()=>{soundOn=!soundOn;$('sound').setAttribute('aria-pressed',String(soundOn));$('sound').querySelector('span').textContent=soundOn?'音效开启':'音效关闭';if(soundOn)beep(440,.08,'triangle');focusGame();});
$('fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('boardShell').requestFullscreen();}catch{}focusGame();});
function openHelp(){if(previous.status===1)pause();clearInput();$('helpDialog').showModal();}
function closeHelp(){$('helpDialog').close();focusGame();}
$('help').addEventListener('click',openHelp);$('closeHelp').addEventListener('click',closeHelp);$('helpReady').addEventListener('click',closeHelp);
canvas.addEventListener('pointerdown',focusGame);

function pressSource(source,bit){
  held.set(source,{bit,order:++order});
  if(bit===128)pendingFire=true;else pendingMove=bit;
}
window.addEventListener('keydown',event=>{
  if($('helpDialog').open)return;
  if(event.target.closest('input,select,textarea'))return;
  if(event.code==='Enter'&&event.target.tagName!=='BUTTON'){event.preventDefault();if(!event.repeat)startOrResume();return;}
  if(event.code==='KeyP'){event.preventDefault();if(!event.repeat)pause();return;}
  if(event.code==='KeyE'){event.preventDefault();if(!event.repeat&&previous.status===1){if(previous.items)execute(512);else toast('先拾取战场上的升级星');}return;}
  if(event.code==='KeyR'){event.preventDefault();if(!event.repeat)restart();return;}
  const bit=keyBits[event.code];if(!bit)return;
  if(event.code==='Space'&&event.target.tagName==='BUTTON')return;
  event.preventDefault();if(event.repeat||previous.status!==1)return;
  pressSource(event.code,bit);
});
window.addEventListener('keyup',event=>held.delete(event.code));
document.querySelectorAll('[data-control]').forEach(button=>{
  const bit=controlBits[button.dataset.control];
  button.addEventListener('pointerdown',event=>{
    event.preventDefault();if(previous.status!==1)return;
    button.setPointerCapture(event.pointerId);button.classList.add('held');pressSource(`touch-${event.pointerId}`,bit);
  });
  const release=event=>{held.delete(`touch-${event.pointerId}`);button.classList.remove('held');};
  button.addEventListener('pointerup',release);button.addEventListener('pointercancel',release);button.addEventListener('lostpointercapture',release);
  button.addEventListener('contextmenu',event=>event.preventDefault());
});
function autoPause(){clearInput();if(previous.status===1){execute(32);note('离开窗口，已自动暂停');}}
window.addEventListener('blur',autoPause);document.addEventListener('visibilitychange',()=>{if(document.hidden)autoPause();});

function rounded(x,y,w,h,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();}
function drawTank(x,y,direction,enemy,time,shield){
  ctx.save();ctx.translate(x+20,y+20);ctx.rotate(direction*Math.PI/2);ctx.translate(-20,-20);
  ctx.shadowColor='#0006';ctx.shadowBlur=4;ctx.shadowOffsetY=2;
  rounded(5,6,9,29,3,enemy?'#4e3731':'#32483c');rounded(26,6,9,29,3,enemy?'#4e3731':'#32483c');
  ctx.shadowBlur=0;ctx.shadowOffsetY=0;
  for(let a=9;a<34;a+=5){rounded(6,a,7,1,0,enemy?'#876b5e':'#728271');rounded(27,a,7,1,0,enemy?'#876b5e':'#728271');}
  rounded(13,8,14,25,3,enemy?'#b46755':'#8aa477');
  rounded(15,10,10,19,2,enemy?'#cb7d65':'#b2c594');
  rounded(15,14,10,12,3,enemy?'#d98e73':'#c0d3a0');
  rounded(18,0,5,20,1,enemy?'#ecae8b':'#d9e3b8');
  ctx.fillStyle=enemy?'#8a4e43':'#697d58';ctx.fillRect(17,28,7,2);
  if(!enemy&&time<muzzleUntil){ctx.fillStyle='#fff3bc';ctx.beginPath();ctx.moveTo(20,-8);ctx.lineTo(23,-2);ctx.lineTo(28,-5);ctx.lineTo(24,2);ctx.lineTo(16,2);ctx.lineTo(13,-4);ctx.lineTo(18,-2);ctx.closePath();ctx.fill();}
  ctx.restore();
  if(shield){ctx.save();ctx.strokeStyle='#c9e4b699';ctx.lineWidth=1.5;ctx.setLineDash([4,4]);ctx.beginPath();ctx.arc(x+20,y+20,18,0,Math.PI*2);ctx.stroke();ctx.restore();}
}

function drawTile(p,tile,time){
  const x=(p&15)*40,y=(p>>>4)*40;
  ctx.fillStyle=((p+(p>>>4))&1)?'#20332f':'#213530';ctx.fillRect(x,y,40,40);
  ctx.strokeStyle='#34473a55';ctx.lineWidth=.7;ctx.strokeRect(x+.5,y+.5,39,39);
  const noise=((p*73+19)%17);if(noise<4){ctx.fillStyle='#77856916';ctx.fillRect(x+noise*6+4,y+noise*5+9,2,2);}
  if(tile===2){
    rounded(x+1,y+1,38,38,2,'#4a5b56');rounded(x+3,y+3,34,34,1,'#65736a');
    ctx.strokeStyle='#9caa8e';ctx.lineWidth=1;ctx.strokeRect(x+5,y+5,29,29);
    ctx.fillStyle='#b5bda3';ctx.fillRect(x+6,y+6,2,2);ctx.fillRect(x+31,y+31,2,2);
    ctx.fillStyle='#384941';ctx.fillRect(x+5,y+34,30,2);
  }else if(tile===1||tile===14){
    ctx.fillStyle='#674b35';ctx.fillRect(x+1,y+1,38,38);
    for(let row=0;row<3;row++){const yy=y+2+row*12;ctx.fillStyle=row&1?'#a7774d':'#b48455';ctx.fillRect(x+2,yy,36,10);ctx.fillStyle='#594330';ctx.fillRect(x+(row===1?10:22),yy,2,10);ctx.fillStyle='#d4a36b55';ctx.fillRect(x+2,yy,36,1);}
    if(tile===14){ctx.strokeStyle='#e2c681';ctx.lineWidth=2;ctx.strokeRect(x+3,y+3,34,34);ctx.fillStyle='#e9d59d';ctx.fillRect(x+5,y+5,4,4);ctx.fillRect(x+31,y+31,4,4);}
  }else if(tile===3){
    ctx.fillStyle='#796335';ctx.fillRect(x+6,y+14,28,22);ctx.fillStyle='#d4b56a';ctx.fillRect(x+7,y+13,26,20);
    ctx.fillRect(x+6,y+5,7,12);ctx.fillRect(x+17,y+5,6,12);ctx.fillRect(x+28,y+5,7,12);ctx.fillStyle='#594d2c';ctx.fillRect(x+17,y+23,7,13);ctx.fillStyle='#e5d99c';ctx.fillRect(x+9,y+17,21,2);
  }else if(tile>=4&&tile<=11)drawTank(x,y,(tile-4)&3,tile>=8,time,tile<8&&game.memory[36>>>2]>0);
  else if(tile===12||tile===13){
    let direction=0;for(let a=0x80;a<0xc0;a+=16)if(game.memory[(a+8)>>>2]&&game.memory[a>>>2]===p){direction=game.memory[(a+4)>>>2];break;}
    ctx.save();ctx.translate(x+20,y+20);ctx.rotate(direction*Math.PI/2);ctx.shadowColor=tile===12?'#f2dda1':'#ed9979';ctx.shadowBlur=8;rounded(-2,-5,4,9,2,tile===12?'#fff1b0':'#efa17d');ctx.restore();
  }else if(tile===15){
    ctx.fillStyle='#625144';ctx.fillRect(x+8,y+14,24,18);ctx.strokeStyle='#e2a46b';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x+9,y+9);ctx.lineTo(x+30,y+31);ctx.moveTo(x+30,y+9);ctx.lineTo(x+9,y+31);ctx.stroke();
  }
}

function resize(){const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=640*ratio;canvas.height=640*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);}
window.addEventListener('resize',resize);resize();
function draw(time,dt){
  const tiles=game.tiles();for(let p=0;p<256;p++)drawTile(p,tiles[p],time);
  const s=previous;
  if(s.pickup!==0xffffffff&&tiles[s.pickup]===0){
    const x=(s.pickup&15)*40+20,y=(s.pickup>>>4)*40+20;
    ctx.save();ctx.translate(x,y);ctx.shadowColor='#e9d16c';ctx.shadowBlur=9;ctx.fillStyle='#f2d67f';ctx.beginPath();
    for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,r=i%2?6:14;ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);}ctx.closePath();ctx.fill();ctx.shadowBlur=0;ctx.fillStyle='#675427';ctx.font='bold 11px sans-serif';ctx.textAlign='center';ctx.fillText('+',0,4);ctx.restore();
  }
  for(let i=0;i<3;i++){
    const record=80+i*16;if(!game.memory[(record+8)>>>2])continue;
    const p=game.memory[record>>>2],x=(p&15)*40,y=(p>>>4)*40,hp=game.memory[((record===80?0x90c:record===96?0x910:0x914)>>>2)];
    const maxHp=game.memory[((record===80?0x92c:record===96?0x930:0x934)>>>2)],color=maxHp===3?'#edce7f':'#8dcae3';
    if(maxHp===3){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.strokeRect(x+12,y+9,16,19);ctx.fillStyle=color;ctx.fillRect(x+11,y+11,3,14);ctx.fillRect(x+26,y+11,3,14);}
    for(let a=0;a<maxHp;a++){ctx.fillStyle=a<hp?color:'#3e4540';ctx.fillRect(x+5+a*10,y+35,8,3);}
  }
  if(s.upgrade&&game.memory[72>>>2]){const p=game.memory[64>>>2],x=(p&15)*40,y=(p>>>4)*40;ctx.strokeStyle='#e7dc8a';ctx.lineWidth=2;ctx.strokeRect(x+12,y+10,16,19);ctx.fillStyle='#e8dc94';for(let a=0;a<s.upgrade;a++)ctx.fillRect(x+12+a*10,y+33,7,3);}
  particles=particles.filter(p=>p.life>0);
  for(const p of particles){p.life-=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=80*dt;ctx.globalAlpha=Math.max(0,p.life/p.max);ctx.fillStyle=p.color;ctx.fillRect(p.x-2,p.y-2,3,3);}
  ctx.globalAlpha=1;rings=rings.filter(r=>r.life>0);
  for(const r of rings){r.life-=dt;ctx.globalAlpha=Math.max(0,r.life/.25);ctx.strokeStyle=r.color;ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(r.x,r.y,3+(1-r.life/.25)*17,0,Math.PI*2);ctx.stroke();}
  ctx.globalAlpha=1;
  if(time>toastUntil)$('toast').classList.remove('visible');
}
function frame(time){
  const dt=Math.min((time-lastTime)/1000,.05);lastTime=time;
  if(previous.status===1){
    let bits=0;
    const direction=[...held.values()].filter(h=>h.bit!==128).sort((a,b)=>b.order-a.order)[0];
    const moveBit=direction?.bit||pendingMove;
    if(moveBit&&inputGate.move(time)){bits|=moveBit;pendingMove=0;}
    else if(direction)pendingMove=direction.bit;
    if((pendingFire||[...held.values()].some(h=>h.bit===128))&&inputGate.fire(time)){bits|=128;pendingFire=false;}
    if(time>=tickAt){bits|=256;tickAt=time+Number($('speed').value);}
    if(bits)execute(bits);
  }else{pendingMove=0;pendingFire=false;}
  draw(time,dt);requestAnimationFrame(frame);
}
updateUI();requestAnimationFrame(frame);
