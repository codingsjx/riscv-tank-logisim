from java_bridge import start,finish,ROOT
from native_runtime import NativeTank
from campaign import run_campaign


def check(J):
    game=NativeTank(J);game.reset()
    assert game.get('LIVES')==3 and game.get('ALIVE')==2
    assert game.tiles()[0xe5]==4 and game.tiles()[0xe7]==3
    assert all(game.tiles()[p]==14 for p in [0xd6,0xd8,0xe6,0xe8])
    game.render(ROOT/'build/panel.png')
    run_campaign(game)
    print('Actual Logisim CPU integration passed.',flush=True)


def check_levels(J):
    game=NativeTank(J)
    game.pin('LEVEL',2);game.reset()
    assert game.get('ALIVE')==6
    assert game.tiles()[0x75]==2 and game.tiles()[0x82]==1
    assert all(game.tiles()[p]==14 for p in [0xd6,0xd8,0xe6,0xe8])
    game.click('START');game.click('STEP')
    assert game.tiles()[0x37]==10
    game.click('STEP')
    assert game.tiles()[0x36]==11
    game.pin('LEVEL',1);game.click('RESTART')
    assert game.get('ALIVE')==4 and game.tiles()[0x75]==0 and game.tiles()[0x82]==1
    game.pin('LEVEL',0);game.click('RESTART')
    assert game.get('ALIVE')==2 and game.tiles()[0x82]==0
    print('Native level MMIO, hard AI cadence, base guards, and all three maps passed.',flush=True)


if __name__=='__main__':
    J=start();code=0
    try:
        import sys
        check_levels(J) if '--levels' in sys.argv else check(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
