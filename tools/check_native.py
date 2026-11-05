from java_bridge import start,finish,ROOT
from native_runtime import NativeTank


def check(J):
    game=NativeTank(J);game.reset()
    assert game.get('LIVES')==3 and game.get('ALIVE')==2
    assert game.tiles()[0xd7]==4 and game.tiles()[0xe7]==3
    game.render(ROOT/'build/panel.png')
    game.click('START');assert game.get('STATUS')==1
    game.click('RIGHT');assert game.tiles()[0xd8]==5
    game.click('LEFT');assert game.tiles()[0xd7]==7
    game.click('RESTART');game.click('START')
    game.click('FIRE');game.click('STEP',atomic=True)
    assert game.tiles()[0xc7]==12
    for _ in range(3):game.click('STEP')
    assert game.get('SCORE')==10 and game.tiles()[0x97]==0
    assert game.get('TICK')==4
    print('Movement, fire, brick destruction, AI, and atomic frames verified.',flush=True)
    game.click('FIRE')
    for _ in range(8):game.click('STEP')
    assert game.get('SCORE')==110 and game.get('ALIVE')==1,game.stats()
    print('Enemy hit and score verified:',game.stats(),flush=True)
    game.click('PAUSE');before=game.get('FRAME')
    game.button('STEP',True);game.button('STEP',False);game.cycles(200)
    assert game.get('STATUS')==2 and game.get('FRAME')==before
    game.click('PAUSE');game.click('STEP')
    assert game.get('LIVES')==2,game.stats()
    print('Pause/resume and enemy damage/respawn verified.',flush=True)
    game.click('DOWN');game.click('FIRE');game.click('STEP')
    assert game.get('STATUS')==3 and game.get('CAUSE')==2 and game.get('BASEHP')==0
    assert game.tiles()[0xe7]==15
    game.click('RESTART')
    assert game.get('STATUS')==0 and game.get('LIVES')==3 and game.get('BEST')==110
    print('Base defeat and restart verified. Actual Logisim CPU integration passed.',flush=True)


if __name__=='__main__':
    J=start();code=0
    try:check(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
