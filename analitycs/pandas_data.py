# script_preparacion.py
import pandas as pd
import json

# --- 1. Cargar y Filtrar los Datos ---
distritos_de_interes = [
    'IQUITOS', 'PUNCHANA', 'BELEN', 
    'SAN JUAN BAUTISTA', 'NAUTA'
]

df = pd.read_csv('../data/PPJJ_ABRIL_2022.csv', encoding='utf-8')
df_filtrado = df[df['Distrito'].isin(distritos_de_interes)].copy()

# --- 2. Limpiar y Estandarizar Datos Clave ---
# Usamos .loc para evitar advertencias de copia
df_filtrado.loc[:, 'CIIU'] = df_filtrado['CIIU'].str.strip().str.upper()
df_filtrado.loc[:, 'nombre via'] = df_filtrado['nombre via'].str.strip().str.upper()
df_filtrado.loc[:, 'Tipo_Via'] = df_filtrado['Tipo_Via'].str.strip().str.upper()

# Crear una columna de 'direccion_completa' para agrupar
df_filtrado['direccion_completa'] = df_filtrado['Tipo_Via'] + ' ' + df_filtrado['nombre via']

# --- 3. Procesar y Estructurar la Información ---
datos_finales = {
    'resumen_distritos': {},
    'actividades_economicas': [],
    'analisis_por_actividad': {},
    'empresas_por_ubicacion': {}
}

# Total por distrito
datos_finales['resumen_distritos'] = df_filtrado['Distrito'].value_counts().to_dict()

# Lista única de actividades
actividades_unicas = df_filtrado['CIIU'].dropna().unique()
datos_finales['actividades_economicas'] = sorted(list(actividades_unicas))

# Análisis detallado por cada actividad
for actividad in datos_finales['actividades_economicas']:
    df_actividad = df_filtrado[df_filtrado['CIIU'] == actividad]
    
    # Conteo por distrito para esta actividad
    conteo_distrito = df_actividad['Distrito'].value_counts().to_dict()
    
    # Direcciones de mayor concentración para esta actividad
    concentracion = df_actividad['direccion_completa'].value_counts().to_dict()
    
    datos_finales['analisis_por_actividad'][actividad] = {
        'conteo_por_distrito': conteo_distrito,
        'concentracion_direcciones': concentracion
    }

    # Guardar la lista de empresas por ubicación
    for direccion, _ in concentracion.items():
        if actividad not in datos_finales['empresas_por_ubicacion']:
            datos_finales['empresas_por_ubicacion'][actividad] = {}
        
        empresas = df_actividad[df_actividad['direccion_completa'] == direccion]
        datos_finales['empresas_por_ubicacion'][actividad][direccion] = empresas.to_dict('records')

# --- 4. Guardar a un archivo JSON ---
with open('datos_empresas.json', 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=4)

print("Procesamiento completado. Archivo 'datos_empresas.json' creado.")