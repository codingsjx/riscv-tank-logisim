export class InputGate {
  constructor(moveInterval = 280, fireInterval = 190) {
    this.moveInterval = moveInterval;
    this.fireInterval = fireInterval;
    this.nextMoveAt = 0;
    this.nextFireAt = 0;
  }

  move(now) {
    if (now < this.nextMoveAt) return false;
    this.nextMoveAt = now + this.moveInterval;
    return true;
  }

  fire(now) {
    if (now < this.nextFireAt) return false;
    this.nextFireAt = now + this.fireInterval;
    return true;
  }

  reset() {
    this.nextMoveAt = 0;
    this.nextFireAt = 0;
  }
}
