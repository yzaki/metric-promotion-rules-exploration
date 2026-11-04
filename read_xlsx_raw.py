"""Read the first sheet of an .xlsx file from its XML, ignoring styles (some ANVUR files have font
settings that openpyxl rejects). Returns a DataFrame of cell values (strings or numbers), no header.
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
    rows = {}
    for c in ET.fromstring(z.read(sheet)).iter("{%s}c" % NS["m"]):
        ref, typ = c.get("r"), c.get("t")
        v = c.find("m:v", NS)
        if v is None:
            is_ = c.find("m:is", NS)
            val = "".join(t.text or "" for t in is_.iter("{%s}t" % NS["m"])) if is_ is not None else None
        elif typ == "s":
            val = shared[int(v.text)]
        else:
            try:
                val = float(v.text)
            except (TypeError, ValueError):
                val = v.text
        r = int(re.search(r"\d+", ref).group(0)) - 1
        rows.setdefault(r, {})[col_index(ref)] = val
    return pd.DataFrame.from_dict(rows, orient="index").sort_index().sort_index(axis=1)


if __name__ == "__main__":
    print(read(sys.argv[1]).head(15).to_string())
