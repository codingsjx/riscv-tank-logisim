"""Operate the actual Logisim presentation circuit and inspect its output pins."""
from java_bridge import ROOT


class NativeTank:
    def __init__(self,J):
        self.J=J
        loader=J.JClass('com.cburch.logisim.file.Loader')(None)
        self.file=loader.openLogisimFile(J.java.io.File(str(ROOT/'tank.circ')))
        self.project=J.JClass('com.cburch.logisim.proj.Project')(self.file)
        self.circuit=self.file.getCircuit('TankBattle')
        self.state=J.JClass('com.cburch.logisim.circuit.CircuitState')(self.project,self.circuit)
        self.prop=self.state.getPropagator();self.prop.propagate()
        def label(c):
            return next((str(c.getAttributeSet().getValue(a)) for a in c.getAttributeSet().getAttributes() if str(a.getName())=='label'),'')
        self.buttons={label(c):c for c in self.circuit.getNonWires() if str(c.getFactory().getName())=='Button'}
        self.inputs={label(c):c for c in self.circuit.getNonWires() if str(c.getFactory().getName())=='Pin'}
        core=next(c for c in self.circuit.getNonWires() if str(c.getFactory().getName())=='TankCore')
        self.core=self.state.getData(core)
        self.outputs={label(c):c for c in self.core.getCircuit().getNonWires() if str(c.getFactory().getName())=='Pin'}
        self.V=J.JClass('com.cburch.logisim.data.Value');self.W=J.JClass('com.cburch.logisim.data.BitWidth')
        self.Single=J.JClass('com.cburch.logisim.instance.InstanceDataSingleton')

    def pin(self,prefix,value):
        c=next(c for name,c in self.inputs.items() if name.startswith(prefix))
        width=int(c.getEnds().get(0).getWidth().getWidth())
        c.getFactory().setValue(self.state.getInstanceState(c),self.V.createKnown(self.W.create(width),value))
        self.state.markComponentAsDirty(c);self.prop.propagate()

    def button(self,name,pressed):
        c=self.buttons[name]
        self.state.setData(c,self.Single(self.V.TRUE if pressed else self.V.FALSE))
        self.state.markComponentAsDirty(c);self.prop.propagate()

    def get(self,name):
        v=self.core.getValue(self.outputs[name].getLocation())
        if not v.isFullyDefined():raise AssertionError(f'{name}={v}')
        return int(v.toIntValue())&0xffffffff

    def tiles(self):
        banks=[self.get(f'FB{i:02d}') for i in range(32)]
        return [(banks[i//8]>>((i%8)*4))&15 for i in range(256)]

    def stats(self):
        return {name:self.get(name) for name in ['STATUS','SCORE','LIVES','ALIVE','CAUSE','BASEHP','TICK','BEST','FRAME']}

    def cycles(self,n):
        for _ in range(n*2):
            self.prop.tick();self.prop.propagate()
            if self.prop.isOscillating():raise AssertionError('Circuit oscillation')

    def until(self,predicate,limit=16000):
        for i in range(limit):
            if predicate():return i
            self.cycles(1)
        raise TimeoutError(f'CPU did not complete frame: {self.stats()}')

    def click(self,*names,atomic=False):
        before=self.get('FRAME')
        snapshot=self.tiles()+[self.get(n) for n in ['STATUS','SCORE','LIVES','ALIVE','CAUSE','BASEHP','TICK','BEST']]
        for name in names:self.button(name,True)
        for name in names:self.button(name,False)
        for _ in range(16000):
            if self.get('FRAME')!=before:break
            if atomic:
                current=self.tiles()+[self.get(n) for n in ['STATUS','SCORE','LIVES','ALIVE','CAUSE','BASEHP','TICK','BEST']]
                assert current==snapshot,'Partial frame appeared before commit'
            self.cycles(1)
        else:raise TimeoutError('Short button click was lost')
        self.cycles(80)

    def reset(self):
        self.pin('MANUAL',1);self.button('CPU RESET',True);self.cycles(5);self.button('CPU RESET',False)
        elapsed=self.until(lambda:self.get('FRAME')==1)
        print('Native CPU initialized in',elapsed,'cycles:',self.stats(),flush=True)

    def render(self,path):
        J=self.J
        image=J.JClass('java.awt.image.BufferedImage')(1460,1040,1)
        g=image.createGraphics();g.setColor(J.JClass('java.awt.Color').WHITE);g.fillRect(0,0,1460,1040)
        context=J.JClass('com.cburch.logisim.comp.ComponentDrawContext')(J.JClass('javax.swing.JPanel')(),self.circuit,self.state,g,g)
        self.circuit.draw(context,J.java.util.Collections.emptySet())
        J.JClass('javax.imageio.ImageIO').write(image,'png',J.java.io.File(str(path)));g.dispose()


def render_native_board(game,path,size=640):
    """Use the display library's exact drawing function to magnify native tiles."""
    J=game.J
    display=next(c for c in game.circuit.getNonWires() if str(c.getFactory().getName())=='Tank Battle Display')
    factory=display.getFactory()
    image=J.JClass('java.awt.image.BufferedImage')(size,size,1);g=image.createGraphics();g.scale(size/320.,size/320.)
    for i,tile in enumerate(game.tiles()):factory.paintTile(g,(i%16)*20,(i//16)*20,tile)
    J.JClass('javax.imageio.ImageIO').write(image,'png',J.java.io.File(str(path)));g.dispose()
