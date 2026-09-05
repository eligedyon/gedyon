#!/usr/bin/env python3
"""GEDYON daily workouts — every day of the 45-week build, Sep 3 2026 ramp-in + Sep 7 2026 – Jul 18 2027."""
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DARK = colors.HexColor('#14141E'); GREY = colors.HexColor('#666677')
GOLD = colors.HexColor('#B08D2B'); LIGHT = colors.HexColor('#F4F2EC')
DELOAD_BG = colors.HexColor('#E8EEF6'); TEST_BG = colors.HexColor('#F3E9D2')
PHASE_TINT = {1: colors.HexColor('#EAF3EA'), 2: colors.HexColor('#E8F0F8'), 3: colors.HexColor('#F3EEE2'),
              4: colors.HexColor('#F6EAE4'), 5: colors.HexColor('#F0E8F4'), 6: colors.HexColor('#FBE9EC')}
PHASE_ACCENT = {1: colors.HexColor('#2E7D46'), 2: colors.HexColor('#2C5F94'), 3: colors.HexColor('#9A7B1E'),
                4: colors.HexColor('#B0562A'), 5: colors.HexColor('#6C4A9E'), 6: colors.HexColor('#B02A3C')}
PHASE_NAME = {1:'REBUILD',2:'BASE',3:'BUILD',4:'THRESHOLD',5:'SHARPEN',6:'RACE'}

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, textColor=DARK, spaceAfter=2, alignment=0)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], fontSize=9.5, textColor=GREY, spaceAfter=8)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], fontSize=8.0, leading=10.2, textColor=DARK)
CELLW = ParagraphStyle('CELLW', parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')
NOTE = ParagraphStyle('NOTE', parent=styles['Normal'], fontSize=8.5, textColor=GREY, leading=11.5, spaceAfter=6)

doc = SimpleDocTemplate('GEDYON-daily-workouts-45wk.pdf', pagesize=letter,
                        leftMargin=0.55*inch, rightMargin=0.55*inch, topMargin=0.55*inch, bottomMargin=0.5*inch)
story = []
start = date(2026, 9, 7)

# ── tiers: paces assuming each gate is passed at the earliest week ──
TIERS = {
 'T1': dict(easy='9:30-10:15', tempo='7:35-7:50', k='7:38-7:53', test='7:25-7:30', hill='8-10',
            wu='5min @ 10:45 shuffle, 5min @ 10:00, last 3-4min @ 9:30', cd='10:30-11:00', flt='10:15+'),
 'T2': dict(easy='9:15-10:00', tempo='7:20-7:35', k='7:25-7:40', test='7:05-7:20', hill='10-12',
            wu='5min @ 10:30 shuffle, 5min @ 9:45, last 3-4min @ 9:15', cd='10:15-10:45', flt='10:00+'),
 'T3': dict(easy='9:00-9:45',  tempo='7:05-7:20', k='7:10-7:25', test='6:55-7:10', hill='12-14',
            wu='5min @ 10:15 shuffle, 5min @ 9:30, last 3-4min @ 9:00', cd='10:00-10:30', flt='9:45+'),
 'T4': dict(easy='8:45-9:30',  tempo='6:55-7:10', k='6:58-7:12', test='6:45-7:00', hill='12-15',
            wu='5min @ 10:00 shuffle, 5min @ 9:15, last 3-4min @ 8:45', cd='9:45-10:15', flt='9:30+'),
 'T5': dict(easy='8:30-9:15',  tempo='6:45-7:00', k='6:48-7:02', test='6:40-6:55', hill='10-12',
            wu='5min @ 9:45 shuffle, 5min @ 9:00, last 3-4min @ 8:30', cd='9:30-10:00', flt='9:15+'),
 'T6': dict(easy='8:30-9:15',  tempo='6:40-6:55', k='6:43-6:57', test='race results', hill='8-10',
            wu='5min @ 9:45 shuffle, 5min @ 9:00, last 3-4min @ 8:30', cd='9:30-10:00', flt='9:15+'),
}
def STRIDES(n):
    return '%dx20s — build to mile effort, relaxed · walk 60-90s between' % n
SETTLE = '2min walk — never jump into rep 1'
SUPP_AM = 'creatine 5g + omega-3 + D3/K2 with breakfast'
SUPP_PM = 'magnesium malate before bed'
DRILLS = 'A-skip 2x20m · B-skip 2x20m · high knees 2x20m — crisp, before strides'
def CORE_A(ph):
    if ph <= 2:
        return 'dead bug 3x12 · plank 3x45s · side plank 3x30s/side · hollow hold 3x20s · glute bridge 3x15 (~10min)'
    if ph <= 4:
        return 'dead bug 3x15 · plank 3x60s · side plank w/ leg lift 3x30s/side · hollow rocks 3x15 · single-leg glute bridge 3x12/side (~12min)'
    return 'plank 3x45s · side plank 3x30s · dead bug 3x12 · glute bridge 3x12 — maintain, do not chase burn in race season (~8min)'
def CORE_B(ph):
    if ph <= 2:
        return 'Copenhagen 3x20s/side · bird dog 3x10/side · plank shoulder taps 3x12 · single-leg glute bridge 3x10/side (~10min)'
    if ph <= 4:
        return 'Copenhagen 3x30s/side · bird dog 3x12/side · plank taps 3x16 · single-leg RDL reach 3x8/side (bodyweight) (~12min)'
    return 'Copenhagen 3x20s/side · bird dog 3x10 · plank taps 3x12 — maintain (~8min)'
def POWER(ph):
    if ph <= 1:
        return 'pogo hops 2x20 · A-skips 2x20m — landing stiffness first, height later'
    if ph <= 3:
        return 'pogo hops 3x20 · bounding 2x30m · squat jumps 3x5 (max intent, full 90s rest) — power lives in FRESH reps'
    if ph <= 5:
        return 'bounding 3x30m · single-leg hops 2x10/side · squat jumps 3x5 — explosive, never grinding'
    return 'pogo hops 2x20 · 2x30m bounding — touch it, keep it, spend nothing'
DUR = 'single-leg calf raises 3x15/side (slow down, drive up) · monster walks or hip airplanes 2x10 — 5min, protects shins/achilles/hips'
def SUPPS(kind):
    if kind == 'quality':
        return SUPP_AM + ' · whey 1 scoop within 30min after the session · tart cherry tonight · ' + SUPP_PM
    if kind == 'long':
        return SUPP_AM + ' · electrolyte complex in the bottle + carbs during (90min+) · whey after · tart cherry tonight · ' + SUPP_PM
    if kind == 'race':
        return SUPP_AM + ' · electrolytes with warm-up · whey after · tart cherry tonight · ' + SUPP_PM
    return SUPP_AM + ' · whey wherever protein is short (target ~140g/day) · ' + SUPP_PM
def L(*parts):
    return '<br/>'.join('<b>%s</b>  %s' % (a, b) for a, b in parts)
def tier(w):
    if w <= 4: return 'T1'
    if w <= 10: return 'T2'
    if w <= 18: return 'T3'
    if w <= 26: return 'T4'
    if w <= 34: return 'T5'
    return 'T6'
def phase_of(w):
    return 1 if w<=6 else 2 if w<=14 else 3 if w<=22 else 4 if w<=30 else 5 if w<=38 else 6
vol_targets = {1:(24,32), 2:(32,40), 3:(40,46), 4:(46,52), 5:(48,52), 6:(38,46)}
def volume(w):
    ph = phase_of(w); lo, hi = vol_targets[ph]
    ph_starts = {1:1,2:7,3:15,4:23,5:31,6:39}; ph_len = {1:6,2:8,3:8,4:8,5:8,6:7}[ph]
    frac = (w - ph_starts[ph]) / max(1, ph_len - 1)
    base = lo + (hi-lo)*min(1.0, frac)
    if ph == 6: base = hi - (hi-lo)*frac
    if w % 4 == 0: base *= 0.70
    return round(base)
races = {10:'5K TIME TRIAL', 18:'INDOOR OPENER (3k/mile)', 22:'INDOOR RACE #2', 26:'2-MILE TT / INDOOR CHAMPS',
         30:'OUTDOOR OPENER', 33:'TUNE-UP RACE', 36:'TUNE-UP RACE (T6 gate)', 39:'CHAMPIONSHIP RACE #1',
         42:'GOAL RACE #1', 45:'GOAL RACE #2 — SEASON FINALE'}

def reps1000(w):
    ph = phase_of(w)
    base = {1:4, 2:5, 3:6, 4:7, 5:6, 6:5}[ph]
    wib = ((w-1) % 4)  # 0,1,2 build → +0,+1,+1 ; deload handled separately
    n = base + (1 if wib >= 1 else 0) + (1 if wib >= 2 else 0)
    return min(n, 9)

def day_rows(w):
    T = TIERS[tier(w)]; ph = phase_of(w); d = (w % 4 == 0); race = races.get(w)
    v = volume(w)
    ez = round(v*0.15); ezpm = max(2, round(v*0.10)); lng = round(v*0.28)
    n = reps1000(w) if not d else max(3, reps1000(w)//2)
    wib = ((w-1) % 4) + 1
    hills = T['hill'] if not d else '6'
    rows = []
    def add(dayname, sess, detail):
        rows.append((dayname, sess, detail))
    add('Mon', 'EASY DOUBLE + CORE', L(
        ('AM', '%dmi @ %s — talk test: full sentences' % (ez, T['easy'])),
        ('DRILLS', DRILLS), ('STRIDES', STRIDES(6)),
        ('PM', '%dmi shake-out @ %s' % (ezpm, T['cd'])),
        ('CORE', CORE_A(ph)),
        ('SUPPS', SUPPS('easy'))))
    if race and w >= 30:
        add('Tue', 'SHARP + LIGHT', L(
            ('WU', '2mi progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '4-6x400m @ race pace'),
            ('REST', '2-3min full walk/stand'),
            ('CD', '1mi @ %s' % T['cd']),
            ('SUPPS', SUPPS('quality'))))
    elif ph == 4:
        add('Tue', 'DOUBLE THRESHOLD (Ingebrigtsen day)', L(
            ('AM', 'WU 2mi progressive + strides + settle · %dx1000m @ %s, HR 148-156 · 60s standing rest · CD 1mi' % (max(4, n-1), T['k'])),
            ('GAP', '6-8 hours between sessions · eat + nap if possible'),
            ('PM', 'WU 1.5mi easy · 8-10x400m @ threshold effort (HR under 158) · 30s rest · CD 1mi'),
            ('RULE', 'BOTH sessions controlled — the magic is two sub-threshold doses, never two races. GREEN days only; yellow = AM only; red = easy'),
            ('DURABILITY', DUR),
            ('SUPPS', SUPPS('quality'))))
    else:
        add('Tue', 'THRESHOLD 1000s', L(
            ('WU', '2mi progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '%dx1000m @ %s · HR 148-158, NEVER above 160 (Norwegian control: lactate ~2.5-3.5 — if you could not do 3 more reps, you went too fast)' % (n, T['k'])),
            ('REST', '%s STANDING — timed, no jogging' % ('90s' if d else '60-75s')),
            ('CD', '1.5mi slow @ %s' % T['cd']),
            ('RULE', 'threshold is a faucet, not a race — control today buys tomorrow'),
            ('DURABILITY', DUR),
            ('SUPPS', SUPPS('quality'))))
    if race and w >= 30:
        wed = ('STRIDES ONLY', L(('RUN', '%dmi easy @ %s' % (max(2, ez-1), T['easy'])), ('STRIDES', STRIDES(6)), ('RULE', 'race week — nothing that costs anything'),
            ('SUPPS', SUPPS('easy'))))
    elif ph >= 5:
        wed = ('SPEED 300s', L(
            ('WU', '1.5mi progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '8x300m @ 1500-race effort — form first'),
            ('REST', '3min full walk/stand'),
            ('CD', '1.5mi @ %s' % T['cd']),
            ('SUPPS', SUPPS('quality'))))
    elif ph >= 3 and wib % 2 == 0:
        wed = ('200s + EASY', L(
            ('WU', '1mi building 10:00 to %s' % T['easy'].split('-')[0]),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '8-10x200m fast-relaxed — mile effort, never straining'),
            ('REST', 'WALK back the full 200m'),
            ('THEN', '%dmi easy @ %s' % (max(2, ez-1), T['easy'])),
            ('POWER', POWER(ph)),
            ('SUPPS', SUPPS('quality'))))
    else:
        wed = ('HILLS + EASY', L(
            ('WU', '0.8mi jog @ %s + 2 strides · %s' % (T['cd'], SETTLE)),
            ('MAIN', '%sx80m hill @ MAX — drive knees, lean in' % hills),
            ('REST', 'WALK all the way down · +30s stand if still breathing hard'),
            ('THEN', '%dmi easy @ %s' % (max(2, ez-1), T['easy'])),
            ('RULE', '8 fresh reps beat 12 tired ones — this is the strength session'),
            ('POWER', POWER(ph)),
            ('SUPPS', SUPPS('quality'))))
    add('Wed', wed[0], wed[1])
    add('Thu', 'EASY DOUBLE + CORE', L(
        ('AM', '%dmi @ %s — conversational' % (ez, T['easy'])),
        ('DRILLS', DRILLS), ('STRIDES', STRIDES(6)),
        ('PM', '%dmi @ %s' % (ezpm, T['cd'])),
        ('CORE', CORE_B(ph)),
        ('SUPPS', SUPPS('easy'))))
    if d:
        add('Fri', 'TEMPO TEST (fresh legs)', L(
            ('WU', '2mi progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('TEST', '20min @ %s · HR cap 162 — hold effort, pace is the readout' % T['test']),
            ('CD', '1mi slow @ %s — 10min max' % T['cd']),
            ('GATE', 'PASS = next tier unlocks · yellow: test Sat · red: skip, retest next block'),
            ('SUPPS', SUPPS('quality'))))
    elif race:
        add('Fri', 'PRE-RACE SHAKEOUT', L(
            ('RUN', '20min easy @ %s' % T['easy']),
            ('STRIDES', STRIDES(4)),
            ('PREP', 'kit out · hydrate · early night'),
            ('SUPPS', SUPPS('easy'))))
    elif wib % 2 == 1:
        add('Fri', 'FARTLEK', L(
            ('WU', '1mi building 10:00 to %s' % T['easy'].split('-')[0]),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '30-40min: 3min hard @ %s / 90s FLOAT @ %s (slow jog!)' % (T['tempo'], T['flt'])),
            ('SURGE', 'at 90s of each hard bout: +15s/mi faster for 30s, then back'),
            ('FINISH', 'last 400m fast'),
            ('CD', '0.5-1mi @ %s' % T['cd']),
            ('SUPPS', SUPPS('quality'))))
    else:
        add('Fri', 'TEMPO', L(
            ('WU', '2mi progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('MAIN', '20-30min @ %s · HR cap 160 — break the cap, slow down' % T['tempo']),
            ('CLOSER', 'final 60s: lift to ~15s/mi faster, tall and composed (Kerr rule: finish everything strong, never strained)'),
            ('CD', '1mi slow @ %s — 10min flush, done, eat within 30min' % T['cd']),
            ('DURABILITY', DUR),
            ('SUPPS', SUPPS('quality'))))
    if race:
        add('Sat', race, L(
            ('WU', '12-15min progressive — %s' % T['wu']),
            ('STRIDES', STRIDES(4)), ('SETTLE', SETTLE),
            ('RACE', 'the result IS the tier gate — log it in the app'),
            ('CD', '10-15min @ %s' % T['cd']),
            ('SUPPS', SUPPS('race'))))
    else:
        if ph >= 2 and wib == 2:
            add('Sat', 'PROGRESSION LONG (Ethiopian thirds)', L(
                ('RUN', '%dmi in thirds — Bekele/Kejelcha style' % lng),
                ('THIRD 1', 'slow end of easy (%s) — patience, boringly slow' % T['easy'].split('-')[1]),
                ('THIRD 2', 'fast end of easy (%s)' % T['easy'].split('-')[0]),
                ('THIRD 3', 'steady, ~40s/mi faster than easy · HR may reach 155, no higher'),
                ('RULE', 'the speed-up is gradual and controlled — teach the body to run fast on tired legs, never sprint the end'),
                ('FUEL', 'at 45min on 90min+ runs'),
                ('SUPPS', SUPPS('long'))))
        else:
            parts = [('RUN', '%dmi @ %s · HR under 145' % (lng, T['easy'])),
                     ('START', 'slow end of the band — settle in before drifting faster')]
            if ph >= 2: parts.append(('FINISH', 'last 10-15min may lift to steady (~45s/mi faster) IF green'))
            parts.append(('FUEL', 'at 45min on 90min+ runs'))
            parts.append(('RULE', 'no strides, no surges, no racing the last mile — base is built with patience (Bekele ran his easy runs EASY)'))
            parts.append(('SUPPS', SUPPS('long')))
            add('Sat', 'LONG RUN', L(*parts))
    add('Sun', 'ACTIVE RECOVERY', L(
        ('MOVE', '30-40min walk/jog · HR under 125 · no pace floor'),
        ('ROLL', '15min — calves, quads, IT band'),
        ('MOBILITY', '10min'),
        ('SUPPS', SUPPS('easy'))) + ('<br/><b>NOTE</b>  weigh-in tomorrow AM' if not race else '<br/><b>NOTE</b>  post-race: extra easy, assess, log'))
    return rows

story.append(Paragraph('GEDYON — DAILY WORKOUTS, ALL 45 WEEKS', H1))
story.append(Paragraph('<b>THE COACHING DNA</b> — every element traces to a system that produced champions: '
    '<b>Lananna/Thomas</b> (championship patience: drills + strides daily, peak in July not October) · '
    '<b>Ingebrigtsen/Norwegian</b> (threshold CONTROLLED at lactate 2.5-3.5, reps always in the bank; double-threshold only in P4, only green days, only earned) · '
    '<b>Kerr/Mackey</b> (power work, composed fast closers on everything) · '
    '<b>Kejelcha/Ethiopian</b> (progression longs — slow start, strong finish, speed on tired legs) · '
    '<b>Bekele</b> (massive patient aerobic base, hills as strength, form never sacrificed). '
    'The thread that unites all five: EASY DAYS ARE INSULTINGLY EASY, hard days are controlled, and nobody races training.', SUB))
story.append(Paragraph('Companion to the 45-Week Build. Every day written out. Paces shown assume each tier gate is PASSED at its earliest week — '
                       'if a gate isn\'t passed yet, keep using your current tier\'s paces for every session (the structure stays identical). '
                       'WHOOP gates every day: yellow = one quality max + HR caps, red = easy/rest and the session moves. '
                       'Updated Fri Sep 4, 2026 — ramp-in below (Fri-Sun), Week 1 starts Mon Sep 7. SUPPS lines use YOUR cabinet. STRENGTH SYSTEM: core Mon/Thu (A/B circuits, progress by phase) · POWER after Wed hills/speed (plyos at max intent, full rest — this is where lean speed comes from) · DURABILITY 5min after Tue/Fri quality (calves/hips — the anti-breakdown work). All bodyweight: powerful and cut, never bulky. The rule: power reps are always FRESH and explosive; core is done to quality, not to burnout.', SUB))


# ── Execution guide: how to run every piece ────────────────────────
story.append(Paragraph('HOW TO RUN EVERY PIECE — THE DETAILS THAT MAKE IT WORK', ParagraphStyle('gh', parent=H1, fontSize=14, spaceBefore=6)))
story.append(Paragraph('Same workout, different execution = different training. Two habits to break, named directly: '
    '<b>(1) the 20-minute one-pace warm-up/cool-down</b> — a long slog at a single moderate pace is junk volume that tires you before the work and blunts recovery after it; warm-ups are short and PROGRESSIVE, cool-downs are short and SLOW. '
    '<b>(2) jumping straight into the work</b> — the first rep on cold legs runs on the wrong energy system, spikes HR, and makes every following rep worse. The strides at the end of the warm-up ARE the ignition — they are not optional decoration.', NOTE))
guide_rows = [[Paragraph(x, CELLW) for x in ['PIECE', 'HOW FAST', 'HOW LONG', 'REST / STRUCTURE', 'WHY IT MATTERS']]]
for g in [
    ('WARM-UP (quality days)',
     'PROGRESSIVE: first 5min at recovery shuffle (10:30+), middle at slow-easy (10:00), last 5min at the FAST end of easy (9:30). Never one flat pace.',
     '12-15min (2mi) — not 20+. More is not better; it is withdrawal from the workout.',
     'Finish with the prescribed strides, take 2min of walking/standing AFTER the last stride, THEN start rep 1.',
     'Raises muscle temp and opens the aerobic system without spending it. The 2min gap lets HR settle so rep 1 starts honest.'),
    ('STRIDES',
     'Build through each one: jog the first 5s, fast by 10s, at ~mile race effort (NOT sprint) for the last 10s. Tall, quick, relaxed — if your face or shoulders tighten, it is too fast.',
     '20 seconds each, 6x on easy days, 4x pre-workout.',
     '60-90s WALK between — full recovery, never jog-loop straight into the next one.',
     'Recruits fast-twitch fibers and sharpens mechanics with zero fatigue cost — but only if each one is rested and relaxed.'),
    ('REST BETWEEN 1000m REPS',
     'STANDING or slow walk. Hands on hips, breathe. Not a jog.',
     '60-75s (build weeks) / 90s (deloads). Time it — cutting rest short turns threshold work into a race.',
     'Start the next rep when the clock says, not when you feel ready (that is what the rest length is calibrated for).',
     'Threshold reps only work at threshold. Short rest or hot reps push lactate past the zone and you train the wrong system.'),
    ('REST BETWEEN HILL REPS',
     'Walk down. Fully. No jogging the descent.',
     'The full walk-down (~90s-2min). If you are still breathing hard at the bottom, stand another 30s.',
     'Every rep at MAX effort requires full recovery — 8 great reps beat 12 tired ones.',
     'Hills train power. Power needs a fresh nervous system every rep — tired hills are just slow intervals with injury risk.'),
    ('FARTLEK FLOATS',
     'The 90s float is a SLOW jog (10:00+), not a steady run. The surge is only a surge if the float is real.',
     '90s between 3min hard bouts.',
     'Hard bouts at tempo effort; the mid-surge gear change is 30s FASTER within the bout, then back to hard — never all-out.',
     'Teaches gear changes for laps 2-3 of the mile. Floats too fast = one long moderate run = nothing trained.'),
    ('COOL-DOWN',
     'SLOW. Recovery shuffle, 10:30+/mi, slower than feels dignified. It is a flush, not a run.',
     '10min (1-1.5mi) after quality. NOT 20min — after a hard session, extra time on your feet is cost, not fitness.',
     'Optional: 5min walk at the end. Then eat within 30min.',
     'Clears metabolites and starts recovery. Running it at easy pace (9:30) quietly adds load to your hardest days — the opposite of its job.'),
    ('EASY RUNS',
     '9:30-10:15 (current tier). Talk test: full sentences OUT LOUD. HR 125-140.',
     'As prescribed — no bonus miles.',
     'No structure needed — this is the one place "just go run" is correct.',
     'The engine is built here, at low cost. Run these too fast and Tuesday/Friday degrade — the classic self-sabotage loop.'),
]:
    guide_rows.append([Paragraph('<b>%s</b>' % g[0], CELL), Paragraph(g[1], CELL), Paragraph(g[2], CELL), Paragraph(g[3], CELL), Paragraph(g[4], CELL)])
gt = Table(guide_rows, colWidths=[0.95*inch, 1.85*inch, 1.25*inch, 1.6*inch, 1.75*inch], repeatRows=1)
gt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK), ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
                        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#DDDAD0')), ('VALIGN',(0,0),(-1,-1),'TOP'),
                        ('TOPPADDING',(0,0),(-1,-1),3.5), ('BOTTOMPADDING',(0,0),(-1,-1),3.5),
                        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4)]))
