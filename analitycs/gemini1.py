import pandas as pd
import numpy as np

# --- 1. Simulación de Datos (Reemplaza con tus archivos reales) ---

# Datos de Personas Jurídicas
# La columna 'CIIU' es la descripción, 'cod_ciiu2' y 'cod_ciiu3' son secundarias
juridicas_dataX = {
    'ddp_numruc': [f'J{i:05d}' for i in range(10959)],
    'ddp_nombre': [f'Empresa Jurídica {i}' for i in range(10959)],
    'ddp_numreg': [np.random.randint(1000, 9999) for _ in range(10959)],
    'Estado': ['ACTIVO'] * 10959,
    'Condicion_Domicilio': ['HABIDO'] * 10959,
    'Departamento': ['LORETO'] * 10959,
    'Provincia': np.random.choice(['MAYNAS', 'LORETO', 'REQUENA'], 10959, p=[0.8, 0.1, 0.1]),
    'Distrito': np.random.choice(['IQUITOS', 'SAN JUAN BAUTISTA', 'PUNCHANA', 'BELEN', 'NAUTA', 'REQUENA', 'OTRO_DISTRITO'], 10959, p=[0.3, 0.2, 0.2, 0.1, 0.1, 0.05, 0.05]),
    'Tipo_Via': np.random.choice(['AV', 'JR', 'CALLE'], 10959),
    'nombre via': [f'Via {i}' for i in range(10959)],
    'número': [str(np.random.randint(100, 999)) for _ in range(10959)],
    'interior': [''] * 10959, 'kilometro': [''] * 10959, 'manzana': [''] * 10959,
    'numedepart': [''] * 10959, 'lote': [''] * 10959, 'tipo_Zona': ['URBANA'] * 10959,
    'nombzona': [''] * 10959,
    'CIIU': np.random.choice([
        'OTRAS ACTIVID.DE TIPO SERVICIO NCP', 'OTRAS ACTIVIDADES EMPRESARIALES NCP.',
        'CONSTRUCCION EDIFICIOS COMPLETOS.', 'VTA. MIN. ALIMENTOS, BEBIDAS, TABACO.',
        'RESTAURANTES, BARES Y CANTINAS.', 'ACTIVIDADES INMOBILIARIAS',
        'TRANSPORTE DE CARGA POR CARRETERA', 'PESCA EN AGUAS CONTINENTALES',
        'CULTIVO DE ARROZ', 'FABRICACION DE PAN Y PRODUCTOS DE PANADERIA'
    ], 10959, p=[0.2, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.1]),
    'cod_ciiu2': ['93098'] * 10959, # Ignoramos estas
    'cod_ciiu3': ['74996'] * 10959  # Ignoramos estas
}
df_juridicasY = pd.DataFrame(juridicas_dataX)

# Datos de Personas Naturales
# La columna 'CIIU' es la descripción, 'ddp_ciiu' es el código principal
naturales_dataX = {
    'ddp_numruc': [f'N{i:05d}' for i in range(65535)],
    'ddp_nombre': [f'Persona Natural {i}' for i in range(65535)],
    'ddp_numreg': [np.random.randint(1000, 9999) for _ in range(65535)],
    'Estado': ['ACTIVO'] * 65535,
    'Condicion_Domicilio': ['HABIDO'] * 65535,
    'Departamento': ['LORETO'] * 65535,
    'Provincia': np.random.choice(['MAYNAS', 'LORETO', 'REQUENA'], 65535, p=[0.8, 0.1, 0.1]),
    'Distrito': np.random.choice(['IQUITOS', 'SAN JUAN BAUTISTA', 'PUNCHANA', 'BELEN', 'NAUTA', 'REQUENA', 'OTRO_DISTRITO'], 65535, p=[0.35, 0.25, 0.2, 0.1, 0.05, 0.02, 0.03]),
    'ddp_ciiu': np.random.choice([
        '9609', '7499', '4100', '4711', '5610', '6810', '4923', '0311', '0111', '1071' # Códigos representativos
    ], 65535, p=[0.2, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.1]),
    'CIIU': np.random.choice([
        'OTRAS ACTIVID.DE TIPO SERVICIO NCP', 'OTRAS ACTIVIDADES EMPRESARIALES NCP.',
        'CONSTRUCCION EDIFICIOS COMPLETOS.', 'VTA. MIN. ALIMENTOS, BEBIDAS, TABACO.',
        'RESTAURANTES, BARES Y CANTINAS.', 'ACTIVIDADES INMOBILIARIAS',
        'TRANSPORTE DE CARGA POR CARRETERA', 'PESCA EN AGUAS CONTINENTALES',
        'CULTIVO DE ARROZ', 'FABRICACION DE PAN Y PRODUCTOS DE PANADERIA'
    ], 65535, p=[0.2, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.1]),
    'cod_ciiu2': ['93098'] * 65535, # Ignoramos estas
    'cod_ciiu3': ['74996'] * 65535  # Ignoramos estas
}
#df_naturales = pd.DataFrame(naturales_data)

