# analyze_density.py
# Análisis de densidad CIIU x Distrito (PJ / PN) + gráficos + export CSV para campo
# Requisitos: pandas, openpyxl, matplotlib

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ========== CONFIG ==========
DATA_DIR = Path(r"C:\RUCFACIL\data")
OUT_DIR = Path(r"C:\RUCFACIL\analitycs\out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR = OUT_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

PJ_CSV = DATA_DIR / "PPJJ_ABRIL_2022.csv"
PN_CSV = DATA_DIR / "PPNN_ABRIL_2022.csv"

TARGET_DEPTO = "LORETO"
TARGET_PROV = "MAYNAS"
TOP_N_CIIU_FOR_HEATMAP = 30
TOP_N_DISTRICTS_PER_CIIU = 3

# Campos / mapeos (intentar manejar variaciones de nombres)
MAP_PJ_KEYS = {
    "ddp_numruc": "RUC", "ddp_nombre": "NOMBRE", "ddp_numreg": "NUMREG",
    "estado": "ESTADO", "condicion_domicilio": "COND_DOM",
    "departamento": "DEPTO", "provincia": "PROV", "distrito": "DIST",
    "ciiu": "CIIU", "cod_ciiu2": "CIIU2", "cod_ciiu3": "CIIU3"
}
MAP_PN_KEYS = {
    "ddp_numruc": "RUC", "ddp_nombre": "NOMBRE", "ddp_numreg": "NUMREG",
    "estado": "ESTADO", "condicion_domicilio": "COND_DOM",
    "departamento": "DEPTO", "provincia": "PROV", "distrito": "DIST",
    "ddp_ciiu": "CIIU", "ciiu": "CIIU_ALT", "cod_ciiu2": "CIIU2", "cod_ciiu3": "CIIU3"
}

# ========== UTILIDADES ==========
def read_csv_flexible(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró: {path}")
    for enc in ("utf-8-sig", "latin-1", "utf-8"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, dtype=str, encoding="latin-1", errors="ignore")

def normalize_and_map(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    # lowercase keys without spaces
    cols = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=cols)
    # build rename map from mapping keys normalized
    rename_map = {}
    for k, v in mapping.items():
        k_norm = k.strip().lower()
        if k_norm in df.columns:
            rename_map[k_norm] = v
    df = df.rename(columns=rename_map)
    # strip string/object cols
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
    # uppercase certain cols if present
    for c in ("DEPTO","PROV","DIST","ESTADO","COND_DOM","CIIU","CIIU2","CIIU3","NOMBRE","RUC"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.upper()
    # normalize RUC
    if "RUC" in df.columns:
        df["RUC"] = df["RUC"].str.replace(r"\s+", "", regex=True)
    return df

def safe_value_counts(df, col):
    if col not in df.columns:
        return pd.Series([], dtype=int)
    return df[col].value_counts()

# ========== CARGA ==========
print("Leyendo CSVs...")
pj_raw = read_csv_flexible(PJ_CSV)
pn_raw = read_csv_flexible(PN_CSV)

pj = normalize_and_map(pj_raw, MAP_PJ_KEYS)
pn = normalize_and_map(pn_raw, MAP_PN_KEYS)

# si PN tuvo CIIU_ALT (mapeo alterno), arreglar
if "CIIU" not in pn.columns and "CIIU_ALT" in pn.columns:
    pn = pn.rename(columns={"CIIU_ALT": "CIIU"})

# rellenar NA con cadena vacía
pj = pj.fillna("")
pn = pn.fillna("")

# elimina duplicados por RUC (si existiera)
if "RUC" in pj.columns:
    pj = pj.drop_duplicates(subset=["RUC"])
if "RUC" in pn.columns:
    pn = pn.drop_duplicates(subset=["RUC"])

# ========== FILTRADO GEOGRAFICO ==========
pj_maynas = pj[(pj.get("DEPTO","") == TARGET_DEPTO) & (pj.get("PROV","") == TARGET_PROV)].copy()
pn_maynas = pn[(pn.get("DEPTO","") == TARGET_DEPTO) & (pn.get("PROV","") == TARGET_PROV)].copy()

print(f"Registros en Maynas: PJ={len(pj_maynas)} | PN={len(pn_maynas)}")

# ========== INDICADORES BASICOS ==========
total_pj = len(pj_maynas)
total_pn = len(pn_maynas)
total_all = total_pj + total_pn

pj_by_dist = safe_value_counts(pj_maynas, "DIST")
pn_by_dist = safe_value_counts(pn_maynas, "DIST")
combined = pd.concat([
    pj_maynas.assign(TIPO="PJ"),
    pn_maynas.assign(TIPO="PN")
], ignore_index=True)
combined_by_dist = safe_value_counts(combined, "DIST")

pj_ciiu_counts = safe_value_counts(pj_maynas, "CIIU")
pn_ciiu_counts = safe_value_counts(pn_maynas, "CIIU")
combined_ciiu_counts = safe_value_counts(combined, "CIIU")

# ========== PIVOT CIIU x DIST =================
pivot_combined = combined.groupby(["CIIU","DIST"]).size().unstack(fill_value=0)
pivot_pj = pj_maynas.groupby(["CIIU","DIST"]).size().unstack(fill_value=0) if not pj_maynas.empty else pd.DataFrame()
pivot_pn = pn_maynas.groupby(["CIIU","DIST"]).size().unstack(fill_value=0) if not pn_maynas.empty else pd.DataFrame()

# ========== TABLA LARGA: CIIU - DIST - COUNT - %CIIU - %DIST - RANK ==========
rows = []
district_totals = combined_by_dist.to_dict()
ciiu_totals = combined_ciiu_counts.to_dict()

for ciiu, row in pivot_combined.iterrows():
    c_total = ciiu_totals.get(ciiu, 0)
    # build ranking across districts for this ciiu
    sr = row.sort_values(ascending=False)
    rank = 1
    for dist, cnt in sr.items():
        if cnt == 0:
            continue
        pct_of_ciiu = cnt / c_total if c_total>0 else 0
        dist_total = district_totals.get(dist, 0)
        pct_of_district = cnt / dist_total if dist_total>0 else 0
        rows.append({
            "CIIU": ciiu,
            "DIST": dist,
            "COUNT": int(cnt),
            "CIIU_TOTAL": int(c_total),
            "PCT_OF_CIIU": round(pct_of_ciiu, 6),
            "DIST_TOTAL": int(dist_total),
            "PCT_OF_DISTRICT": round(pct_of_district, 6),
            "RANK_IN_CIIU": rank
        })
        rank += 1

ciiu_district_df = pd.DataFrame(rows)
ciiu_district_df = ciiu_district_df.sort_values(["CIIU","RANK_IN_CIIU"])

# top districts per ciiu (top N)
top_districts = ciiu_district_df.groupby("CIIU").head(TOP_N_DISTRICTS_PER_CIIU).reset_index(drop=True)

# ========== SCORE de prioridad (incluye densidad por CIIU x DIST) ==========
# build a quick lookup for rank_in_ciiu by (ciiu,dist)
rank_lookup = ciiu_district_df.set_index(["CIIU","DIST"])["RANK_IN_CIIU"].to_dict()

def compute_score_row(row, tipo):
    score = 0
    estado = row.get("ESTADO","")
    cond = row.get("COND_DOM","")
    ciiu = row.get("CIIU","")
    dist = row.get("DIST","")
    # cond domicilio problemático
    if cond in {"NO HABIDO","NO HALLADO","PENDIENTE","DOMICILIO FISCAL DESCONOCIDO"}:
        score += 3
    elif cond == "HABIDO":
        score += 1
    # estado
    if estado == "ACTIVO":
        score += 2
    elif "BAJA" in estado:
        score += 0
    # tipo PN bias (sensible a precio)
    if tipo == "PN":
        score += 1
    # missing CIIU
    if not ciiu or ciiu == "":
        score += 1
    # density bonus: si el distrito está entre top 1-2 para ese CIIU -> +2, top 3 -> +1
    if (ciiu, dist) in rank_lookup:
        r = rank_lookup[(ciiu, dist)]
        if r == 1:
            score += 2
        elif r == 2:
            score += 1
        elif r == 3:
            score += 1
    return score

def build_visitas(df, tipo):
    keep = ["RUC","NOMBRE","ESTADO","COND_DOM","DEPTO","PROV","DIST","CIIU","CIIU2","CIIU3"]
    for c in keep:
        if c not in df.columns:
            df[c] = ""
    out = df[keep].copy()
    out["TIPO"] = "PJ" if tipo=="PJ" else "PN"
    out["SCORE"] = out.apply(lambda r: compute_score_row(r, tipo), axis=1)
    # filtra bajas si quieres descartarlas
    out = out[~out["ESTADO"].str.contains("BAJA", na=False)]
    out = out.sort_values(["SCORE","DIST","NOMBRE"], ascending=[False, True, True])
    return out

vis_pj = build_visitas(pj_maynas, "PJ")
vis_pn = build_visitas(pn_maynas, "PN")
visitas = pd.concat([vis_pj, vis_pn], ignore_index=True)

# ========== GRAFICOS ==========
ts = datetime.now().strftime("%Y%m%d_%H%M")
# top CIIU bar
top20 = combined_ciiu_counts.head(20)
plt.figure(figsize=(10,6))
plt.bar(top20.index.astype(str), top20.values)
plt.xticks(rotation=60, ha="right")
plt.title("Top 20 CIIU - Maynas (combinado)")
plt.tight_layout()
plt.savefig(CHART_DIR / f"top20_ciiu_{ts}.png")
plt.close()

# PJ vs PN pie
plt.figure(figsize=(6,6))
plt.pie([total_pj, total_pn], labels=["PJ","PN"], autopct="%1.1f%%")
plt.title("PJ vs PN (Maynas)")
plt.tight_layout()
plt.savefig(CHART_DIR / f"pj_vs_pn_{ts}.png")
plt.close()

# heatmap: top N CIIU x districts
top_ciuis = list(combined_ciiu_counts.head(TOP_N_CIIU_FOR_HEATMAP).index)
if len(top_ciuis) > 0:
    heat = pivot_combined.reindex(top_ciuis).fillna(0)
    fig_h = plt.figure(figsize=(8, max(6, 0.25*len(top_ciuis))))
    ax = fig_h.add_subplot(111)
    im = ax.imshow(heat.values, aspect='auto', interpolation='nearest')
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index)
    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels(heat.columns, rotation=45, ha="right")
    ax.set_title(f"Heatmap: CIIU x Distrito (Top {len(top_ciuis)} CIIU)")
    fig_h.colorbar(im, ax=ax, fraction=0.02)
    plt.tight_layout()
    plt.savefig(CHART_DIR / f"heatmap_ciiu_distritos_{ts}.png")
    plt.close()

# small charts per district (optional)
# guardamos algunas gráficas por distrito: top CIIU en cada uno
for dist in combined_by_dist.index:
    subset = combined[combined["DIST"]==dist]
    if subset.empty:
        continue
    top = subset["CIIU"].value_counts().head(10)
    plt.figure(figsize=(8,4))
    plt.bar(top.index.astype(str), top.values)
    plt.xticks(rotation=60, ha="right")
    plt.title(f"Top CIIU - {dist}")
    plt.tight_layout()
    safe_name = dist.replace(" ","_").lower()
    plt.savefig(CHART_DIR / f"top_ciiu_{safe_name}_{ts}.png")
    plt.close()

# ========== EXPORTS ==========
excel_path = OUT_DIR / "indicadores_sunat.xlsx"
with pd.ExcelWriter(excel_path) as writer:
    # Totales
    pd.DataFrame({
        "Categoria":["PJ","PN","Total"],
        "Cantidad":[total_pj, total_pn, total_all]
    }).to_excel(writer, sheet_name="Totales", index=False)
    # By district
    pj_by_dist.rename_axis("DIST").reset_index(name="PJ_COUNT").to_excel(writer, sheet_name="PJ_by_Dist", index=False)
    pn_by_dist.rename_axis("DIST").reset_index(name="PN_COUNT").to_excel(writer, sheet_name="PN_by_Dist", index=False)
    combined_by_dist.rename_axis("DIST").reset_index(name="TOTAL_COUNT").to_excel(writer, sheet_name="Total_by_Dist", index=False)
    # Top CIIU
    pj_ciiu_counts.rename_axis("CIIU").reset_index(name="PJ_COUNT").to_excel(writer, sheet_name="TopCIIU_PJ", index=False)
    pn_ciiu_counts.rename_axis("CIIU").reset_index(name="PN_COUNT").to_excel(writer, sheet_name="TopCIIU_PN", index=False)
    combined_ciiu_counts.rename_axis("CIIU").reset_index(name="TOTAL_COUNT").to_excel(writer, sheet_name="TopCIIU_All", index=False)
    # pivots
    if not pivot_combined.empty:
        pivot_combined.to_excel(writer, sheet_name="Pivot_CIIUxDIST")
    if not pivot_pj.empty:
        pivot_pj.to_excel(writer, sheet_name="Pivot_PJ_CIIUxDIST")
    if not pivot_pn.empty:
        pivot_pn.to_excel(writer, sheet_name="Pivot_PN_CIIUxDIST")
    # ciiu-district density and top districts
    ciiu_district_df.to_excel(writer, sheet_name="CIIU_District_Long", index=False)
    top_districts.to_excel(writer, sheet_name="TopDistricts_per_CIIU", index=False)
    # visitas (top 1000)
    visitas.head(5000).to_excel(writer, sheet_name="Visitas_Top5000", index=False)

csv_density = OUT_DIR / f"ciiu_district_density_{ts}.csv"
csv_top = OUT_DIR / f"top_districts_per_ciiu_{ts}.csv"
csv_visitas = OUT_DIR / f"visitas_recomendadas_{ts}.csv"

ciiu_district_df.to_csv(csv_density, index=False)
top_districts.to_csv(csv_top, index=False)
visitas.to_csv(csv_visitas, index=False)

print("✅ Proceso finalizado.")
print(f"- Excel: {excel_path}")
print(f"- CSV densidad: {csv_density}")
print(f"- CSV top districts: {csv_top}")
print(f"- CSV visitas: {csv_visitas}")
print(f"- Charts en: {CHART_DIR}")