story.append(gt)
story.append(Paragraph('WU/CD paces above are for your CURRENT tier (T1). When a tier gate is passed, shift them with it: warm-up always ends at the fast end of that tier\'s easy band, cool-down is always ~60s/mi slower than easy. The quality-day template never changes: progressive WU -> strides -> 2min settle -> work -> short slow CD.', NOTE))
story.append(PageBreak())

# ── Ramp-in Sep 3-6 ────────────────────────────────────────────────
ramp = [
 ('Fri Sep 4', 'TEMPO — first gate attempt', L(('WU','2mi progressive - 10:45 to 9:30'),('STRIDES',STRIDES(4)),('SETTLE',SETTLE),('GREEN','20min @ 7:25-7:30 under HR 165 - the T2 gate'),('YELLOW','7:40-7:50 capped at 160 instead'),('CD','1mi slow'),('SUPPS', SUPPS('quality')))),
 ('Sat Sep 5', 'LONG RUN', L(('RUN','7mi @ 9:45-10:30 · HR under 145'),('RULE','no strides, no surges'),('SUPPS', SUPPS('long')))),
 ('Sun Sep 6', 'ACTIVE RECOVERY', L(('MOVE','30-40min walk/jog · HR under 125'),('ROLL','15min foam roll + 10min mobility'),('SUPPS', SUPPS('easy')))),
]
rows = [[Paragraph(x, CELLW) for x in ['DAY', 'SESSION', 'WORKOUT']]]
for r in ramp:
    rows.append([Paragraph('<b>%s</b>' % r[0], CELL), Paragraph('<b>%s</b>' % r[1], CELL), Paragraph(r[2], CELL)])
