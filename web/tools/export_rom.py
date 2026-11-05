"""Export the course ROM and deterministic cross-language CPU fixtures."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT.parent if (ROOT.parent/'software/tank.s').exists() else ROOT.parent/'tank');args=parser.parse_args()
sys.path.insert(0,str(args.source/'tools'))
from rv32 import build,Machine
words,labels=build(args.source)
(ROOT/'dist/rom.js').write_text('// Generated from tank/software/tank.s; run python tools/export_rom.py.\nexport const ROM = '+json.dumps(words,separators=(',',':'))+';\nexport const SYMBOLS = '+json.dumps(labels,separators=(',',':'))+';\n',encoding='utf-8')
m=Machine(words);m.mem[0x708]=0;m.until(lambda m:m.pc==labels['main']);checkpoints=[]
def record(events=None,level=None,bulletPeriod=None,patch=None):
    if level is not None:m.mem[0x710]=level
    if bulletPeriod is not None:m.mem[0x714]=bulletPeriod
    if patch:m.mem.update(patch)
    if events is not None:
        m.set_keys(events);m.set_keys(0);m.step();m.until(lambda m:m.pc==labels['main'])
    checkpoints.append(dict(events=events,level=level,bulletPeriod=bulletPeriod,patch=patch,registers=m.reg[:],memory=[m.mem.get(i*4,0) for i in range(1024)],cycles=m.cycles,pc=m.pc))
record();record(16)
for tick in range(1,37):
    record(384)
    if tick==7:record(32);record(32)
for events in [64,16,4,384,64]:record(events)
for level in [1,2,0]:
    record(64,level);record(16)
    for tick in range(1,61):record(384 if tick%4 else 385)
    record(32);record(64)
record(64,2);record(16)
record(384,patch={80:0xd5,0x90c:1})
for events in [256,1,512,32,512,32,64]:record(events)
for period in [1,3,2]:
    record(64,0,period);record(16);record(128)
    for _ in range(6):record(256)
(ROOT/'tests/fixtures.json').write_text(json.dumps(checkpoints,separators=(',',':')),encoding='utf-8')
print(f'Exported {len(words)} instructions and {len(checkpoints)} CPU checkpoints across three levels.')
