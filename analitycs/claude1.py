import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings

warnings.filterwarnings('ignore')

class ProcesadorDatos:
    def __init__(self, directorio_data='data'):
        self.directorio_data = directorio_data
        self.archivo_ppjj = 'PPJJ_ABRIL_2022.csv'
        self.archivo_ppnn = 'PPNN_ABRIL_2022.csv'
        
    def cargar_y_limpiar_datos(self, archivo_path, tipo_persona):
        """Cargar y limpiar datos de un archivo CSV"""
        try:
            print(f"Procesando {tipo_persona}: {archivo_path}")
            
            # Cargar datos
            df = pd.read_csv(archivo_path, encoding='utf-8')
            print(f"Registros iniciales {tipo_persona}: {len(df)}")
            print(f"Columnas encontradas: {df.columns.tolist()}")
            
            # Eliminar columnas duplicadas
            df = df.loc[:, ~df.columns.duplicated()]
            print(f"Columnas después de eliminar duplicados: {df.columns.tolist()}")
            
            # Limpiar datos básicos
            df = df.dropna(subset=['ddp_numruc', 'ddp_nombre'])
            print(f"Registros válidos {tipo_persona}: {len(df)}")
            
            # Agregar columna de tipo de persona
            df['tipo_persona'] = 'Jurídica' if tipo_persona == 'personas jurídicas' else 'Natural'
            
            return df
            
        except Exception as e:
            print(f"❌ Error cargando {archivo_path}: {str(e)}")
            return None

    def estandarizar_columnas(self, df_ppjj, df_ppnn):
        """Estandarizar columnas entre ambos DataFrames"""
        print("Estandarizando columnas...")
        
        # Eliminar duplicados en columnas por si acaso
        df_ppjj = df_ppjj.loc[:, ~df_ppjj.columns.duplicated()]
        df_ppnn = df_ppnn.loc[:, ~df_ppnn.columns.duplicated()]
        
        print(f"Columnas en PPJJ: {df_ppjj.columns.tolist()}")
        print(f"Columnas en PPNN: {df_ppnn.columns.tolist()}")
        
        # Identificar columnas comunes
        columnas_ppjj = set(df_ppjj.columns)
        columnas_ppnn = set(df_ppnn.columns)
        columnas_comunes = columnas_ppjj.intersection(columnas_ppnn)
        
        # Definir columnas que queremos mantener (priorizando las comunes)
        columnas_deseadas = [
            'ddp_numruc', 'ddp_nombre', 'Estado', 'Departamento', 
            'Provincia', 'Distrito', 'CIIU', 'tipo_persona'
        ]
        
        # Agregar columnas adicionales que estén en ambos DataFrames
        columnas_adicionales = ['Tipo_Via', 'nombre via', 'número', 'interior', 
                               'kilometro', 'manzana', 'lote', 'Condicion_Domicilio']
        
        columnas_finales = []
        for col in columnas_deseadas:
            if col in columnas_comunes:
                columnas_finales.append(col)
        
        for col in columnas_adicionales:
            if col in columnas_comunes and col not in columnas_finales:
                columnas_finales.append(col)
        
        # Agregar ddp_ciiu solo para PPNN
        if 'ddp_ciiu' in df_ppnn.columns:
            df_ppnn_std = df_ppnn[columnas_finales + ['ddp_ciiu']].copy()
        else:
            df_ppnn_std = df_ppnn[columnas_finales].copy()
            
        df_ppjj_std = df_ppjj[columnas_finales].copy()
        
        # Agregar columna ddp_ciiu vacía para PPJJ para mantener consistencia
        if 'ddp_ciiu' not in df_ppjj_std.columns:
            df_ppjj_std['ddp_ciiu'] = None
        
        print(f"Columnas finales PPJJ: {df_ppjj_std.columns.tolist()}")
        print(f"Columnas finales PPNN: {df_ppnn_std.columns.tolist()}")
        
        return df_ppjj_std, df_ppnn_std

    def crear_mapeo_ciiu(self, df_ppnn):
        """Crear mapeo de códigos CIIU basado en PPNN"""
        print("\nCreando mapeo de códigos CIIU...")
        
        # Filtrar registros que tengan tanto código como descripción
        df_mapeo = df_ppnn[
            (df_ppnn['ddp_ciiu'].notna()) & 
            (df_ppnn['CIIU'].notna()) & 
            (df_ppnn['ddp_ciiu'] != '') & 
            (df_ppnn['CIIU'] != '')
        ].copy()
        
        # Crear mapeo único código -> descripción
        mapeo_codigo_descripcion = df_mapeo.groupby('ddp_ciiu')['CIIU'].first().to_dict()
        
        print(f"Total códigos CIIU mapeados: {len(mapeo_codigo_descripcion)}")
        print("Muestra del mapeo código -> descripción:")
        for i, (codigo, descripcion) in enumerate(list(mapeo_codigo_descripcion.items())[:10]):
            print(f"  {codigo}: {descripcion[:50]}...")
        
        return mapeo_codigo_descripcion

    def clasificar_sectores_por_descripcion(self, descripcion_ciiu):
        """Clasificar sector económico basado en la descripción CIIU"""
        if pd.isna(descripcion_ciiu):
            return 'No Clasificado'
        
        desc = str(descripcion_ciiu).upper()
        
        # Clasificación por palabras clave en la descripción
        if any(palabra in desc for palabra in ['COMERCIO', 'VENTA', 'VTA', 'ALMACEN', 'TIENDA']):
            if any(palabra in desc for palabra in ['MAYOR', 'MAYORISTA']):
                return 'Comercio Mayorista'
            else:
                return 'Comercio Minorista'
        elif any(palabra in desc for palabra in ['RESTAURANTE', 'BAR', 'CANTINA', 'COMIDA', 'BEBIDA']):
            return 'Restaurantes y Servicios de Comida'
        elif any(palabra in desc for palabra in ['CONSTRUCCION', 'EDIFICIO', 'OBRA']):
            return 'Construcción'
        elif any(palabra in desc for palabra in ['SERVICIO', 'ACTIVID']):
            if any(palabra in desc for palabra in ['SALUD', 'MEDIC', 'HOSPITAL', 'CLINIC']):
                return 'Servicios de Salud'
            elif any(palabra in desc for palabra in ['ENSEÑANZA', 'EDUCACION', 'ESCUELA']):
                return 'Educación'
            else:
                return 'Otros Servicios'
        elif any(palabra in desc for palabra in ['TRANSPORTE', 'TAXI', 'MOTOTAXI']):
            return 'Transporte'
        elif any(palabra in desc for palabra in ['INMOBILIARIA', 'BIENES RAICES']):
            return 'Actividades Inmobiliarias'
        elif any(palabra in desc for palabra in ['MANUFACTURA', 'FABRICA', 'INDUSTRIA', 'PRODUCCION']):
            return 'Manufactura'
        elif any(palabra in desc for palabra in ['AGRICULTURA', 'CULTIVO', 'AGRICOLA']):
            return 'Agricultura'
        elif any(palabra in desc for palabra in ['PESCA', 'PESQUER']):
            return 'Pesca'
        elif any(palabra in desc for palabra in ['HOTEL', 'HOSPEDAJE', 'ALOJAMIENTO']):
            return 'Alojamiento'
        else:
            return 'Otros'

    def analizar_sectores_economicos(self, df):
        """Analizar distribución por sectores económicos"""
        print("\n=== ANÁLISIS DE SECTORES ECONÓMICOS ===")
        
        # Aplicar clasificación por descripción CIIU
        df['sector_economico'] = df['CIIU'].apply(self.clasificar_sectores_por_descripcion)
        
        # Estadísticas por sector
        sector_stats = df.groupby('sector_economico').size().sort_values(ascending=False)
        
        print("Sectores económicos principales:")
        for i, (sector, cantidad) in enumerate(sector_stats.items(), 1):
            porcentaje = (cantidad / len(df)) * 100
            print(f"{i:2d}. {sector:<30} {cantidad:6,} ({porcentaje:5.2f}%)")
        
        return sector_stats

    def analizar_por_distrito_y_sector(self, df):
        """Analizar concentración por distrito y sector"""
        print("\n=== ANÁLISIS POR DISTRITO Y SECTOR ===")
        
        # Crear tabla cruzada distrito vs sector
        distrito_sector = pd.crosstab(df['Distrito'], df['sector_economico'], margins=True)
        
        # Mostrar top distritos con más diversidad de sectores
        print("Top 10 distritos por diversidad de sectores:")
        diversidad_distritos = (distrito_sector > 0).sum(axis=1).sort_values(ascending=False)
        
        for i, (distrito, num_sectores) in enumerate(diversidad_distritos.head(10).items(), 1):
            if distrito != 'All':  # Excluir la fila de totales
                total_empresas = distrito_sector.loc[distrito, 'All']
                print(f"{i:2d}. {distrito:<25} {num_sectores:2d} sectores, {total_empresas:5,} empresas")
        
        return distrito_sector

    def analizar_vias_principales(self, df):
        """Analizar concentración en vías principales"""
        print("\n=== ANÁLISIS DE VÍAS PRINCIPALES ===")
        
        # Verificar qué columnas de vías están disponibles
        columnas_via = [col for col in df.columns if 'via' in col.lower() or 'tipo' in col.lower()]
        print(f"Columnas relacionadas con vías disponibles: {columnas_via}")
        
        # Verificar si tenemos las columnas necesarias
        tiene_tipo_via = any(col in df.columns for col in ['Tipo_Via', 'tipo_via', 'TipoVia'])
        tiene_nombre_via = any(col in df.columns for col in ['nombre via', 'nombre_via', 'NombreVia'])
        
        if not tiene_nombre_via:
            print("❌ No se encontró columna de nombre de vía. Saltando análisis de vías.")
            return pd.Series(), pd.DataFrame()
        
        # Determinar nombres exactos de columnas
        col_tipo_via = None
        col_nombre_via = None
        
        for col in ['Tipo_Via', 'tipo_via', 'TipoVia']:
            if col in df.columns:
                col_tipo_via = col
                break
                
        for col in ['nombre via', 'nombre_via', 'NombreVia']:
            if col in df.columns:
                col_nombre_via = col
                break
        
        print(f"Usando columna tipo vía: {col_tipo_via}")
        print(f"Usando columna nombre vía: {col_nombre_via}")
        
        # Crear dataset para análisis de vías
        if col_tipo_via is not None:
            # Filtrar solo avenidas y jirones
            df_vias = df[
                (df[col_tipo_via].notna()) & 
                (df[col_nombre_via].notna()) &
                (df[col_tipo_via].str.upper().isin(['AVENIDA', 'JIRON', 'JIRÓN', 'AV', 'JR']))
            ].copy()
            
            # Combinar tipo de vía y nombre
            df_vias['via_completa'] = df_vias[col_tipo_via].str.upper() + ' ' + df_vias[col_nombre_via].str.upper()
        else:
            # Solo usar nombre de vía si no hay tipo
            print("⚠️ No se encontró columna de tipo de vía. Analizando solo por nombre.")
            df_vias = df[df[col_nombre_via].notna()].copy()
            df_vias['via_completa'] = df_vias[col_nombre_via].str.upper()
            
            # Filtrar por nombres que parezcan avenidas o jirones
            patron_vias = r'(^AV\.|^AVENIDA|^JR\.|^JIRON|^JIRÓN)'
            df_vias = df_vias[df_vias['via_completa'].str.contains(patron_vias, regex=True, na=False)]
        
        print(f"Total empresas en vías principales: {len(df_vias):,}")
        
        if len(df_vias) == 0:
            print("❌ No se encontraron empresas en vías principales.")
            return pd.Series(), pd.DataFrame()
        
        # Top vías por número de empresas
        vias_empresas = df_vias.groupby('via_completa').size().sort_values(ascending=False)
        
        print(f"\nTop 20 vías con mayor concentración empresarial:")
        for i, (via, cantidad) in enumerate(vias_empresas.head(20).items(), 1):
            porcentaje_total = (cantidad / len(df)) * 100
            porcentaje_vias = (cantidad / len(df_vias)) * 100
            print(f"{i:2d}. {via:<35} {cantidad:4,} ({porcentaje_vias:4.1f}% vías, {porcentaje_total:3.1f}% total)")
        
        # Análisis por sector en vías principales
        if 'sector_economico' in df_vias.columns:
            print(f"\nDistribución de sectores en vías principales:")
            sectores_vias = df_vias.groupby('sector_economico').size().sort_values(ascending=False)
            
            for sector, cantidad in sectores_vias.items():
                porcentaje = (cantidad / len(df_vias)) * 100
                print(f"• {sector:<30} {cantidad:4,} ({porcentaje:5.2f}%)")
        
        return vias_empresas, df_vias

    def crear_dataset_dashboard(self, df, distrito_sector, vias_empresas, df_vias):
        """Crear dataset optimizado para dashboard"""
        print("\n=== CREANDO DATASET PARA DASHBOARD ===")
        
        # Verificar columnas disponibles
        columnas_disponibles = df.columns.tolist()
        print(f"Columnas disponibles: {columnas_disponibles}")
        
        # Definir columnas básicas que siempre incluiremos
        columnas_basicas = ['ddp_numruc', 'ddp_nombre', 'tipo_persona', 'Estado',
                           'Provincia', 'Distrito', 'sector_economico', 'CIIU']
        
        # Agregar columnas opcionales si están disponibles
        columnas_opcionales = ['Tipo_Via', 'nombre via', 'número', 'ddp_ciiu']
        
        columnas_finales = columnas_basicas.copy()
        for col in columnas_opcionales:
            if col in columnas_disponibles:
                columnas_finales.append(col)
        
        print(f"Columnas incluidas en dashboard: {columnas_finales}")
        
        # Dataset principal simplificado
        df_dashboard = df[columnas_finales].copy()
        
        # Agregar flag de vía principal
        if len(df_vias) > 0:
            # Marcar empresas que están en vías principales
            df_dashboard['via_principal'] = df_dashboard['ddp_numruc'].isin(df_vias['ddp_numruc'])
        else:
            df_dashboard['via_principal'] = False
        
        print(f"Dataset dashboard creado: {len(df_dashboard):,} registros")
        print(f"Empresas en vías principales: {df_dashboard['via_principal'].sum():,}")
        
        return df_dashboard

    def analizar_distribucion_geografica(self, df):
        """Analizar distribución geográfica"""
        print("\n=== ANÁLISIS GEOGRÁFICO ===")
        
        # Por provincia
        print("Distribución por Provincia:")
        provincias = df.groupby('Provincia').size().sort_values(ascending=False)
        for provincia, cantidad in provincias.items():
            porcentaje = (cantidad / len(df)) * 100
            print(f"• {provincia:<25} {cantidad:6,} ({porcentaje:5.2f}%)")
        
        print(f"\nTotal provincias: {len(provincias)}")
        
        # Por distrito (top 15)
        print("\nTop 15 distritos:")
        distritos = df.groupby(['Provincia', 'Distrito']).size().sort_values(ascending=False)
        for i, ((provincia, distrito), cantidad) in enumerate(distritos.head(15).items(), 1):
            porcentaje = (cantidad / len(df)) * 100
            print(f"{i:2d}. {distrito} ({provincia}): {cantidad:,} ({porcentaje:.2f}%)")
        
        return provincias, distritos

    def analizar_tipos_empresa(self, df):
        """Analizar tipos de empresa"""
        print("\n=== ANÁLISIS TIPOS DE EMPRESA ===")
        
        # Por tipo de persona
        tipos = df.groupby('tipo_persona').size().sort_values(ascending=False)
        print("Distribución por tipo:")
        for tipo, cantidad in tipos.items():
            porcentaje = (cantidad / len(df)) * 100
            print(f"• {tipo:<15} {cantidad:6,} ({porcentaje:5.2f}%)")
        
        # Por estado
        if 'Estado' in df.columns:
            print("\nDistribución por estado:")
            estados = df.groupby('Estado').size().sort_values(ascending=False)
            for estado, cantidad in estados.items():
                porcentaje = (cantidad / len(df)) * 100
                print(f"• {estado:<15} {cantidad:6,} ({porcentaje:5.2f}%)")
        
        return tipos

    def generar_reporte_resumen(self, df, sector_stats, provincias, tipos):
        """Generar reporte resumen ejecutivo"""
        print("\n" + "="*60)
        print("REPORTE RESUMEN EJECUTIVO - EMPRESAS LORETO")
        print("="*60)
        
        total_empresas = len(df)
        print(f"📊 CIFRAS GENERALES:")
        print(f"   Total de empresas registradas: {total_empresas:,}")
        print(f"   Fecha de datos: Abril 2022")
        
        print(f"\n🏢 COMPOSICIÓN EMPRESARIAL:")
        for tipo, cantidad in tipos.items():
            porcentaje = (cantidad / total_empresas) * 100
            print(f"   • {tipo}: {cantidad:,} ({porcentaje:.1f}%)")
        
        print(f"\n🌍 DISTRIBUCIÓN GEOGRÁFICA:")
        print(f"   • Total provincias: {len(provincias)}")
        print(f"   • Provincia principal: {provincias.index[0]} ({provincias.iloc[0]:,} empresas)")
        
        print(f"\n💼 SECTORES PRINCIPALES:")
        for i, (sector, cantidad) in enumerate(sector_stats.head(5).items(), 1):
            porcentaje = (cantidad / total_empresas) * 100
            print(f"   {i}. {sector}: {cantidad:,} ({porcentaje:.1f}%)")
        
        # Estadísticas adicionales
        print(f"\n📈 ESTADÍSTICAS ADICIONALES:")
        empresas_activas = df[df['Estado'] == 'ACTIVO'].shape[0] if 'Estado' in df.columns else 'N/A'
        if empresas_activas != 'N/A':
            print(f"   • Empresas activas: {empresas_activas:,}")
            print(f"   • Tasa de actividad: {(empresas_activas/total_empresas)*100:.1f}%")

    def guardar_resultados(self, df_principal, df_dashboard=None):
        """Guardar datos procesados"""
        try:
            # Guardar dataset principal
            ruta_principal = os.path.join(self.directorio_data, 'empresas_loreto_completo.csv')
            df_principal.to_csv(ruta_principal, index=False, encoding='utf-8')
            print(f"\n✅ Dataset completo guardado en: {ruta_principal}")
            print(f"   Registros: {len(df_principal):,}")
            
            # Guardar dataset para dashboard si existe
            if df_dashboard is not None:
                ruta_dashboard = os.path.join(self.directorio_data, 'empresas_loreto_dashboard.csv')
                df_dashboard.to_csv(ruta_dashboard, index=False, encoding='utf-8')
                print(f"✅ Dataset dashboard guardado en: {ruta_dashboard}")
                print(f"   Registros: {len(df_dashboard):,}")
                
        except Exception as e:
            print(f"❌ Error guardando archivos: {str(e)}")

