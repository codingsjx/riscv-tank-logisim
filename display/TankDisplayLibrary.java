package tankio;
import java.util.Arrays;
import java.util.List;
import com.cburch.logisim.tools.AddTool;
import com.cburch.logisim.tools.Library;
import com.cburch.logisim.tools.Tool;

public final class TankDisplayLibrary extends Library {
    private final List<Tool> tools=Arrays.<Tool>asList(new AddTool(new TankDisplay()));
    @Override public String getName(){return "TankDisplay";}
    @Override public List<? extends Tool> getTools(){return tools;}
}
