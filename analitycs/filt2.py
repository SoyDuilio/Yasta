# -*- coding: utf-8 -*-
"""
filt2.py
Análisis y priorización de contribuyentes en Maynas (Loreto) + gráficos + CSV de visitas.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

# =============== CONFIG ===============
# Ajusta estas rutas según tu estructura
DATA_DIR = Path(r"C:\RUCFACIL\data")  # carpeta donde están los CSV fuente
OUT_DIR = Path(r"C:\RUCFACIL\analitycs\out")  # carpeta de salidas
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR = OUT_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

PJ_CSV = DATA_DIR / "personas_juridicas.csv"
PN_CSV = DATA_DIR / "personas_naturales.csv"

# Campos esperados (mapeo flexible por si varían mayúsculas/acentos)
MAP_PJ = {
    "ddp_numruc": "RUC",
    "ddp_nombre": "NOMBRE",
    "ddp_numreg": "NUMREG",
    "Estado": "ESTADO",
    "Condicion_Domicilio": "COND_DOM",
    "Departamento": "DEPTO",
    "Provincia": "PROV",
    "Distrito": "DIST",
    "Tipo_Via": "TIPO_VIA",
    "nombre via": "NOM_VIA",
    "número": "NUM_VIA",
    "interior": "INTERIOR",
    "kilometro": "KM",
    "manzana": "MZ",
    "numedepart": "DPTO_NUM",
    "lote": "LOTE",
    "tipo_Zona": "TIPO_ZONA",
    "nombzona": "NOM_ZONA",
    "CIIU": "CIIU",
    "cod_ciiu2": "CIIU2",
    "cod_ciiu3": "CIIU3",
}

MAP_PN = {
    "ddp_numruc": "RUC",
    "ddp_nombre": "NOMBRE",
    "ddp_numreg": "NUMREG",
    "Estado": "ESTADO",
    "Condicion_Domicilio": "COND_DOM",
    "Departamento": "DEPTO",
    "Provincia": "PROV",
    "Distrito": "DIST",
    "ddp_ciiu": "CIIU",
    "CIIU": "CIIU_ALT",     # por si viniera doble
    "cod_ciiu2": "CIIU2",
    "cod_ciiu3": "CIIU3",
}

TARGET_DEPTO = "LORETO"
TARGET_PROV = "MAYNAS"

# Sectores típicamente sensibles a precio (ajusta a tu realidad local)
CIIU_PRICE_SENSITIVE = {
    "4711", "4719", "4721", "4729",  # comercio minorista
    "5610", "5630",                  # restaurantes y bares
    "4772", "4773",                  # farmacias / perfumerías
    "4540",                          # venta de motos y partes
}

# =============== UTILIDADES ===============
def read_csv_flexible(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    # intentos de encoding comunes
    for enc in ["utf-8-sig", "latin-1", "utf-8"]:
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
    # último intento sin encoding
    return pd.read_csv(path, dtype=str)

def normalize_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    # normaliza headers a minúsculas sin espacios
    std = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=std)
    # aplica mapeo si la clave existe
    rename_map = {}
    for original_key, new_key in mapping.items():
        ok = original_key.strip().lower()
        if ok in df.columns:
            rename_map[ok] = new_key
    df = df.rename(columns=rename_map)
    return df

def strip_object_cols(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df

def upper_cols(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].str.upper()
    return df

def safe_valcounts_ratio(df: pd.DataFrame, col: str, top=None) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame(columns=[col, "Ratio"])
    vc = df[col].value_counts(normalize=True, dropna=False)
    if top:
        vc = vc.head(top)
    return vc.rename("Ratio").reset_index(names=[col])

def plot_save_bar(series_df: pd.DataFrame, label_col: str, value_col: str, title: str, fname: Path):
    if series_df.empty:
        return
    plt.figure()
    plt.bar(series_df[label_col].astype(str), series_df[value_col].astype(float))
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()

def plot_save_pie(series_df: pd.DataFrame, label_col: str, value_col: str, title: str, fname: Path):
    if series_df.empty:
        return
    plt.figure()
    plt.pie(series_df[value_col].astype(float), labels=series_df[label_col].astype(str), autopct="%1.1f%%")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()

# =============== CARGA Y LIMPIEZA ===============
pj_raw = read_csv_flexible(PJ_CSV)
pn_raw = read_csv_flexible(PN_CSV)

pj = normalize_columns(pj_raw, MAP_PJ)
pn = normalize_columns(pn_raw, MAP_PN)

pj = strip_object_cols(pj)
pn = strip_object_cols(pn)

# completa CIIU faltante en PN si tuviera CIIU_ALT
if "CIIU" not in pn.columns and "CIIU_ALT" in pn.columns:
    pn = pn.rename(columns={"CIIU_ALT": "CIIU"})

# estandariza ubicación y campos clave
for df in (pj, pn):
    df.fillna("", inplace=True)
    upper_cols(df, ["DEPTO", "PROV", "DIST", "ESTADO", "COND_DOM", "CIIU", "CIIU2", "CIIU3", "NOMBRE"])
    # normaliza RUC como texto sin espacios
    if "RUC" in df.columns:
        df["RUC"] = df["RUC"].str.replace(r"\s+", "", regex=True)

# elimina duplicados por RUC si existe
if "RUC" in pj.columns:
    pj = pj.drop_duplicates(subset=["RUC"])
if "RUC" in pn.columns:
    pn = pn.drop_duplicates(subset=["RUC"])

# =============== FILTRO GEOGRÁFICO ===============
pj_maynas = pj[(pj.get("DEPTO", "") == TARGET_DEPTO) & (pj.get("PROV", "") == TARGET_PROV)].copy()
pn_maynas = pn[(pn.get("DEPTO", "") == TARGET_DEPTO) & (pn.get("PROV", "") == TARGET_PROV)].copy()

total_pj = len(pj_maynas)
total_pn = len(pn_maynas)
total_all = total_pj + total_pn

# =============== INDICADORES ===============
estado_pj = safe_valcounts_ratio(pj_maynas, "ESTADO")
estado_pn = safe_valcounts_ratio(pn_maynas, "ESTADO")

cond_pj = safe_valcounts_ratio(pj_maynas, "COND_DOM")
cond_pn = safe_valcounts_ratio(pn_maynas, "COND_DOM")

ciiu_pj_top10 = safe_valcounts_ratio(pj_maynas, "CIIU", top=10)
ciiu_pn_top10 = safe_valcounts_ratio(pn_maynas, "CIIU", top=10)

dist_pj = safe_valcounts_ratio(pj_maynas, "DIST")
dist_pn = safe_valcounts_ratio(pn_maynas, "DIST")

ratio_df = pd.DataFrame({
    "Tipo": ["Personas Jurídicas", "Personas Naturales"],
    "Cantidad": [total_pj, total_pn]
})
if total_all > 0:
    ratio_df["Ratio"] = ratio_df["Cantidad"] / total_all
else:
    ratio_df["Ratio"] = 0.0

# =============== GRÁFICOS (matplotlib, 1 figura por gráfico) ===============
# Top CIIU
plot_save_bar(ciiu_pj_top10.rename(columns={"index": "CIIU"}), "CIIU", "Ratio",
              "Top 10 CIIU PJ - Maynas", CHART_DIR / "top10_ciiu_pj.png")
plot_save_bar(ciiu_pn_top10.rename(columns={"index": "CIIU"}), "CIIU", "Ratio",
              "Top 10 CIIU PN - Maynas", CHART_DIR / "top10_ciiu_pn.png")

# Estado y Condición
plot_save_pie(estado_pj.rename(columns={"index": "ESTADO"}), "ESTADO", "Ratio",
              "Estado - PJ Maynas", CHART_DIR / "estado_pj.png")
plot_save_pie(estado_pn.rename(columns={"index": "ESTADO"}), "ESTADO", "Ratio",
              "Estado - PN Maynas", CHART_DIR / "estado_pn.png")

plot_save_pie(cond_pj.rename(columns={"index": "COND_DOM"}), "COND_DOM", "Ratio",
              "Condición Domicilio - PJ Maynas", CHART_DIR / "cond_pj.png")
plot_save_pie(cond_pn.rename(columns={"index": "COND_DOM"}), "COND_DOM", "Ratio",
              "Condición Domicilio - PN Maynas", CHART_DIR / "cond_pn.png")

# Distritos
plot_save_bar(dist_pj.rename(columns={"index": "DIST"}), "DIST", "Ratio",
              "Distritos - PJ Maynas", CHART_DIR / "dist_pj.png")
plot_save_bar(dist_pn.rename(columns={"index": "DIST"}), "DIST", "Ratio",
              "Distritos - PN Maynas", CHART_DIR / "dist_pn.png")

# Pie PJ vs PN
plot_save_pie(ratio_df, "Tipo", "Cantidad", "Distribución PJ vs PN (Maynas)", CHART_DIR / "pj_vs_pn.png")

# =============== SCORE DE PRIORIDAD DE VISITA ===============
def compute_score(row, tipo: str) -> int:
    score = 0
    estado = row.get("ESTADO", "")
    cond = row.get("COND_DOM", "")
    ciiu = row.get("CIIU", "")

    # 1) Regularización / riesgo (alto valor para visita)
    if cond in {"NO HABIDO", "NO HALLADO", "PENDIENTE", "DOMICILIO FISCAL DESCONOCIDO"}:
        score += 3
    elif cond in {"HABIDO"}:
        score += 1

    # 2) Estado
    if estado in {"ACTIVO"}:
        score += 2
    elif "BAJA" in estado:
        score += 0  # descartables

    # 3) Sensibilidad a precio
    if any(ciiu.startswith(x) for x in CIIU_PRICE_SENSITIVE if isinstance(ciiu, str)):
        score += 1

    # 4) Tipo de contribuyente (ligero sesgo a PN por precio)
    if tipo == "PN":
        score += 1

    # 5) Bonus si falta CIIU (puede estar mal clasificado y requerir orientación)
    if not ciiu:
        score += 1

    return score

def build_visitas_df(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    keep_cols = ["RUC", "NOMBRE", "ESTADO", "COND_DOM", "DEPTO", "PROV", "DIST", "CIIU", "CIIU2", "CIIU3"]
    for c in keep_cols:
        if c not in df.columns:
            df[c] = ""
    out = df[keep_cols].copy()
    out["TIPO"] = "PJ" if tipo == "PJ" else "PN"
    out["SCORE"] = out.apply(lambda r: compute_score(r, tipo), axis=1)
    # descarta bajas
    out = out[~out["ESTADO"].str.contains("BAJA", na=False)]
    # ordena por score desc y luego por distrito/nombre
    out = out.sort_values(by=["SCORE", "DIST", "NOMBRE"], ascending=[False, True, True])
    return out

vis_pj = build_visitas_df(pj_maynas, "PJ")
vis_pn = build_visitas_df(pn_maynas, "PN")

visitas = pd.concat([vis_pj, vis_pn], ignore_index=True)

# =============== EXPORTS ===============
ts = datetime.now().strftime("%Y%m%d_%H%M")
excel_path = OUT_DIR / "indicadores_sunat.xlsx"
csv_path = OUT_DIR / f"visitas_recomendadas_{ts}.csv"

with pd.ExcelWriter(excel_path) as writer:
    estado_pj.to_excel(writer, sheet_name="Estado_PJ", index=False)
    estado_pn.to_excel(writer, sheet_name="Estado_PN", index=False)
    cond_pj.to_excel(writer, sheet_name="Condicion_PJ", index=False)
    cond_pn.to_excel(writer, sheet_name="Condicion_PN", index=False)
    ciiu_pj_top10.to_excel(writer, sheet_name="Top10_CIIU_PJ", index=False)
    ciiu_pn_top10.to_excel(writer, sheet_name="Top10_CIIU_PN", index=False)
    dist_pj.to_excel(writer, sheet_name="Distritos_PJ", index=False)
    dist_pn.to_excel(writer, sheet_name="Distritos_PN", index=False)
    ratio_df.to_excel(writer, sheet_name="PJ_vs_PN", index=False)
    visitas.head(1000).to_excel(writer, sheet_name="Top1000_Visitas", index=False)

visitas.to_csv(csv_path, index=False)

print("✅ Listo.")
print(f"- Excel indicadores: {excel_path}")
print(f"- CSV visitas (con SCORE): {csv_path}")
print(f"- Gráficos PNG en: {CHART_DIR}")
print(f"Resumen: PJ={total_pj}, PN={total_pn}, Total={total_all}")