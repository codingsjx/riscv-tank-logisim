from java_bridge import start,finish,ROOT
from native_runtime import NativeTank
from campaign import run_campaign


def check(J):
    game=NativeTank(J);game.reset()
    assert game.get('LIVES')==3 and game.get('ALIVE')==2
    assert game.tiles()[0xd7]==4 and game.tiles()[0xe7]==3
    game.render(ROOT/'build/panel.png')
    run_campaign(game)
    print('Actual Logisim CPU integration passed.',flush=True)


if __name__=='__main__':
    J=start();code=0
    try:check(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
