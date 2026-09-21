"""
VFX Budget System v05 — Demo Data Seeder
=========================================
Creates showcase project: "NOVA SERIES — Season 1"
Uses app.init_project_db() so schema is always correct.

Run:  python seed_demo.py
Then: python app.py  →  open http://localhost:5000
"""

import sqlite3, json, os, sys, random
from datetime import date, timedelta

# ── import app schema builder ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from app import init_project_db

BASE = os.path.dirname(__file__)
os.makedirs(os.path.join(BASE, 'projects'), exist_ok=True)

PROJ       = os.path.join(BASE, 'projects', 'NOVA_S1_DEMO.vfxdb')
PJDB       = os.path.join(BASE, 'projects.db')
EP_START   = 101
EP_END     = 106

random.seed(42)

def d(days_ago=0):
    return (date.today() - timedelta(days=days_ago)).isoformat()

def rand_efc(est, spread=0.22):
    return round(est * random.uniform(1 - spread / 2, 1 + spread), 0)

# ── 1. Register in projects.db ────────────────────────────────────────────────
pj = sqlite3.connect(PJDB)
pj.execute("DELETE FROM projects WHERE db_path=?", (PROJ,))
pj.execute(
    "INSERT INTO projects (name, season, db_filename, db_path, ep_start, ep_end) VALUES (?,?,?,?,?,?)",
    ('NOVA SERIES', 'S1', os.path.basename(PROJ), PROJ, EP_START, EP_END)
)
pj.commit(); pj.close()
print("  [1/9] Project registered in projects.db")

# ── 2. Create project DB via app schema ───────────────────────────────────────
if os.path.exists(PROJ):
    os.remove(PROJ)
init_project_db(PROJ, EP_START, EP_END)
db = sqlite3.connect(PROJ)
db.row_factory = sqlite3.Row
c = db.cursor()
print("  [2/9] Project DB created with correct app schema")

# ── 3. Shots ──────────────────────────────────────────────────────────────────
VENDORS      = ['DNEG', 'ILM', 'FRAMESTORE', 'MPC', 'WETA']
SHOT_TYPES   = ['COMP', 'CG', 'FX', 'EXTENSION', 'CREATURE', 'PLATE', 'COMP']
COMPLEXITIES = ['Low', 'Medium', 'Medium', 'High', 'Hero']
STATUSES     = ['In Progress', 'In Progress', 'Delivered', 'Review', 'Not Started']
LOCATIONS    = [
    'INT. COMMAND DECK - NIGHT', 'EXT. NOVA CITY SKYLINE - DAY',
    'INT. REACTOR CORE - CONTINUOUS', 'EXT. ASTEROID BELT - SPACE',
    'INT. MEDICAL BAY - DAY', 'EXT. JUNGLE OUTPOST - DUSK',
    'INT. BRIDGE - NIGHT', 'EXT. DEEP SPACE - CONTINUOUS',
    'INT. HANGAR BAY - DAY', 'EXT. ORBITAL STATION - SPACE',
]
VFX_DESCS = [
    'Full CG environment replacement with lens flare and mist layers',
    'Creature performance — digital double with facial replacement',
    'Explosion FX with debris simulation and shockwave rings',
    'Screen extension with holographic displays and animated UI',
    'CG spacecraft flyby with engine glow and thruster trails',
    'Background crowd replacement with 400 digital extras',
    'Wire removal and sky replacement with volumetric clouds',
    'Muzzle flash, energy beam and particle trail composite',
    'Full CG cityscape with atmospheric haze and traffic sim',
    'Digital double creature in full motion capture performance',
]

