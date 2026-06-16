"""
SCRIPT DE CONVERSIÓN: Excel → Parquet
======================================
Ejecuta este script en tu PC cada vez que actualices los archivos Excel.
Requiere: pip install pandas openpyxl pyarrow

Uso:
    python convertir_a_parquet.py

Los archivos .parquet se generan en la misma carpeta que los Excel.
Luego súbelos a GitHub junto con el código normalmente.
"""

import pandas as pd
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────────────────
ARCHIVOS = {
    "metaR.xlsx": "metaR.parquet",
    "cruces.xlsx": "cruces.parquet",
}

def convertir(excel_path: Path, parquet_path: Path):
    print(f"Leyendo  {excel_path.name} ...")
    df = pd.read_excel(excel_path)

    # Conversiones de tipo según el archivo
    if excel_path.name == "metaR.xlsx":
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y.%m.%d', errors='coerce')
        df['Top1']  = pd.to_numeric(df['Top1'],  errors='coerce')
        df['Top3']  = pd.to_numeric(df['Top3'],  errors='coerce')

    elif excel_path.name == "cruces.xlsx":
        df['fecha'] = pd.to_datetime(df['fecha'], format='%Y.%m.%d', errors='coerce')

    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"  ✓ Guardado {parquet_path.name}  ({len(df)} filas, {parquet_path.stat().st_size // 1024} KB)")

# ── Ejecución ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base = Path(__file__).parent          # misma carpeta que este script
    errores = []

    for excel_nombre, parquet_nombre in ARCHIVOS.items():
        excel_path   = base / excel_nombre
        parquet_path = base / parquet_nombre

        if not excel_path.exists():
            print(f"  ✗ No encontrado: {excel_path}  (¿está en la misma carpeta?)")
            errores.append(excel_nombre)
            continue

        try:
            convertir(excel_path, parquet_path)
        except Exception as e:
            print(f"  ✗ Error al convertir {excel_nombre}: {e}")
            errores.append(excel_nombre)

    print()
    if errores:
        print(f"Terminado con errores en: {', '.join(errores)}")
    else:
        print("¡Listo! Sube los .parquet a GitHub y la app los leerá automáticamente.")
