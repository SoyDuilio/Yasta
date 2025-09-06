import pandas as pd

# =====================
# 1. Cargar los datos
# =====================
# Supongamos que tienes los datos en CSV separados (uno para PJ y otro para PN)
pj = pd.read_csv("PPJJ_ABRIL_2022.csv", dtype=str)  # dtype=str para evitar errores con RUC
pn = pd.read_csv("PPNN_ABRIL_2022.csv", dtype=str)

# =====================
# 2. Estandarizar y limpiar
# =====================
def limpiar_df(df):
    # Quitar espacios
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Eliminar duplicados
    df = df.drop_duplicates(subset=["ddp_numruc"])
    return df

pj = limpiar_df(pj)
pn = limpiar_df(pn)

# =====================
# 3. Filtrar por ubicación (Iquitos, Maynas, Loreto)
# =====================
pj_maynas = pj[(pj["Departamento"]=="LORETO") & (pj["Provincia"]=="MAYNAS")]
pn_maynas = pn[(pn["Departamento"]=="LORETO") & (pn["Provincia"]=="MAYNAS")]

# =====================
# 4. Indicadores básicos
# =====================

# Conteo por estado de domicilio
estado_pj = pj_maynas["Estado"].value_counts(normalize=True).rename("Ratio").reset_index()
estado_pn = pn_maynas["Estado"].value_counts(normalize=True).rename("Ratio").reset_index()

# Conteo por condición (habido/no habido)
cond_pj = pj_maynas["Condicion_Domicilio"].value_counts(normalize=True).rename("Ratio").reset_index()
cond_pn = pn_maynas["Condicion_Domicilio"].value_counts(normalize=True).rename("Ratio").reset_index()

# Top 10 actividades económicas (CIIU)
ciiu_pj = pj_maynas["CIIU"].value_counts(normalize=True).head(10).reset_index()
ciiu_pn = pn_maynas["ddp_ciiu"].value_counts(normalize=True).head(10).reset_index()

# =====================
# 5. Ratios e indicadores útiles
# =====================

# % de personas jurídicas vs naturales en Maynas
total_pj = len(pj_maynas)
total_pn = len(pn_maynas)
ratio_pj_pn = total_pj / (total_pj + total_pn)

# Distribución geográfica por distrito
dist_pj = pj_maynas["Distrito"].value_counts(normalize=True).reset_index()
dist_pn = pn_maynas["Distrito"].value_counts(normalize=True).reset_index()

# =====================
# 6. Exportar resultados para análisis
# =====================
with pd.ExcelWriter("indicadores_sunat.xlsx") as writer:
    estado_pj.to_excel(writer, sheet_name="Estado_PJ", index=False)
    estado_pn.to_excel(writer, sheet_name="Estado_PN", index=False)
    cond_pj.to_excel(writer, sheet_name="Condicion_PJ", index=False)
    cond_pn.to_excel(writer, sheet_name="Condicion_PN", index=False)
    ciiu_pj.to_excel(writer, sheet_name="Top10_CIIU_PJ", index=False)
    ciiu_pn.to_excel(writer, sheet_name="Top10_CIIU_PN", index=False)
    dist_pj.to_excel(writer, sheet_name="Distritos_PJ", index=False)
    dist_pn.to_excel(writer, sheet_name="Distritos_PN", index=False)

print("✅ Indicadores calculados y guardados en 'indicadores_sunat.xlsx'")
print(f"Personas Jurídicas en Maynas: {total_pj}")
print(f"Personas Naturales en Maynas: {total_pn}")
print(f"Proporción PJ vs PN: {ratio_pj_pn:.2%}")
