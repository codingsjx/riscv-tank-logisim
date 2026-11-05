package tankio;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import com.cburch.logisim.data.Attribute;
import com.cburch.logisim.data.Bounds;
import com.cburch.logisim.data.Value;
import com.cburch.logisim.instance.InstanceFactory;
import com.cburch.logisim.instance.InstancePainter;
import com.cburch.logisim.instance.InstanceState;
import com.cburch.logisim.instance.Port;

/** Tile and HUD output only. Movement, AI, collision and scoring run on the CPU. */
public final class TankDisplay extends InstanceFactory {
    public TankDisplay(){
        super("Tank Battle Display");
        setAttributes(new Attribute[0],new Object[0]);
        setOffsetBounds(Bounds.create(0,-40,410,490));
        Port[] ports=new Port[40];
        for(int i=0;i<32;i++) ports[i]=new Port(0,i*10,Port.INPUT,32);
        for(int i=32;i<40;i++) ports[i]=new Port(0,330+(i-32)*10,Port.INPUT,32);
        setPorts(ports);
    }
    @Override public void propagate(InstanceState state){}

    private static int read(InstancePainter p,int index){
        Value value=p.getPort(index);return value.isFullyDefined()?value.toIntValue():0;
    }
    private static void tank(Graphics graphics,int x,int y,int direction,boolean enemy){
        Graphics2D g=(Graphics2D)graphics.create();
        g.translate(x,y);g.rotate(direction*Math.PI/2,10,10);
        g.setColor(enemy?new Color(92,42,42):new Color(34,74,57));
        g.fillRect(2,3,5,15);g.fillRect(13,3,5,15);
        g.setColor(new Color(165,175,171));
        for(int i=4;i<18;i+=4){g.fillRect(2,i,5,1);g.fillRect(13,i,5,1);}
        g.setColor(enemy?new Color(233,83,75):new Color(72,212,128));
        g.fillRect(6,4,8,13);g.fillOval(6,6,8,8);
        g.setColor(enemy?new Color(255,189,155):new Color(171,255,202));
        g.fillRect(9,0,3,11);g.dispose();
    }
    public static void paintTile(Graphics g,int x,int y,int tile){
        g.setColor(new Color(25,43,44));g.fillRect(x,y,20,20);
        g.setColor(new Color(30,50,50));g.drawRect(x,y,19,19);
        if(tile==1){
            g.setColor(new Color(173,89,50));g.fillRect(x+1,y+1,18,18);
            g.setColor(new Color(101,57,41));
            for(int k=6;k<20;k+=6)g.drawLine(x+1,y+k,x+18,y+k);
            g.drawLine(x+10,y+1,x+10,y+6);g.drawLine(x+5,y+7,x+5,y+12);g.drawLine(x+13,y+13,x+13,y+18);
        }else if(tile==2){
            g.setColor(new Color(116,137,148));g.fillRect(x+1,y+1,18,18);
            g.setColor(new Color(178,196,201));g.drawRect(x+3,y+3,13,13);
            g.fillRect(x+3,y+3,2,2);g.fillRect(x+15,y+15,2,2);
        }else if(tile==3){
            g.setColor(new Color(232,186,67));g.fillRect(x+3,y+6,14,12);
            g.fillRect(x+3,y+2,4,6);g.fillRect(x+13,y+2,4,6);
            g.setColor(new Color(94,69,26));g.fillRect(x+8,y+12,4,6);
        }else if(tile>=4&&tile<=11){tank(g,x,y,(tile-4)&3,tile>=8);
        }else if(tile==12||tile==13){
            g.setColor(tile==12?new Color(255,245,173):new Color(255,109,71));
            g.fillOval(x+7,y+7,6,6);
        }else if(tile==14||tile==15){
            g.setColor(new Color(242,103,41));
            g.fillPolygon(new int[]{x+2,x+8,x+10,x+13,x+19,x+14,x+16,x+10,x+5,x+6},
                          new int[]{y+5,y+6,y,y+6,y+4,y+11,y+18,y+15,y+19,y+11},10);
        }
    }
    @Override public void paintInstance(InstancePainter p){
        Graphics g=p.getGraphics();int x=p.getLocation().getX(),y=p.getLocation().getY();
        g.setColor(new Color(13,27,38));g.fillRoundRect(x+35,y-35,350,480,12,12);
        g.setColor(new Color(232,239,244));g.setFont(new Font("SansSerif",Font.BOLD,15));
        g.drawString("RISC-V TANK BATTLE",x+50,y-13);
        for(int row=0;row<16;row++)for(int col=0;col<16;col++){
            int packed=read(p,row*2+col/8);int tile=(packed>>>((col%8)*4))&15;
            paintTile(g,x+50+col*20,y+row*20,tile);
        }
        int status=read(p,32),score=read(p,33),lives=read(p,34),alive=read(p,35);
        int cause=read(p,36),base=read(p,37),tick=read(p,38),best=read(p,39);
        String text=status==0?"准备：按 START 开始":status==1?"战斗进行中":status==2?"已暂停":status==4?"胜利！敌军已全部消灭":cause==2?"失败：基地被毁":"失败：生命耗尽";
        g.setColor(status==3?new Color(255,122,105):status==4?new Color(94,233,163):new Color(235,212,128));
        g.setFont(new Font("SansSerif",Font.BOLD,14));g.drawString(text,x+50,y+350);
        g.setColor(new Color(219,231,238));g.setFont(new Font("SansSerif",Font.PLAIN,13));
        g.drawString("分数 "+score+"   生命 "+lives+"   剩余敌军 "+alive,x+50,y+378);
        g.drawString("基地 "+(base!=0?"完好":"损毁")+"   最高分 "+best,x+50,y+402);
        g.drawString("逻辑步数 "+tick+"   砖墙可破坏 / 钢墙不可破坏",x+50,y+426);
        p.drawPorts();
    }
}
