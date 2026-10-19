#!/usr/bin/env python3
"""
Checks a study studio's kit.json before you build anything from it.

    python3 scripts/validate_kit.py kit.json
    python3 scripts/validate_kit.py kit.json --calc-dir calcs/ --files-dir kit/

Errors (exit code 1) are things that would break a lesson: a chip flying from
a cell that doesn't exist, a step revealing a chart layer that isn't there, a
blank that never gets filled, a quiz answer out of range. Warnings are worth a
look: with --calc-dir, every number in a lesson's captions is compared with
what that lesson's calc_<lesson-id>.py prints (plus the numbers already in its
facts table and working), so a typo in a caption shows up here.

Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

LINE_KINDS = {'eq', 'head', 'note', 'total', 'formula'}
LAYER_KINDS = {'line', 'points', 'hline', 'vline', 'segments', 'bars', 'area', 'label', 'box'}
LAYER_FIELDS = {
    'line': ['points'], 'points': ['points'], 'hline': ['y'], 'vline': ['x'],
    'segments': ['segments'], 'bars': ['bars'], 'area': ['points'], 'label': ['x', 'y', 'text'],
    'box': ['y', 'h', 'min', 'q1', 'med', 'q3', 'max'],
}
TONES = {'info', 'hl', 'ok', 'bad', 'muted'}
FORMATS = {'n', '$', '%', 'd1', 'd2'}
CELL = re.compile(r'^(\d+)\.(\d+)$')
NUM = re.compile(r'(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?')


def canon(tok):
    t = tok.replace(',', '').rstrip('.')
    if re.fullmatch(r'\d+\.\d+', t):
        t = t.rstrip('0').rstrip('.')
    t = t.lstrip('0') or '0'
    return '0' + t if t.startswith('.') else t


def numbers(text):
    return {canon(m.group(0)) for m in NUM.finditer(str(text or ''))}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f'{where}: {msg}')

    def warn(self, where, msg):
        self.warnings.append(f'{where}: {msg}')


def is_list(v):
    return isinstance(v, list)


def check_lesson(L, r, calc_dir):
    lid = L.get('id', '?')
    where = f'lesson {lid}'
    table = L.get('table') or {}
    headers, rows = table.get('headers'), table.get('rows')
    if not is_list(headers) or not is_list(rows):
        r.err(where, 'table needs "headers" and "rows" lists')
        return
    ncols = len(headers)
    for k, row in enumerate(rows):
        if not is_list(row) or len(row) != ncols:
            r.warn(where, f'table row {k} has {len(row) if is_list(row) else "no"} cells for {ncols} headers')

    def cell_ok(ref):
        m = CELL.match(str(ref))
        if not m:
            return False
        rr, cc = int(m.group(1)), int(m.group(2))
        return rr < len(rows) and is_list(rows[rr]) and cc < len(rows[rr])

    line_ids, slots, terms = set(), {}, set()
    for line in L.get('lines') or []:
        i = line.get('id')
        if i in line_ids:
            r.err(where, f'duplicate line id {i!r}')
        line_ids.add(i)
        if line.get('kind', 'eq') not in LINE_KINDS:
            r.err(where, f'line {i!r}: unknown kind {line.get("kind")!r}')
        for p in line.get('parts') or []:
            if isinstance(p, str):
                continue
            if isinstance(p, dict) and 's' in p:
                if p['s'] in slots:
                    r.err(where, f'slot {p["s"]!r} appears twice')
                slots[p['s']] = i
            elif isinstance(p, dict) and 'f' in p:
                terms.add(p['f'])
            else:
                r.err(where, f'line {i!r}: a part must be text, {{"s": slot}} or {{"f": term, "text": ...}}')

    layers = set()
    chart = L.get('chart')
    if chart:
        for axis in ('x', 'y'):
            a = chart.get(axis) or {}
            if not (isinstance(a.get('min'), (int, float)) and isinstance(a.get('max'), (int, float)) and a['min'] < a['max']):
                r.err(where, f'chart axis {axis} needs numeric min < max')
            if a.get('fmt', 'n') not in FORMATS:
                r.err(where, f'chart axis {axis}: fmt must be one of {sorted(FORMATS)}')
        for ly in chart.get('layers') or []:
            i = ly.get('id')
            if i in layers:
                r.err(where, f'duplicate chart layer {i!r}')
            layers.add(i)
            kind = ly.get('kind')
            if kind not in LAYER_KINDS:
                r.err(where, f'layer {i!r}: unknown kind {kind!r}')
                continue
            for field in LAYER_FIELDS[kind]:
                if field not in ly:
                    r.err(where, f'layer {i!r} ({kind}) is missing {field!r}')
            if ly.get('tone', 'info') not in TONES:
                r.err(where, f'layer {i!r}: tone must be one of {sorted(TONES)}')

    steps = L.get('steps') or []
    if not steps:
        r.err(where, 'has no steps')
    filled = set()
    for n, st in enumerate(steps, 1):
        sw = f'{where} step {n}'
        if not isinstance(st.get('say'), str) or not st['say'].strip():
            r.err(sw, 'needs a "say" caption')
        if 'dur' in st and not (isinstance(st['dur'], (int, float)) and st['dur'] > 0):
            r.err(sw, '"dur" must be a positive number of milliseconds')
        for key in ('hl', 'strike'):
            for ref in st.get(key) or []:
                if not cell_ok(ref):
                    r.err(sw, f'{key} cell {ref!r} is not in the table')
        for ref in (st.get('cells') or {}):
            if not cell_ok(ref):
                r.err(sw, f'cells override {ref!r} is not in the table')
        for i in st.get('show') or []:
            if i not in line_ids:
                r.err(sw, f'show: no line {i!r}')
        for i in st.get('focus') or []:
            if i not in slots and i not in terms:
                r.err(sw, f'focus: no slot or term {i!r}')
        for i in st.get('reveal') or []:
            if i not in layers:
                r.err(sw, f'reveal: no chart layer {i!r}')
        for f in st.get('fly') or []:
            src, dst = str(f.get('from', '')), f.get('to')
            if src.startswith('@'):
                if src[1:] not in slots:
                    r.err(sw, f'fly from {src!r}: no such slot')
                elif src[1:] not in filled:
                    r.err(sw, f'fly from {src!r}: that slot is not filled yet')
            elif not cell_ok(src):
                r.err(sw, f'fly from {src!r}: not a table cell ("row.col")')
            if dst not in slots:
                r.err(sw, f'fly to {dst!r}: no such slot')
            filled.add(dst)
        for s in (st.get('calc') or {}):
            if s not in slots:
                r.err(sw, f'calc {s!r}: no such slot')
            filled.add(s)
    for s in slots:
        if s not in filled:
            r.err(where, f'slot {s!r} is never filled')

    if calc_dir:
        script = os.path.join(calc_dir, f'calc_{lid}.py')
        if not os.path.exists(script):
            r.warn(where, f'no {os.path.basename(script)} to check caption numbers against')
            return
        try:
            out = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            r.err(where, f'{os.path.basename(script)} timed out')
            return
        if out.returncode != 0:
            r.err(where, f'{os.path.basename(script)} failed: {out.stderr.strip()[-300:]}')
            return
        known = numbers(out.stdout) | numbers(json.dumps(table)) | numbers(json.dumps(L.get('lines')))
        for n, st in enumerate(steps, 1):
            for num in sorted(numbers(st.get('say')) - known):
                if not (num.isdigit() and int(num) <= 12):
                    r.warn(f'{where} step {n}', f'caption number {num} is not in the calc output, the table or the working')


def main():
    ap = argparse.ArgumentParser(description='Check a study studio kit.json.')
    ap.add_argument('kit')
    ap.add_argument('--calc-dir', help='folder with calc_<lesson-id>.py scripts')
    ap.add_argument('--files-dir', help='folder the downloads are relative to')
    args = ap.parse_args()

    r = Report()
    try:
        kit = json.load(open(args.kit, encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        print(f'ERROR {args.kit} does not parse: {e}')
        return 1
    for key in ('meta', 'start', 'lessons', 'practice', 'quiz', 'memory'):
        if key not in kit:
            r.err('kit', f'missing "{key}"')

    meta = kit.get('meta') or {}
    for key in ('code', 'name', 'assessment', 'lessonOrder'):
        if key not in meta:
            r.err('meta', f'missing "{key}"')

    lessons = kit.get('lessons') or []
    ids = [L.get('id') for L in lessons]
    for i in set(ids):
        if ids.count(i) > 1:
            r.err('lessons', f'duplicate lesson id {i!r}')
    order = meta.get('lessonOrder') or []
    if set(order) != set(ids) or len(order) != len(set(order)):
        r.err('meta', 'lessonOrder must list every lesson id exactly once')
    for L in lessons:
        check_lesson(L, r, args.calc_dir)
    lesson_ids = set(ids)

    start = kit.get('start') or {}
    for item in start.get('likely') or []:
        if item.get('lesson') and item['lesson'] not in lesson_ids:
            r.err('start.likely', f'no lesson {item["lesson"]!r}')
    scope = start.get('scope') or {}
    if not is_list(scope.get('in')):
        r.warn('start.scope', 'no "in" list: say what the test covers')

    pids = set()
    for p in kit.get('practice') or []:
        w = f'practice {p.get("id", "?")}'
        if p.get('id') in pids:
            r.err(w, 'duplicate id')
        pids.add(p.get('id'))
        parts = p.get('parts') or []
        if not parts:
            r.err(w, 'has no parts')
        for k, part in enumerate(parts, 1):
            if not part.get('q') or not part.get('answer'):
                r.err(w, f'part {k} needs "q" and "answer"')
            if part.get('lesson') and part['lesson'] not in lesson_ids:
                r.err(w, f'part {k}: no lesson {part["lesson"]!r}')

    qids = set()
    for q in kit.get('quiz') or []:
        w = f'quiz {q.get("id", "?")}'
        if q.get('id') in qids:
            r.err(w, 'duplicate id')
        qids.add(q.get('id'))
        opts = q.get('options')
        if not is_list(opts) or len(opts) < 2:
            r.err(w, 'needs at least two options')
        elif not (isinstance(q.get('answer'), int) and 0 <= q['answer'] < len(opts)):
            r.err(w, f'answer must be an option index from 0 to {len(opts) - 1}')
        if q.get('lesson') and q['lesson'] not in lesson_ids:
            r.err(w, f'no lesson {q["lesson"]!r}')

    memory = kit.get('memory') or {}
    for key in ('formulas', 'cards', 'tables', 'traps'):
        if not is_list(memory.get(key)):
            r.warn('memory', f'no "{key}" list')

    if args.files_dir:
        for d in kit.get('downloads') or []:
            for rel in [d.get('file')] + list(d.get('previews') or []):
                if rel and not os.path.exists(os.path.join(args.files_dir, rel)):
                    r.err('downloads', f'{rel} is missing from {args.files_dir}')

    for e in r.errors:
        print('ERROR', e)
    for w in r.warnings:
        print('WARN ', w)
    steps = sum(len(L.get('steps') or []) for L in lessons)
    status = 'OK' if not r.errors else 'FAIL'
    print(f'{status}: {len(lessons)} lessons, {steps} steps, {len(kit.get("practice") or [])} practice questions, '
          f'{len(kit.get("quiz") or [])} quiz questions; {len(r.errors)} errors, {len(r.warnings)} warnings')
    return 1 if r.errors else 0


if __name__ == '__main__':
    sys.exit(main())
