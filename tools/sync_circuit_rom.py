"""Synchronize only the embedded TankCore ROM payload from build/tank.hex."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
circuit_path = ROOT / 'tank.circ'
rom_path = ROOT / 'build' / 'tank.hex'
source = circuit_path.read_text(encoding='utf-8')
hex_lines = rom_path.read_text(encoding='ascii').splitlines()
if not hex_lines or hex_lines[0] != 'v2.0 raw':
    raise SystemExit('Unexpected build/tank.hex header')
words = hex_lines[1:]
if not words or len(words) > 1024:
    raise SystemExit(f'Invalid ROM size: {len(words)} words')

core_match = re.search(r'<circuit\s+name="TankCore"[^>]*>.*?</circuit>', source, re.S)
if core_match is None:
    raise SystemExit('TankCore circuit not found')
core = core_match.group(0)
rom_pattern = re.compile(
    r'(<comp(?=[^>]*\blib="4")(?=[^>]*\bloc="\(460,860\)")'
    r'(?=[^>]*\bname="ROM")[^>]*>.*?<a\s+name="contents">)'
    r'(.*?)(</a>)',
    re.S,
)
rom_matches = list(rom_pattern.finditer(core))
if len(rom_matches) != 1:
    raise SystemExit(f'Expected one program ROM in TankCore, found {len(rom_matches)}')
old_payload = rom_matches[0].group(2)
old_words = old_payload.splitlines()[1:] if old_payload.startswith('addr/data: 10 32\n') else []
if len(old_words) != 889:
    raise SystemExit(f'Unexpected old TankCore ROM size: {len(old_words)}; refusing to overwrite')
new_payload = 'addr/data: 10 32\n' + '\n'.join(words) + '\n'
new_core = rom_pattern.sub(lambda m: m.group(1) + new_payload + m.group(3), core, count=1)
updated = source[:core_match.start()] + new_core + source[core_match.end():]
if updated == source:
    raise SystemExit('TankCore ROM payload was not changed')

# Parse before writing to catch malformed XML while preserving the rest of its formatting.
import xml.etree.ElementTree as ET
root = ET.fromstring(updated)
core_node = next(node for node in root.findall('circuit') if node.get('name') == 'TankCore')
rom_node = next(node for node in core_node.findall('comp') if node.get('name') == 'ROM' and node.get('loc') == '(460,860)')
contents = next(node for node in rom_node if node.get('name') == 'contents').text or ''
if len(contents.splitlines()) - 1 != len(words):
    raise SystemExit('Embedded ROM word count verification failed')
circuit_path.write_text(updated, encoding='utf-8', newline='')
print(f'Updated only TankCore ROM payload: {len(old_words)} -> {len(words)} words.')
