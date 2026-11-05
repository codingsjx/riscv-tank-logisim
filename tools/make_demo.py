"""Record a real Logisim CPU campaign, including victory and base defeat."""
import json
from java_bridge import start,finish,ROOT
from native_runtime import NativeTank,render_native_board


def demonstrate(J):
    from PIL import Image,ImageDraw,ImageFont
    game=NativeTank(J);game.reset()
    dest=ROOT/'build/demo_frames';dest.mkdir(exist_ok=True)
    font_path=r'C:\Windows\Fonts\msyh.ttc';bold_path=r'C:\Windows\Fonts\msyhbd.ttc'
    def font(size,bold=False):return ImageFont.truetype(bold_path if bold else font_path,size)
    frames=[];durations=[];record=[]
    def capture(action,duration=650):
        stats=game.stats();index=len(frames)
        png=dest/f'{index:02d}_board.png';render_native_board(game,png)
        with Image.open(png) as board:board=board.convert('RGB').copy()
        image=Image.new('RGB',(1240,900),'#101e2a');draw=ImageDraw.Draw(image)
        draw.text((40,22),'坦克世界大战 · RISC-V CPU 实际运行',font=font(30,True),fill='#f2f6fa')
        draw.text((42,69),'绿色玩家 / 红色敌军 / 砖墙可破坏 / 钢墙不可破坏 / 保护金色基地',font=font(17),fill='#aabccc')
        image.paste(board,(42,128));draw.rectangle((41,127,682,768),outline='#526b7c',width=2)
        status=stats['STATUS']
        text={0:'准备开始',1:'战斗进行中',2:'已暂停',3:'基地被毁' if stats['CAUSE']==2 else '生命耗尽',4:'胜利！敌军全部消灭'}[status]
        draw.text((730,135),'当前状态',font=font(17),fill='#aabccc')
        draw.text((730,169),text,font=font(25,True),fill='#f7aa73' if status==3 else '#63dca6')
        for i,(name,label) in enumerate([('SCORE','得分'),('LIVES','生命'),('ALIVE','剩余敌军')]):
            y=240+i*105
            draw.rounded_rectangle((730,y,1190,y+86),radius=12,fill='#1c3041')
            draw.text((751,y+14),label,font=font(20),fill='#aabccc')
            draw.text((1070,y+10),str(stats[name]),font=font(37,True),fill='#f1f6fa')
        draw.text((730,575),'基地：'+('完好' if stats['BASEHP'] else '损毁'),font=font(21),fill='#eac966')
        draw.text((730,631),action,font=font(23,True),fill='#87cdf2')
        draw.text((730,690),f"逻辑步数 {stats['TICK']}   画面 {stats['FRAME']}",font=font(17),fill='#aabccc')
        draw.text((42,810),'游戏逻辑由实际 Logisim CPU 执行；按状态取帧，非实时录屏。',font=font(18),fill='#aabccc')
        image.save(dest/f'{index:02d}_demo.png')
        frames.append(image);durations.append(duration);record.append({'step':index,'action':action,**stats})
        if action.startswith('击毁第一辆'):image.save(ROOT/'build/tank-demo-poster.png')
        print('DEMO',index,action,stats,flush=True)

    capture('初始战场',2200)
    game.click('START');capture('START：开始战斗',1300)
    game.click('FIRE','STEP');capture('FIRE：发射第一枚炮弹',1000)
    for tick in range(2,24):
        game.click(*(('FIRE','STEP') if tick in (5,14,18) else ('STEP',)))
        if tick==4:
            assert game.get('SCORE')==10
            capture('炮弹击碎砖墙，+10 分',1800)
        elif tick==12:
            assert game.get('SCORE')==110 and game.get('ALIVE')==1
            capture('击毁第一辆敌军，+100 分',2000)
            game.click('PAUSE');capture('PAUSE：暂停战斗',1500)
            old=game.get('FRAME');game.cycles(200);assert game.get('FRAME')==old
            game.click('PAUSE');capture('恢复战斗',1000)
        elif tick==13:
            assert game.get('LIVES')==2
            capture('被敌弹击中，损失一条生命',1900)
        elif tick==23:
            assert game.get('STATUS')==4 and game.get('ALIVE')==0
            capture('消灭全部敌军，获胜',3000)
        else:capture('发射炮弹' if tick in (5,14,18) else '炮弹推进，敌军移动',450)
    game.click('RESTART');capture('RESTART：保留最高分',1700)
    assert game.get('BEST')==210 and game.get('LIVES')==3
    game.click('START');game.click('DOWN');capture('向基地转向，移动被阻挡',1300)
    game.click('FIRE','STEP')
    assert game.get('STATUS')==3 and game.get('CAUSE')==2 and game.get('BASEHP')==0
    capture('误伤基地也会失败',2400)
    game.click('RESTART');capture('重新开始，基地和砖墙恢复',1700)
    frames[0].save(ROOT/'build/tank-demo.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=True)
    (ROOT/'build/demo-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    game.render(ROOT/'build/panel.png')
    print('Native campaign demo complete:',len(frames),'frames,',sum(durations),'ms',flush=True)


if __name__=='__main__':
    J=start();code=0
    try:demonstrate(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
