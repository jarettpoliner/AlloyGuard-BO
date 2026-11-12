import pandas as pd
from alloyguard.data import FILENAME,process,COMPOSITION,HARDNESS,RANK
from helpers import ROOT

def test_replicates_aggregated_once_and_preserved():
    raw=pd.read_csv(ROOT/"data/raw"/FILENAME,encoding="utf-8-sig")
    grouped=process(raw)
    reps=grouped[grouped.replicate_count>1]
    assert sorted(reps.replicate_count)==[3,3]
    assert sum(grouped.replicate_count)==86
    for row in reps.itertuples():
        import json
        original=raw.iloc[json.loads(row.raw_row_ids)]
        assert row.hardness_gpa==original[HARDNESS].mean()
        assert row.ductility_rank==original[RANK].min()
    assert grouped.alloy_id.is_unique
    assert grouped.alloy_id.tolist()==process(raw.sample(frac=1,random_state=9)).alloy_id.tolist()
