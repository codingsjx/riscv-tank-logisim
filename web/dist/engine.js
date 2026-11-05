import { ROM, SYMBOLS } from './rom.js';

const sign = (value, bits) => (value << (32 - bits)) >> (32 - bits);

/** Functional RV32 interpreter. All game behavior is executed from the course ROM. */
export class TankMachine {
  constructor() {
    this.registers = new Uint32Array(32);
    this.memory = new Uint32Array(1024);
    this.pc = 0;
    this.cycles = 0;
    this.frames = 0;
    this.display = new Uint32Array(32);
    this.hud = new Uint32Array(17);
    this.runUntilMain();
  }

  load(address) {
    address >>>= 0;
    if ((address & 3) || address >= 4096) throw new Error(`Invalid memory read: ${address}`);
    if (address === 0x704) return this.cycles >>> 0;
    if (address === 0x708) return 0; // Frontend supplies the same STEP input at wall-clock intervals.
    return this.memory[address >>> 2];
  }

  store(address, value) {
    address >>>= 0; value >>>= 0;
    if ((address & 3) || address >= 4096) throw new Error(`Invalid memory write: ${address}`);
    this.memory[address >>> 2] = value;
    if (address === 0x70c) this.memory[0x700 >>> 2] &= ~value;
    if (address === 0x760) {
      this.display.set(this.memory.subarray(0x800 >>> 2, 0x880 >>> 2));
      this.hud.set(this.memory.subarray(0x740 >>> 2, 0x784 >>> 2));
      this.frames = value;
    }
  }

  step() {
    if ((this.pc & 3) || (this.pc >>> 2) >= ROM.length) throw new Error(`PC outside ROM: ${this.pc}`);
    const w = ROM[this.pc >>> 2] >>> 0;
    const opcode = w & 127, rd = (w >>> 7) & 31, f3 = (w >>> 12) & 7;
    const rs1 = (w >>> 15) & 31, rs2 = (w >>> 20) & 31, f7 = w >>> 25;
    const x = this.registers[rs1], y = this.registers[rs2];
    let next = this.pc + 4, value;
    const n = sign(w >>> 20, 12);
    if (opcode === 0x33) {
      if (f3 === 0) value = f7 === 32 ? x - y : x + y;
      else if (f3 === 7) value = x & y;
      else if (f3 === 6) value = x | y;
      else if (f3 === 2) value = +( (x | 0) < (y | 0) );
      else if (f3 === 3) value = +(x < y);
      else throw new Error(`Unsupported R instruction ${w.toString(16)}`);
    } else if (opcode === 0x13) {
      if (f3 === 0) value = x + n;
      else if (f3 === 7) value = x & n;
      else if (f3 === 6) value = x | n;
      else if (f3 === 4) value = x ^ n;
      else if (f3 === 2) value = +((x | 0) < n);
      else if (f3 === 3) value = +(x < (n >>> 0));
      else if (f3 === 1) value = x << rs2;
      else if (f3 === 5) value = f7 === 32 ? (x | 0) >> rs2 : x >>> rs2;
      else throw new Error(`Unsupported immediate instruction ${w.toString(16)}`);
    } else if (opcode === 3 && f3 === 2) value = this.load((x + n) >>> 0);
    else if (opcode === 0x23 && f3 === 2) {
      const offset = sign(((w >>> 25) << 5) | ((w >>> 7) & 31), 12);
      this.store((x + offset) >>> 0, y);
    } else if (opcode === 0x63 && (f3 === 0 || f3 === 1)) {
      const offset = sign(((w >>> 31) << 12) | (((w >>> 7) & 1) << 11) | (((w >>> 25) & 63) << 5) | (((w >>> 8) & 15) << 1), 13);
      if ((x === y) === (f3 === 0)) next = this.pc + offset;
    } else if (opcode === 0x6f) {
      const offset = sign(((w >>> 31) << 20) | (((w >>> 12) & 255) << 12) | (((w >>> 20) & 1) << 11) | (((w >>> 21) & 1023) << 1), 21);
      value = this.pc + 4; next = this.pc + offset;
    } else if (opcode === 0x67 && f3 === 0) {
      value = this.pc + 4; next = (x + n) & 0xfffffffe;
    } else throw new Error(`Unsupported instruction ${w.toString(16)}`);
    if (value !== undefined && rd) this.registers[rd] = value >>> 0;
    this.registers[0] = 0;
    this.pc = next >>> 0;
    this.cycles++;
  }

  runUntilMain(forceIteration = false) {
    let steps = 0;
    if (forceIteration) { this.step(); steps++; }
    while (this.pc !== SYMBOLS.main) {
      this.step();
      if (++steps > 200000) throw new Error('CPU execution timeout');
    }
    return steps;
  }

  setBulletPeriod(period) { this.memory[0x714 >>> 2] = Math.max(1, Math.min(3, Number(period) | 0)); }

  setLevel(level) { this.memory[0x710 >>> 2] = Math.max(0, Math.min(2, Number(level) | 0)); }

  dispatch(events) {
    this.memory[0x700 >>> 2] |= events & 1023;
    this.runUntilMain(true);
    return this.state();
  }

  tiles() {
    return Array.from({ length: 256 }, (_, i) => (this.display[i >>> 3] >>> ((i & 7) * 4)) & 15);
  }

  state() {
    const names = ['status','score','lives','enemies','cause','base','tick','best','frame','upgrade','pickup','items','armor1','armor2','uses','pos1','pos2'];
    return {...Object.fromEntries(names.map((name, i) => [name, this.hud[i]])), level:this.memory[12], total:this.memory[13], reserves:this.memory[14]};
  }
}
