"""Posthoc data-provenance overlap check, not a cohort-selection/tuning procedure."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from workbook_reader import read_workbook
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    f=pd.read_csv(root/'results/citrine/cohort.csv')
    path=root/'data/additional/raw/MPEA_parsed_mechanical_database.xlsx'
    if not path.exists():raise FileNotFoundError('Prior Mendeley input is needed to regenerate the overlap diagnostic; source fields/target values must not be invented')
    new=next(iter(read_workbook(path)[0].values()))
    y=pd.to_numeric(new['Yield Strength (MPa)'],errors='coerce');e=pd.to_numeric(new['Elongation (%)'],errors='coerce')
    elements=json.loads((root/'results/citrine/feature_schema.json').read_text())['element_columns'];matches=[]
    for r in f.itertuples():
        candidate=new[np.isclose(y,r.yield_strength_mpa,atol=1e-9)&np.isclose(e,r.elongation_percent,atol=1e-9)]
        for s in candidate.itertuples():
            if all(abs(float(getattr(s,c,0))-getattr(r,c))<=.003 for c in elements):
                matches.append({'case_id':r.case_id,'citrine_master_row':r.master_row,'mendeley_excel_row':int(new.loc[s.Index,'__excel_row']),
                    'evidence':'Exact target pair plus composition-coordinate agreement within0.003 (rounded data); possible shared source observation, not proof of independent replicate'})
    result={'status':'POSTHOC_PROVENANCE_OVERLAP_AUDIT','citrine_qualified_cases_with_possible_prior_software_dataset_overlap':len({r['case_id'] for r in matches}),
        'matches':matches,'scope':'Original strength development used Mendeley data for provisional execution only; no final Citrine policy outcomes were used to tune defaults. Citrine is not claimed to be a pristine external dataset holdout.'}
    (root/'results/citrine/prior_dataset_overlap.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='matches'})
