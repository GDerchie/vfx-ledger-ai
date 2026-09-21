"""
VFX Budget System v04 — Security & Deployment Guide PDF Generator
Run: python generate_security_guide.py
Output: VFX_Budget_System_Security_Guide.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG      = colors.HexColor('#0d0e18')
C_PANEL   = colors.HexColor('#12152a')
C_BORDER  = colors.HexColor('#2e3050')
C_GOLD    = colors.HexColor('#f0b429')
C_BLUE    = colors.HexColor('#4a9cf0')
C_GREEN   = colors.HexColor('#52c46a')
C_RED     = colors.HexColor('#e05252')
C_ORANGE  = colors.HexColor('#e08232')
C_MUTED   = colors.HexColor('#7880a0')
C_TEXT    = colors.HexColor('#d0d8f0')
C_ACCENT  = colors.HexColor('#1e2240')
C_DARK    = colors.HexColor('#1a1d35')
C_PURPLE  = colors.HexColor('#9b59b6')

W, H = A4
OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_Security_Guide.pdf')

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def P(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        'cover_title':   P('cover_title',   fontSize=30, leading=36, textColor=C_RED,
                            fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6),
        'cover_sub':     P('cover_sub',     fontSize=13, leading=18, textColor=C_MUTED,
                            fontName='Helvetica', alignment=TA_CENTER, spaceAfter=4),
        'cover_version': P('cover_version', fontSize=10, leading=14, textColor=C_BLUE,
                            fontName='Helvetica-Bold', alignment=TA_CENTER),
        'toc_entry':     P('toc_entry',     fontSize=11, leading=16, textColor=C_TEXT,
                            fontName='Helvetica', leftIndent=8, spaceAfter=2),
        'toc_sub':       P('toc_sub',       fontSize=9.5, leading=14, textColor=C_MUTED,
                            fontName='Helvetica', leftIndent=20, spaceAfter=1),
        'ch_num':        P('ch_num',        fontSize=9, leading=12, textColor=C_RED,
                            fontName='Helvetica-Bold', spaceAfter=0),
        'ch_title':      P('ch_title',      fontSize=20, leading=24, textColor=C_RED,
                            fontName='Helvetica-Bold', spaceAfter=4),
        'ch_sub':        P('ch_sub',        fontSize=11, leading=16, textColor=C_MUTED,
                            fontName='Helvetica', spaceAfter=8),
        'section':       P('section',       fontSize=13, leading=17, textColor=C_BLUE,
                            fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=4),
        'body':          P('body',          fontSize=10, leading=15, textColor=C_TEXT,
                            fontName='Helvetica', spaceAfter=6),
        'bullet':        P('bullet',        fontSize=10, leading=14, textColor=C_TEXT,
                            fontName='Helvetica', leftIndent=14, spaceAfter=3,
                            bulletText='*', bulletIndent=4),
        'sub_bullet':    P('sub_bullet',    fontSize=9.5, leading=13, textColor=C_MUTED,
                            fontName='Helvetica', leftIndent=28, spaceAfter=2,
                            bulletText='-', bulletIndent=18),
        'tip':           P('tip',           fontSize=9.5, leading=14, textColor=C_GREEN,
                            fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4),
        'warn':          P('warn',          fontSize=9.5, leading=14, textColor=C_ORANGE,
                            fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4),
        'critical':      P('critical',      fontSize=9.5, leading=14, textColor=C_RED,
                            fontName='Helvetica-Bold', leftIndent=12, spaceAfter=4),
        'code':          P('code',          fontSize=8.5, leading=13, textColor=C_BLUE,
                            fontName='Courier', leftIndent=14, spaceAfter=4,
                            backColor=C_ACCENT),
        'label':         P('label',         fontSize=8, leading=11, textColor=C_MUTED,
                            fontName='Helvetica-Bold', spaceAfter=2),
        'caption':       P('caption',       fontSize=8.5, leading=12, textColor=C_MUTED,
                            fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4),
        'arch_box':      P('arch_box',      fontSize=9, leading=13, textColor=C_GREEN,
                            fontName='Courier', leftIndent=10, spaceAfter=2),
    }

S = make_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(pts=6):   return Spacer(1, pts)
def hr(c=C_BORDER, t=0.5): return HRFlowable(width='100%', thickness=t, color=c, spaceAfter=6, spaceBefore=4)
def body(t):     return Paragraph(t, S['body'])
def section(t):  return Paragraph(t, S['section'])
def bullet(t):   return Paragraph(t, S['bullet'])
def sub_b(t):    return Paragraph(t, S['sub_bullet'])
def tip(t):      return Paragraph(f'TIP  {t}', S['tip'])
def warn(t):     return Paragraph(f'WARNING  {t}', S['warn'])
def critical(t): return Paragraph(f'CRITICAL  {t}', S['critical'])
def code(t):     return Paragraph(t, S['code'])
def arch(t):     return Paragraph(t, S['arch_box'])

def chapter_header(num, title, subtitle=''):
    items = [
        Paragraph(f'CHAPTER {num}', S['ch_num']),
        Paragraph(title, S['ch_title']),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, S['ch_sub']))
    items.append(hr(C_RED, 1))
    items.append(sp(4))
    return items

def info_table(rows, col_widths=None):
    data = [[Paragraph(f'<b>{r[0]}</b>', S['label']),
             Paragraph(str(r[1]), S['body'])] for r in rows]
    w = col_widths or [50*mm, 110*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C_ACCENT),
        ('GRID',       (0,0),(-1,-1), 0.4, C_BORDER),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TEXTCOLOR',  (0,0),(0,-1), C_GOLD),
    ]))
    return [t, sp(8)]

def col_table(headers, rows, col_widths=None):
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = [[Paragraph(str(c), S['body']) for c in r] for r in rows]
    data = [head_row] + body_rows
    n = len(headers)
    w = col_widths or [(160/n)*mm]*n
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_PANEL),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ACCENT, C_BG]),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR',     (0,0),(-1,0), C_GOLD),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

def rating_table(rows):
    """rows = (option, security, cost, effort, recommended)"""
    headers = ['OPTION', 'SECURITY', 'COST', 'EFFORT', 'RECOMMENDED']
    sec_colors = {'Maximum': '#52c46a', 'Very High': '#52c46a',
                  'High': '#f0b429', 'Medium': '#e08232', 'Low': '#e05252'}
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = []
    for r in rows:
        sc = sec_colors.get(r[1], '#d0d8f0')
        rec_color = '#52c46a' if 'YES' in str(r[4]).upper() else '#4a5080'
        body_rows.append([
            Paragraph(str(r[0]), S['body']),
            Paragraph(f'<font color="{sc}"><b>{r[1]}</b></font>', S['body']),
            Paragraph(str(r[2]), S['body']),
            Paragraph(str(r[3]), S['body']),
            Paragraph(f'<font color="{rec_color}"><b>{r[4]}</b></font>', S['body']),
        ])
    data = [head_row] + body_rows
    w = [52*mm, 28*mm, 22*mm, 22*mm, 32*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_PANEL),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ACCENT, C_BG]),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR',     (0,0),(-1,0), C_GOLD),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

def arch_box(lines):
    """Code-style architecture diagram box"""
    data = [[Paragraph(line, S['arch_box'])] for line in lines]
    t = Table(data, colWidths=[160*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#080a14')),
        ('BOX',        (0,0),(-1,-1), 0.8, C_GREEN),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
        ('LEFTPADDING',(0,0),(-1,-1), 10),
    ]))
    return [t, sp(8)]

def week_table(rows):
    headers = ['PHASE', 'ACTION', 'TIME', 'CODE CHANGE?']
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = []
    for r in rows:
        cc_color = '#e05252' if r[3] == 'Yes' else '#52c46a'
        body_rows.append([
            Paragraph(str(r[0]), S['body']),
            Paragraph(str(r[1]), S['body']),
            Paragraph(str(r[2]), S['body']),
            Paragraph(f'<font color="{cc_color}"><b>{r[3]}</b></font>', S['body']),
        ])
    data = [head_row] + body_rows
    w = [22*mm, 82*mm, 22*mm, 30*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_PANEL),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ACCENT, C_BG]),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR',     (0,0),(-1,0), C_GOLD),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

# ── Page callbacks ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H - 12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_RED)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H - 7*mm, 'VFX BUDGET SYSTEM v04  --  SECURITY & DEPLOYMENT GUIDE')
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawRightString(W - 15*mm, H - 7*mm, 'CONFIDENTIAL')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 3.5*mm, 'Internal Use Only -- Do Not Distribute')
    canvas.drawRightString(W - 15*mm, 3.5*mm, f'Page {doc.page}')
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Red top bar
    canvas.setFillColor(C_RED)
    canvas.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BG)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(W/2, H - 11*mm, 'VFX BUDGET SYSTEM  --  SECURITY & DEPLOYMENT GUIDE')
    # Red left stripe accent
    canvas.setFillColor(colors.HexColor('#3a0808'))
    canvas.rect(0, 0, 4*mm, H, fill=1, stroke=0)
    # Bottom bar
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_RED)
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawCentredString(W/2, 5*mm, 'CONFIDENTIAL -- INTERNAL USE ONLY -- DO NOT DISTRIBUTE')
    canvas.restoreState()

# ── Content ────────────────────────────────────────────────────────────────────

def cover():
    e = []
    e.append(sp(55))
    e.append(Paragraph('SECURITY &amp; DEPLOYMENT', S['cover_title']))
    e.append(sp(4))
    e.append(Paragraph('VFX Budget System v04', S['cover_sub']))
    e.append(sp(2))
    e.append(Paragraph('Production Infrastructure Guide', S['cover_version']))
    e.append(sp(20))
    e.append(hr(C_RED, 1.5))
    e.append(sp(10))
    for k, v in [
        ('CLASSIFICATION', 'Confidential — Internal Only'),
        ('SCOPE',          'Deployment, Security, Access Control, Cloud Infrastructure'),
        ('AUDIENCE',       'Production Technology, IT, VFX Producers'),
        ('STATUS',         'Recommended Architecture — 2024'),
    ]:
        e.append(Paragraph(
            f'<font color="#e05252"><b>{k}&nbsp;&nbsp;</b></font>'
            f'<font color="#7880a0">{v}</font>',
            S['cover_sub']))
        e.append(sp(2))
    e.append(sp(30))
    e.append(Paragraph('HIGH SECURITY CONFIGURATION', S['cover_version']))
    e.append(PageBreak())
    return e

def toc():
    e = []
    e.append(Paragraph('TABLE OF CONTENTS', S['ch_title']))
    e.append(hr(C_RED, 1))
    e.append(sp(6))
    chapters = [
        ('1', 'Why Security Matters for This System',    ['What data is at risk', 'Threat model', 'Studio standards']),
        ('2', 'Security Layers Explained',               ['Layer 1: VPN', 'Layer 2: Authentication', 'Layer 3: HTTPS', 'Layer 4: Encryption at rest', 'Layer 5: Audit logging']),
        ('3', 'VPN — Keeping the App Off the Internet',  ['What VPN does', 'Tailscale setup', 'Studio network option']),
        ('4', 'Authentication — Login System',           ['Flask-Login', 'Google OAuth', 'SSO / Azure AD']),
        ('5', 'Railway.app Deployment',                  ['What Railway does', 'Full setup steps', 'Costs']),
        ('6', 'Database — SQLite to PostgreSQL',         ['Why the switch', 'Migration plan', 'Code changes']),
        ('7', 'File Storage — Cloudflare R2',            ['What it replaces', 'Setup steps', 'Excel/PDF to R2']),
        ('8', 'Google Drive Integration',                ['Drive as backup', 'Drive Picker for imports', 'Team collaboration model']),
        ('9', 'Recommended Architecture',                ['Full diagram', 'Component roles', 'Data flow']),
        ('10','Implementation Roadmap',                  ['Phase plan', 'Code change impact', 'Timeline']),
    ]
    for num, title, subs in chapters:
        e.append(Paragraph(
            f'<font color="#e05252"><b>{num}.</b></font>  <b>{title}</b>',
            S['toc_entry']))
        for s in subs:
            e.append(Paragraph(f'> {s}', S['toc_sub']))
        e.append(sp(3))
    e.append(PageBreak())
    return e

def ch1():
    e = []
    e += chapter_header('1', 'Why Security Matters', 'Understanding what is at risk in this system')

    e.append(section('What Data This System Holds'))
    e.append(body('The VFX Budget System is not a general productivity tool. It contains commercially '
                   'sensitive financial data that has direct value to competitors and vendors:'))
    e += col_table(
        ['Data Type', 'Sensitivity', 'Risk if Leaked'],
        [
            ['Vendor bid prices',         'CRITICAL', 'Competitors undercut your vendors; vendors collude on pricing'],
            ['Invoice amounts & terms',   'CRITICAL', 'Exposes negotiated rates and payment schedules'],
            ['Episode EFC / budgets',     'HIGH',     'Reveals production financial health to market'],
            ['Awarded vendor decisions',  'HIGH',     'Reveals which vendors won bids before announcement'],
            ['Shot counts per episode',   'MEDIUM',   'Signals production scope and complexity'],
            ['VFX notes / feedback',      'MEDIUM',   'Contains creative and editorial decisions'],
        ],
        col_widths=[45*mm, 22*mm, 93*mm]
    )

    e.append(section('Threat Model'))
    e.append(body('The realistic threats for a production tool of this type:'))
    e.append(bullet('<b>External attacker</b> — finds a public URL, brute-forces login or exploits unpatched Flask'))
    e.append(bullet('<b>Vendor phishing</b> — a vendor employee tricks a team member into sharing credentials'))
    e.append(bullet('<b>Insider leak</b> — a team member shares the URL or screenshots with a competitor'))
    e.append(bullet('<b>Accidental exposure</b> — URL shared in a Slack message, Google Doc, or email chain'))
    e.append(bullet('<b>Data loss</b> — server crash, accidental delete, no backup'))
    e.append(sp(4))
    e.append(critical('A public URL with no authentication is unacceptable for this class of data.'))

    e.append(section('Studio Industry Standard'))
    e.append(body('Major VFX facilities (ILM, DNEG, Framestore, MPC) all follow these practices '
                   'for internal financial and production tools:'))
    e.append(bullet('All internal tools are VPN-gated — no public internet access'))
    e.append(bullet('Authentication via studio SSO (Google Workspace or Azure AD)'))
    e.append(bullet('All data encrypted in transit (HTTPS) and at rest'))
    e.append(bullet('Audit logs for all financial data changes'))
    e.append(bullet('Regular automated database backups'))

    e.append(PageBreak())
    return e

def ch2():
    e = []
    e += chapter_header('2', 'Security Layers', 'Five layers that together provide high security')

    e.append(body('Security is built in layers. Each layer stops a different type of attack. '
                   'You do not need all five on day one — but you should aim to have all five in production.'))

    layers = [
        ('Layer 1', 'VPN — Network Access Control', C_RED,
         'Prevents anyone without VPN access from even reaching the app. '
         'The app has no public URL. This is your strongest defence.',
         'Tailscale (free), Studio VPN, WireGuard'),
        ('Layer 2', 'Authentication — Login', C_ORANGE,
         'Even if someone gets through the VPN, they must have valid credentials. '
         'Stops insider threats and accidental sharing.',
         'Flask-Login, Google OAuth, Azure AD SSO'),
        ('Layer 3', 'HTTPS — Encrypted Transit', C_GOLD,
         'All data between browser and server is encrypted. '
         'Prevents interception on shared networks (hotel WiFi, etc.).',
         'Caddy (auto SSL), Railway (automatic), Let\'s Encrypt'),
        ('Layer 4', 'Encryption at Rest', C_BLUE,
         'Database files are encrypted on disk. '
         'If the server is compromised, raw data files are unreadable.',
         'PostgreSQL (default), SQLCipher for SQLite, Cloud provider encryption'),
        ('Layer 5', 'Audit Log', C_GREEN,
         'Every data change records who did it, when, and what changed. '
         'Required for financial accountability and incident investigation.',
         'Custom audit_log table in database (to be built)'),
    ]

    for lnum, ltitle, lcolor, ldesc, ltools in layers:
        data = [
            [Paragraph(f'<font color="{lcolor.hexval()}"><b>{lnum}</b></font>', S['body']),
             Paragraph(f'<font color="{lcolor.hexval()}"><b>{ltitle}</b></font>', S['body'])],
            [Paragraph('', S['body']),
             Paragraph(ldesc, S['body'])],
            [Paragraph('', S['body']),
             Paragraph(f'<font color="#7880a0">Tools: {ltools}</font>', S['body'])],
        ]
        t = Table(data, colWidths=[18*mm, 142*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), C_ACCENT),
            ('BOX',        (0,0),(-1,-1), 0.6, lcolor),
            ('TOPPADDING', (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING',(0,0),(-1,-1), 8),
            ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ]))
        e.append(t)
        e.append(sp(6))

    e.append(PageBreak())
    return e

def ch3():
    e = []
    e += chapter_header('3', 'VPN — Network Access Control', 'Keeping the app invisible to the public internet')

    e.append(section('What a VPN Does'))
    e.append(body('A VPN creates a private encrypted network between your team members\' devices. '
                   'The Flask app only listens on this private network — it is completely invisible '
                   'to anyone not connected to the VPN.'))

    e += arch_box([
        'WITHOUT VPN:',
        '  Anyone on the internet  -->  https://your-app.railway.app  -->  sees the app',
        '',
        'WITH VPN:',
        '  Public internet         -->  no URL exists  -->  connection refused',
        '  Team member + VPN       -->  100.x.x.x (private)  -->  sees the app',
    ])

    e.append(section('Tailscale — Recommended for Small Teams'))
    e.append(body('<b>Tailscale</b> is the simplest modern VPN. It is free for up to 3 users '
                   'and uses WireGuard encryption under the hood (military-grade).'))

    e += col_table(
        ['Step', 'Action', 'Who Does It'],
        [
            ['1', 'Go to tailscale.com and create a free account', 'System admin'],
            ['2', 'Install Tailscale on the server running Flask', 'System admin'],
            ['3', 'Install Tailscale on each team member\'s laptop', 'Each team member'],
            ['4', 'Approve each device in Tailscale admin console', 'System admin'],
            ['5', 'Configure Flask to listen on Tailscale IP only', 'Developer'],
            ['6', 'Share the private IP with the team (e.g. 100.64.0.1:5000)', 'System admin'],
        ],
        col_widths=[10*mm, 100*mm, 50*mm]
    )
    e.append(tip('Tailscale generates a unique 100.x.x.x IP for each device. The app URL '
                  'becomes something like http://100.64.0.1:5000 -- only reachable by team members.'))

    e.append(section('Studio Network Option (On-Premise)'))
    e.append(body('If your studio has an existing IT infrastructure and VPN:'))
    e.append(bullet('Request a server on the internal studio network from IT'))
    e.append(bullet('Deploy Flask on that server behind the studio firewall'))
    e.append(bullet('Team accesses it via the studio VPN they already use'))
    e.append(bullet('No external cloud service needed -- data stays in-house'))
    e.append(warn('Coordinate with studio IT before deploying any internal server. '
                   'There may be security policies and approval processes to follow.'))

    e.append(section('Tailscale Pricing'))
    e += info_table([
        ('Free tier',     'Up to 3 users, unlimited devices per user -- suitable for small team'),
        ('Personal Pro',  '$6/user/month -- up to 6 users'),
        ('Teams',         '$6/user/month -- unlimited users, admin controls'),
        ('Enterprise',    'Custom -- SSO, audit logs, compliance'),
    ])

    e.append(PageBreak())
    return e

def ch4():
    e = []
    e += chapter_header('4', 'Authentication', 'Controlling who can log in to the system')

    e.append(body('Even behind a VPN, the app should require a login. '
                   'This stops accidental access if a device is lost or a VPN credential is shared.'))

    e.append(section('Option A — Flask-Login (Username + Password)'))
    e.append(body('The simplest option. Adds a login page to your existing Flask app. '
                   'Users are stored in the database with hashed passwords.'))
    e += info_table([
        ('Install',     'pip install flask-login werkzeug'),
        ('Effort',      'Low — 2-3 hours to implement'),
        ('Best for',    'Small teams, quick deployment'),
        ('Limitation',  'Passwords must be managed manually, no SSO'),
    ])
    e.append(code('# Passwords stored as bcrypt hashes -- never plain text'))
    e.append(code('# from werkzeug.security import generate_password_hash, check_password_hash'))

    e.append(section('Option B — Google OAuth (Recommended)'))
    e.append(body('Team members log in with their existing Google / Google Workspace account. '
                   'No separate passwords to manage. If a team member leaves, revoke their Google account '
                   'and they instantly lose access.'))
    e += info_table([
        ('Install',     'pip install flask-dance google-auth-oauthlib'),
        ('Effort',      'Medium -- 4-6 hours including Google Console setup'),
        ('Best for',    'Teams already using Google Workspace (Gmail, Drive)'),
        ('Advantage',   'Uses existing studio Google accounts, MFA inherited from Google'),
        ('Setup',       'Create OAuth credentials in Google Cloud Console, whitelist your domain'),
    ])

    e += arch_box([
        'Google OAuth Flow:',
        '',
        '  User visits app  -->  redirected to Google login',
        '  Google authenticates  -->  returns token to app',
        '  App checks if email is in allowed list  -->  grants access',
        '  Session valid for X hours  -->  re-authenticate required',
    ])

    e.append(tip('Restrict login to @yourstudio.com Google accounts only. '
                  'Anyone outside that domain cannot log in even with a valid Google account.'))

    e.append(section('Option C — Azure AD / Okta SSO'))
    e.append(body('Enterprise-grade Single Sign-On. Integrates with studio HR systems '
                   '-- when a contractor\'s contract ends, their access is automatically revoked.'))
    e += info_table([
        ('Effort',      'High -- requires IT involvement and enterprise licenses'),
        ('Best for',    'Large studios with existing Azure/Okta infrastructure'),
        ('Advantage',   'Centralized access management, compliance reporting, MFA enforced'),
    ])

    e.append(section('Comparison'))
    e += rating_table([
        ('Flask-Login (passwords)',  'Medium',   'Free',      'Low',    'Starter'),
        ('Google OAuth',            'High',      'Free',      'Medium', 'YES'),
        ('Azure AD / Okta SSO',     'Maximum',   'Enterprise','High',   'Large Studios'),
    ])

    e.append(PageBreak())
    return e

def ch5():
    e = []
    e += chapter_header('5', 'Railway.app Deployment', 'Running Flask on a managed cloud platform')

    e.append(body('Railway is a cloud platform that runs your Flask app 24/7 on managed infrastructure. '
                   'You push code to GitHub -- Railway automatically builds and deploys it.'))

    e.append(section('How Railway Works'))
    e += arch_box([
        'Your laptop  --git push-->  GitHub repo',
        '                               |',
        '                          Railway detects change',
        '                               |',
        '                          Builds Python environment',
        '                          Installs requirements.txt',
        '                          Starts Gunicorn + Flask',
        '                               |',
        '                     https://your-app.railway.app  (public)',
        '                      or  100.x.x.x  (VPN-only, recommended)',
    ])

    e.append(section('Setup Steps'))
    e += col_table(
        ['Step', 'Action'],
        [
            ['1', 'Create a GitHub account and push your UPDATE-SISTEM04 folder to a private repo'],
            ['2', 'Sign up at railway.app -- connect your GitHub account'],
            ['3', 'Click "New Project" --> "Deploy from GitHub repo" --> select your repo'],
            ['4', 'Railway auto-detects Python and installs requirements.txt'],
            ['5', 'Add a Procfile to tell Railway how to start the app'],
            ['6', 'Set environment variables (database URL, secret key)'],
            ['7', 'Add PostgreSQL plugin (2 clicks in Railway dashboard)'],
            ['8', 'Railway provides a URL -- configure VPN/Tailscale to restrict access'],
        ],
        col_widths=[10*mm, 150*mm]
    )

    e.append(section('Required Files to Add'))
    e.append(body('<b>Procfile</b> — tells Railway how to run the app:'))
    e.append(code('web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2'))
    e.append(body('<b>requirements.txt</b> — must include:'))
    e.append(code('flask\ngunicorn\nopenpyxl\npsycopg2-binary\nrequests\nflask-login'))
    e.append(body('<b>runtime.txt</b> — specify Python version:'))
    e.append(code('python-3.11.0'))

    e.append(section('Environment Variables'))
    e += col_table(
        ['Variable', 'Value', 'Purpose'],
        [
            ['SECRET_KEY',    'Long random string (32+ chars)',   'Flask session security'],
            ['DATABASE_URL',  'Provided by Railway PostgreSQL',   'Database connection'],
            ['OLLAMA_URL',    'http://your-ollama-server:11434',  'AI / LLM endpoint'],
            ['FLASK_ENV',     'production',                       'Disables debug mode'],
        ],
        col_widths=[38*mm, 55*mm, 67*mm]
    )
    e.append(critical('Never commit SECRET_KEY or DATABASE_URL to GitHub. '
                       'Always use environment variables for secrets.'))

    e.append(section('Cost'))
    e += info_table([
        ('Railway Starter',     '$5/month -- includes 512MB RAM, 1GB storage'),
        ('PostgreSQL add-on',   'Included in Starter plan up to 1GB'),
        ('Custom domain',       'Free SSL + custom domain included'),
        ('Total',               '~$5-8/month depending on usage'),
    ])

    e.append(PageBreak())
    return e

def ch6():
    e = []
    e += chapter_header('6', 'Database — SQLite to PostgreSQL', 'Why the switch is necessary and how to do it')

    e.append(section('Why SQLite Breaks on Cloud Deployment'))
    e.append(body('SQLite stores data in a single file on disk. On cloud platforms this file:'))
    e.append(bullet('Is wiped on every redeploy (ephemeral filesystem)'))
    e.append(bullet('Cannot be accessed by multiple app instances simultaneously'))
    e.append(bullet('Has no built-in access control or encryption'))
    e.append(bullet('Cannot be backed up automatically'))

    e.append(section('What PostgreSQL Gives You'))
    e.append(bullet('Data persists permanently across deploys and server restarts'))
    e.append(bullet('Multiple users can read/write simultaneously'))
    e.append(bullet('Encrypted at rest by default on Railway/Supabase'))
    e.append(bullet('Automatic daily backups on managed services'))
    e.append(bullet('Same SQL syntax -- most queries need no changes'))

    e.append(section('Migration Strategy'))
    e.append(body('The goal is to change as little application code as possible:'))
    e += col_table(
        ['What Changes', 'What Stays the Same'],
        [
            ['Database connector: sqlite3 --> psycopg2',   'All SQL queries (SELECT, INSERT, UPDATE, DELETE)'],
            ['Connection string format',                    'All table schemas'],
            ['Parameter placeholder: ? --> %s',            'All API endpoints'],
            ['Connection pooling needed',                   'All business logic in app.py'],
        ],
        col_widths=[75*mm, 85*mm]
    )

    e.append(section('Code Change Example'))
    e.append(body('Current SQLite connection:'))
    e.append(code('conn = sqlite3.connect("projects/myproject.db")\nconn.row_factory = sqlite3.Row'))
    e.append(body('PostgreSQL replacement:'))
    e.append(code('import psycopg2\nfrom psycopg2.extras import RealDictCursor\nconn = psycopg2.connect(os.environ["DATABASE_URL"])\ncursor = conn.cursor(cursor_factory=RealDictCursor)'))

    e.append(section('Data Migration'))
    e.append(body('To move existing project data from SQLite to PostgreSQL:'))
    e += col_table(
        ['Step', 'Action'],
        [
            ['1', 'Export all tables from SQLite to CSV (use the existing Export buttons)'],
            ['2', 'Create PostgreSQL tables using the same schema'],
            ['3', 'Import CSVs into PostgreSQL via pgAdmin or psql'],
            ['4', 'Verify row counts match'],
            ['5', 'Switch DATABASE_URL environment variable to PostgreSQL'],
        ],
        col_widths=[10*mm, 150*mm]
    )
    e.append(tip('Supabase offers a free PostgreSQL tier (500MB) with a web GUI -- '
                  'good for testing the migration before committing to Railway.'))

    e.append(PageBreak())
    return e

def ch7():
    e = []
    e += chapter_header('7', 'File Storage — Cloudflare R2', 'Storing Excel uploads and PDF exports in the cloud')

    e.append(section('The Problem with Local File Storage'))
    e.append(body('Currently, when users import a BIDCOMPARE Excel file or any other upload, '
                   'the file is saved to the local disk of the server. On Railway or any cloud platform, '
                   'this file disappears on the next deployment.'))

    e.append(section('What Cloudflare R2 Is'))
    e.append(body('R2 is cloud object storage -- think of it as a secure folder in the cloud '
                   'that your Flask app can read from and write to programmatically. '
                   'Compatible with the Amazon S3 API, so the same code works with both.'))
    e += info_table([
        ('Free tier',       '10 GB storage, 1 million requests/month -- free forever'),
        ('Pricing above',   '$0.015/GB/month -- extremely cheap'),
        ('Access',          'Private bucket -- only your app can access it via API keys'),
        ('Encryption',      'AES-256 encryption at rest by default'),
        ('Speed',           'Global CDN -- fast from anywhere'),
    ])

    e.append(section('Setup Steps'))
    e += col_table(
        ['Step', 'Action'],
        [
            ['1', 'Create a free Cloudflare account at cloudflare.com'],
            ['2', 'Go to R2 --> Create Bucket --> name it "vfx-budget-files"'],
            ['3', 'Set bucket to Private (no public access)'],
            ['4', 'Create an API token with R2 read/write permissions'],
            ['5', 'Add R2 credentials to Railway environment variables'],
            ['6', 'Install boto3: pip install boto3'],
            ['7', 'Update file upload code to send files to R2 instead of local disk'],
        ],
        col_widths=[10*mm, 150*mm]
    )

    e.append(section('What Gets Stored in R2'))
    e += col_table(
        ['File Type', 'When Created', 'Current Behaviour', 'With R2'],
        [
            ['BIDCOMPARE .xlsx', 'On import',       'Saved to /tmp locally',   'Uploaded to R2, deleted locally'],
            ['EP export .xlsx',  'On export click', 'Streamed to browser',     'Also saved to R2 with timestamp'],
            ['Tutorial PDF',     'On generate',     'Saved locally',           'Uploaded to R2, shareable link'],
            ['DB backup .db',    'Manual/scheduled','Not implemented',          'Backed up to R2 automatically'],
        ],
        col_widths=[35*mm, 32*mm, 42*mm, 51*mm]
    )

    e.append(section('Google Drive vs Cloudflare R2'))
    e += col_table(
        ['Feature', 'Google Drive', 'Cloudflare R2'],
        [
            ['Free storage',     '15 GB',              '10 GB'],
            ['API access',       'Yes (complex OAuth)', 'Yes (simple S3 API)'],
            ['Team familiarity', 'HIGH -- you use it',  'Low -- new tool'],
            ['Browser picker',   'Yes (Google Picker)', 'No -- code only'],
            ['Best for',         'Manual import/export','Automated app storage'],
        ],
        col_widths=[45*mm, 55*mm, 60*mm]
    )
    e.append(tip('Use both: Google Drive for manual imports/exports (your team browses files), '
                  'Cloudflare R2 for automated app storage (database backups, processed files).'))

    e.append(PageBreak())
    return e

def ch8():
    e = []
    e += chapter_header('8', 'Google Drive Integration', 'Leveraging your existing Drive expertise')

    e.append(body('Since your team is already comfortable with Google Drive, it can serve as the primary '
                   'file sharing and backup layer -- without requiring changes to the core database logic.'))

    e.append(section('Level 1 — Zero Code Change (Use Today)'))
    e.append(body('If Google Drive Desktop is installed on the machine running Flask:'))
    e += arch_box([
        'Move UPDATE-SISTEM04 folder  -->  inside Google Drive folder',
        '',
        'Result:',
        '  projects/myshow.db  -->  auto-syncs to Google Drive cloud',
        '  Any export .xlsx    -->  auto-syncs to Google Drive cloud',
        '  Any team member with Drive access  -->  can see the files',
    ])
    e.append(tip('This works immediately with no code changes. The .db file syncs to Drive '
                  'as a backup every time it changes.'))

    e.append(section('Level 2 — Drive Buttons in the UI'))
    e.append(body('Add Google Drive integration directly into the Flask app:'))
    e += col_table(
        ['Button', 'Page', 'What it Does'],
        [
            ['Backup DB to Drive',      'Settings',     'Uploads the current .db file to a Drive folder'],
            ['Restore from Drive',      'Settings',     'Downloads a .db from Drive and replaces local'],
            ['Import from Drive',       'Bid Compare',  'Google Picker -- browse Drive, select Excel, import'],
            ['Export to Drive',         'Distribution', 'Sends generated .xlsx directly to Drive'],
            ['Export PDF to Drive',     'Settings',     'Uploads Tutorial / report PDF to Drive'],
        ],
        col_widths=[42*mm, 30*mm, 88*mm]
    )

    e.append(section('Google Drive API Setup'))
    e += col_table(
        ['Step', 'Action'],
        [
            ['1', 'Go to console.cloud.google.com'],
            ['2', 'Create a new project (e.g. "VFX Budget System")'],
            ['3', 'Enable: Google Drive API + Google Picker API'],
            ['4', 'Create OAuth 2.0 credentials (Web Application type)'],
            ['5', 'Add your app URL to "Authorised redirect URIs"'],
            ['6', 'Download credentials JSON -- store as environment variable'],
            ['7', 'pip install google-api-python-client google-auth-oauthlib'],
            ['8', 'First use: user clicks "Connect Drive" -- one-time Google permission screen'],
        ],
        col_widths=[10*mm, 150*mm]
    )
    e.append(code('pip install google-api-python-client google-auth-oauthlib google-auth-httplib2'))

    e.append(section('Team Collaboration Model with Drive'))
    e += arch_box([
        'Google Drive (shared team folder)',
        '|-- VFX_BUDGET/',
        '    |-- projects/',
        '    |   |-- ANDOR_S2.db       <-- synced automatically',
        '    |   |-- SHOW_B.db',
        '    |-- exports/',
        '    |   |-- EP201_shots.xlsx',
        '    |   |-- bidcompare_v3.xlsx',
        '    |-- backups/',
        '        |-- ANDOR_S2_2024-03-11.db   <-- dated backup',
    ])
    e.append(warn('Only one person should edit the database at a time in this model. '
                   'Google Drive syncs the .db file but cannot merge simultaneous edits. '
                   'For simultaneous multi-user editing, PostgreSQL is required.'))

    e.append(PageBreak())
    return e

def ch9():
    e = []
    e += chapter_header('9', 'Recommended Architecture', 'Full system design for high-security production use')

    e.append(section('High-Security Architecture Diagram'))
    e += arch_box([
        'TEAM DEVICES (VPN connected)',
        '  Laptop A  -->|',
        '  Laptop B  -->|-- Tailscale VPN -->  Private Network (100.x.x.x)',
        '  Laptop C  -->|                              |',
        '                                              v',
        '                                    RAILWAY.APP (private)',
        '                                    |-- Caddy (HTTPS)',
        '                                    |-- Gunicorn + Flask',
        '                                    |-- Google OAuth (login)',
        '                                    |-- Audit log middleware',
        '                                              |',
        '                              ________________|________________',
        '                             |                                 |',
        '                    PostgreSQL DB                    Cloudflare R2',
        '                    (Railway managed)               (file storage)',
        '                    Encrypted at rest               AES-256 encrypted',
        '                    Auto daily backup               Private bucket',
        '                             |',
        '                    Google Drive Sync',
        '                    (DB backup + exports)',
    ])

    e.append(section('Component Roles'))
    e += col_table(
        ['Component', 'Role', 'Why This Choice'],
        [
            ['Tailscale',        'VPN -- network access control',        'Free, easy, WireGuard encryption'],
            ['Railway.app',      'Cloud server running Flask',           'Git push deploy, managed SSL'],
            ['Gunicorn',         'Production WSGI server',               'Replaces Flask dev server'],
            ['Google OAuth',     'Authentication -- login with Google',  'Reuses existing studio Google accounts'],
            ['PostgreSQL',       'Production database',                  'Persistent, concurrent, encrypted'],
            ['Cloudflare R2',    'File storage (Excel/PDF uploads)',      'Free 10GB, S3-compatible'],
            ['Google Drive',     'Backup + team file sharing',           'Team already uses it'],
            ['Caddy',            'HTTPS + reverse proxy',                'Auto SSL certificates'],
            ['Audit log table',  'Financial change tracking',            'Accountability + incident response'],
        ],
        col_widths=[32*mm, 48*mm, 80*mm]
    )

    e.append(section('Data Flow for a Typical Action'))
    e.append(body('Example: User imports a BIDCOMPARE Excel file'))
    e += arch_box([
        '1. User on Laptop A -- connected to Tailscale VPN',
        '2. Opens https://100.64.0.1:5000/bidcompare',
        '3. Google OAuth checks session -- valid, allows access',
        '4. User clicks "Import from Drive" -- Google Picker opens',
        '5. User selects BIDCOMPARE_v3.xlsx from their Drive',
        '6. Flask receives file -- validates format',
        '7. File backed up to Cloudflare R2',
        '8. Data parsed and inserted into PostgreSQL',
        '9. Audit log records: user@studio.com imported 847 rows at 14:32:01',
        '10. Bid Compare table refreshes -- all team members see updated data',
    ])

    e.append(section('Google Drive Path (Simpler Alternative)'))
    e += arch_box([
        'TEAM DEVICES (VPN connected)',
        '  Laptop A  -->|',
        '  Laptop B  -->|-- Tailscale VPN -->  Mac Mini / NUC at studio',
        '  Laptop C  -->|                       |-- Flask + Gunicorn',
        '                                        |-- SQLite .db file',
        '                                        |-- Google Drive Desktop',
        '                                                |',
        '                                        Google Drive cloud',
        '                                        (auto-sync backup)',
    ])
    e.append(body('This simpler path keeps SQLite, avoids PostgreSQL migration, '
                   'uses Google Drive for backup, and costs near-zero. '
                   'Suitable for a small team (2-5 people, not simultaneous editing).'))

    e.append(PageBreak())
    return e

def ch10():
    e = []
    e += chapter_header('10', 'Implementation Roadmap', 'Phased plan to reach high-security production')

    e.append(section('Phase Plan'))
    e += week_table([
        ('Phase 1\n(Day 1)',   'Install Tailscale on server + all team laptops. App becomes VPN-only.',                        '1 hour',  'No'),
        ('Phase 2\n(Week 1)', 'Add Google OAuth login (Flask-Dance). Restrict to @yourstudio.com.',                            '1 day',   'Yes'),
        ('Phase 3\n(Week 2)', 'Add Google Drive backup/restore buttons in Settings page.',                                     '1 day',   'Yes'),
        ('Phase 4\n(Week 3)', 'Add Google Drive Picker for Bid Compare + Assets import.',                                      '2 days',  'Yes'),
        ('Phase 5\n(Week 4)', 'Deploy to Railway.app + Gunicorn. App runs 24/7 in cloud.',                                     '1 day',   'Yes'),
        ('Phase 6\n(Month 2)','Migrate database from SQLite to PostgreSQL.',                                                    '3 days',  'Yes'),
        ('Phase 7\n(Month 2)','Add Cloudflare R2 for file storage. Add audit log table.',                                      '2 days',  'Yes'),
        ('Phase 8\n(Month 3)','Penetration test + security review. Add rate limiting + CSRF protection.',                      '1 week',  'Yes'),
    ])

    e.append(section('What Stays the Same Throughout'))
    e.append(body('These parts of the system do NOT change in any phase:'))
    e.append(bullet('All page templates (distribution, ep, assets, notes, bidcompare, vendortracker, invoicelog)'))
    e.append(bullet('All Tabulator table logic and inline editing'))
    e.append(bullet('All API endpoint paths (/api/shots, /api/assets, /api/bidcompare, etc.)'))
    e.append(bullet('All AI / LLM streaming features'))
    e.append(bullet('All Excel import/export logic'))
    e.append(bullet('All risk scoring and confidence badge calculations'))

    e.append(section('Cost Summary at Full Deployment'))
    e += col_table(
        ['Service', 'Plan', 'Monthly Cost'],
        [
            ['Tailscale',       'Free (up to 3 users) or Teams',  'Free / $6 per user'],
            ['Railway.app',     'Starter (includes PostgreSQL)',   '$5-8'],
            ['Cloudflare R2',   'Free tier (10GB)',                'Free'],
            ['Google Drive',    'Existing Workspace plan',         '$0 additional'],
            ['Domain (optional)','yourstudio.com subdomain',       '~$1/month'],
            ['TOTAL',           '',                                '~$8-15/month'],
        ],
        col_widths=[40*mm, 60*mm, 60*mm]
    )

    e.append(section('Minimum Viable Security (Start Here)'))
    e.append(body('If you do nothing else, do Phase 1 and Phase 2:'))
    e.append(bullet('<b>Phase 1 — Tailscale</b>: Makes the app invisible to the public internet. Free. No code change. Do this today.'))
    e.append(bullet('<b>Phase 2 — Google OAuth</b>: Adds a login page using existing Google accounts. One day of development.'))
    e.append(sp(6))
    e.append(Paragraph(
        'These two phases together provide a level of security appropriate for '
        'commercial production financial data.',
        S['body']
    ))

    e.append(sp(14))
    e.append(hr(C_RED, 1))
    e.append(sp(6))
    e.append(Paragraph('End of Security &amp; Deployment Guide  --  VFX Budget System v04', S['cover_sub']))
    e.append(Paragraph('Confidential -- Internal Use Only', S['caption']))

    return e

# ── Build ─────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=18*mm,
    )
    story = []
    story += cover()
    story += toc()
    story += ch1()
    story += ch2()
    story += ch3()
    story += ch4()
    story += ch5()
    story += ch6()
    story += ch7()
    story += ch8()
    story += ch9()
    story += ch10()

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    print(f'PDF generated: {OUT}')

if __name__ == '__main__':
    build()