def main():
    print("=== INICIANDO PROCESAMIENTO DE DATOS EMPRESARIALES LORETO ===")
    print(f"Fecha de procesamiento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Inicializar procesador
        procesador = ProcesadorDatos()
        
        # Verificar archivos
        archivo_ppjj = os.path.join(procesador.directorio_data, procesador.archivo_ppjj)
        archivo_ppnn = os.path.join(procesador.directorio_data, procesador.archivo_ppnn)
        
        if not os.path.exists(archivo_ppjj):
            print(f"❌ No se encuentra el archivo: {archivo_ppjj}")
            return
        
        if not os.path.exists(archivo_ppnn):
            print(f"❌ No se encuentra el archivo: {archivo_ppnn}")
            return
        
        # Cargar datos
        df_ppjj = procesador.cargar_y_limpiar_datos(archivo_ppjj, 'personas jurídicas')
        df_ppnn = procesador.cargar_y_limpiar_datos(archivo_ppnn, 'personas naturales')
        
        if df_ppjj is None or df_ppnn is None:
            print("❌ Error en la carga de datos")
            return
        
        # Crear mapeo CIIU
        mapeo_ciiu = procesador.crear_mapeo_ciiu(df_ppnn)
        
        # Estandarizar columnas
        df_ppjj_std, df_ppnn_std = procesador.estandarizar_columnas(df_ppjj, df_ppnn)
        
        # Combinar datos
        print("\nCombinando datos...")
        df_combined = pd.concat([df_ppjj_std, df_ppnn_std], ignore_index=True)
        print(f"Total registros combinados: {len(df_combined):,}")
        
        # Realizar análisis
        sector_stats = procesador.analizar_sectores_economicos(df_combined)
        distrito_sector = procesador.analizar_por_distrito_y_sector(df_combined)
        vias_empresas, df_vias = procesador.analizar_vias_principales(df_combined)
        provincias, distritos = procesador.analizar_distribucion_geografica(df_combined)
        tipos = procesador.analizar_tipos_empresa(df_combined)
        
        # Crear dataset para dashboard
        df_dashboard = procesador.crear_dataset_dashboard(df_combined, distrito_sector, vias_empresas, df_vias)
        
        # Generar reporte resumen
        procesador.generar_reporte_resumen(df_combined, sector_stats, provincias, tipos)
        
        # Guardar resultados
        procesador.guardar_resultados(df_combined, df_dashboard)
        
        print(f"\n✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print(f"   Total empresas procesadas: {len(df_combined):,}")
        print(f"   Empresas en vías principales: {len(df_vias):,}")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()