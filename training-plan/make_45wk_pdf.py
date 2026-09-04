#!/usr/bin/env python3
"""GEDYON 45-week macrocycle PDF — Sep 7, 2026 to Jul 18, 2027."""
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

GOLD = colors.HexColor('#B08D2B')
DARK = colors.HexColor('#14141E')
GREY = colors.HexColor('#666677')
GREEN = colors.HexColor('#1E7D46')
RED = colors.HexColor('#B02A3C')
AMBER = colors.HexColor('#B07A1E')
LIGHT = colors.HexColor('#F4F2EC')
DELOAD_BG = colors.HexColor('#E8EEF6')
TEST_BG = colors.HexColor('#F3E9D2')

PHASE_TINT = {1: colors.HexColor('#EAF3EA'), 2: colors.HexColor('#E8F0F8'), 3: colors.HexColor('#F3EEE2'),
              4: colors.HexColor('#F6EAE4'), 5: colors.HexColor('#F0E8F4'), 6: colors.HexColor('#FBE9EC')}
PHASE_ACCENT = {1: colors.HexColor('#2E7D46'), 2: colors.HexColor('#2C5F94'), 3: colors.HexColor('#9A7B1E'),
                4: colors.HexColor('#B0562A'), 5: colors.HexColor('#6C4A9E'), 6: colors.HexColor('#B02A3C')}
PHASE_NAME = {1:'REBUILD',2:'BASE',3:'BUILD',4:'THRESHOLD',5:'SHARPEN',6:'RACE'}


styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=21, textColor=DARK, spaceAfter=2, alignment=0)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], fontSize=9.5, textColor=GREY, spaceAfter=10)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=GOLD, spaceBefore=12, spaceAfter=4)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], fontSize=9, leading=12.5, textColor=DARK)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], fontSize=8.2, leading=10.6, textColor=DARK)
CELLW = ParagraphStyle('CELLW', parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')
NOTE = ParagraphStyle('NOTE', parent=BODY, fontSize=8.5, textColor=GREY, leading=11.5)

doc = SimpleDocTemplate('GEDYON-45-week-plan.pdf', pagesize=letter,
                        leftMargin=0.6*inch, rightMargin=0.6*inch, topMargin=0.55*inch, bottomMargin=0.5*inch)
story = []

story.append(Paragraph('GEDYON — THE 45-WEEK BUILD', H1))
story.append(Paragraph('Mon Sep 7, 2026 – Sun Jul 18, 2027 · Elias Gedyon · Boulder, CO · Mission: 2028 Olympic Trials. '
                       'This macrocycle starts from CURRENT fitness (165 lb, effective ~VDOT mid-40s) and earns its way up. '
                       '(Sep 3–6 is the ramp-in — follow the 12-day block sheet, then start Week 1 here.)', SUB))

# ── Phase map ──────────────────────────────────────────────────────
story.append(Paragraph('THE SIX PHASES', H2))
phases = [
    ('P1 · REBUILD', 'Wk 1–6', 'Sep 7 – Oct 18', 'Aerobic base + durability at honest paces. Weight work is here: 1 lb/wk. Hills = strength.', '24→32 mi'),
    ('P2 · BASE', 'Wk 7–14', 'Oct 19 – Dec 13', 'Volume climbs, threshold 1000s become weekly bread. First 5k time trial (wk 10) resets VDOT with real evidence.', '32→40 mi'),
    ('P3 · BUILD', 'Wk 15–22', 'Dec 14 – Feb 7', 'VO2 work enters (Wed hills become alternating hills/200s). Indoor race opportunities — every race feeds the engine number.', '40→46 mi'),
    ('P4 · THRESHOLD', 'Wk 23–30', 'Feb 8 – Apr 4', 'Norwegian double-threshold weeks (the doubles you asked about live HERE, earned). Peak volume. Outdoor season opens.', '46→52 mi'),
    ('P5 · SHARPEN', 'Wk 31–38', 'Apr 5 – May 30', 'Race-specific: mile/1500 pace work, tune-up races every 2–3 weeks. Volume holds, intensity peaks.', '~50 mi'),
    ('P6 · RACE', 'Wk 39–45', 'May 31 – Jul 18', 'Championship season. Taper cycles around goal races. Everything you built gets spent on purpose.', '38→45 mi'),
]
rows = [[Paragraph(x, CELLW) for x in ['PHASE', 'WEEKS', 'DATES', 'WHAT IT DOES', 'VOLUME']]]
for pi, p in enumerate(phases, start=1):
    pst = ParagraphStyle('P%d'%pi, parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')
    rows.append([Paragraph(p[0], pst), Paragraph(p[1], CELL), Paragraph(p[2], CELL), Paragraph(p[3], CELL), Paragraph(p[4], CELL)])
t = Table(rows, colWidths=[1.05*inch, 0.72*inch, 1.05*inch, 3.85*inch, 0.63*inch])
phase_col = [('BACKGROUND', (0,i), (0,i), PHASE_ACCENT[i]) for i in range(1,7)]
phase_row = [('BACKGROUND', (1,i), (-1,i), PHASE_TINT[i]) for i in range(1,7)]
t.setStyle(TableStyle(phase_col + phase_row + [
    ('BACKGROUND', (0,0), (-1,0), DARK),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(t)

# ── Pace ladder ────────────────────────────────────────────────────
story.append(Paragraph('THE PACE LADDER — GATED, NOT DATED', H2))
story.append(Paragraph('The engine of this plan: <b>every block is 3 weeks of building, then a deload week that ENDS with a fresh-legs tempo test</b> — '
                       '20 minutes at the next tier\'s pace, under the HR cap. Pass and the whole pace card moves up for the next block; '
                       'fail and you keep building at the current tier and retest in 4 weeks, having lost nothing. '
                       'Races and time trials count as tests too (they outrank them). Week numbers are the EARLIEST a tier may start — '
                       'the plan never asks for a pace you haven\'t proven.', NOTE))
ladder = [
    ('T1', 'now', 'Easy 9:30–10:15 · Tempo 7:35–7:50 · 1000s 7:38–7:53', 'Gate to T2: 20min @ 7:25–7:30 under HR 165 (green day)'),
    ('T2', 'wk 5+', 'Easy 9:15–10:00 · Tempo 7:20–7:35 · 1000s 7:25–7:40', 'Gate to T3: 5k time trial ≤ 22:30 (wk 10) or equivalent race'),
    ('T3', 'wk 11+', 'Easy 9:00–9:45 · Tempo 7:05–7:20 · 1000s 7:10–7:25 · 200s @ 40–42s', 'Gate to T4: 5k ≤ 21:15 or 20min tempo @ 6:55 under cap'),
    ('T4', 'wk 19+', 'Easy 8:45–9:30 · Tempo 6:55–7:10 · 1000s 6:58–7:12', 'Gate to T5: race result (indoor mile/3k) confirming VDOT +2'),
    ('T5', 'wk 27+', 'Easy 8:30–9:15 · Tempo 6:45–7:00 · 1000s 6:48–7:02 · race-pace 400s', 'Gate to T6: outdoor race, season opener'),
    ('T6', 'wk 35+', 'Easy 8:30–9:15 · Tempo 6:40–6:55 · full race-specific menu', 'Championship tier — race results drive everything'),
]
rows = [[Paragraph(x, CELLW) for x in ['TIER', 'EARLIEST', 'PACES', 'GATE TO ADVANCE']]]
for l in ladder:
    rows.append([Paragraph('<b>%s</b>' % l[0], CELL), Paragraph(l[1], CELL), Paragraph(l[2], CELL), Paragraph(l[3], CELL)])
t = Table(rows, colWidths=[0.5*inch, 0.68*inch, 3.6*inch, 2.52*inch])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DARK),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT]),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(t)

# ── Standing rules ─────────────────────────────────────────────────
story.append(Paragraph('STANDING RULES — ALL 45 WEEKS', H2))
for line in [
    '<b>Weekly rhythm:</b> Mon easy double + core · Tue quality (threshold) · Wed hills/speed + easy · Thu easy double + core · Fri quality (fartlek or threshold, alternating) · Sat long run · Sun active recovery.',
    '<b>The 4-week engine: build · build · build · deload+TEST.</b> Every 4th week (marked D) drops volume −30% and cuts reps in half — then Friday, on fresh legs, you run the 20-min tempo test at the next tier\'s pace. Deloads are where adaptation happens AND where progress gets proven — never skip one to "stay on pace."',
    '<b>WHOOP gates every day:</b> Green = as written. Yellow = one quality max, HR-capped, doubles lose their PM. Red = easy or rest, workout moves to next green day. (The app enforces this automatically.)',
    '<b>Effort beats pace, always.</b> Every quality session carries an HR cap. Breaking the cap to hit a pace is a failed session, not a brave one.',
    '<b>Weight:</b> 165 → ~150 by week 30, then HOLD through race season. ~0.7 lb/wk in P1–P3, fueled quality days always. Never cut on a quality or long day.',
    '<b>Doubles with two quality sessions</b> exist only in P4+, only on green days, only after T4 paces are unlocked. Until then every double is easy AM + easy PM.',
]:
    story.append(Paragraph(line, BODY)); story.append(Spacer(1, 3))

story.append(PageBreak())

# ── 45-week table ─────────────────────────────────────────────────
start = date(2026, 9, 7)  # Monday, week 1

def wk_dates(w):
    a = start + timedelta(weeks=w-1)
    b = a + timedelta(days=6)
    return '%s–%s' % (a.strftime('%b %d').replace(' 0', ' '), b.strftime('%b %d').replace(' 0', ' '))

def phase_of(w):
    if w <= 6: return 1
    if w <= 14: return 2
    if w <= 22: return 3
    if w <= 30: return 4
    if w <= 38: return 5
    return 6

# volume model: climbs +1.5/wk within phase bounds, deload = 70%
vol_targets = {1:(24,32), 2:(32,40), 3:(40,46), 4:(46,52), 5:(48,52), 6:(38,46)}
def volume(w):
    ph = phase_of(w)
    lo, hi = vol_targets[ph]
    ph_starts = {1:1, 2:7, 3:15, 4:23, 5:31, 6:39}
    ph_len = {1:6, 2:8, 3:8, 4:8, 5:8, 6:7}[ph]
    frac = (w - ph_starts[ph]) / max(1, ph_len - 1)
    base = lo + (hi - lo) * min(1.0, frac)
    if ph == 6:  # race season oscillates down toward races
        base = hi - (hi - lo) * frac
    if w % 4 == 0: base *= 0.70
    return int(round(base))

special = {
    10: ('TT',   '5K TIME TRIAL — resets VDOT with real evidence (T3 gate)'),
    18: ('RACE', 'Indoor opener (3k or mile) — rust-buster, no taper'),
    22: ('RACE', 'Indoor race #2 — T4 gate lives here'),
    26: ('TT',   '2-mile time trial or indoor championship race'),
    30: ('RACE', 'Outdoor season opener (T5 gate) — mini-taper this week'),
    33: ('RACE', 'Tune-up race (1500/5k)'),
    36: ('RACE', 'Tune-up race — T6 gate'),
    39: ('RACE', 'First championship-season race'),
    42: ('RACE', 'Goal race #1 — full taper week 41'),
    45: ('RACE', 'Season finale / goal race #2 — the year\'s report card'),
}

def tier_label(w):
    if w <= 4: return 'T1'
    if w <= 10: return 'T2*'
    if w <= 18: return 'T3*'
    if w <= 26: return 'T4*'
    if w <= 34: return 'T5*'
    return 'T6*'

def key_sessions(w):
    ph = phase_of(w)
    d = (w % 4 == 0)
    if w in special and special[w][0] in ('TT', 'RACE'):
        return 'Race/TT week: Tue light 1000s (60%%), Fri pre-race shakeout + strides, %s. Long run easy or moved after race.' % special[w][1].split(' — ')[0]
    if d:
        return 'DELOAD + TEST: Tue 1000s at 50%% reps · easy days · <b>Fri TEMPO TEST on fresh legs: 20min at the NEXT tier\'s pace, under the HR cap (green day; yellow = push test to Sat, red = skip, retest next block)</b> · Sat long −30%%.'
    if ph == 1:
        n = 4 + min(2, (w-1)//2)
        return 'Tue %d×1000m · Wed 8–10×80m hills · Fri 20–25min tempo or fartlek · Sat long %d–%d mi.' % (n, 6 + w//3, 7 + w//3)
    if ph == 2:
        n = 5 + min(3, (w-7)//2)
        return 'Tue %d×1000m · Wed 10–12×80m hills · Fri alternating fartlek / 20–30min tempo · Sat long %d–%d mi with steady finish.' % (n, 9, 11)
    if ph == 3:
        return 'Tue 6–8×1000m · Wed alternate hills / 8–10×200m @ T3 speed · Fri fartlek w/ gear-change surges · Sat long 11–13 mi, last 2 steady.'
    if ph == 4:
        return 'DOUBLE-THRESHOLD (green days only): Tue AM 5×1000m + PM 4×1000m sub-threshold · Wed hills · Fri tempo 25–30min · Sat long 12–14 mi.'
    if ph == 5:
        return 'Tue 1000s @ T5 · Wed 300s/400s at 1500-race pace · Fri tempo or pre-race · Sat long 10–12 mi easy. Races every 2–3 wks.'
    return 'Race-week pattern: Tue sharp 600s/400s (low volume) · Wed strides only · Fri shakeout · race Sat/Sun · recover, repeat.'

story.append(Paragraph('THE 45 WEEKS', H1))
story.append(Paragraph('Rhythm: 3 build weeks, then D = deload week ending in the Friday tempo test · TT/RACE weeks shaded gold · T* = pace tier IF its gate has been passed (otherwise stay on the tier you own). '
                       'Mileage is the green-week target — yellow/red days reduce it and that is correct, not a miss.', SUB))
leg_cells = []
for i in range(1, 7):
    leg_cells.append(Paragraph('P%d %s' % (i, PHASE_NAME[i]), ParagraphStyle('lg%d'%i, parent=CELL, textColor=colors.white, fontName='Helvetica-Bold', alignment=1)))
leg_cells.append(Paragraph('DELOAD+TEST', ParagraphStyle('lgd', parent=CELL, fontName='Helvetica-Bold', alignment=1)))
leg_cells.append(Paragraph('RACE / TT', ParagraphStyle('lgr', parent=CELL, fontName='Helvetica-Bold', alignment=1)))
lt = Table([leg_cells], colWidths=[0.92*inch]*6 + [1.05*inch, 0.85*inch])
lt.setStyle(TableStyle([('BACKGROUND', (i-1,0), (i-1,0), PHASE_ACCENT[i]) for i in range(1,7)] + [
    ('BACKGROUND', (6,0), (6,0), DELOAD_BG), ('BACKGROUND', (7,0), (7,0), TEST_BG),
    ('GRID', (0,0), (-1,-1), 0.5, colors.white),
    ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story.append(lt)
story.append(Spacer(1, 6))

hdr = [Paragraph(x, CELLW) for x in ['WK', 'DATES', 'PH', 'MI', 'TIER', 'KEY SESSIONS & NOTES']]
rows = [hdr]
row_styles = []
for w in range(1, 46):
    d = (w % 4 == 0)
    sp = special.get(w)
    note = key_sessions(w)
    if sp and sp[0] == 'TEST':
        note += ' · <b>%s</b>' % sp[1]
    wk_cell = '%d%s' % (w, ' D' if d else '')
    rows.append([
        Paragraph('<b>%s</b>' % wk_cell, ParagraphStyle('wkc', parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph(wk_dates(w), CELL),
        Paragraph('P%d' % phase_of(w), CELL),
        Paragraph('%d' % volume(w), CELL),
        Paragraph(tier_label(w), CELL),
        Paragraph(note, CELL),
    ])
    i = len(rows) - 1
    ph = phase_of(w)
    # phase color runs down the WK column so the shape of the build is visible at a glance
    row_styles.append(('BACKGROUND', (0,i), (0,i), PHASE_ACCENT[ph]))
    row_styles.append(('TEXTCOLOR', (0,i), (0,i), colors.white))
    if sp:
        row_styles.append(('BACKGROUND', (1,i), (-1,i), TEST_BG))
    elif d:
        row_styles.append(('BACKGROUND', (1,i), (-1,i), DELOAD_BG))
    else:
        row_styles.append(('BACKGROUND', (1,i), (-1,i), PHASE_TINT[ph]))

t = Table(rows, colWidths=[0.42*inch, 0.95*inch, 0.32*inch, 0.35*inch, 0.42*inch, 4.84*inch], repeatRows=1)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DARK),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 3.5), ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
] + row_styles))
story.append(t)

story.append(Spacer(1, 10))
story.append(Paragraph('HOW TO USE THIS', H2))
for line in [
    '<b>Print the current 2 weeks from the app (PRINT MONTH) for daily detail;</b> this document is the map, the app is the turn-by-turn. They run the same engine.',
    '<b>When a gate is passed,</b> tell KODA (or approve the changeset in the COACH REVIEW queue) — every pace in the app moves up together, and this sheet\'s next tier becomes active.',
    '<b>When life breaks a week,</b> resume where the calendar says, not where you left off. The gap protocol in the app re-places you automatically. Never stack missed quality.',
    '<b>Race weeks beat plan weeks.</b> Real results are worth more than any workout — if a race conflicts with a listed session, race, then give it 48h of easy.',
    '<b>The only unbreakable rule:</b> 45 weeks of showing up at honest effort beats 15 weeks of heroics followed by injury. Every rule above exists to serve this one.',
]:
    story.append(Paragraph(line, BODY)); story.append(Spacer(1, 3))

doc.build(story)
print('PDF written')
