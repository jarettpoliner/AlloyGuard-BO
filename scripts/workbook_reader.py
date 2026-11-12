"""Read cached XLSX cells as data using stdlib OOXML; never evaluate formulas."""
from __future__ import annotations
from pathlib import Path
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

NS={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL="http://schemas.openxmlformats.org/package/2006/relationships"


def column_index(reference):
    match=re.fullmatch(r"([A-Z]+)[0-9]+",reference)
    if not match: raise ValueError(f"Unexpected cell reference: {reference}")
    n=0
    for char in match.group(1): n=n*26+ord(char)-64
    return n-1


def read_workbook(path):
    sheets={}; inspections=[]
    with zipfile.ZipFile(path) as z:
        if sum(info.file_size for info in z.infolist())>50_000_000:
            raise ValueError("Unexpected expanded workbook size")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            shared=["".join(t.text or "" for t in node.findall(".//s:t",NS))
                    for node in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si",NS)]
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets={r.get("Id"):r.get("Target") for r in rels if r.get("TargetMode")!="External"}
        for sheet in workbook.findall("s:sheets/s:sheet",NS):
            target=targets[sheet.get("{"+NS["r"]+"}id")]
            target=target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/"+target)
            rows=[]; excel_rows=[]; formulas=0
            for row in ET.fromstring(z.read(target)).findall("s:sheetData/s:row",NS):
                cells={}
                for cell in row.findall("s:c",NS):
                    index=column_index(cell.get("r")); kind=cell.get("t")
                    val=cell.find("s:v",NS)
                    if cell.find("s:f",NS) is not None:
                        formulas+=1
                        if val is None: raise ValueError("Uncached formula requires publisher-provided values")
                    value=val.text if val is not None else None
                    if kind=="s": value=shared[int(value)] if value is not None else None
                    elif kind=="inlineStr": value="".join(t.text or "" for t in cell.findall(".//s:t",NS))
                    elif kind=="e": raise ValueError("Workbook contains an Excel error cell")
                    elif value is not None and kind not in ("str",):
                        value=float(value)
                    cells[index]=value
                if any(v is not None and str(v).strip() for v in cells.values()):
                    rows.append(cells);excel_rows.append(int(row.get("r")))
            if not rows: raise ValueError("Empty sheet")
            width=max(max(row.keys(),default=-1) for row in rows)+1
            labels=[];counts={}
            for i in range(width):
                value=rows[0].get(i)
                name=str(value).strip() if value is not None and str(value).strip() else f"__blank_{i+1}"
                counts[name]=counts.get(name,0)+1
                if counts[name]>1: name=f"{name}__duplicate_{counts[name]}"
                labels.append(name)
            frame=pd.DataFrame([[row.get(i) for i in range(width)] for row in rows[1:]],columns=labels)
            frame.insert(0,"__excel_row",excel_rows[1:])
            sheets[sheet.get("name")]=frame
            inspections.append({"sheet":sheet.get("name"),"data_rows":len(frame),"columns":labels,
                                "cached_formula_cells":formulas,"nonempty_excel_rows":len(rows)})
    return sheets,inspections
