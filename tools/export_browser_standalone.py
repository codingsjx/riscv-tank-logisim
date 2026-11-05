"""Create a double-click playable HTML file, without a server or login."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'tank-play'
html=(ROOT/'dist/index.html').read_text(encoding='utf-8')
css=(ROOT/'dist/style.css').read_text(encoding='utf-8')
parts=[]
for name in ['rom.js','engine.js','app.js']:
 text=(ROOT/'dist'/name).read_text(encoding='utf-8')
 text='\n'.join(line for line in text.splitlines() if not line.startswith('import '))
 text=text.replace('export const ','const ').replace('export class ','class ')
 parts.append(text)
html=html.replace('<link rel="stylesheet" href="./style.css">','<style>'+css+'</style>')
html=html.replace('<script type="module" src="./app.js"></script>','<script>\n'+ '\n'.join(parts)+'\n</script>')
output=ROOT.parent/'坦克世界大战_点击试玩.html'
output.write_text(html,encoding='utf-8')
(Path(__file__).resolve().parents[1]/'浏览器试玩.html').write_text(html,encoding='utf-8')
print(output)
