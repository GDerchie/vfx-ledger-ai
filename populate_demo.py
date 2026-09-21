"""
populate_demo.py -- Creates and fully populates a SHOWCASE demo project.
Run once:  python populate_demo.py
Then open the app and select SHOWCASE S1.
"""
import sqlite3, os, json, sys
from datetime import datetime, timedelta

# -- paths --------------------------------------------------------------------
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, 'projects')
os.makedirs(PROJECTS_DIR, exist_ok=True)
PROJECTS_DB  = os.path.join(BASE_DIR, 'projects.db')
DEMO_DB      = os.path.join(PROJECTS_DIR, 'SHOWCASE_S1.vfxdb')

# -- helpers -------------------------------------------------------------------
def pconn():
    c = sqlite3.connect(PROJECTS_DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c

def dconn():
    c = sqlite3.connect(DEMO_DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c

def date_ago(days):
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

def date_from_now(days):
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

# ---------------------------------------------------------------------------
# 1. Register project in projects.db
# ---------------------------------------------------------------------------
print('Creating project entry…')
pc = pconn()
pc.execute('''CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
    season TEXT NOT NULL DEFAULT 'S1', db_filename TEXT NOT NULL,
    db_path TEXT NOT NULL, ep_start INTEGER DEFAULT 101,
    ep_end INTEGER DEFAULT 108, description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_opened TIMESTAMP
)''')
pc.execute('DELETE FROM projects WHERE db_filename=?', ('SHOWCASE_S1.vfxdb',))
cur = pc.cursor()
cur.execute('''INSERT INTO projects (name, season, db_filename, db_path, ep_start, ep_end, description)
              VALUES (?,?,?,?,?,?,?)''',
           ('SHOWCASE', 'S1', 'SHOWCASE_S1.vfxdb', DEMO_DB, 101, 108,
            'Full demo project -- all features enabled'))
proj_id = cur.lastrowid
pc.commit(); pc.close()
print(f'  -> project id={proj_id}')

# ---------------------------------------------------------------------------
# 2. Init schema
# ---------------------------------------------------------------------------
print('Initialising schema…')
sys.path.insert(0, BASE_DIR)
import core
core.init_project_db(DEMO_DB, 101, 108)
dc = dconn()

# ---------------------------------------------------------------------------
# 3. Vendor registry
# ---------------------------------------------------------------------------
print('Populating vendor registry…')
vendors_reg = [
    ('FRAMESTORE', 'UK',      0.88, 0.20, 0.39, 'bid@framestore.com'),
    ('MPC',        'BC',      0.73, 0.12, 0.32, 'vfx@mpc.com'),
    ('DNEG',       'BC',      0.73, 0.12, 0.32, 'production@dneg.com'),
    ('ILM',        'US',      1.00, 0.08, 0.00, 'ilm@ilm.com'),
    ('RISING SUN', 'AU',      0.65, 0.10, 0.30, 'bid@risingsun.com.au'),
]
for v in vendors_reg:
    dc.execute('''INSERT OR IGNORE INTO vendor_registry
        (vendor, region, fx_rate, tax_pct, rebate_pct, contact) VALUES (?,?,?,?,?,?)''', v)

# ---------------------------------------------------------------------------
# 4. Vendor capacity
# ---------------------------------------------------------------------------
print('Populating vendor capacity…')
vendor_caps = [
    ('FRAMESTORE',  60, 0.90),
    ('MPC',         80, 0.95),
    ('DNEG',        75, 0.92),
    ('ILM',         50, 0.88),
    ('RISING SUN',  40, 0.85),
]
for v in vendor_caps:
    dc.execute('INSERT OR IGNORE INTO vendor_capacity (vendor, shots_per_month, efficiency_pct) VALUES (?,?,?)', v)

# ---------------------------------------------------------------------------
# 5. EP meta
# ---------------------------------------------------------------------------
print('Populating EP meta…')
ep_meta = {
    101: ('v4', 'v3', 'LOCKED',    0,       ''),
    102: ('v5', 'v4', 'LOCKED',    15000,   'Opening titles cut from 3 shots'),
    103: ('v3', 'v2', 'PICTURE LOCK', 0,    ''),
    104: ('v6', 'v5', 'VFX TURNOVER', 22000,'Storm sequence revised -- added 4 shots'),
    105: ('v2', 'v1', 'PRODUCTION', 0,      'Script v2 pending director notes'),
    106: ('v4', 'v3', 'LOCKED',    8000,    'Chase sequence reduced 2 shots'),
    107: ('v3', 'v2', 'VFX TURNOVER', 0,   ''),
    108: ('v1', '',   'PRODUCTION', 0,      'Season finale -- hero sequence TBC'),
}
for ep, (sv, ev, st, red, notes) in ep_meta.items():
    dc.execute('''UPDATE ep_meta SET script_v=?, edit_v=?, status=?, est_reduction=?, notes=?
                  WHERE ep=?''', (sv, ev, st, red, notes, ep))

# ---------------------------------------------------------------------------
# 6. Shots (12-16 per episode, varied types/complexity/vendors)
# ---------------------------------------------------------------------------
print('Populating shots…')

# (scene_code, s_code, location, ext_int, shot_type, complexity, vfx_desc, award_vendor, cost_est, efc, edit_count)
shots_by_ep = {
101: [
    ('SC_01','101A','SPACE STATION EXT','EXT','ENV','STANDARD','Wide orbital environment plate replacement','MPC',        18000, 17200, 1),
    ('SC_01','101B','SPACE STATION EXT','EXT','ENV','HIGH',    'Debris field CG extension full sky replace', 'MPC',       42000, 44500, 3),
    ('SC_02','102A','AIRLOCK INT',      'INT','COMP','STANDARD','Screen replacements x3 + HUD overlay',     'FRAMESTORE', 12000, 11800, 0),
    ('SC_02','102B','AIRLOCK INT',      'INT','FX',  'HIGH',    'Explosive decompression particle sim',      'FRAMESTORE', 55000, 58000, 4),
    ('SC_03','103A','CORRIDOR INT',     'INT','COMP','STANDARD','Wire removal + dust motes',                 'DNEG',        8000,  7900, 0),
    ('SC_04','104A','PLANET SURFACE EXT','EXT','ENV','HEAVY',  'Full CG alien landscape replace + 2 moons', 'MPC',        95000, 98000, 5),
    ('SC_04','104B','PLANET SURFACE EXT','EXT','CG', 'HERO',   'Hero creature -- full body sim + cloth',     'ILM',       180000,185000, 7),
    ('SC_05','105A','BRIDGE INT',       'INT','COMP','STANDARD','Holographic display comp',                  'FRAMESTORE', 15000, 14500, 1),
    ('SC_05','105B','BRIDGE INT',       'INT','GFX', 'STANDARD','Navigation screen content + alerts',       'RISING SUN',  9000,  8800, 0),
    ('SC_06','106A','HANGAR EXT',       'EXT','CG',  'HIGH',   'CG shuttle landing with dust FX',           'MPC',        62000, 65000, 3),
    ('SC_06','106B','HANGAR EXT',       'EXT','FX',  'HIGH',   'Engine exhaust + heat haze sim',            'MPC',        38000, 39500, 2),
    ('SC_07','107A','ENGINE ROOM INT',  'INT','FX',  'STANDARD','Steam vents + sparks practical ext',       'DNEG',       14000, 13500, 1),
    ('SC_08','108A','COMMAND CENTRE INT','INT','COMP','STANDARD','Window replacement + exterior comp',      'FRAMESTORE', 22000, 21000, 2),
    ('SC_09','109A','ESCAPE POD INT',   'INT','COMP','HIGH',   'Zero-G debris simulation + actor rig removal','ILM',      48000, 51000, 4),
],
102: [
    ('SC_10','201A','CITY ROOFTOP EXT', 'EXT','ENV','HIGH',    'Futuristic skyline full CG extension',      'DNEG',       72000, 74000, 3),
    ('SC_10','201B','CITY ROOFTOP EXT', 'EXT','COMP','STANDARD','Sky replacement + ambient light adjust',   'DNEG',       18000, 17000, 1),
    ('SC_11','202A','ALLEY INT',        'INT','FX',  'STANDARD','Hologram projector beam practical ext',    'RISING SUN', 11000, 10500, 0),
    ('SC_11','202B','ALLEY INT',        'INT','COMP','HIGH',   'Crowd digital extension + 40 crowd sims',   'MPC',        55000, 58000, 4),
    ('SC_12','203A','LAB INT',          'INT','GFX', 'STANDARD','Screen content x6 + holotable display',   'RISING SUN', 13000, 12500, 1),
    ('SC_12','203B','LAB INT',          'INT','CG',  'HIGH',   'Microscopic CG sequence -- full CG env',    'FRAMESTORE', 88000, 91000, 5),
    ('SC_13','204A','UNDERGROUND EXT',  'EXT','ENV','HEAVY',   'Cave tunnel CG extension 200m depth',      'MPC',        78000, 80000, 4),
    ('SC_13','204B','UNDERGROUND EXT',  'EXT','FX',  'HIGH',   'Rock collapse simulation 3000 chunks',     'MPC',        65000, 67000, 3),
    ('SC_14','205A','HOSPITAL INT',     'INT','COMP','STANDARD','Window replacement + weather outside',     'DNEG',       16000, 15500, 1),
    ('SC_14','205B','HOSPITAL INT',     'INT','FX',  'HIGH',   'Biotech scanning beam full VFX build',     'FRAMESTORE', 49000, 52000, 3),
    ('SC_15','206A','FOREST EXT',       'EXT','ENV','STANDARD','Subtle sky enhancement + tree extension',  'RISING SUN', 14000, 13500, 0),
    ('SC_16','207A','WAREHOUSE INT',    'INT','COMP','STANDARD','Wire + rig removal x8',                   'DNEG',        9500,  9200, 0),
    ('SC_17','208A','CONTROL ROOM INT', 'INT','GFX', 'HIGH',   'Full wall display content + alerts CG',    'FRAMESTORE', 38000, 40000, 2),
],
103: [
    ('SC_18','301A','OCEAN EXT',        'EXT','ENV','HEAVY',   'Full CG ocean + storm surge 300m wide',    'ILM',       145000,150000, 6),
    ('SC_18','301B','OCEAN EXT',        'EXT','FX',  'HERO',   'Hero wave destruction sim -- ship impact',  'ILM',       195000,200000, 8),
    ('SC_19','302A','SUBMARINE INT',    'INT','COMP','STANDARD','Porthole water comp + caustics',           'FRAMESTORE', 22000, 21500, 1),
    ('SC_19','302B','SUBMARINE INT',    'INT','FX',  'HIGH',   'Pressure breach water ingress sim',        'FRAMESTORE', 58000, 61000, 4),
    ('SC_20','303A','RESEARCH BASE EXT','EXT','ENV','HIGH',    'Arctic CG extension -- full sky + ice',     'DNEG',       68000, 70000, 3),
    ('SC_20','303B','RESEARCH BASE EXT','EXT','CG',  'HEAVY',  'CG blizzard + 200 snow particle sims',    'DNEG',       85000, 88000, 5),
    ('SC_21','304A','CAVE SYSTEM EXT',  'EXT','ENV','STANDARD','Stalactite extension + atmospheric',       'MPC',        25000, 24000, 1),
    ('SC_21','304B','CAVE SYSTEM EXT',  'EXT','FX',  'HIGH',   'Bioluminescent particle system 80K pts',  'MPC',        44000, 46000, 3),
    ('SC_22','305A','MESS HALL INT',    'INT','COMP','STANDARD','Hero food CG + steam sim',                'RISING SUN', 12000, 11500, 0),
    ('SC_23','306A','DOCKING BAY EXT',  'EXT','CG',  'HERO',   'Hero spacecraft -- full CG build + anim',  'ILM',       220000,228000, 9),
    ('SC_23','306B','DOCKING BAY EXT',  'EXT','ENV','HIGH',    'Full facility extension + 40 CG extras',  'MPC',        72000, 75000, 4),
    ('SC_24','307A','MEDICAL BAY INT',  'INT','COMP','STANDARD','Surgical screen replacement + glow fx',   'DNEG',       18000, 17500, 1),
    ('SC_25','308A','BRIDGE INT',       'INT','GFX', 'HIGH',   'Battle tactical overlay -- 8 screens',     'FRAMESTORE', 42000, 44000, 2),
],
104: [
    ('SC_26','401A','VOLCANO EXT',      'EXT','ENV','HERO',    'Active volcano -- full CG replacement 4K', 'ILM',       210000,215000, 8),
    ('SC_26','401B','VOLCANO EXT',      'EXT','FX',  'HERO',   'Lava flow hero sim -- 800K particles',     'ILM',       185000,190000, 7),
    ('SC_27','402A','JUNGLE EXT',       'EXT','ENV','HIGH',    'Dense jungle CG extension + creature rig','MPC',        78000, 81000, 4),
    ('SC_27','402B','JUNGLE EXT',       'EXT','CG',  'HEAVY',  'Alien flora animated -- 200 unique plants','MPC',        92000, 95000, 5),
    ('SC_28','403A','BUNKER INT',       'INT','COMP','STANDARD','Explosion comp behind window x2',         'DNEG',       28000, 27500, 2),
    ('SC_28','403B','BUNKER INT',       'INT','FX',  'HIGH',   'Shockwave distortion + structural damage', 'DNEG',      56000, 59000, 3),
    ('SC_29','404A','DESERT EXT',       'EXT','ENV','HEAVY',   'Sand dune CG replace + storm approach',   'RISING SUN', 65000, 67000, 3),
    ('SC_29','404B','DESERT EXT',       'EXT','FX',  'HIGH',   'Sandstorm full sim -- hero vehicle buried','RISING SUN', 55000, 57000, 4),
    ('SC_30','405A','COMMAND SHIP INT', 'INT','GFX', 'HIGH',   'War room holographic battle display',     'FRAMESTORE', 48000, 50000, 3),
    ('SC_30','405B','COMMAND SHIP INT', 'INT','COMP','STANDARD','Practical explosion ext + grading',      'FRAMESTORE', 19000, 18500, 1),
    ('SC_31','406A','CITY STREET EXT',  'EXT','COMP','HIGH',   'Post-battle destruction ext + 60 extras', 'MPC',        72000, 74000, 4),
    ('SC_32','407A','ESCAPE TUNNEL INT','INT','FX',  'STANDARD','Dust + concrete debris practical ext',   'DNEG',       16000, 15500, 1),
    ('SC_33','408A','SATELLITE EXT',    'EXT','CG',  'HERO',   'Full CG orbital platform + solar panels', 'ILM',       165000,170000, 6),
],
105: [
    ('SC_34','501A','ICE PLANET EXT',   'EXT','ENV','HEAVY',   'Full alien ice world CG replacement',     'ILM',       155000,160000, 6),
    ('SC_34','501B','ICE PLANET EXT',   'EXT','FX',  'HIGH',   'Cracking ice sim 500K rigid body frags',  'ILM',       110000,115000, 5),
    ('SC_35','502A','FORTRESS EXT',     'EXT','ENV','HEAVY',   'Gothic CG fortress + sky + environment',  'DNEG',      120000,125000, 6),
    ('SC_35','502B','FORTRESS EXT',     'EXT','COMP','HIGH',   'Siege machine comp + dust + fire ext',    'DNEG',       68000, 71000, 4),
    ('SC_36','503A','THRONE ROOM INT',  'INT','CG',  'HERO',   'Hero creature -- facial anim + cloth sim', 'ILM',       190000,195000, 8),
    ('SC_36','503B','THRONE ROOM INT',  'INT','COMP','HIGH',   'Particle energy beam + glow fx',          'FRAMESTORE', 52000, 54000, 3),
    ('SC_37','504A','BATTLEFIELD EXT',  'EXT','COMP','HEAVY',  '300 CG crowd agents -- battle simulation', 'MPC',       108000,112000, 6),
    ('SC_37','504B','BATTLEFIELD EXT',  'EXT','FX',  'HEAVY',  'Explosion array -- 12 hero blasts + fire','MPC',        95000, 98000, 5),
    ('SC_38','505A','WAR CAMP EXT',     'EXT','ENV','STANDARD','Background tent extension + fire glow',   'RISING SUN', 22000, 21000, 1),
    ('SC_38','505B','WAR CAMP EXT',     'EXT','COMP','STANDARD','Sky replacement + mood relighting',      'RISING SUN', 15000, 14500, 0),
    ('SC_39','506A','TOWER INT',        'INT','COMP','HIGH',   'Magic particle system + practical ext',   'FRAMESTORE', 58000, 61000, 3),
    ('SC_40','507A','DUNGEON INT',      'INT','FX',  'STANDARD','Torch fire sim + smoke trails',          'DNEG',       14000, 13500, 0),
    ('SC_41','508A','CLIFFSIDE EXT',    'EXT','ENV','HIGH',    'Vertical cliff CG extension 500m drop',   'MPC',        62000, 64000, 3),
    ('SC_41','508B','CLIFFSIDE EXT',    'EXT','FX',  'HIGH',   'Rockfall sim 2000 rigid body chunks',     'MPC',        48000, 50000, 3),
],
106: [
    ('SC_42','601A','DEEP SPACE EXT',   'EXT','ENV','HERO',    'Nebula + star field full CG replacement', 'ILM',       175000,180000, 7),
    ('SC_42','601B','DEEP SPACE EXT',   'EXT','CG',  'HERO',   'Fleet of 12 CG ships -- full battle anim','ILM',       240000,248000,10),
    ('SC_43','602A','COCKPIT INT',      'INT','GFX', 'HIGH',   'Targeting HUD + proximity alerts x4',    'FRAMESTORE', 38000, 39500, 2),
    ('SC_43','602B','COCKPIT INT',      'INT','COMP','STANDARD','Space background through canopy',        'FRAMESTORE', 20000, 19500, 1),
    ('SC_44','603A','ENEMY SHIP EXT',   'EXT','CG',  'HEAVY',  'CG dreadnought -- full asset build + anim','MPC',      135000,140000, 7),
    ('SC_44','603B','ENEMY SHIP EXT',   'EXT','FX',  'HEAVY',  'Shield impact VFX -- energy bubble sim',  'MPC',        88000, 91000, 5),
    ('SC_45','604A','WEAPONS BAY INT',  'INT','FX',  'HIGH',   'Railgun charge + fire sim + flash',       'DNEG',       52000, 54000, 3),
    ('SC_45','604B','WEAPONS BAY INT',  'INT','COMP','STANDARD','Muzzle flash comp + practical ext',      'DNEG',       18000, 17500, 1),
    ('SC_46','605A','ASTEROID FIELD EXT','EXT','CG', 'HEAVY',  '500 CG asteroids -- collision physics',   'ILM',       118000,122000, 6),
    ('SC_46','605B','ASTEROID FIELD EXT','EXT','FX', 'HIGH',   'Debris explosion -- 20K fragment sim',    'ILM',        78000, 80000, 4),
    ('SC_47','606A','ESCAPE POD EXT',   'EXT','COMP','STANDARD','CG pod against star field',              'RISING SUN', 18000, 17500, 1),
    ('SC_47','606B','ESCAPE POD EXT',   'EXT','ENV','STANDARD','Planet approach CG atmosphere entry',    'RISING SUN', 28000, 27500, 2),
    ('SC_48','607A','MEDICAL BAY INT',  'INT','COMP','STANDARD','Bio-monitor screen replacement x3',     'FRAMESTORE', 12000, 11500, 0),
],
107: [
    ('SC_49','701A','RUINS EXT',        'EXT','ENV','HEAVY',   'Ancient city full CG ruin extension',    'DNEG',       115000,119000, 5),
    ('SC_49','701B','RUINS EXT',        'EXT','CG',  'HEAVY',  'Alien overgrowth animated -- 400 plants', 'DNEG',       92000, 95000, 5),
    ('SC_50','702A','SHRINE INT',       'INT','FX',  'HERO',   'Mystical energy manifestation hero VFX', 'ILM',       200000,208000, 9),
    ('SC_50','702B','SHRINE INT',       'INT','COMP','HIGH',   'Practical candle ext + CG glow build',   'FRAMESTORE', 44000, 46000, 3),
    ('SC_51','703A','CLIFFTOP EXT',     'EXT','ENV','HIGH',    'Coastal CG extension + stormy sea',      'MPC',        72000, 74000, 4),
    ('SC_51','703B','CLIFFTOP EXT',     'EXT','FX',  'HIGH',   'Lightning strike + thunder FX build',    'MPC',        48000, 50000, 3),
    ('SC_52','704A','CAVE MOUTH EXT',   'EXT','ENV','STANDARD','Rock arch extension + atmosphere',       'RISING SUN', 20000, 19500, 1),
    ('SC_52','704B','CAVE MOUTH EXT',   'EXT','COMP','HIGH',   'Creature reveal -- digital double hero',  'ILM',        88000, 91000, 5),
    ('SC_53','705A','VILLAGE EXT',      'EXT','COMP','HEAVY',  '500 CG crowd agents -- village evacuation','MPC',      105000,108000, 6),
    ('SC_53','705B','VILLAGE EXT',      'EXT','FX',  'HIGH',   'Fire spread sim -- 8 buildings burning',  'MPC',        78000, 81000, 4),
    ('SC_54','706A','ARMORY INT',       'INT','GFX', 'STANDARD','Weapons scan display + inventory UI',   'RISING SUN', 16000, 15500, 1),
    ('SC_55','707A','PASS EXT',         'EXT','ENV','HIGH',    'Mountain pass CG extension + fog sim',   'DNEG',       62000, 64000, 3),
    ('SC_55','707B','PASS EXT',         'EXT','FX',  'HEAVY',  'Avalanche sim -- 50K snow chunks',        'DNEG',       95000, 98000, 5),
    ('SC_56','708A','COMMAND TENT INT', 'INT','GFX', 'HIGH',   'Battle map holographic display',         'FRAMESTORE', 35000, 36500, 2),
],
108: [
    ('SC_57','801A','FINAL BATTLEFIELD EXT','EXT','ENV','HERO','Apocalyptic sky full CG -- ash + red sun', 'ILM',       220000,228000,10),
    ('SC_57','801B','FINAL BATTLEFIELD EXT','EXT','CG','HERO', 'Final battle CG armies -- 1000 agents',   'ILM',       280000,290000,12),
    ('SC_57','801C','FINAL BATTLEFIELD EXT','EXT','FX','HERO', 'Mass destruction FX -- 30 explosion sims','ILM',       195000,200000, 9),
    ('SC_58','802A','THRONE ROOM INT',  'INT','CG',  'HERO',   'Final boss creature -- full hero build',  'ILM',       245000,252000,11),
    ('SC_58','802B','THRONE ROOM INT',  'INT','FX',  'HERO',   'Energy clash hero FX -- climactic build', 'FRAMESTORE',165000,170000, 8),
    ('SC_59','803A','PALACE EXT',       'EXT','ENV','HEAVY',   'Full palace CG rebuild -- post destruction','DNEG',    138000,142000, 7),
    ('SC_59','803B','PALACE EXT',       'EXT','FX',  'HEAVY',  'Structural collapse sim -- 200K frags',   'DNEG',      118000,122000, 6),
    ('SC_60','804A','ESCAPE ROUTE INT', 'INT','COMP','HIGH',   'Collapsing tunnel comp + debris sim',    'MPC',        68000, 71000, 4),
    ('SC_60','804B','ESCAPE ROUTE INT', 'INT','FX',  'HIGH',   'Water ingress sim + particle system',    'MPC',        55000, 57000, 3),
    ('SC_61','805A','ORBIT EXT',        'EXT','ENV','HEAVY',   'Final orbital platform CG environment',  'ILM',       158000,163000, 7),
    ('SC_61','805B','ORBIT EXT',        'EXT','CG',  'HEAVY',  'Station destruction -- 400K fragment sim','ILM',       178000,184000, 8),
    ('SC_62','806A','ESCAPE SHIP INT',  'INT','COMP','STANDARD','Window replacement -- fire + debris',     'FRAMESTORE', 32000, 31000, 2),
    ('SC_62','806B','ESCAPE SHIP INT',  'INT','GFX', 'HIGH',   'Emergency panel displays x8 + alarms',   'RISING SUN', 28000, 27500, 2),
    ('SC_63','807A','SUNSET BEACH EXT', 'EXT','ENV','STANDARD','Ending -- hero sky enhancement',          'RISING SUN', 12000, 11500, 0),
],
}

for ep, shot_list in shots_by_ep.items():
    for i, (sc, scode, loc, ei, stype, cmp, vdesc, vendor, cost, efc, edits) in enumerate(shot_list, 1):
        dc.execute('''INSERT INTO shots
            (ep, shot_num, scene_code, s_code, location, ext_int, shot_type, complexity,
             vfx_desc, script_desc, award_vendor, cost_est, budget_est, budget_award_cost,
             efc, edit_count, shot_est)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)''',
            (ep, i, sc, scode, loc, ei, stype, cmp,
             vdesc, vdesc, vendor, cost, cost, cost, efc, edits))

print(f'  -> {sum(len(v) for v in shots_by_ep.values())} shots across 8 episodes')

# ---------------------------------------------------------------------------
# 7. Assets
# ---------------------------------------------------------------------------
print('Populating assets…')
assets = [
    (103, 'SC_23', 'Hero Spacecraft',         'CG Hero ship -- primary transport',        'Vehicle',     0, 225000, 'ILM'),
    (104, 'SC_33', 'Orbital Platform',        'Full CG satellite build + animation rig', 'Environment', 0, 185000, 'ILM'),
    (103, 'SC_23', 'Alien Creature Alpha',    'Bipedal predator -- hero creature build',  'Character',   1, 210000, 'ILM'),
    (101, 'SC_04', 'Space Station',           'Full modular station -- 14 sections',      'Environment', 0, 320000, 'MPC'),
    (102, 'SC_13', 'Underground Complex',     'Cave system -- procedural geometry',       'Environment', 0, 145000, 'MPC'),
    (106, 'SC_44', 'Enemy Dreadnought',       'Hostile capital ship -- full CG asset',    'Vehicle',     0, 295000, 'MPC'),
    (101, 'SC_04', 'Planet Surface Alpha',    'Alien terrain -- 2km2 tile system',        'Environment', 0, 178000, 'MPC'),
    (107, 'SC_49', 'Ancient Ruins',           'Procedural ruin system -- 80 buildings',   'Environment', 0, 165000, 'DNEG'),
    (103, 'SC_20', 'Research Base',           'Arctic facility -- modular CG build',      'Environment', 0, 142000, 'DNEG'),
    (108, 'SC_59', 'Palace Destruction',      'Full palace geometry for destruction sim','Environment', 1, 198000, 'DNEG'),
    (105, 'SC_35', 'Fortress',                'Gothic fortification -- stone + towers',   'Environment', 0, 188000, 'DNEG'),
    (101, 'SC_06', 'Shuttle Craft',           'Small landing craft -- 4 variants',        'Vehicle',     0,  85000, 'MPC'),
    (108, 'SC_58', 'Final Boss Creature',     'Hero antagonist creature -- hero build',   'Character',   1, 265000, 'ILM'),
    (102, 'SC_12', 'Microscopic World',       'Full CG micro-environment -- unique world','Environment', 0, 112000, 'FRAMESTORE'),
]
for ep, sc, name, desc, atype, repeat, budget, vendor in assets:
    dc.execute('''INSERT INTO assets
        (ep, scene_code, asset_name, description, asset_type, repeat_asset,
         est_budget, actual_spend, award_vendor)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (ep, sc, name, desc, atype, repeat, budget, int(budget*0.97), vendor))

# ---------------------------------------------------------------------------
# 8. Bid Compare (3-4 vendors per scene for EPs 101-105)
# ---------------------------------------------------------------------------
print('Populating bid compare…')

# (ep, sc, setting, novfx, scount, vfxtype, version, award, lockbudget, efc, {vendor: bid})
bids = [
  # EP 101
  (101,'SC_01','SPACE STATION EXT',0,2,'ENV',   1,'MPC',       60000, 61700,
   {'MPC':60000,'FRAMESTORE':68000,'DNEG':57500,'ILM':72000}),
  (101,'SC_04','PLANET SURFACE EXT',0,2,'ENV+CG',1,'ILM',     275000,283000,
   {'ILM':275000,'MPC':295000,'FRAMESTORE':310000}),
  (101,'SC_06','HANGAR EXT',       0,2,'CG+FX',  1,'MPC',     100000,104500,
   {'MPC':100000,'DNEG':108000,'ILM':115000,'RISING SUN':95000}),
  (101,'SC_08','COMMAND CENTRE INT',0,1,'COMP',  1,'FRAMESTORE',22000,21000,
   {'FRAMESTORE':22000,'DNEG':24000,'RISING SUN':20000}),
  # EP 102
  (102,'SC_10','CITY ROOFTOP EXT', 0,2,'ENV',    1,'DNEG',     90000, 91000,
   {'DNEG':90000,'MPC':96000,'FRAMESTORE':102000,'RISING SUN':88000}),
  (102,'SC_12','LAB INT',          0,2,'GFX+CG',  1,'FRAMESTORE',101000,103500,
   {'FRAMESTORE':101000,'MPC':108000,'ILM':112000}),
  (102,'SC_13','UNDERGROUND EXT',  0,2,'ENV+FX',  1,'MPC',     143000,147000,
   {'MPC':143000,'DNEG':152000,'RISING SUN':138000,'ILM':161000}),
  # EP 103
  (103,'SC_18','OCEAN EXT',        0,2,'ENV+FX',  1,'ILM',     340000,350000,
   {'ILM':340000,'MPC':368000,'FRAMESTORE':385000}),
  (103,'SC_20','RESEARCH BASE EXT',0,2,'ENV+CG',  1,'DNEG',    153000,158000,
   {'DNEG':153000,'MPC':165000,'ILM':172000,'RISING SUN':148000}),
  (103,'SC_23','DOCKING BAY EXT',  0,2,'CG+ENV',  1,'ILM',     292000,303000,
   {'ILM':292000,'MPC':315000,'FRAMESTORE':328000}),
  # EP 104
  (104,'SC_26','VOLCANO EXT',      0,2,'ENV+FX',  1,'ILM',     395000,405000,
   {'ILM':395000,'MPC':420000,'FRAMESTORE':438000}),
  (104,'SC_27','JUNGLE EXT',       0,2,'ENV+CG',  1,'MPC',     170000,176000,
   {'MPC':170000,'DNEG':182000,'ILM':195000,'RISING SUN':165000}),
  (104,'SC_33','SATELLITE EXT',    0,1,'CG',      1,'ILM',     165000,170000,
   {'ILM':165000,'MPC':178000,'FRAMESTORE':185000}),
  # EP 105
  (105,'SC_36','THRONE ROOM INT',  0,2,'CG+COMP', 1,'ILM',     242000,249000,
   {'ILM':242000,'FRAMESTORE':258000,'MPC':271000}),
  (105,'SC_37','BATTLEFIELD EXT',  0,2,'COMP+FX', 1,'MPC',     203000,210000,
   {'MPC':203000,'DNEG':218000,'ILM':228000,'RISING SUN':198000}),
  (105,'SC_41','CLIFFSIDE EXT',    0,2,'ENV+FX',  1,'MPC',     110000,114000,
   {'MPC':110000,'DNEG':118000,'FRAMESTORE':124000,'RISING SUN':106000}),
  # V2 revision for SC_26
  (104,'SC_26','VOLCANO EXT',      0,2,'ENV+FX',  2,'ILM',     395000,406000,
   {'ILM':395000,'MPC':415000,'FRAMESTORE':432000}),
  # NO VFX scenes
  (101,'SC_03','CORRIDOR INT',     1,3,'--',       1,'',         0,     0,     {}),
  (102,'SC_15','FOREST EXT',       1,2,'--',       1,'',         0,     0,     {}),
]

for b in bids:
    ep,sc,setting,novfx,scount,vfxtype,ver,award,lb,efc,vbids = b
    dc.execute('''INSERT INTO bid_compare
        (ep, sc, setting, novfx, scount, vfxtype, version, award, lockbudget, efc, vendor_bids)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (ep,sc,setting,novfx,scount,vfxtype,ver,award,lb,efc,json.dumps(vbids)))

# ---------------------------------------------------------------------------
# 9. Vendor Tracker
# ---------------------------------------------------------------------------
print('Populating vendor tracker…')

# (vendor, region, ep, tot_award, paid, pending)
tracker_rows = [
  ('FRAMESTORE','UK', 101, 169000, 169000,     0),
  ('FRAMESTORE','UK', 102, 189000, 189000,     0),
  ('FRAMESTORE','UK', 103, 164000, 120000, 44000),
  ('FRAMESTORE','UK', 104,  67000,      0, 67000),
  ('FRAMESTORE','UK', 105, 110000,      0,110000),
  ('FRAMESTORE','UK', 106,  70000,      0, 70000),
  ('FRAMESTORE','UK', 107,  79000,      0, 79000),
  ('FRAMESTORE','UK', 108, 197000,      0,197000),

  ('MPC',       'BC', 101, 160000, 160000,     0),
  ('MPC',       'BC', 102, 280000, 280000,     0),
  ('MPC',       'BC', 103, 241000, 200000, 41000),
  ('MPC',       'BC', 104, 345000, 180000,165000),
  ('MPC',       'BC', 105, 403000,      0,403000),
  ('MPC',       'BC', 106, 426000,      0,426000),
  ('MPC',       'BC', 107, 378000,      0,378000),
  ('MPC',       'BC', 108, 123000,      0,123000),

  ('DNEG',      'BC', 101,  22000,  22000,     0),
  ('DNEG',      'BC', 102, 162500, 162500,     0),
  ('DNEG',      'BC', 103, 325000, 200000,125000),
  ('DNEG',      'BC', 104,  74000,      0, 74000),
  ('DNEG',      'BC', 105,       0,     0,     0),
  ('DNEG',      'BC', 107, 572000,      0,572000),
  ('DNEG',      'BC', 108, 256000,      0,256000),

  ('ILM',       'US', 101, 228000, 228000,     0),
  ('ILM',       'US', 102,       0,     0,     0),
  ('ILM',       'US', 103, 660000, 400000,260000),
  ('ILM',       'US', 104, 555000, 200000,355000),
  ('ILM',       'US', 105, 778000,      0,778000),
  ('ILM',       'US', 106, 813000,      0,813000),
  ('ILM',       'US', 107, 288000,      0,288000),
  ('ILM',       'US', 108,1318000,      0,      0),

  ('RISING SUN','AU', 101,   9000,   9000,     0),
  ('RISING SUN','AU', 102,  38500,  38500,     0),
  ('RISING SUN','AU', 103,  12000,  12000,     0),
  ('RISING SUN','AU', 104, 120000,  60000, 60000),
  ('RISING SUN','AU', 105,  37000,      0, 37000),
  ('RISING SUN','AU', 106,  46000,      0, 46000),
  ('RISING SUN','AU', 107,  16000,      0, 16000),
  ('RISING SUN','AU', 108,  40500,      0, 40500),
]

for vendor, region, ep, tot_award, paid, pending in tracker_rows:
    remaining = tot_award - paid - pending
    fx = {'UK':0.88,'BC':0.73,'AU':0.65,'US':1.0}.get(region,1.0)
    rebate = {'UK':0.39,'BC':0.32,'AU':0.30,'US':0.0}.get(region,0.0)
    tax    = {'UK':0.20,'BC':0.12,'AU':0.10,'US':0.08}.get(region,0.0)
    gross_local = tot_award / fx if fx else tot_award
    gross_usd   = tot_award
    tax_amt     = gross_local * tax
    gross_tax   = gross_local + tax_amt
    rebate_amt  = gross_local * rebate
    net         = gross_tax - rebate_amt
    dc.execute('''INSERT INTO vendor_tracker
        (vendor, region, ep, award_ep, tot_award, paid, pending, remaining,
         gross_local, gross_usd, sale_tax_amount, gross_plus_tax,
         tax_rebate_amt, net_after_rebate, final_price)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (vendor, region, ep, tot_award, tot_award, paid, pending, remaining,
         round(gross_local), gross_usd, round(tax_amt),
         round(gross_tax), round(rebate_amt), round(net), round(net)))

# ---------------------------------------------------------------------------
# 10. Invoice Log
# ---------------------------------------------------------------------------
print('Populating invoice log…')

invoices = [
  # FRAMESTORE
  ('FRAMESTORE',101,'FS-2024-001',date_ago(180),  84500,'Paid',    date_ago(175),'EP101 first delivery'),
  ('FRAMESTORE',101,'FS-2024-002',date_ago(140),  84500,'Paid',    date_ago(135),'EP101 final delivery'),
  ('FRAMESTORE',102,'FS-2024-003',date_ago(130), 189000,'Paid',    date_ago(125),'EP102 full delivery'),
  ('FRAMESTORE',103,'FS-2024-004',date_ago( 80), 120000,'Paid',    date_ago( 75),'EP103 first delivery'),
  ('FRAMESTORE',103,'FS-2024-005',date_ago( 20),  44000,'Approved',date_ago( 18),'EP103 final delivery'),
  ('FRAMESTORE',104,'FS-2024-006',date_from_now(15), 67000,'Pending','','EP104 delivery due'),
  ('FRAMESTORE',105,'FS-2024-007',date_from_now(45),110000,'Pending','','EP105 pre-production'),
  # MPC
  ('MPC',       101,'MPC-2024-001',date_ago(170),160000,'Paid',    date_ago(165),'EP101 full delivery'),
  ('MPC',       102,'MPC-2024-002',date_ago(125),140000,'Paid',    date_ago(120),'EP102 first delivery'),
  ('MPC',       102,'MPC-2024-003',date_ago( 90),140000,'Paid',    date_ago( 85),'EP102 final delivery'),
  ('MPC',       103,'MPC-2024-004',date_ago( 60),200000,'Paid',    date_ago( 55),'EP103 first delivery'),
  ('MPC',       103,'MPC-2024-005',date_ago( 15), 41000,'Approved',date_ago( 12),'EP103 VFX finals'),
  ('MPC',       104,'MPC-2024-006',date_from_now( 5),172500,'Pending','','EP104 first delivery'),
  ('MPC',       104,'MPC-2024-007',date_from_now(35),172500,'Pending','','EP104 final delivery'),
  # DNEG
  ('DNEG',      101,'DN-2024-001', date_ago(165),  22000,'Paid',   date_ago(160),'EP101 comp delivery'),
  ('DNEG',      102,'DN-2024-002', date_ago(115), 162500,'Paid',   date_ago(110),'EP102 full delivery'),
  ('DNEG',      103,'DN-2024-003', date_ago( 50), 200000,'Paid',   date_ago( 45),'EP103 environment delivery'),
  ('DNEG',      103,'DN-2024-004', date_ago(  8), 125000,'Approved',date_ago( 5),'EP103 FX delivery'),
  ('DNEG',      104,'DN-2024-005', date_from_now(20), 74000,'Pending','','EP104 bunker sequence'),
  # ILM
  ('ILM',       101,'ILM-2024-001',date_ago(160), 228000,'Paid',   date_ago(155),'EP101 creature + ship'),
  ('ILM',       103,'ILM-2024-002',date_ago( 70), 400000,'Paid',   date_ago( 65),'EP103 ocean hero delivery'),
  ('ILM',       103,'ILM-2024-003',date_ago( 10), 260000,'Approved',date_ago( 8),'EP103 final VFX'),
  ('ILM',       104,'ILM-2024-004',date_from_now( 3), 277500,'Pending','','EP104 volcano first delivery'),
  ('ILM',       104,'ILM-2024-005',date_from_now(30), 277500,'Pending','','EP104 volcano final delivery'),
  # RISING SUN
  ('RISING SUN',101,'RS-2024-001', date_ago(155),   9000,'Paid',   date_ago(150),'EP101 GFX screens'),
  ('RISING SUN',102,'RS-2024-002', date_ago(105),  38500,'Paid',   date_ago(100),'EP102 full delivery'),
  ('RISING SUN',103,'RS-2024-003', date_ago( 55),  12000,'Paid',   date_ago( 50),'EP103 mess hall'),
  ('RISING SUN',104,'RS-2024-004', date_ago( 10),  60000,'Approved',date_ago( 7),'EP104 desert first'),
  ('RISING SUN',104,'RS-2024-005', date_from_now(25), 60000,'Pending','','EP104 desert final'),
]

for inv in invoices:
    vendor, ep, inv_num, inv_date, amount, status, approve_date, notes = inv
    dc.execute('''INSERT INTO invoice_log
        (vendor, episode, inv_num, inv_date, amount, status, approve_date, notes)
        VALUES (?,?,?,?,?,?,?,?)''',
        (vendor, ep, inv_num, inv_date, amount, status, approve_date, notes))

# ---------------------------------------------------------------------------
# 11. Sequences
# ---------------------------------------------------------------------------
print('Populating sequences…')
seqs = [
  (101,'SPACE STATION','SPACE',   14, 14, 588000,  605000),
  (102,'CITY PURSUIT', 'URBAN',   13, 12, 621500,  635000),
  (103,'OCEAN DESCENT','OCEAN',   13, 13, 1022000,1048000),
  (104,'VOLCANO RUN',  'TERRAIN', 13, 13, 1000000,1030000),
  (105,'SIEGE',        'BATTLE',  14, 14, 1115000,1147000),
  (106,'SPACE BATTLE', 'SPACE',   13, 11,  984000,1012000),
  (107,'RUINS QUEST',  'TERRAIN', 14, 14,  983000,1012000),
  (108,'FINAL STAND',  'BATTLE',  14, 14, 2356000,2430000),
]
for ep, name, loc, est, cur, budget, efc in seqs:
    dc.execute('''INSERT INTO sequences
        (ep, seq_name, location, est_shots, current_cut, lbudget, efc, status)
        VALUES (?,?,?,?,?,?,?,?)''',
        (ep, name, loc, est, cur, budget, efc, 'Active'))

# ---------------------------------------------------------------------------
# 12. Notes
# ---------------------------------------------------------------------------
print('Populating notes…')
notes = [
  (1,'PRODUCER', 'EP108 finale budget under review -- director wants additional destruction shots. Estimate +$180K.', date_ago(5),0),
  (2,'VFX SUPE', 'ILM creature rig delivery delayed by 2 weeks -- impacts EP105 and EP108 schedule.', date_ago(12),0),
  (3,'PRODUCER', 'MPC confirmed EP104 jungle extension scope increase -- 4 additional plant species.', date_ago(18),1),
  (4,'VFX COORD','FRAMESTORE invoice FS-2024-005 received -- routing to finance for approval.', date_ago(20),1),
  (5,'VFX SUPE', 'DNEG EP103 ocean environment approved at dailies. Outstanding: foam simulation pass.', date_ago(25),1),
  (6,'PRODUCER', 'Budget review: total season VFX award tracking +4.2% vs locked budget. Contingency activated.', date_ago(8),0),
  (7,'VFX COORD','All EP101 and EP102 vendors fully paid -- tracker reconciled.', date_ago(3),1),
  (8,'VFX SUPE', 'EP106 space battle scope: ILM requested +2 weeks for fleet destruction hero shot.', date_ago(2),0),
]
for item_num, author, text, nd, resolved in notes:
    dc.execute('INSERT INTO vfx_notes (item_num, author, note_text, note_date, resolved) VALUES (?,?,?,?,?)',
               (item_num, author, text, nd, resolved))

# ---------------------------------------------------------------------------
# 13. EP Forecast
# ---------------------------------------------------------------------------
print('Populating EP forecast…')
ep_fc = {
    101: (0.10, 588000,  588000, 0.70, 0.18),
    102: (0.10, 690000,  671000, 0.65, 0.18),
    103: (0.12,1100000,1068000,  0.72, 0.20),
    104: (0.12,1050000,1030000,  0.68, 0.20),
    105: (0.15,1200000,1147000,  0.70, 0.20),
    106: (0.15,1050000,1012000,  0.62, 0.18),
    107: (0.15,1050000,1012000,  0.65, 0.20),
    108: (0.20,2500000,2430000,  0.75, 0.22),
}
for ep, (cont, budget, award, elig_pct, rebate_pct) in ep_fc.items():
    eligible = award * elig_pct
    dc.execute('''UPDATE ep_forecast SET contingency=?, budget=?, award=?, eligible=?,
                  global_rebate_pct=?, global_pct=? WHERE ep=?''',
               (cont, budget, award, eligible, rebate_pct, rebate_pct*elig_pct, ep))

# ---------------------------------------------------------------------------
# 14. Commit
# ---------------------------------------------------------------------------
dc.commit()
dc.close()

print()
print('-' * 58)
print('  SHOWCASE S1 demo project created successfully!')
print(f'  DB: {DEMO_DB}')
print()

# Summary
dc2 = dconn()
shots_n = dc2.execute('SELECT COUNT(*) FROM shots').fetchone()[0]
bids_n  = dc2.execute('SELECT COUNT(*) FROM bid_compare').fetchone()[0]
inv_n   = dc2.execute('SELECT COUNT(*) FROM invoice_log').fetchone()[0]
ast_n   = dc2.execute('SELECT COUNT(*) FROM assets').fetchone()[0]
dc2.close()

print(f'  Shots:          {shots_n}')
print(f'  Bid compare:    {bids_n}')
print(f'  Invoices:       {inv_n}')
print(f'  Assets:         {ast_n}')
print(f'  Episodes:       8  (101-108)')
print(f'  Vendors:        5  (FRAMESTORE, MPC, DNEG, ILM, RISING SUN)')
print()
print('  -> Start the app and select SHOWCASE S1')
print('-' * 58)
