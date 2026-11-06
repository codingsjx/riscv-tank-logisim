import test from 'node:test';
import assert from 'node:assert/strict';
import { InputGate } from '../dist/input.js';

test('tap and held movement share a 280ms rate limit', () => {
  const gate=new InputGate();
  assert.equal(gate.move(1000),true);
  assert.equal(gate.move(1100),false);
  assert.equal(gate.move(1279),false);
  assert.equal(gate.move(1280),true);
  assert.equal(gate.move(1560),true);
});

test('firing cadence is independent from movement and reset clears both', () => {
  const gate=new InputGate();
  assert.equal(gate.move(0),true);
  assert.equal(gate.fire(0),true);
  assert.equal(gate.fire(189),false);
  assert.equal(gate.fire(190),true);
  assert.equal(gate.move(279),false);
  gate.reset();
  assert.equal(gate.move(0),true);
  assert.equal(gate.fire(0),true);
});
