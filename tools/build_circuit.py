"""Attach the tank application and peripherals to the original forwarding CPU."""
import copy
import json
import xml.etree.ElementTree as E
from rv32 import build
from java_bridge import start,finish,ROOT


def generate(J):
    words,labels=build(ROOT)
    project=E.parse(ROOT/'original/cpu21-riscv.circ').getroot()
    loader=J.JClass('com.cburch.logisim.file.Loader')(None)
    loader.openLogisimFile(J.java.io.File(str(ROOT/'cpu_reference.circ')))
    factories={};libs={}
    groups={'0':['Pin','Tunnel','Constant','Bit Extender','Splitter','Probe'],
            '1':['AND Gate','OR Gate','NOT Gate'],'2':['Multiplexer'],
            '3':['Comparator','Adder'],'4':['Register','D Flip-Flop'],
            '5':['Button'],'6':['Text']}
    for number,names in groups.items():
        for library in loader.getBuiltin().getLibraries():
            for name in names:
                tool=library.getTool(name)
                if tool is not None:factories[name]=tool.getFactory();libs[name]=number
    library=loader.loadJarLibrary(J.java.io.File(str(ROOT/'tank-display.jar')),'tankio.TankDisplayLibrary')
    factories['Tank Battle Display']=library.getTool('Tank Battle Display').getFactory();libs['Tank Battle Display']='9'
    E.SubElement(project,'lib',name='9',desc='jar#tank-display.jar#tankio.TankDisplayLibrary')
    Loc=J.JClass('com.cburch.logisim.data.Location')
    def point(x,y):return f'({x},{y})'
    def comp(c,name,x,y,**attrs):
        el=E.SubElement(c,'comp',lib=libs[name],name=name,loc=point(x,y))
        factory=factories[name];aset=factory.createAttributeSet()
        for key,value in attrs.items():
            E.SubElement(el,'a',name=key,val=str(value))
            attr=next(a for a in list(aset.getAttributes()) if str(a.getName())==key)
            aset.setValue(attr,attr.parse(str(value)))
        native=factory.createComponent(Loc.create(x,y),aset)
        return [(int(e.getLocation().getX()),int(e.getLocation().getY()),int(e.getWidth().getWidth())) for e in native.getEnds()]
    def tunnel(c,end,label):
        x,y,width=end;comp(c,'Tunnel',x,y,width=width,label=label,facing='east')
    def const(c,end,value):
        x,y,width=end;comp(c,'Constant',x,y,width=width,value=hex(value&((1<<width)-1)))
    def wire(c,p,q):E.SubElement(c,'wire',{'from':point(*p[:2]),'to':point(*q[:2])})
    def text(c,x,y,value,size=13):comp(c,'Text',x,y,text=value,font=f'SansSerif plain {size}',halign='left')
    def gate(c,x,y,name,inputs,out):
        e=comp(c,name,x,y,width=1,inputs=2,size=30,facing='east')
        tunnel(c,e[0],out)
        for pin,label in zip(e[1:],inputs):tunnel(c,pin,label)
    def compare(c,x,y,width,left,right,out):
        e=comp(c,'Comparator',x,y,width=width,mode='unsigned')
        tunnel(c,e[0],left);const(c,e[1],right);tunnel(c,e[3],out)

    core=copy.deepcopy(project.findall('circuit')[8]);core.set('name','TankCore')
    core.find("a[@name='circuit']").set('val','TankCore');project.append(core)
    for el in core.findall('comp'):
        if el.get('name')=='Pin':
            a={v.get('name'):v.get('val') for v in el.findall('a')}
            if a.get('output')=='true':el.set('name','Probe')
            else:
                el.set('name','Constant')
                for child in list(el):el.remove(child)
                E.SubElement(el,'a',name='width',val=a.get('width','1'));E.SubElement(el,'a',name='value',val='0x0')
        if el.get('name')=='Button' and el.get('loc')=='(50,50)':
            el.set('name','Pin');el.set('lib','0')
            for child in list(el):el.remove(child)
            for k,v in {'facing':'east','output':'false','width':'1','tristate':'false','label':'RESET'}.items():E.SubElement(el,'a',name=k,val=v)
            tunnel(core,(50,50,1),'Tank.Reset')
        if el.get('name')=='ROM':
            el.find("a[@name='contents']").text='addr/data: 10 32\n'+'\n'.join(f'{w:08x}' for w in words)+'\n'
        if el.get('name')=='Tunnel' and el.get('loc')=='(1610,1010)':el.find("a[@name='label']").set('val','Tank.RamWrite')
    for w in list(core.findall('wire')):
        if {w.get('from'),w.get('to')}=={'(1720,930)','(1850,930)'}:core.remove(w)
    tunnel(core,(1720,930,32),'Tank.RamData');tunnel(core,(1850,930,32),'Tank.ReadData')
    key=(2800,100,10);period=(2800,160,32);level=(2800,220,2);bullet=(2800,280,2)
    for end,name in [(key,'KEYS'),(period,'PERIOD'),(level,'LEVEL'),(bullet,'BULLET')]:
        comp(core,'Pin',*end[:2],width=end[2],output='false',tristate='false',facing='east',label=name)
        tunnel(core,end,'Tank.'+name)
    compare(core,7000,100,32,'MEM.AluResult',0x70c,'Tank.AckAddress')
    gate(core,7100,160,'AND Gate',['Tank.AckAddress','MemWrite'],'Tank.AckWrite')
    raw=comp(core,'Splitter',7000,320,facing='east',fanout=10,incoming=10,appear='center',**{f'bit{i}':str(i) for i in range(10)})
    ack=comp(core,'Splitter',7200,320,facing='east',fanout=10,incoming=32,appear='center',**{f'bit{i}':str(i) if i<10 else 'none' for i in range(32)})
    pending=comp(core,'Splitter',7400,320,facing='west',fanout=10,incoming=10,appear='center',**{f'bit{i}':str(i) for i in range(10)})
    tunnel(core,raw[0],'Tank.KEYS');tunnel(core,ack[0],'MDin');tunnel(core,pending[0],'Tank.Pending')
    for i in range(10):
        tunnel(core,raw[i+1],f'Raw.{i}');tunnel(core,ack[i+1],f'Ack.{i}');tunnel(core,pending[i+1],f'Pending.{i}')
        y=550+i*160
        gate(core,7100,y,'AND Gate',[f'Ack.{i}','Tank.AckWrite'],f'Clear.{i}')
        gate(core,7200,y+60,'OR Gate',[f'Clear.{i}','Tank.Reset'],f'Reset.{i}')
        ff=comp(core,'D Flip-Flop',7400,y,trigger='rising',enable='false')
        const(core,ff[0],1);tunnel(core,ff[1],f'Pending.{i}');tunnel(core,ff[3],f'Reset.{i}');const(core,ff[4],0);tunnel(core,ff[5],f'Raw.{i}')
    e=comp(core,'Bit Extender',2920,100,in_width=10,out_width=32,type='zero')
    tunnel(core,e[0],'Tank.Keys32');tunnel(core,e[1],'Tank.Pending')
    e=comp(core,'Bit Extender',2920,220,in_width=2,out_width=32,type='zero')
    tunnel(core,e[0],'Tank.Level32');tunnel(core,e[1],'Tank.LEVEL')
    e=comp(core,'Bit Extender',2920,280,in_width=2,out_width=32,type='zero')
    tunnel(core,e[0],'Tank.Bullet32');tunnel(core,e[1],'Tank.BULLET')
    e=comp(core,'Register',3100,180,width=32,trigger='rising',Select='low')
    tunnel(core,e[0],'Tank.Cycles');tunnel(core,e[1],'Tank.NextCycles');tunnel(core,e[2],'CLK');tunnel(core,e[3],'Tank.Reset');const(core,e[4],1)
    e=comp(core,'Adder',3040,280,width=32)
    tunnel(core,e[0],'Tank.Cycles');const(core,e[1],1);tunnel(core,e[2],'Tank.NextCycles');const(core,e[3],0)

    fields=[(0x800+4*i,f'FB{i:02d}') for i in range(32)]
    hud=['STATUS','SCORE','LIVES','ALIVE','CAUSE','BASEHP','TICK','BEST','FRAME','UPGRADE','PICKUP','ITEMS','ARMOR1','ARMOR2','USES','POS1','POS2']
    fields += [(0x740+4*i,name) for i,name in enumerate(hud)]
    reads=[(0x700,'Tank.Keys32'),(0x704,'Tank.Cycles'),(0x708,'Tank.PERIOD'),(0x710,'Tank.Level32'),(0x714,'Tank.Bullet32')]
    outputs=[]
    for i,(addr,name) in enumerate(fields):
        x,y=3100+(i//12)*700,440+(i%12)*150
        compare(core,x-200,y,32,'MEM.AluResult',addr,'Select.'+name)
        gate(core,x-100,y+60,'AND Gate',['Select.'+name,'MemWrite'],'Write.'+name)
        e=comp(core,'Register',x,y,width=32,trigger='rising',Select='low',label='Stage '+name)
        tunnel(core,e[0],'Stage.'+name);tunnel(core,e[1],'MDin');tunnel(core,e[2],'CLK');tunnel(core,e[3],'Tank.Reset');tunnel(core,e[4],'Write.'+name)
        reads.append((addr,'Stage.'+name))
        visible='Stage.'+name
        if name!='FRAME':
            e=comp(core,'Register',x+240,y,width=32,trigger='rising',Select='low',label='Display '+name)
            visible='Display.'+name;tunnel(core,e[0],visible);tunnel(core,e[1],'Stage.'+name);tunnel(core,e[2],'CLK');tunnel(core,e[3],'Tank.Reset');tunnel(core,e[4],'Write.FRAME')
        pin=(x+360,y,32);comp(core,'Pin',pin[0],pin[1],width=32,output='true',facing='west',label=name);tunnel(core,pin,visible)
        outputs.append((name,pin))
    e=comp(core,'Splitter',6800,240,facing='east',fanout=1,incoming=32,appear='center',**{f'bit{i}':'none' if i<8 else '0' for i in range(32)})
    tunnel(core,e[0],'MEM.AluResult');tunnel(core,e[1],'Tank.Page')
    compare(core,6800,100,24,'Tank.Page',7,'Tank.Page7');compare(core,6800,180,24,'Tank.Page',8,'Tank.Page8')
    gate(core,6900,400,'OR Gate',['Tank.Page7','Tank.Page8'],'Tank.IsIO')
    e=comp(core,'NOT Gate',6900,460,width=1,size=20,facing='east');tunnel(core,e[1],'Tank.IsIO');tunnel(core,e[0],'Tank.NotIO')
    gate(core,6900,520,'AND Gate',['Tank.NotIO','MemWrite'],'Tank.RamWrite')
    const(core,(5800,250,32),0);tunnel(core,(5800,250,32),'Tank.Zero');prev='Tank.Zero'
    for i,(addr,value) in enumerate(reads):
        x,y=6000,350+i*100;select=f'ReadSelect.{i}';out=f'ReadMux.{i}'
        compare(core,x-100,y,32,'MEM.AluResult',addr,select)
        e=comp(core,'Multiplexer',x,y,width=32,select=1,enable='false',selloc='tr',facing='east')
        tunnel(core,e[0],prev);tunnel(core,e[1],value);tunnel(core,e[2],select);tunnel(core,e[3],out);prev=out
    e=comp(core,'Multiplexer',6400,300,width=32,select=1,enable='false',selloc='tr',facing='east')
    tunnel(core,e[0],'Tank.RamData');tunnel(core,e[1],prev);tunnel(core,e[2],'Tank.IsIO');tunnel(core,e[3],'Tank.ReadData')

    appearance=E.SubElement(core,'appear')
    E.SubElement(appearance,'rect',x='60',y='90',width='340',height='530',fill='#e8f2ee',stroke='#31574c')
    for y,value in [(260,'RISC-V'),(285,'5-stage CPU'),(310,'Tank Battle')]:E.SubElement(appearance,'text',x='220',y=str(y),**{'font-size':'16','text-anchor':'middle'}).text=value
    def port(pin,x,y,name,output=False):
        size=10 if output else 8
        E.SubElement(appearance,'circ-port',pin=f'{pin[0]},{pin[1]}',x=str(x-size//2),y=str(y-size//2),width=str(size),height=str(size))
        E.SubElement(appearance,'text',x=str(x-8 if output else x+8),y=str(y-5),**{'font-size':'9','text-anchor':'end' if output else 'start'}).text=name
    port(key,60,150,'KEYS');port(period,60,230,'PERIOD');port(level,60,310,'LEVEL');port(bullet,60,350,'BULLET');port((50,50,1),60,430,'RESET')
    positions={}
    for i,(name,pin) in enumerate(outputs):
        y=100+i*10 if i<32 else 430+(i-32)*10
        port(pin,400,y,name,True);positions[name]=(640,350+y-100,32)
    E.SubElement(appearance,'circ-anchor',x='197',y='97',width='6',height='6',facing='east')
    main=E.Element('circuit',name='TankBattle');E.SubElement(main,'a',name='circuit',val='TankBattle')
    E.SubElement(main,'comp',name='TankCore',loc='(440,350)')
    project.insert(list(project).index(project.findall('circuit')[0]),main);project.find('main').set('name','TankBattle')
    text(main,80,65,'坦克世界大战 · 自制 RISC-V CPU 团队项目',22)
    text(main,80,100,'消灭全部敌军获胜；生命耗尽或基地被毁则失败。',14)
    text(main,80,130,'方向键：移动/转向    FIRE：射击    PAUSE：暂停/恢复    RESTART：重开',12)
    text(main,80,160,'绿色玩家 / 红色敌军 / 橙色砖墙可破坏 / 灰色钢墙不可破坏 / 金色基地',12)
    for i,name in enumerate(['UP','RIGHT','DOWN','LEFT','START','PAUSE','RESTART','FIRE','STEP','USE']):
        x,y=110,230+i*50
        e=comp(main,'Button',x,y,facing='east',label=name,labelloc='west',color='#74d6aa')
        wire(main,e[0],(180,y));tunnel(main,(180,y,1),f'K{i}')
    e=comp(main,'Splitter',230,400,facing='west',fanout=10,incoming=10,appear='center',**{f'bit{i}':str(i) for i in range(10)})
    tunnel(main,e[0],'Keys')
    for i,end in enumerate(e[1:]):comp(main,'Tunnel',end[0],end[1],width=1,label=f'K{i}',facing='east',labelfont='SansSerif plain 8')
    tunnel(main,(300,400,10),'Keys')
    for y,width,label,signal in [(740,1,'MANUAL 0/1','Manual'),(800,2,'SPEED 0/1/2/3','Speed'),(860,2,'LEVEL 0/1/2 (RESTART)','Level'),(920,2,'BULLET 0/2=normal,1=fast,3=slow','Bullet')]:
        e=comp(main,'Pin',200,y,width=width,output='false',tristate='false',facing='east',label=label)
        wire(main,e[0],(260,y));tunnel(main,(260,y,width),signal)
    tunnel(main,(300,560,2),'Level')
    tunnel(main,(300,600,2),'Bullet')
    e=comp(main,'Multiplexer',250,1020,width=32,select=2,enable='false',selloc='tr',facing='east')
    for pin,value in zip(e[:4],[8192,4096,2048,1024]):const(main,pin,value)
    tunnel(main,e[4],'Speed');tunnel(main,e[5],'AutoPeriod')
    e=comp(main,'Multiplexer',250,480,width=32,select=1,enable='false',selloc='tr',facing='east')
    tunnel(main,e[0],'AutoPeriod');const(main,e[1],0);tunnel(main,e[2],'Manual');wire(main,e[3],(300,480))
    e=comp(main,'Button',230,680,facing='east',label='CPU RESET',labelloc='west',color='#ff9292');wire(main,e[0],(300,680))
    screen=comp(main,'Tank Battle Display',1000,350)
    for i in range(32):wire(main,positions[f'FB{i:02d}'],screen[i])
    for i,name in enumerate(n for n in hud if n!='FRAME'):wire(main,positions[name],screen[32+i])
    wire(main,positions['FRAME'],(800,760));comp(main,'Probe',800,760,facing='west',radix='10unsigned',label='FRAME',labelloc='north')
    text(main,1000,970,'开启仿真时钟，然后按 START。MANUAL=1 可用 STEP 推进战斗。',12)
    text(main,1000,1000,'手动模式下 FIRE 发射后，按 STEP 推进炮弹与敌方逻辑。',12)
    text(main,1000,1060,'LEVEL 0/1/2：训练 2 辆 / 进阶 4 辆 / 困难 6 辆，切换后按 RESTART。',12)
    text(main,1000,1030,'每消灭一辆敌军 +100；玩家打掉一块砖墙 +10。',12)
    text(main,1000,1090,'星形道具：移动拾取，USE 激活。一级增加弹药，二级增强伤害；满级后修复生命。',12)
    E.indent(project,space='  ')
    (ROOT/'tank.circ').write_bytes(E.tostring(project,encoding='UTF-8',xml_declaration=True))
    (ROOT/'build/symbols.json').write_text(json.dumps(labels,indent=2),encoding='utf-8')
    print(f'Built tank.circ with {len(words)} instructions; original CPU preserved.')


if __name__=='__main__':
    J=start();code=0
    try:generate(J)
    except BaseException:
        import traceback;traceback.print_exc();code=1
    finally:finish(J,code)
