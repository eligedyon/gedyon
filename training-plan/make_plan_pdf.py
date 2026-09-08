#!/usr/bin/env python3
"""GEDYON 12-day training block PDF — Sep 3-14, 2026, calibrated to current fitness."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

GOLD = colors.HexColor('#B08D2B')
DARK = colors.HexColor('#14141E')
GREY = colors.HexColor('#666677')
GREEN = colors.HexColor('#1E7D46')
RED = colors.HexColor('#B02A3C')
AMBER = colors.HexColor('#B07A1E')
LIGHT = colors.HexColor('#F4F2EC')

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22,
                    textColor=DARK, spaceAfter=2, alignment=0)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], fontSize=9.5, textColor=GREY, spaceAfter=10)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12,
                    textColor=GOLD, spaceBefore=12, spaceAfter=4)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], fontSize=9, leading=12.5, textColor=DARK)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], fontSize=8.4, leading=11, textColor=DARK)
CELLB = ParagraphStyle('CELLB', parent=CELL, fontName='Helvetica-Bold')
CELLW = ParagraphStyle('CELLW', parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')
NOTE = ParagraphStyle('NOTE', parent=BODY, fontSize=8.5, textColor=GREY, leading=11.5)

doc = SimpleDocTemplate('GEDYON-training-block-sep3-14.pdf', pagesize=letter,
                        leftMargin=0.65*inch, rightMargin=0.65*inch,
                        topMargin=0.6*inch, bottomMargin=0.55*inch)
story = []

story.append(Paragraph('GEDYON — 12-DAY TRAINING BLOCK', H1))
story.append(Paragraph('Wed Sep 3 – Sun Sep 14, 2026 · Elias Gedyon · Boulder, CO (~5,300 ft) · calibrated to CURRENT fitness (165 lb, rebuild phase) — not PR fitness. Paces rise only when the green-day test says so.', SUB))

# ── Pace card ──────────────────────────────────────────────────────
story.append(Paragraph('YOUR PACES RIGHT NOW', H2))
pace_rows = [
    [Paragraph('ZONE', CELLW), Paragraph('PACE', CELLW), Paragraph('HEART RATE', CELLW), Paragraph('FEEL / RULE', CELLW)],
    [Paragraph('<b>Recovery</b>', CELL), Paragraph('10:30+ /mi', CELL), Paragraph('&lt; 125', CELL),
     Paragraph('Shuffle. No pace floor — slower is fine.', CELL)],
    [Paragraph('<b>Easy</b>', CELL), Paragraph('9:30–10:15 /mi', CELL), Paragraph('125–140', CELL),
     Paragraph('Full sentences out loud. Most of your miles live here.', CELL)],
    [Paragraph('<b>Steady</b>', CELL), Paragraph('8:40–9:00 /mi', CELL), Paragraph('140–150', CELL),
     Paragraph('Short phrases. Used for long-run finishes.', CELL)],
    [Paragraph('<b>Tempo</b>', CELL), Paragraph('7:35–7:50 /mi', CELL), Paragraph('152–160 · CAP 162', CELL),
     Paragraph('Comfortably hard. If HR breaks the cap, slow down — hold the effort, not the number.', CELL)],
    [Paragraph('<b>Strides / Hills</b>', CELL), Paragraph('fast &amp; short', CELL), Paragraph('spikes OK', CELL),
     Paragraph('20s strides, 80m hills. Full recovery between reps — never a grind.', CELL)],
]
t = Table(pace_rows, colWidths=[1.05*inch, 1.25*inch, 1.35*inch, 3.55*inch])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DARK),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT]),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
]))
story.append(t)
story.append(Paragraph('The <b>green-day tempo test</b> (Fri 9/5 &amp; Fri 9/12): on a green WHOOP day, run the 20-min tempo at 7:25–7:30. '
    'If HR stays under 165 and it feels "comfortably hard," the tempo band moves up to 7:20–7:35 for the next block. If not, nothing changes and nothing is lost.', NOTE))

# ── Readiness rules ────────────────────────────────────────────────
story.append(Paragraph('READINESS RULES — CHECK WHOOP FIRST, EVERY MORNING', H2))
ready_rows = [
    [Paragraph('<b>GREEN (67%+)</b>', ParagraphStyle('g', parent=CELLB, textColor=GREEN)),
     Paragraph('Run the day as written. Green quality days are where fitness is made — do not bank them.', CELL)],
    [Paragraph('<b>YELLOW (34–66%)</b>', ParagraphStyle('y', parent=CELLB, textColor=AMBER)),
     Paragraph('ONE quality session max. A double\'s PM becomes 30 min easy. Cap tempo at HR 160. If HR won\'t settle in the first 8 min, convert to easy and take the session on the next green day.', CELL)],
    [Paragraph('<b>RED (&lt;34%)</b>', ParagraphStyle('r', parent=CELLB, textColor=RED)),
     Paragraph('No quality. Easy 30–40 min under HR 135, or full rest. The workout moves — it is never "made up" by stacking.', CELL)],
]
t2 = Table(ready_rows, colWidths=[1.45*inch, 5.75*inch])
t2.setStyle(TableStyle([
    ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, LIGHT]),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
]))
story.append(t2)

# ── The 12 days ────────────────────────────────────────────────────
days = [
    ('WED 9/3', 'TEMPO (single)', 'PM only — the missed AM is gone, don\'t chase it. 10–12 min easy warm-up + 2×20s strides · <b>20 min tempo at 7:35–7:45, HR cap 160</b> (yellow recovery today) · 10 min easy cool-down. ~4.5 mi total.'),
    ('THU 9/4', 'EASY DOUBLE + CORE', 'AM 3 mi easy (9:30–10:15) + 6×20s strides · PM 2 mi shake-out, truly easy · Core: dead bug 3×12, plank 3×45s, Copenhagen 3×20s each side.'),
    ('FRI 9/5', 'TEMPO — GREEN-DAY TEST', 'If WHOOP is green: 2 mi easy WU + 4×20s strides · <b>20 min at 7:25–7:30</b> (the test — see pace card) · 1.5 mi CD. If yellow: 20 min at 7:40–7:50 capped at 160 instead. ~6 mi.'),
    ('SAT 9/6', 'LONG RUN', '7–8 mi at 9:45–10:30, HR ceiling 145. Last 10 min may drift to steady (8:50–9:00) if feeling good. Fuel before, water on route.'),
    ('SUN 9/7', 'ACTIVE RECOVERY', '30–40 min walk/jog under HR 125 · 15 min foam roll (calves, quads, IT band) · 10 min mobility. This is where the week\'s work becomes fitness.'),
    ('MON 9/8', 'EASY DOUBLE + CORE', 'AM 3 mi easy + 6×20s strides · PM 2 mi shake-out · Core circuit 8 min. Weigh-in this morning — trend, not the number.'),
    ('TUE 9/9', 'THRESHOLD 1000s', '2 mi easy WU + 4×20s strides · <b>5×1000m at 4:45–4:55/km (7:38–7:53/mi), 90s standing rest</b> · HR ceiling 164 · 1.5 mi CD. Reps should feel repeatable — the last one no harder than the third. ~6.5 mi.'),
    ('WED 9/10', 'HILLS + EASY', '0.8 mi jog WU · <b>8×80m hill at max effort</b> (8–10% grade or treadmill incline 8.0–10.0) · walk down = full recovery · 2.5 mi easy after. This is your strength session — no gym needed.'),
    ('THU 9/11', 'EASY DOUBLE + CORE', 'AM 3 mi easy + strides · PM 2 mi shake-out · Core circuit. Nothing heroic — tomorrow matters more.'),
    ('FRI 9/12', 'TEMPO — GREEN-DAY TEST #2', 'Same as 9/5: green → 20 min at <b>7:25–7:30</b>; yellow → 7:40–7:50 capped. Two passed tests in one block = the whole pace card moves up next block. ~6 mi.'),
    ('SAT 9/13', 'LONG RUN', '8–9 mi at 9:45–10:30, HR ceiling 145 · last 15 min steady (8:50) if the day is green. Longest run of the block — fuel at 45 min.'),
    ('SUN 9/14', 'ACTIVE RECOVERY', '30–40 min walk/jog + foam roll + mobility. Block done — next block\'s paces come from what THIS block\'s data says.'),
]
story.append(Paragraph('THE 12 DAYS', H2))
day_rows = [[Paragraph('DAY', CELLW), Paragraph('SESSION', CELLW), Paragraph('WHAT TO DO', CELLW)]]
for d, s, w in days:
    day_rows.append([Paragraph('<b>%s</b>' % d, CELL), Paragraph('<b>%s</b>' % s, CELL), Paragraph(w, CELL)])
t3 = Table(day_rows, colWidths=[0.72*inch, 1.55*inch, 4.93*inch], repeatRows=1)
quality_idx = [1, 3, 7, 8, 10, 11]  # rows (1-based data rows) that are quality days: 9/3,9/5,9/9,9/10,9/12,9/13(long)
style_cmds = [
    ('BACKGROUND', (0,0), (-1,0), DARK),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDAD0')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 4.5), ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
    ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
]
for i in range(1, len(day_rows)):
    style_cmds.append(('BACKGROUND', (0,i), (-1,i), LIGHT if i in quality_idx else colors.white))
t3.setStyle(TableStyle(style_cmds))
story.append(t3)
story.append(Paragraph('Shaded rows = quality or long days — these are the ones the readiness rules gate. Weekly volume ~22–26 mi; if any run must be cut, cut easy miles, never the warm-up or cool-down of a quality day.', NOTE))

# ── Non-negotiables ────────────────────────────────────────────────
story.append(Paragraph('NON-NEGOTIABLES', H2))
for line in [
    '<b>1. Effort beats pace on every hard day.</b> The HR cap is the contract: break it, slow down. A tempo at 7:50 under the cap builds more than 7:30 over it.',
    '<b>2. Never two quality days back-to-back.</b> If a session moves (red/yellow day), it lands on the next green day and the following quality day slides — the block bends, it doesn\'t stack.',
    '<b>3. Easy means easy.</b> 9:30–10:15 will feel slow. That\'s the point — it\'s what lets Tuesday and Friday be real.',
    '<b>4. Weight comes off the same way pace comes back: quietly.</b> Fuel the quality days fully; trim on recovery days. Never run a hard session under-fueled to chase the scale.',
    '<b>5. Log every run with HR.</b> The app now reads pace-at-heart-rate to move your prescriptions — every logged run makes the next block smarter.',
]:
    story.append(Paragraph(line, BODY))
    story.append(Spacer(1, 3))

doc.build(story)
print('PDF written')
