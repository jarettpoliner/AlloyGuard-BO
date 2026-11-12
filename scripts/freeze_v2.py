"""One-way protocol freeze, before any v2 comparative replay."""
from pathlib import Path
import json,hashlib,datetime,xml.etree.ElementTree as ET
import yaml
from alloyguard_strength.replay import config_hash
from alloyguard_v2.policies import POLICIES
r=Path(__file__).resolve().parents[1];dest=r/'configs/v2/frozen.json'
if dest.exists() or (r/'results/v2/evaluation').exists():raise FileExistsError('Freeze cannot be replaced')
xml=ET.parse(r/'results/v2/pre_freeze_tests.xml');suites=list(xml.getroot().iter('testsuite'))
assert suites and sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites)==0
old=json.loads((r/'results/v2/v1_preservation.json').read_text())
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in old.items())
c=yaml.safe_load((r/'configs/citrine/frozen.yaml').read_text())
c.update(revision='v2_risk_continuous_exploratory',policies=list(POLICIES),risk={'minimum_probability':.75,'total_budget':3.75},ductility={'log_noise':.15,'log_scale_floor':.5},goals={'failure_ratio_max':.85,'auc_ratio_min':.98},parameter_selection='FIXED_ENGINEERING_ASSUMPTIONS_NO_SEARCH',frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
paths=[*r.glob('src/alloyguard_v2/*.py'),*r.glob('src/alloyguard_strength/*.py'),*r.glob('src/alloyguard_citrine/*.py'),r/'scripts/run_v2.py',r/'tests/test_v2.py',r/'configs/v2/protocol.md',r/'requirements.lock',r/'results/citrine/cohort.csv',r/'results/citrine/feature_schema.json']
c['frozen_files']={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
c['config_hash']=config_hash(c);dest.write_text(json.dumps(c,indent=2)+'\n')
(r/'results/v2/freeze_evidence.json').write_text(json.dumps({'timestamp':c['frozen_at'],'config_hash':c['config_hash'],'tests':sum(int(s.attrib['tests']) for s in suites),'evaluation_existed':False,'v1_files_unchanged':len(old)},indent=2)+'\n')
print(c['config_hash'])
