
import pandas as pd
from pathlib import Path
from typing import List

REQUIRED_COLS = ["id","prompt","category","subcategory","maturity","source","criteria_selection"]

def _guess_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower().strip(): c for c in df.columns}
    out = pd.DataFrame()
    idc = next((cols[k] for k in cols if k in ["id","uid","sample_id"]), None)
    pc = next((cols[k] for k in cols if k in ["prompt","question","input"]), None)
    cat = next((cols[k] for k in cols if k in ["category","cat"]), None)
    sub = next((cols[k] for k in cols if k in ["subcategory","subcat","sub_category"]), None)
    mat = next((cols[k] for k in cols if k in ["maturity","age_band","age","band"]), None)
    crit = next((cols[k] for k in cols if k in ["criteria_selection","criteria","preset","criteria pattern"]), None)
    out["id"] = df[idc] if idc else pd.RangeIndex(start=0, stop=len(df))
    out["prompt"] = df[pc] if pc else ""
    out["category"] = df[cat] if cat else ""
    out["subcategory"] = df[sub] if sub else ""
    out["maturity"] = df[mat] if mat else ""
    out["criteria_selection"] = df[crit] if crit else ""
    return out

def load_all(paths: List[Path]) -> pd.DataFrame:
    frames = []
    for p in paths:
        if not p.exists():
            continue
        if p.suffix.lower() == ".csv":
            df = pd.read_csv(p)
        elif p.suffix.lower() in [".xlsx",".xls"]:
            df = pd.read_excel(p)
        else:
            continue
        df2 = _guess_columns(df)
        df2["source"] = p.name
        frames.append(df2)
    if not frames:
        return pd.DataFrame(columns=REQUIRED_COLS)
    all_df = pd.concat(frames, ignore_index=True)
    def norm_m(x):
        s = str(x).lower()
        if "child" in s or "6" in s or "8" in s:
            return "Child"
        if "teen" in s or "9" in s or "12" in s:
            return "Teen"
        if "young" in s or "13" in s or "17" in s:
            return "YoungAdult"
        if "emerging" in s or "18" in s or "25" in s:
            return "Emerging"
        return ""
    all_df["maturity"] = all_df["maturity"].map(norm_m)
    if "criteria_selection" in all_df.columns:
        all_df["criteria_selection"] = (
            all_df["criteria_selection"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        all_df.loc[all_df["criteria_selection"].isin(["nan", "NaN", "None"]), "criteria_selection"] = ""
    all_df = all_df[all_df["prompt"].astype(str).str.len() > 0].copy()
    for c in REQUIRED_COLS:
        if c not in all_df.columns:
            all_df[c] = "" if c != "id" else range(len(all_df))
    return all_df[REQUIRED_COLS]
