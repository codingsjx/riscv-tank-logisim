"""Smoke the new rules on the actual forwarding CPU and native peripherals."""
from java_bridge import start,finish,ROOT
from native_runtime import NativeTank


def check(J):
    game=NativeTank(J);game.reset()
    assert game.tiles()[0xe5]==4 and game.tiles()[0xd7]==0
    assert all(game.tiles()[p]==14 for p in [0xd6,0xd8,0xe6,0xe8])
    assert game.get('PICKUP')==0xffffffff and game.get('ITEMS')==0
    game.click('START');game.click('RIGHT');game.click('FIRE')
    game.click('STEP')
    assert game.tiles()[0xe6]==14 # First tick does not move the projectile.
    game.click('STEP')
    assert game.tiles()[0xe6]==1 and game.get('SCORE')==0
    game.click('FIRE','STEP');game.click('STEP',atomic=True)
    assert game.tiles()[0xe6]==0 and game.get('SCORE')==10 and game.get('BASEHP')==1
    print('Native slowed bullets and two-hit base guards passed.',flush=True)
    game.click('PAUSE')
    pending=next(c for c in game.core.getCircuit().getNonWires() if str(c.getFactory().getName())=='Tunnel' and any(str(a.getName())=='label' and str(c.getAttributeSet().getValue(a))=='Tank.Pending' for a in c.getAttributeSet().getAttributes()))
    game.button('USE',True);game.button('USE',False)
    assert int(game.core.getValue(pending.getLocation()).toIntValue())&512
    game.cycles(100)
    assert not (int(game.core.getValue(pending.getLocation()).toIntValue())&512)
    assert game.get('UPGRADE')==0 and game.get('USES')==0
    game.pin('LEVEL',2);game.click('RESTART')
    assert game.get('ALIVE')==6 and game.get('ARMOR1')==3 and game.get('ARMOR2')==3
    assert all(game.tiles()[p]==14 for p in [0xd6,0xd8,0xe6,0xe8])
    game.render(ROOT/'build/panel.png')
    print('Native elite armor, upgrade HUD, 10-bit input/ACK, restart, and atomic commit passed.',flush=True)


if __name__=='__main__':
    J=start();code=0
    try:check(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