shots_inserted = 0
for ep in range(EP_START, EP_END + 1):
    n_shots = random.randint(14, 22)
    ep_vendor = random.choice(VENDORS)
    for i in range(1, n_shots + 1):
        loc    = random.choice(LOCATIONS)
        stype  = random.choice(SHOT_TYPES)
        comp   = random.choice(COMPLEXITIES)
        cost   = round(random.uniform(8000, 95000), 0)
        efc    = rand_efc(cost)
        ext_int = 'INT' if loc.startswith('INT') else 'EXT'
        dn     = 'NIGHT' if 'NIGHT' in loc or 'SPACE' in loc else 'DAY'
        vendor = ep_vendor if random.random() > 0.35 else ''
        omit   = 1 if random.random() < 0.04 else 0
        sc     = f'{random.randint(1,60)}{random.choice(["","A","B",""])}'
        c.execute('''INSERT INTO shots
            (ep, shot_num, scene_code, s_code, location, ext_int,
             shot_type, complexity, vfx_desc, award_vendor,
             cost_est, efc, shot_est, omit)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            ep, i, sc, f'EP{ep}-SC{i:03d}',
            loc, ext_int, stype, comp,
            random.choice(VFX_DESCS), vendor,
            cost, efc, 1, omit
        ))
        shots_inserted += 1
    # ep_meta already seeded by init_project_db
    c.execute("UPDATE ep_meta SET script_v=?, edit_v=? WHERE ep=?",
              (f'v{random.randint(3,8)}', f'v{random.randint(2,5)}', ep))
db.commit()
print(f"  [3/9] {shots_inserted} shots seeded across EPs {EP_START}–{EP_END}")

# ── 4. Assets (app schema: est_budget, actual_spend, vendor_bids, orig_id) ────
ASSET_DEFS = [
    (101,'12','CG_NOVA_SHIP',    'Environment',
     'Full CG hero spacecraft — NOVA CLASS destroyer. 4.2M poly, PBR textures, '
     'engine glow FX, battle damage variants. 3 LOD levels required.',
     'ILM', 185000, 172000),
    (101,'18','CG_COMMANDER',   'Character',
     'Digital double of Commander Reyes. Full facial rig with FACS blendshapes, '
     'hero cloth sim, armour with 8 material variants.',
     'DNEG', 142000, 148000),
    (102,'5', 'ENV_NOVA_CITY',  'Environment',
     '42 blocks of procedural CG buildings, atmospheric haze, population sims, '
     '4 lighting rigs: day / dusk / night / storm.',
     'FRAMESTORE', 98000, 101000),
    (102,'31','CG_REACTOR',     'Prop',
     'Hero CG reactor core with energy simulation, interactive lighting, '
     '12 damage states, particle system for coolant venting.',
     'MPC', 67000, 67000),
    (103,'7', 'CG_CREATURE_VORN','Character',
     'VORN creature full digital double. Quadruped rig with muscle simulation, '
     'procedural fur, 6 behaviour states, bioluminescence FX.',
     'WETA', 220000, 235000),
    (103,'22','ENV_JUNGLE',     'Environment',
     'Jungle outpost — procedural foliage, 3 lighting states, '
     'CG structures, matte painting sky dome.',
     'FRAMESTORE', 55000, 55000),
    (104,'9', 'GFX_HOLO_UI',   'Other',
     '34 unique holographic screen designs, 8 hologram variants, '
     'animated looping states, reactive close-up versions.',
     'ILM', 38000, 39000),
    (104,'14','CG_FIGHTER',    'Prop',
     'Hero fighter craft — 2.8M poly, 6 weapons states, engine thrust FX, '
     'cockpit interior, damage progression rig.',
     'DNEG', 89000, 91000),
    (105,'3', 'ENV_ORBITAL_STN','Environment',
     'Orbital station full CG environment — modular construction, '
     'docking bay, solar arrays, atmospheric entry FX.',
     'ILM', 175000, 175000),
    (105,'28','CG_DRONE_SWARM','Character',
     '2,000+ agent drone swarm sim — collision avoidance, attack behaviours, '
     'destruction FX, particle trails and glow pass.',
     'MPC', 72000, 78000),
    (106,'11','CG_TITAN',      'Character',
     'TITAN mech hero asset — 7.1M poly, hydraulic rig, battle damage system, '
     '14 weapons attachments.',
     'WETA', 310000, 310000),
    (106,'44','ENV_ASTEROID',  'Environment',
     'Asteroid belt — procedural rock instancing, volumetric dust, '
     'debris collision sim, NOVA SHIP engine glow lighting.',
     'FRAMESTORE', 61000, 61000),
]
for i, row in enumerate(ASSET_DEFS, 1):
    ep, sc, name, atype, desc, vendor, cost, actual = row
    bids = {v: round(cost * random.uniform(0.88, 1.15), 0)
            for v in random.sample(VENDORS, k=random.randint(2, 4))}
    bids[vendor] = cost   # winning vendor always in bids
    c.execute('''INSERT INTO assets
        (orig_id, ep, scene_code, asset_name, asset_type, description,
         award_vendor, est_budget, actual_spend, omit, vendor_bids)
        VALUES (?,?,?,?,?,?,?,?,?,0,?)''',
        (i, ep, sc, name, atype, desc, vendor, cost, actual, json.dumps(bids)))
db.commit()
print(f"  [4/9] {len(ASSET_DEFS)} assets seeded")

# ── 5. Bid Compare ────────────────────────────────────────────────────────────
BID_SHOTS = [
    (101,'12A','INT. COMMAND DECK - NIGHT',  'COMP + ENV',    1,42000,45000,
     {'DNEG':44000,'ILM':52000,'FRAMESTORE':41000,'MPC':48000},'DNEG'),
    (101,'18', 'EXT. NOVA CITY - DAY',       'CG FULL ENV',   1,88000,92000,
     {'DNEG':91000,'ILM':88000,'FRAMESTORE':95000,'WETA':104000},'ILM'),
    (101,'24', 'INT. REACTOR CORE',          'FX + COMP',     1,31000,33000,
     {'DNEG':30000,'ILM':35000,'MPC':28000},'MPC'),
    (101,'31', 'EXT. ASTEROID BELT',         'CG ENV',        1,55000,58000,
     {'ILM':55000,'WETA':62000,'FRAMESTORE':57000},'ILM'),
    (102,'5',  'INT. BRIDGE - NIGHT',        'EXTENSION',     1,18000,19000,
     {'DNEG':17500,'ILM':20000,'MPC':16800},'DNEG'),
    (102,'9',  'EXT. JUNGLE OUTPOST',        'COMP + FX',     1,27000,28500,
     {'FRAMESTORE':27000,'WETA':31000,'MPC':25500},'FRAMESTORE'),
    (102,'15', 'INT. MEDICAL BAY',           'CREATURE',      1,64000,68000,
     {'WETA':64000,'ILM':71000,'DNEG':68000},'WETA'),
    (102,'22', 'EXT. ORBITAL STATION',       'CG FULL',       1,95000,99000,
     {'ILM':94000,'WETA':105000,'FRAMESTORE':97000},'ILM'),
    (103,'7',  'INT. HANGAR BAY',            'COMP + CG',     1,38000,41000,
     {'DNEG':38000,'ILM':43000,'MPC':36500},'DNEG'),
    (103,'14', 'EXT. DEEP SPACE',            'CG ENV',        1,72000,76000,
     {'ILM':71000,'WETA':79000,'FRAMESTORE':74000},'ILM'),
    (103,'19', 'INT. COMMAND DECK',          'GFX + COMP',    1,22000,23500,
     {'DNEG':21000,'ILM':24500,'MPC':20500},'MPC'),
    (104,'3',  'EXT. NOVA CITY SKYLINE',     'CG EXTENSION',  1,48000,51000,
     {'FRAMESTORE':47000,'ILM':52000,'DNEG':49000},'FRAMESTORE'),
    (104,'8',  'INT. REACTOR CORE',          'FX SIMULATION', 1,39000,42000,
     {'MPC':38000,'ILM':44000,'DNEG':40500},'MPC'),
    (104,'17', 'EXT. ASTEROID BELT',         'CREATURE + FX', 1,85000,90000,
     {'WETA':84000,'ILM':92000,'FRAMESTORE':88000},'WETA'),
    (105,'11', 'INT. BRIDGE',                'COMP',          1,14000,14800,
     {'DNEG':13500,'ILM':15500,'MPC':13800},'DNEG'),
    (105,'25', 'EXT. ORBITAL STATION',       'CG FULL ENV',   1,110000,116000,
     {'ILM':108000,'WETA':118000,'FRAMESTORE':112000},'ILM'),
    (106,'6',  'INT. COMMAND DECK',          'CG + COMP',     1,52000,55000,
     {'DNEG':50000,'ILM':56000,'MPC':51500},'DNEG'),
    (106,'13', 'EXT. JUNGLE',               'FX + EXTENSION', 1,33000,35500,
     {'FRAMESTORE':32000,'ILM':36000,'MPC':31500},'FRAMESTORE'),
]
for row in BID_SHOTS:
    ep, sc, setting, vtype, ver, lock, efc_b, bids, award = row
    c.execute('''INSERT INTO bid_compare
        (ep, sc, setting, vfxtype, version, lockbudget, efc, vendor_bids, award, novfx)
        VALUES (?,?,?,?,?,?,?,?,?,0)''',
        (ep, sc, setting, vtype, ver, lock, efc_b, json.dumps(bids), award))
# no-vfx rows
for ep in [101, 102, 103]:
    c.execute('''INSERT INTO bid_compare (ep, sc, setting, vfxtype, version, novfx)
        VALUES (?,?,?,?,?,1)''',
        (ep, f'{random.randint(40,99)}', 'INT. CORRIDOR - DAY', 'NO VFX', 1))
db.commit()
print(f"  [5/9] {len(BID_SHOTS)} bid-compare rows seeded")

# ── 6. Vendor Registry + Capacity ────────────────────────────────────────────
REGISTRY = [
    ('DNEG',       'UK', 1.27, 0.0,  8.0,  'bids@dneg.com'),
    ('ILM',        'US', 1.0,  0.0,  0.0,  'production@ilm.com'),
    ('FRAMESTORE', 'UK', 1.27, 0.0,  6.0,  'vfx@framestore.com'),
    ('MPC',        'CA', 1.36, 0.0,  12.0, 'mpc-prod@mpc.com'),
    ('WETA',       'NZ', 1.62, 15.0, 5.0,  'production@weta.com'),
]
for row in REGISTRY:
    c.execute('''INSERT OR REPLACE INTO vendor_registry
        (vendor, region, fx_rate, tax_pct, rebate_pct, contact)
        VALUES (?,?,?,?,?,?)''', row)

CAP = [('DNEG',80,0.92),('ILM',95,0.90),('FRAMESTORE',70,0.95),('MPC',60,0.88),('WETA',50,0.94)]
for row in CAP:
    c.execute('''INSERT OR REPLACE INTO vendor_capacity
        (vendor, shots_per_month, efficiency_pct) VALUES (?,?,?)''', row)
db.commit()
print(f"  [6/9] Vendor registry ({len(REGISTRY)} vendors) + capacity seeded")

# ── 7. Invoice Log (app schema: episode col, not ep) ─────────────────────────
INVOICES = [
    ('ILM',        101,'ILM-2024-0441', d(120),143000,'Paid',     d(110),'Full delivery payment'),
    ('DNEG',       101,'DNEG-0812',     d(115), 89000,'Paid',     d(100),'Final payment approved'),
    ('ILM',        102,'ILM-2024-0518', d(90), 100000,'Paid',     d(80), 'Phase 1 payment'),
    ('ILM',        102,'ILM-2024-0519', d(45),  92000,'Approved', d(40), 'Phase 2 pending payment'),
    ('FRAMESTORE', 102,'FS-24-1102',    d(70),  55000,'Paid',     d(60), 'ENV first payment'),
    ('FRAMESTORE', 102,'FS-24-1103',    d(20),  27000,'Pending',  '',    'Awaiting approval'),
    ('WETA',       102,'WETA-2411',     d(65),  32000,'Paid',     d(55), 'Creature round 1'),
    ('WETA',       102,'WETA-2412',     d(10),  32000,'Approved', d(5),  'Creature round 2'),
    ('ILM',        103,'ILM-2024-0601', d(60),  80000,'Paid',     d(50), 'Phase 1'),
    ('ILM',        103,'ILM-2024-0602', d(15),  30000,'Pending',  '',    'Awaiting DI lock'),
    ('DNEG',       103,'DNEG-0891',     d(55),  60500,'Paid',     d(45), 'All shots delivered'),
    ('MPC',        103,'MPC-P2024-33',  d(30),  20000,'Approved', d(25), 'FX round 2'),
    ('FRAMESTORE', 104,'FS-24-1201',    d(50),  70000,'Paid',     d(40), 'Extension pass 1'),
    ('MPC',        104,'MPC-P2024-41',  d(28),  50000,'Approved', d(20), 'Reactor FX'),
    ('WETA',       104,'WETA-2498',     d(22),  84000,'Paid',     d(18), 'Creature lock final'),
    ('ILM',        105,'ILM-2025-0101', d(14),  75000,'Approved', d(10), 'Orbital station phase 1'),
    ('DNEG',       105,'DNEG-0944',     d(12),  13500,'Paid',     d(8),  'Bridge composites'),
    ('DNEG',       106,'DNEG-0961',     d(5),   25000,'Pending',  '',    'Work in progress'),
]
for row in INVOICES:
    vendor, ep, inv_num, inv_date, amount, status, approve_date, notes = row
    c.execute('''INSERT INTO invoice_log
        (vendor, episode, inv_num, inv_date, amount, status, approve_date, notes)
        VALUES (?,?,?,?,?,?,?,?)''',
        (vendor, ep, inv_num, inv_date, amount, status, approve_date, notes))
db.commit()
print(f"  [7/9] {len(INVOICES)} invoices seeded")

# ── 8. VFX Notes (app schema: resolved INTEGER not status TEXT) ───────────────
NOTES = [
    (101,'VFX Supervisor',
     'ILM flagged reactor FX needs additional simulation pass. '
     'Budget impact TBC — estimate +$12k. Awaiting formal change order.', 0),
    (101,'Producer',
     'EP101 EFC tracking $18k over EST. Main driver is CG_NOVA_SHIP asset overrun. '
     'Review with ILM Thursday.', 0),
    (101,'VFX Coordinator',
     'DNEG delivered CG_COMMANDER v3 for review. Client has notes on facial '
     'performance — needs revision. Logged as Round 4.', 0),
    (102,'VFX Supervisor',
     'FRAMESTORE jungle environment approved by director. No further notes.', 1),
    (102,'Producer',
     'MPC creature FX rounds taking longer than scheduled. Risk of EP102 delivery '
     'slipping by 1 week. Monitoring daily.', 0),
    (102,'VFX Coordinator',
     'ILM orbital station concept art approved. Full CG build greenlit.', 1),
    (103,'VFX Supervisor',
     'WETA VORN creature — motion capture session rescheduled to next week. '
     'No budget impact.', 0),
    (103,'Producer',
     'EP103 total EFC tracking $6k under EST. Good position — flag to exec producer.', 0),
    (103,'VFX Coordinator',
     'All DNEG bridge composites delivered and locked. Final payment approved.', 1),
    (104,'VFX Supervisor',
     'GFX_HOLO_UI from ILM approved in full — 34 screens delivered. '
     'Outstanding: 2 reactive close-up versions.', 0),
    (104,'Producer',
     'MPC reactor FX round 3 — director requesting practical element integration. '
     'May require reshoot. URGENT.', 0),
    (105,'VFX Supervisor',
     'ILM orbital station — scale reference confirmed with director. '
     'Build proceeding. First look in 3 weeks.', 0),
    (105,'Producer',
     'Drone swarm sim from MPC impressive but needs more behaviour variation. '
     'Round 2 requested.', 0),
    (106,'VFX Supervisor',
     'TITAN mech asset (WETA) — hydraulic rig approved. '
     'Weapons attachment system under review. On schedule.', 0),
    (106,'Producer',
     'EP106 earliest in schedule. DNEG have capacity. '
     'Recommend accelerating shots to hit delivery window.', 0),
    (101,'VFX Coordinator',
     'REMINDER: ILM requires approved edit cut by Friday for EP101 final composite. '
     'Chasing editorial now.', 0),
]
for i, (ep, author, text, resolved) in enumerate(NOTES, 1):
    c.execute('''INSERT INTO vfx_notes
        (item_num, author, note_text, note_date, resolved)
        VALUES (?,?,?,?,?)''',
        (i, author, text, d(random.randint(0, 30)), resolved))
db.commit()
print(f"  [8/10] {len(NOTES)} VFX notes seeded")

# ── 9. Sequences (Breakdown by Sequence & Headlines) ─────────────────────────
SEQ_DEFS = [
    # (ep, seq_name, location, est_shots, lbudget, efc, status, est_reductions, turnover_deadline, notes)
    (101, 'SC 1-4',   'INT. COMMAND DECK - NIGHT',       4,  185000, 192000, '⚠ Over Budget',
     'Consider reducing particle layer count on 3 shots',  '2026-04-15', 'ILM lead vendor'),
    (101, 'SC 5-7',   'EXT. NOVA CITY SKYLINE - DAY',    3,  168000, 172000, '✓ On Budget',
     '',                                                    '2026-04-22', 'Full CG ENV build'),
    (101, 'SC 8-9',   'INT. REACTOR CORE - CONTINUOUS',  2,   88000,  91000, '✓ On Budget',
     '',                                                    '2026-04-28', 'MPC handling FX'),
    (101, 'SC 10-12', 'EXT. ASTEROID BELT - SPACE',      3,  122000, 128000, '⚠ Over Budget',
     'WETA scope increase — added debris sim',              '2026-05-02', 'Under review'),
    (101, 'SC 13-14', 'INT. HANGAR BAY - DAY',           2,   65000,  65000, '✓ On Budget',
     '',                                                    '2026-05-10', 'DNEG assigned'),

    (102, 'SC 1-3',   'EXT. NOVA CITY SKYLINE - DAY',    3,  105000, 108000, '✓ On Budget',
     '',                                                    '2026-05-15', 'FRAMESTORE - ENV'),
    (102, 'SC 4-5',   'INT. BRIDGE - NIGHT',              2,   74000,  78000, '⚠ Over Budget',
     'Extra compositing rounds requested',                  '2026-05-20', 'DNEG'),
    (102, 'SC 6-8',   'INT. MEDICAL BAY - DAY',           3,   96000, 100000, '? Editorial-Driven',
     '',                                                    '2026-05-28', 'WETA creature shots'),
    (102, 'SC 9-11',  'EXT. ORBITAL STATION - SPACE',    3,  152000, 155000, '✓ On Budget',
     '',                                                    '2026-06-02', 'ILM full CG'),
    (102, 'SC 12-13', 'EXT. JUNGLE OUTPOST - DUSK',      2,   62000,  63000, '✓ On Budget',
     '',                                                    '2026-06-08', 'FRAMESTORE'),

    (103, 'SC 1-2',   'INT. COMMAND DECK - NIGHT',       2,   72000,  74000, '✓ On Budget',
     '',                                                    '2026-06-12', 'MPC'),
    (103, 'SC 3-6',   'EXT. JUNGLE OUTPOST - DUSK',      4,  148000, 162000, '⚠ Over Budget',
     'VORN creature rounds extending budget — cap at 5 rounds', '2026-06-20', 'WETA lead'),
    (103, 'SC 7-9',   'INT. HANGAR BAY - DAY',           3,   85000,  83000, '↓ Reducing',
     'Simplified 2 background shots to plate work',         '2026-06-25', 'DNEG'),
    (103, 'SC 10-13', 'EXT. DEEP SPACE - CONTINUOUS',    4,  142000, 145000, '✓ On Budget',
     '',                                                    '2026-07-02', 'ILM'),
    (103, 'SC 14-15', 'INT. REACTOR CORE - CONTINUOUS',  2,   58000,  58000, '✓ On Budget',
     '',                                                    '2026-07-08', 'MPC FX'),

    (104, 'SC 1-3',   'EXT. NOVA CITY SKYLINE - DAY',   3,  112000, 120000, '⚠ Over Budget',
     'Director added camera moves requiring full CG rebuild', '2026-07-15', 'FRAMESTORE'),
    (104, 'SC 4-6',   'INT. REACTOR CORE - CONTINUOUS',  3,   98000, 107000, '⚠ Over Budget',
     'Practical element integration — reshoot TBC',         '2026-07-22', 'MPC — URGENT'),
    (104, 'SC 7-10',  'EXT. ASTEROID BELT - SPACE',      4,  138000, 145000, '? Editorial-Driven',
     '',                                                    '2026-07-28', 'WETA + ILM split'),
    (104, 'SC 11-13', 'INT. BRIDGE - NIGHT',              3,   82000,  80000, '↓ Reducing',
     'Consolidated 2 wide shots to single extension',       '2026-08-02', 'DNEG'),
    (104, 'SC 14-15', 'INT. HANGAR BAY - DAY',           2,   58000,  59000, '✓ On Budget',
     '',                                                    '2026-08-08', 'ILM'),

    (105, 'SC 1-5',   'EXT. ORBITAL STATION - SPACE',    5,  210000, 215000, '✓ On Budget',
     '',                                                    '2026-08-15', 'ILM flagship sequence'),
    (105, 'SC 6-8',   'INT. COMMAND DECK - NIGHT',       3,   95000,  98000, '✓ On Budget',
     '',                                                    '2026-08-20', 'DNEG'),
    (105, 'SC 9-10',  'INT. MEDICAL BAY - DAY',          2,   68000,  71000, '⚠ Over Budget',
     'Extra round for creature interaction',                '2026-08-26', 'WETA'),
    (105, 'SC 11-14', 'EXT. ASTEROID BELT - SPACE',      4,  148000, 150000, '✓ On Budget',
     '',                                                    '2026-09-02', 'Drone swarm — MPC'),
    (105, 'SC 15-17', 'EXT. DEEP SPACE - CONTINUOUS',    3,  108000, 109000, '✓ On Budget',
     '',                                                    '2026-09-08', 'ILM wide shots'),

    (106, 'SC 1-3',   'INT. COMMAND DECK - NIGHT',       3,  105000, 108000, '✓ On Budget',
     '',                                                    '2026-09-12', 'DNEG'),
    (106, 'SC 4-6',   'EXT. JUNGLE OUTPOST - DUSK',      3,   82000,  84000, '✓ On Budget',
     '',                                                    '2026-09-18', 'FRAMESTORE + ILM'),
    (106, 'SC 7-10',  'EXT. ASTEROID BELT - SPACE',      4,  175000, 178000, '✓ On Budget',
     '',                                                    '2026-09-25', 'TITAN mech — WETA'),
    (106, 'SC 11-12', 'INT. HANGAR BAY - DAY',           2,   68000,  68000, '✓ On Budget',
     '',                                                    '2026-10-02', 'DNEG composites'),
    (106, 'SC 13-14', 'EXT. DEEP SPACE - CONTINUOUS',    2,   55000,  56000, '✓ On Budget',
     '',                                                    '2026-10-08', 'Final sequence'),
]
for i, (ep, seq_name, location, est_shots, lbudget, efc, status, est_red, deadline, notes_txt) in enumerate(SEQ_DEFS, 1):
    variance = efc - lbudget
    c.execute('''INSERT INTO sequences
        (ep, seq_name, location, est_shots, current_cut, lbudget, efc, variance_val,
         status, est_reductions, est_ctd, turnover_deadline, notes, auto_sync)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)''',
        (ep, seq_name, location, est_shots, est_shots, lbudget, efc, variance,
         status, est_red, round(efc * 0.65, 0), deadline, notes_txt))
db.commit()
print(f"  [9/9] {len(SEQ_DEFS)} sequences seeded across EPs {EP_START}–{EP_END}")

# ── 10. Scenario (budget_scenario + ep_forecast) ─────────────────────────────
SCENARIOS = [
    ('Baseline',       101, 0.0, 100.0, 0),
    ('Baseline',       102, 0.0, 100.0, 0),
    ('Baseline',       103, 0.0, 100.0, 0),
    ('Conservative',   101, 15.0, 85.0, 0),
    ('Conservative',   102, 15.0, 85.0, 0),
    ('Conservative',   103, 15.0, 85.0, 0),
    ('Optimistic',     101, 8.0, 92.0, 0),
    ('Optimistic',     102, 8.0, 92.0, 0),
    ('Worst Case',     101, 25.0, 75.0, 0),
]
for row in SCENARIOS:
    stype, ep, tax_pct, eligible_pct, net_cost = row
    c.execute('''INSERT INTO budget_scenario
        (scenario_type, ep, tax_pct, eligible_pct, net_cost)
        VALUES (?,?,?,?,?)''', (stype, ep, tax_pct, eligible_pct, net_cost))

# ep_forecast — already has rows from init_project_db, just update values
FORECAST_DATA = {
    101: (0.15, 388000, 355000, 0.40, 0.25, 0.20),
    102: (0.18, 466000, 420000, 0.35, 0.22, 0.18),
    103: (0.12, 392000, 371000, 0.38, 0.28, 0.22),
    104: (0.20, 358000, 340000, 0.42, 0.30, 0.20),
    105: (0.15, 510000, 475000, 0.38, 0.25, 0.18),
    106: (0.22, 421000, 395000, 0.40, 0.27, 0.20),
}
for ep, (cont, budget, award, elig, glob_reb, glob_pct) in FORECAST_DATA.items():
    c.execute('''UPDATE ep_forecast SET
        contingency=?, budget=?, award=?, eligible=?,
        global_rebate_pct=?, global_pct=?
        WHERE ep=?''', (cont, budget, award, elig, glob_reb, glob_pct, ep))

db.commit()
db.close()
print(f"  [10/10] Scenarios + ep_forecast seeded")

# ── Summary ────────────────────────────────────────────────────────────────────
print()
print("=" * 58)
print("  DEMO DATA SEEDED SUCCESSFULLY")
print("=" * 58)
print(f"  Project  : NOVA SERIES S1")
print(f"  Episodes : {EP_START} - {EP_END}  ({EP_END - EP_START + 1} episodes)")
print(f"  Shots    : {shots_inserted}")
print(f"  Assets   : {len(ASSET_DEFS)}")
print(f"  Bids     : {len(BID_SHOTS)}")
print(f"  Vendors  : {len(REGISTRY)}")
print(f"  Invoices : {len(INVOICES)}")
print(f"  Notes    : {len(NOTES)}")
print(f"  Sequences: {len(SEQ_DEFS)} rows")
print(f"  Scenarios: {len(SCENARIOS)} rows")
print()
print("  To launch:  python app.py")
print("  Then open:  http://localhost:5000")
print("  Click:      NOVA SERIES S1")
print("=" * 58)
