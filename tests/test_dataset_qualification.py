"""New qualification assertions do not change the preserved GE scientific code."""
import sys,zipfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from workbook_reader import read_workbook,column_index
from qualify_datasets import numeric_pairs,normalize_study,connected_components


def test_real_new_workbook_counts_and_cell_parsing():
    mpea,meta=read_workbook(ROOT/"data/additional/raw/MPEA_parsed_mechanical_database.xlsx")
    f=mpea["Sheet1"]
    assert len(f)==1713 and meta[0]["data_rows"]==1713
    assert f.iloc[0].Composition=="Al0.2Co1.5CrFeNi1.5Ti0.55Si0.1"
    assert f.iloc[0]["Al"]==.034
    y,e,p,v=numeric_pairs(f,"Yield Strength (MPa)","Elongation (%)")
    assert p.sum()==v.sum()==457
    assert (e[v]>=10).sum()==341 and (e[v]<10).sum()==116


def test_steel_exact_deduplication_does_not_count_id_as_measurement():
    sheets,_=read_workbook(ROOT/"data/additional/raw/Steel database with labelled clusters.xlsx")
    f=sheets["Sheet1"]
    fields=[c for c in f if c not in ("__excel_row","Entry") and not c.startswith("__blank")]
    assert len(f)==3234
    d=f.drop_duplicates(fields)
    assert len(d)==1943 and (d["Ductility (%)"].astype(float)<10).sum()==32


def test_numeric_screening_preserves_zero_elongation_and_rejects_invalid_targets():
    f=pd.DataFrame({"ys":[100,100,100,-1,100,np.inf,"<200"],
                    "el":[0,10,101,20,np.nan,20,20]})
    y,e,p,v=numeric_pairs(f,"ys","el")
    assert v.tolist()==[True,True,False,False,False,False,False]


def test_study_normalization_and_transitive_leakage_groups():
    assert normalize_study("https://DOI.org/10.1016/J.TEST.2020.123.")=="10.1016/j.test.2020.123"
    assert normalize_study("unknown") is None
    groups=connected_components(["a","a","b","c"],[(1,0),(0,1),(0,1),(.5,.5)])
    assert sorted(map(len,groups))==[1,3]


def test_column_indices():
    assert column_index("A1")==0 and column_index("AA17")==26 and column_index("AU2")==46
    with pytest.raises(ValueError): column_index("bad")


def workbook_fixture(tmp_path,cells):
    path=tmp_path/"fixture.xlsx"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("xl/workbook.xml",'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="test" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>name</t></is></c><c r="B1" t="inlineStr"><is><t>value</t></is></c></row>'+cells+'</sheetData></worksheet>')
    return path


def test_reader_uses_cached_formula_as_data_without_execution(tmp_path):
    p=workbook_fixture(tmp_path,'<row r="2"><c r="A2" t="inlineStr"><is><t>fixture only</t></is></c><c r="B2"><f>1+1</f><v>2</v></c></row>')
    sheets,meta=read_workbook(p)
    assert sheets["test"].iloc[0]["value"]==2
    assert meta[0]["cached_formula_cells"]==1


def test_uncached_formula_rejected(tmp_path):
    p=workbook_fixture(tmp_path,'<row r="2"><c r="B2"><f>1+1</f></c></row>')
    with pytest.raises(ValueError,match="Uncached formula"): read_workbook(p)


def test_preserved_ge_frozen_scientific_source_and_lock():
    import json,hashlib
    from alloyguard.replay import source_hash
    manifest=json.loads((ROOT/"results/primary/benchmark_manifest.json").read_text())
    assert source_hash(ROOT)==manifest["source_hash"]
    assert hashlib.sha256((ROOT/"requirements.lock").read_bytes()).hexdigest()==manifest["lock_sha256"]
