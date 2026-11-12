import numpy as np
import pandas as pd
import pytest
from alloyguard.data import FILENAME,COMPOSITION,HARDNESS,RANK,validate_frame,process,sha256_file
from helpers import ROOT

def raw():
    return pd.read_csv(ROOT/"data/raw"/FILENAME,encoding="utf-8-sig")

def test_real_data_integrity_schema_and_support():
    f=raw(); validate_frame(f); grouped=process(f)
    assert len(f)==86 and len(grouped)==82
    assert int((grouped.ductility_rank>=3).sum())==7
    assert sha256_file(ROOT/"data/raw"/FILENAME)=="a9f2b7aaf4b7305535c321bf1354115ac0c157ef1159b23829dff850212ceacd"
    assert np.allclose(grouped[[c.split('(')[0] for c in COMPOSITION]].sum(axis=1),1,atol=1e-8)

@pytest.mark.parametrize("change",["negative","sum","missing","rank","hardness","schema"])
def test_invalid_data_rejected(change):
    f=raw()
    if change=="negative": f.loc[0,COMPOSITION[0]]=-1
    if change=="sum": f.loc[0,COMPOSITION[0]]=1
    if change=="missing": f.loc[0,HARDNESS]=np.nan
    if change=="rank": f.loc[0,RANK]=6
    if change=="hardness": f.loc[0,HARDNESS]=-1
    if change=="schema": f=f.rename(columns={RANK:"strain"})
    with pytest.raises(ValueError): validate_frame(f)
