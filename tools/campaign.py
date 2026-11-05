"""A deterministic user-input campaign that checks both interception cases."""


def run_campaign(game,capture=lambda action,duration=650:None):
    capture('初始战场',1800)
    game.click('START');capture('START：开始战斗',1200)
    for tick in range(1,37):
        game.click('FIRE','STEP',atomic=tick==7)
        assert game.get('TICK')==tick
        if tick==4:
            assert game.get('SCORE')==10 and game.tiles()[0x97]==0
            capture('炮弹击碎砖墙，+10 分',1500)
        elif tick==6:
            assert game.tiles()[0x67]==13 and game.tiles()[0x87]==12
            capture('两弹接近同一格',1700)
        elif tick==7:
            assert all(game.tiles()[p]==0 for p in (0x67,0x77,0x87))
            assert game.get('LIVES')==3 and game.get('ALIVE')==2 and game.get('SCORE')==10
            capture('同格相撞，双方炮弹消失',2100)
            print('Native same-cell interception and atomic display verified.',flush=True)
            game.click('PAUSE');capture('PAUSE：暂停战斗',1100)
            old=game.get('FRAME');game.cycles(160);assert game.get('FRAME')==old
            game.click('PAUSE');capture('恢复战斗',800)
        elif tick==17:
            assert game.tiles()[0x87]==13 and game.tiles()[0x97]==12
            capture('迎面交叉前',1700)
        elif tick==18:
            assert game.tiles()[0x87]==0 and game.tiles()[0x97]==0
            assert game.get('LIVES')==3 and game.get('ALIVE')==2 and game.get('SCORE')==10
            capture('交叉抵消，不会穿过彼此',2100)
            print('Native crossing interception verified.',flush=True)
        elif tick==28:
            assert game.get('SCORE')==110 and game.get('ALIVE')==1
            capture('击毁第一辆敌军，+100 分',1700)
        elif tick==36:
            assert game.get('STATUS')==4 and game.get('SCORE')==210 and game.get('ALIVE')==0
            capture('消灭全部敌军，获胜',2300)
        else:capture('发射、推进与敌军反击',350)
    game.click('RESTART');capture('RESTART：保留最高分',1300)
    assert game.get('BEST')==210 and game.get('LIVES')==3
    game.click('START');game.click('DOWN');capture('基地前转向，移动被阻挡',1000)
    game.click('FIRE','STEP')
    assert game.get('STATUS')==3 and game.get('CAUSE')==2 and game.get('BASEHP')==0
    assert game.tiles()[0xe7]==15
    capture('基地被毁仍会失败',1700)
    game.click('RESTART');capture('重新开始，基地和砖墙恢复',1300)
    assert game.get('STATUS')==0 and game.get('BEST')==210 and game.get('BASEHP')==1
    print('Complete native campaign, base defeat, and restart verified.',flush=True)