t = Table(rows, colWidths=[0.85*inch, 1.5*inch, 5.05*inch], repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK), ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
                       ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#DDDAD0')), ('VALIGN',(0,0),(-1,-1),'TOP'),
                       ('TOPPADDING',(0,0),(-1,-1),3.5), ('BOTTOMPADDING',(0,0),(-1,-1),3.5),
                       ('LEFTPADDING',(0,0),(-1,-1),5), ('RIGHTPADDING',(0,0),(-1,-1),5)]))
story.append(KeepTogether([Paragraph('RAMP-IN · SEP 4-6', ParagraphStyle('h', parent=CELLW, fontSize=10, textColor=GOLD, spaceBefore=6, spaceAfter=3)), t]))
story.append(Spacer(1, 8))

# ── 45 weeks of days ───────────────────────────────────────────────
for w in range(1, 46):
    ph = phase_of(w); d = (w % 4 == 0); race = races.get(w)
    a = start + timedelta(weeks=w-1)
    hdr_txt = 'WEEK %d · %s · P%d %s · %s · ~%d mi · %s%s' % (
        w, a.strftime('%b %d') + ' - ' + (a+timedelta(days=6)).strftime('%b %d, %Y'),
        ph, PHASE_NAME[ph], tier(w) + ' paces', volume(w),
        'DELOAD + TEST' if d else 'BUILD %d/3' % (((w-1)%4)+1),
        (' · ' + race) if race else '')
    hdr_style = ParagraphStyle('wh%d'%w, parent=CELLW, fontSize=9.5)
    hdr_tbl = Table([[Paragraph(hdr_txt, hdr_style)]], colWidths=[7.4*inch])
    hdr_tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), PHASE_ACCENT[ph]),
                                 ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
                                 ('LEFTPADDING',(0,0),(-1,-1),6)]))
    rows = []
    day_data = day_rows(w)
    for i, (dn, sess, detail) in enumerate(day_data):
        dt = a + timedelta(days=i)
        rows.append([Paragraph('<b>%s %s</b>' % (dn, dt.strftime('%m/%d')), CELL),
                     Paragraph('<b>%s</b>' % sess, CELL), Paragraph(detail, CELL)])
    t = Table(rows, colWidths=[0.85*inch, 1.55*inch, 5.0*inch])
    cmds = [('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#DDDAD0')), ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),5), ('RIGHTPADDING',(0,0),(-1,-1),5)]
    for i, (dn, sess, detail) in enumerate(day_data):
        if 'TEST' in sess or 'RACE' in sess.upper() or 'TT' in sess:
            bg = TEST_BG
        elif dn in ('Tue','Fri') or sess.startswith('HILLS') or sess.startswith('SPEED') or sess.startswith('200'):
            bg = PHASE_TINT[ph]
        elif d:
            bg = DELOAD_BG
        else:
            bg = colors.white
        cmds.append(('BACKGROUND',(0,i),(-1,i),bg))
    t.setStyle(TableStyle(cmds))
    story.append(KeepTogether([hdr_tbl, t, Spacer(1, 7)]))

story.append(Paragraph('Every day above obeys the standing rules of the 45-Week Build sheet: WHOOP gates the day, HR caps gate the session, '
                       'tier gates gate the paces. If a week breaks, resume where the calendar says — never stack missed quality.', NOTE))
doc.build(story)
print('PDF written')
