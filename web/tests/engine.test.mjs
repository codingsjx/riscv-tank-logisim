import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { TankMachine } from '../dist/engine.js';

test('browser CPU matches Python instruction runner at every campaign checkpoint', () => {
  const checkpoints=JSON.parse(fs.readFileSync(new URL('./fixtures.json',import.meta.url),'utf8'));
  const game=new TankMachine();
  checkpoints.forEach((expected,index) => {
    if (expected.level !== null) game.setLevel(expected.level);
    if (expected.bulletPeriod !== null) game.setBulletPeriod(expected.bulletPeriod);
    for(const [address,value] of Object.entries(expected.patch||{})) game.memory[Number(address)>>>2]=value;
    if (expected.events !== null) game.dispatch(expected.events);
    assert.equal(game.pc,expected.pc,`checkpoint ${index}: PC`);
    assert.equal(game.cycles,expected.cycles,`checkpoint ${index}: instruction cycles`);
    assert.deepEqual(Array.from(game.registers),expected.registers,`checkpoint ${index}: registers`);
    assert.deepEqual(Array.from(game.memory),expected.memory,`checkpoint ${index}: RAM`);
  });
});

test('same-cell and crossing cancellation remain in the course ROM', () => {
  for(const [first,dir,second,otherDir] of [[0x75,1,0x77,3],[0x75,1,0x76,3]]) {
    const game=new TankMachine();game.dispatch(16);
    for(const [slot,pos,direction,owner] of [[0x80,first,dir,0],[0x90,second,otherDir,1]]) {
      game.memory[slot>>>2]=pos;game.memory[(slot+4)>>>2]=direction;game.memory[(slot+8)>>>2]=1;game.memory[(slot+12)>>>2]=owner;
    }
    game.dispatch(256);game.dispatch(256);
    assert.equal(game.memory[0x88>>>2],0);assert.equal(game.memory[0x98>>>2],0);
    assert.equal(game.state().lives,3);assert.equal(game.state().score,0);
  }
});

test('pause ignores movement and firing; restart restores the battlefield', () => {
  const game=new TankMachine();game.dispatch(16);game.dispatch(32);
  const before=game.tiles();const tick=game.state().tick;
  game.dispatch(1|128|256);
  assert.deepEqual(game.tiles(),before);assert.equal(game.state().tick,tick);
  game.dispatch(32);assert.equal(game.state().status,1);
  game.memory[64>>>2]=0xd7;game.dispatch(4);game.dispatch(128|256);game.dispatch(256);
  assert.equal(game.state().status,3);assert.equal(game.state().base,0);
  game.dispatch(64);assert.equal(game.state().status,0);assert.equal(game.state().base,1);
});


test('level selection resets waves, cover, and AI cadence in the course ROM', () => {
  const game=new TankMachine();
  for(const level of [0,1,2]) {
    game.setLevel(level);game.dispatch(64);
    assert.equal(game.state().level,level);
    assert.equal(game.state().total,2+level*2);
    assert.equal(game.state().enemies,2+level*2);
    assert.equal(game.state().reserves,level*2);
    for(const p of [0xd6,0xd7,0xd8,0xe6,0xe8]) assert.equal(game.tiles()[p],14);
    assert.equal(game.memory[120>>>2],Number(level>0));
    assert.deepEqual([game.memory[88>>>2],game.memory[104>>>2],game.memory[120>>>2]],[1,1,Number(level>0)]);
    assert.equal(game.tiles()[0xf7],2);
    game.dispatch(16);
    for(let tick=1;tick<4-level;tick++) game.dispatch(256);
    assert.equal(game.memory[80>>>2],0x37);
    game.dispatch(256);assert.equal(game.memory[80>>>2],0x36);
  }
});


test('roof guard needs two hits before opening the base lane', () => {
  const game=new TankMachine();game.setBulletPeriod(1);game.dispatch(16);
  assert.equal(game.tiles()[0xd7],14);
  for(let hit=1;hit<=2;hit++){
    game.memory[0x80>>>2]=0xc7;game.memory[0x84>>>2]=2;game.memory[0x88>>>2]=1;game.memory[0x8c>>>2]=1;
    game.dispatch(256);
    assert.equal(game.tiles()[0xd7],hit===1?1:0);
    assert.equal(game.state().base,1);
  }
});

test('slower projectile cadence is independent of the chosen enemy level', () => {
  for(const period of [1,2,3]) {
    const game=new TankMachine();game.setBulletPeriod(period);game.dispatch(16);game.dispatch(128);
    for(let i=1;i<period;i++) game.dispatch(256);
    assert.equal(game.memory[0x80>>>2],0xe5);
    game.dispatch(256);assert.equal(game.memory[0x80>>>2],0xd5);
  }
});

test('only elite enemies drop upgrade items', () => {
  const game=new TankMachine();game.dispatch(16);game.setBulletPeriod(1);
  assert.deepEqual([game.memory[0x90c>>>2],game.memory[0x910>>>2]],[3,1]);
  for(let hit=1;hit<=3;hit++){
    game.memory[80>>>2]=0x47;game.memory[0x90c>>>2]=4-hit;game.memory[0x92c>>>2]=3;
    game.memory[60>>>2]=0;game.memory[0x80>>>2]=0x57;
    game.memory[0x84>>>2]=0;game.memory[0x88>>>2]=1;game.memory[0x8c>>>2]=0;
    game.dispatch(256);
    assert.equal(game.state().pickup,hit===3?0x47:0xffffffff);
  }
  assert.equal(game.memory[88>>>2],0);
  assert.equal(game.state().pickup,0x47);
  assert.equal(game.state().items,0);
});