# Si ya tienes los CSV, reemplaza las líneas anteriores con:
df_juridicas = pd.read_csv('../data/PPJJ_ABRIL_2022.csv')
df_naturales = pd.read_csv('../data/PPNN_ABRIL_2022.csv')

# --- 2. Preprocesamiento y Limpieza ---

# Añadir un identificador de tipo de persona
df_juridicas['Tipo_Persona'] = 'Jurídica'
df_naturales['Tipo_Persona'] = 'Natural'

# Para personas jurídicas, crearemos una columna 'Actividad_Principal_CIIU_Code'
# Si no tienen el código, podemos intentar mapearlo desde la descripción si tenemos una tabla de mapeo.
# Por ahora, la dejaremos vacía o con un marcador.
df_juridicas['Actividad_Principal_CIIU_Code'] = 'N/A' # No disponible directamente
df_naturales['Actividad_Principal_CIIU_Code'] = df_naturales['ddp_ciiu']

# Renombrar 'CIIU' a 'Actividad_Principal_Descripcion' para claridad
df_juridicas.rename(columns={'CIIU': 'Actividad_Principal_Descripcion'}, inplace=True)
df_naturales.rename(columns={'CIIU': 'Actividad_Principal_Descripcion'}, inplace=True)

# Seleccionar columnas relevantes para el análisis unificado
cols_juridicas = ['ddp_numruc', 'ddp_nombre', 'Tipo_Persona', 'Estado', 'Condicion_Domicilio',
                  'Departamento', 'Provincia', 'Distrito', 'Actividad_Principal_Descripcion',
                  'Actividad_Principal_CIIU_Code', 'Tipo_Via', 'nombre via', 'número', 'interior',
                  'kilometro', 'manzana', 'numedepart', 'lote', 'tipo_Zona', 'nombzona']
cols_naturales = ['ddp_numruc', 'ddp_nombre', 'Tipo_Persona', 'Estado', 'Condicion_Domicilio',
                  'Departamento', 'Provincia', 'Distrito', 'Actividad_Principal_Descripcion',
                  'Actividad_Principal_CIIU_Code']

# Unificar DataFrames (manejar columnas faltantes)
df_juridicas_filtered = df_juridicas[cols_juridicas]
df_naturales_filtered = df_naturales[cols_naturales]

# Rellenar columnas de dirección faltantes en naturales para una unión coherente (aunque serán NaN)
for col in ['Tipo_Via', 'nombre via', 'número', 'interior', 'kilometro', 'manzana', 'numedepart', 'lote', 'tipo_Zona', 'nombzona']:
    if col not in df_naturales_filtered.columns:
        df_naturales_filtered[col] = np.nan

df_unificado = pd.concat([df_juridicas_filtered, df_naturales_filtered], ignore_index=True)

# Limpiar y estandarizar nombres de distritos y actividades
df_unificado['Distrito'] = df_unificado['Distrito'].str.upper().str.strip()
df_unificado['Actividad_Principal_Descripcion'] = df_unificado['Actividad_Principal_Descripcion'].str.upper().str.strip()

