import pandas as pd
import numpy as np
import os
import json
import warnings
import re

warnings.filterwarnings('ignore')

class ProcesadorDashboard:
    def __init__(self, directorio_data='data', directorio_salida='dashboard/dist_json_output'):
        self.directorio_data = directorio_data
        self.directorio_salida = directorio_salida
        self.archivo_ppjj = 'PPJJ_ABRIL_2022.csv'
        self.archivo_ppnn = 'PPNN_ABRIL_2022.csv'
        
        # Crear directorio de salida si no existe
        os.makedirs(self.directorio_salida, exist_ok=True)
        print(f"Directorio de salida listo en: {self.directorio_salida}")

    def cargar_y_unificar(self):
        """Carga ambos CSVs, los limpia y los unifica."""
        try:
            path_ppjj = os.path.join(self.directorio_data, self.archivo_ppjj)
            path_ppnn = os.path.join(self.directorio_data, self.archivo_ppnn)

            df_ppjj = pd.read_csv(path_ppjj, encoding='utf-8', low_memory=False)
            df_ppnn = pd.read_csv(path_ppnn, encoding='utf-8', low_memory=False)
            
            df_ppjj['Tipo_Persona'] = 'Jurídica'
            df_ppnn['Tipo_Persona'] = 'Natural'
            
            # Unificar los DataFrames
            df_unificado = pd.concat([df_ppjj, df_ppnn], ignore_index=True)
            print(f"Total de registros unificados: {len(df_unificado):,}")
            return df_unificado
        except Exception as e:
            print(f"❌ Error al cargar los datos: {e}")
            return None

    def clasificar_sector(self, descripcion_ciiu):
        """Clasifica una descripción CIIU en un sector de alto nivel."""
        if pd.isna(descripcion_ciiu): return 'No Clasificado'
        desc = str(descripcion_ciiu).upper()
        if any(palabra in desc for palabra in ['COMERCIO', 'VENTA', 'VTA', 'ALMACEN']): return 'Comercio'
        if any(palabra in desc for palabra in ['RESTAURANTE', 'BAR', 'CANTINA', 'COMIDA']): return 'Restaurantes y Alojamiento'
        if any(palabra in desc for palabra in ['CONSTRUCCION', 'EDIFICIO', 'OBRA']): return 'Construcción'
        if any(palabra in desc for palabra in ['TRANSPORTE', 'CARGA', 'PASAJERO']): return 'Transporte'
        if any(palabra in desc for palabra in ['SALUD', 'MEDIC', 'DENTISTA']): return 'Servicios de Salud'
        if any(palabra in desc for palabra in ['ENSEÑANZA', 'EDUCACION', 'COLEGIO']): return 'Educación'
        if any(palabra in desc for palabra in ['AGRICULTURA', 'CULTIVO', 'GANADERIA']): return 'Agricultura y Ganadería'
        if any(palabra in desc for palabra in ['MANUFACTURA', 'FABRICA', 'INDUSTRIA']): return 'Manufactura'
        if any(palabra in desc for palabra in ['INMOBILIARIA']): return 'Actividades Inmobiliarias'
        if any(palabra in desc for palabra in ['SERVICIO']): return 'Otros Servicios'
        return 'Otros Sectores'

    def enriquecer_datos(self, df):
        """Añade columnas de valor para la inteligencia de negocios."""
        print("Enriqueciendo datos para el dashboard...")
        
        # 1. Limpieza de columnas clave
        df['Distrito'] = df['Distrito'].str.strip().str.upper().fillna('NO ESPECIFICADO')
        df['CIIU'] = df['CIIU'].str.strip()
        
        # 2. Crear sector agrupado (inteligencia de negocios)
        df['sector_agrupado'] = df['CIIU'].apply(self.clasificar_sector)
        
        # 3. Crear dirección completa y estandarizada
        df['nombre via'] = df['nombre via'].fillna('')
        df['Tipo_Via'] = df['Tipo_Via'].fillna('')
        df['número'] = df['número'].fillna('').astype(str).str.replace('.0', '', regex=False)
        df['direccion_completa'] = df['Tipo_Via'] + ' ' + df['nombre via'] + ' ' + df['número']
        df['direccion_completa'] = df['direccion_completa'].str.strip()
        
        # 4. Calcular puntaje de prioridad para visitas
        distritos_prioritarios = ['IQUITOS', 'BELEN', 'SAN JUAN BAUTISTA', 'PUNCHANA']
        sectores_prioritarios = ['Comercio', 'Restaurantes y Alojamiento', 'Construcción']
        
        df['prioridad'] = 0
        df.loc[df['Distrito'].isin(distritos_prioritarios), 'prioridad'] += 3
        df.loc[df['sector_agrupado'].isin(sectores_prioritarios), 'prioridad'] += 2
        df.loc[df['Tipo_Persona'] == 'Jurídica', 'prioridad'] += 1
        
        # 5. Seleccionar y renombrar columnas finales para el JSON
        columnas_finales = {
            'ddp_nombre': 'nombre',
            'Tipo_Persona': 'tipo_persona',
            'Distrito': 'distrito',
            'direccion_completa': 'direccion',
            'CIIU': 'ciiu_descripcion',
            'ddp_ciiu': 'ciiu_codigo',
            'sector_agrupado': 'sector',
            'prioridad': 'prioridad'
        }
        df_final = df[columnas_finales.keys()].copy()
        df_final.rename(columns=columnas_finales, inplace=True)
        df_final['ciiu_codigo'] = df_final['ciiu_codigo'].fillna('N/A')
        
        print("Enriquecimiento completado.")
        return df_final

    def generar_archivos_json(self, df):
        """Genera un JSON por distrito y un archivo de metadatos."""
        print("Generando archivos JSON para el dashboard...")
        
        distritos = df['distrito'].unique()
        sectores = df['sector'].unique()
        
        # 1. Guardar metadatos para los filtros del dashboard
        metadata = {
            'distritos': sorted(list(distritos)),
            'sectores': sorted(list(sectores))
        }
        path_metadata = os.path.join(self.directorio_salida, 'metadata.json')
        with open(path_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"✅ Metadatos guardados en: {path_metadata}")
        
        # 2. Guardar un JSON por cada distrito
        for distrito in distritos:
            df_distrito = df[df['distrito'] == distrito]
            
            # Convertir a una lista de diccionarios (JSON)
            datos_json = df_distrito.to_dict(orient='records')
            
            # Crear un nombre de archivo seguro
            nombre_archivo = re.sub(r'[^a-z0-9]+', '_', distrito.lower()) + '.json'
            path_archivo = os.path.join(self.directorio_salida, nombre_archivo)
            
            with open(path_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos_json, f, ensure_ascii=False)
            print(f"  -> Generado {nombre_archivo} con {len(df_distrito)} registros.")
            
        print("✅ Generación de archivos JSON completada.")

def main():
    procesador = ProcesadorDashboard()
    df_unificado = procesador.cargar_y_unificar()
    if df_unificado is not None:
        df_enriquecido = procesador.enriquecer_datos(df_unificado)
        procesador.generar_archivos_json(df_enriquecido)

if __name__ == "__main__":
    main()