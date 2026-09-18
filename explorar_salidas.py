import os

path_salidas = r'\\snfserver2\EscaneosBkp\DESPACHO SALIDAS JUDICIALES'
print(f"Examinando: {path_salidas}")

for item in os.listdir(path_salidas):
    full = os.path.join(path_salidas, item)
    if os.path.isdir(full):
        try:
            subitems = os.listdir(full)
            pdfs = [x for x in subitems if x.lower().endswith('.pdf')]
            print(f"\n[CARPETA] {item} -> Total archivos: {len(subitems)}, PDFs: {len(pdfs)}")
            print("  Ejemplos de PDFs:")
            for p in pdfs[:5]:
                print(f"    - {p}")
        except Exception as e:
            print(f"  Error leyendo {item}: {e}")
    else:
        print(f"\n[ARCHIVO] {item}")
