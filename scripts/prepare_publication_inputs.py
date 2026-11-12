"""Offline, checksum-checked materialization of already committed historical inputs.

Does not download, alter the primary Citrine cohort, or overwrite any input.
The steel upload remains license-unqualified; used only by historical audit tests.
"""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]

def main():
    items=[('GE_RefractoryAlloyScreeningDataset_FINAL.csv','data/raw/GE_RefractoryAlloyScreeningDataset_FINAL.csv',
            'a9f2b7aaf4b7305535c321bf1354115ac0c157ef1159b23829dff850212ceacd')]
    for name in ['mpea','steel']:
        m=json.loads((ROOT/f'results/dataset_qualification/{name}_manifest.json').read_text())
        items.append((m['repository_path'],'data/additional/raw/'+m['filename'],m['sha256']))
    for source,destination,digest in items:
        src=ROOT/source;dest=ROOT/destination
        assert hashlib.sha256(src.read_bytes()).hexdigest()==digest,source
        if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest,destination
        else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    print('Three existing historical inputs verified/materialized; no network access.')

if __name__=='__main__':main()