# --- 3. Definir Distritos Prioritarios ---
distritos_prioritarios = ['IQUITOS', 'BELEN', 'SAN JUAN BAUTISTA', 'PUNCHANA']
df_unificado['Prioritario'] = df_unificado['Distrito'].isin(distritos_prioritarios)

# --- 4. Análisis para el Dashboard ---

# a) Resumen General
total_empresas = len(df_unificado)
total_juridicas = len(df_unificado[df_unificado['Tipo_Persona'] == 'Jurídica'])
total_naturales = len(df_unificado[df_unificado['Tipo_Persona'] == 'Natural'])
total_activos = len(df_unificado[df_unificado['Estado'] == 'ACTIVO'])

# b) Distribución por Tipo de Persona
distribucion_tipo_persona = df_unificado['Tipo_Persona'].value_counts(normalize=True).mul(100).round(2)

# c) Empresas en Distritos Prioritarios
empresas_prioritarias = df_unificado[df_unificado['Prioritario']]
conteo_distritos_prioritarios = empresas_prioritarias['Distrito'].value_counts().reset_index()
conteo_distritos_prioritarios.columns = ['Distrito', 'Cantidad']
conteo_distritos_prioritarios['Porcentaje'] = (conteo_distritos_prioritarios['Cantidad'] / len(empresas_prioritarias) * 100).round(2)

# d) Top Sectores Económicos (descripción CIIU) en Distritos Prioritarios
top_sectores_prioritarios = empresas_prioritarias['Actividad_Principal_Descripcion'].value_counts().head(10).reset_index()
top_sectores_prioritarios.columns = ['Sector_Descripcion', 'Cantidad']
top_sectores_prioritarios['Porcentaje'] = (top_sectores_prioritarios['Cantidad'] / len(empresas_prioritarias) * 100).round(2)

# e) Top Sectores Económicos (código CIIU) de Personas Naturales en Distritos Prioritarios
top_ciiu_codes_naturales_prioritarios = empresas_prioritarias[
    (empresas_prioritarias['Tipo_Persona'] == 'Natural') &
    (empresas_prioritarias['Actividad_Principal_CIIU_Code'].notna()) &
    (empresas_prioritarias['Actividad_Principal_CIIU_Code'] != 'N/A')
]['Actividad_Principal_CIIU_Code'].value_counts().head(10).reset_index()
top_ciiu_codes_naturales_prioritarios.columns = ['CIIU_Code', 'Cantidad']
top_ciiu_codes_naturales_prioritarios['Porcentaje'] = (
    top_ciiu_codes_naturales_prioritarios['Cantidad'] /
    len(empresas_prioritarias[empresas_prioritarias['Tipo_Persona'] == 'Natural']) * 100
).round(2)


# f) Distribución general por distrito (todos los distritos)
distribucion_general_distritos = df_unificado['Distrito'].value_counts().reset_index()
distribucion_general_distritos.columns = ['Distrito', 'Cantidad']
distribucion_general_distritos['Porcentaje'] = (distribucion_general_distritos['Cantidad'] / total_empresas * 100).round(2)


# --- 5. Preparar Datos para HTML ---
# Convertir DataFrames a formato JSON o listas de diccionarios para facilitar la inserción en HTML/JS
data_for_html = {
    'resumen_general': {
        'total_empresas': total_empresas,
        'total_juridicas': total_juridicas,
        'total_naturales': total_naturales,
        'total_activos': total_activos
    },
    'distribucion_tipo_persona': distribucion_tipo_persona.to_dict(),
    'distritos_prioritarios': distritos_prioritarios,
    'conteo_distritos_prioritarios': conteo_distritos_prioritarios.to_dict(orient='records'),
    'top_sectores_prioritarios': top_sectores_prioritarios.to_dict(orient='records'),
    'top_ciiu_codes_naturales_prioritarios': top_ciiu_codes_naturales_prioritarios.to_dict(orient='records'),
    'distribucion_general_distritos': distribucion_general_distritos.to_dict(orient='records')
}

# Puedes guardar esto en un archivo JSON o pasarlo directamente a tu template engine si usas Flask/Django
import json
with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data_for_html, f, ensure_ascii=False, indent=4)

print("Análisis completado y datos guardados en 'dashboard_data.json'")