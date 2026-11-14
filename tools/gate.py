"""Fail the build if the run's checks found anything unexpected (reads out/run.log, written by ./run.sh).

Expected: on the CrowPanel deck (d8k) only the two known contacts, the panel passing the snap bumps on its way into the display
front (panel-in) and the outer FaderBuddy boards' rear corners on the plate's way in (plate-in ... faderbuddy). Screen-less decks:
no contacts at all. Every variant: all four feet fully supported, no page errors, no wall cut through below the plate.
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = open(os.path.join(ROOT, 'out', 'run.log')).read()
problems, seen = [], []
for block in re.split(r'^===== ', log, flags=re.M)[1:]:
    v = block.split(' =====', 1)[0].strip(); seen.append(v); body = block.split('\n', 1)[1]
    for line in body.splitlines():
        if 'page error' in line: problems.append(f'{v}: {line.strip()}')
        m = re.match(r'(\S+)\s.*?crossings\s+(\d+) depth ([\d.]+).*?\| inside\s+(\d+)', line.strip())
        if m and (int(m.group(2)) or int(m.group(4))):
            known = v == 'd8k' and (m.group(1).startswith('panel-in') or (m.group(1).startswith('plate-in') and 'faderbuddy' in m.group(1)))
            if not known: problems.append(f'{v}: contact {line.strip()}')
        m = re.match(r'(x_\S+) vol (-?[\d.]+)', line.strip())   # two printed parts overlapping
        if m and float(m.group(2)) > 0.01: problems.append(f'{v}: parts overlap {m.group(1)} ({m.group(2)} mm³)')
        m = re.match(r'wallsLost vol ([\d.]+)', line.strip())
        if m and float(m.group(1)) > 0.05 and v != 'd8k': problems.append(f'{v}: wall cut through below the plate ({m.group(1)} mm³)')
    feet = re.search(r'^feet: .*', body, flags=re.M)
    if not feet or not feet.group(0).rstrip().endswith('OK'): problems.append(f'{v}: feet check {feet.group(0) if feet else "missing"}')
print(f'checked {len(seen)} variants: {" ".join(seen)}')
if problems: print('\n'.join(problems)); sys.exit(1)
print('all checks as expected')
