"""Deterministic input campaign: loot, upgrade, interception, victory and defeat."""


def run_campaign(game,capture=lambda action,duration=650:None):
    capture('基地护墙与侧边出生',1600)
    game.click('START');game.click('LEFT');game.click('UP')
    game.click('FIRE');game.click('STEP');game.click('STEP')
    assert game.get('SCORE')==10 and game.tiles()[0xc4]==0
    capture('减速炮弹击碎普通砖墙',1500)
    for name in ['UP']*6+['RIGHT']*3+['UP']*3:game.click(name)
    game.pin('BULLET',1)
    for _ in range(3):
        if game.get('PICKUP')!=0xffffffff:break
        game.click('FIRE');game.click('STEP')
    game.pin('BULLET',2)
    assert game.get('SCORE')==110 and game.get('ALIVE')==1 and game.get('PICKUP')==0x37
    capture('击毁敌军，掉落升级星',1900)
    game.click('UP')
    assert game.get('ITEMS')==1 and game.get('PICKUP')==0xffffffff
    capture('接触升级星，自动拾取',1600)
    game.click('USE')
    assert game.get('UPGRADE')==1 and game.get('ITEMS')==0 and game.get('USES')==1
    capture('USE：升级弹药容量',1900)
    game.click('PAUSE');old=game.get('FRAME');game.cycles(100);assert game.get('FRAME')==old
    capture('暂停后道具和战斗状态保留',1000);game.click('PAUSE')
    game.click('RIGHT')
    for _ in range(24):
        if game.get('STATUS')!=1:break
        game.click('FIRE','STEP')
        capture('对射拦截并消灭剩余敌军',350)
    assert game.get('STATUS')==4 and game.get('SCORE')==210 and game.get('ALIVE')==0
    capture('强化坦克守住基地，任务完成',2000)
    game.click('RESTART')
    assert game.get('BEST')==210 and game.get('UPGRADE')==0 and game.get('ITEMS')==0
    game.click('START');game.click('UP');game.click('UP') # The second UP is blocked by a brick.
    game.click('RIGHT');game.click('FIRE') # Facing a two-hit guard from (5,13).
    for _ in range(2):game.click('STEP')
    assert game.tiles()[0xd6]==1
    capture('基地护墙第一次命中后开裂',1600)
    game.click('FIRE')
    for _ in range(2):game.click('STEP')
    assert game.tiles()[0xd6]==0
    capture('基地护墙第二次命中后破坏',1600)
    game.click('RIGHT');game.click('RIGHT');game.click('DOWN');game.click('FIRE')
    for _ in range(2):game.click('STEP')
    assert game.get('STATUS')==3 and game.get('CAUSE')==2 and game.get('BASEHP')==0
    capture('基地被命中仍会失败',1700)
    game.click('RESTART')
    assert game.get('STATUS')==0 and all(game.tiles()[p]==14 for p in [0xd6,0xd8,0xe6,0xe8])
    capture('重开恢复护墙与初始装备',1200)
    print('Campaign: slowed bullets, two-hit guards, loot, manual upgrade, pause, victory, base defeat and restart passed.',flush=True)
