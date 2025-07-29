import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrapear_tabla_expediente(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "html.parser")

    filas = []
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 8:
            fila = {
                "n_fila": cols[0].get_text(strip=True),
                "oficio": cols[1].get_text(strip=True),
                "identificador": cols[2].get_text(strip=True),
                "titulo": cols[3].get_text(strip=True),
                "emisor": cols[4].get_text(strip=True),
                "receptor": cols[5].get_text(strip=True),
                "fecha": cols[6].get_text(strip=True),
                "url_documento": cols[7].find("button")["onclick"].split("'")[1]
            }
            filas.append(fila)
    return pd.DataFrame(filas)

url = "https://seia.sea.gob.cl/expediente/xhr_expediente2.php?id_expediente=2160211381"
df_actual = scrapear_tabla_expediente(url)
df_actual = df_actual[:312]  # forzar alerta en testeo

# Si no existe archivo anterior, crear uno vacío
archivo_csv = "ultimo_expediente.csv"
if not os.path.exists(archivo_csv):
    df_actual.iloc[:0].to_csv(archivo_csv, index=False)

df_anterior = pd.read_csv(archivo_csv)

# Comparar
nuevos = df_actual[~df_actual["url_documento"].isin(df_anterior["url_documento"])]

if not nuevos.empty:
    print("⚠️ Nuevos documentos encontrados:")
    print(nuevos[["identificador", "titulo", "fecha", "url_documento"]])
else:
    print("✅ Sin cambios en la tabla.")

# Guardar nuevo estado
df_actual.to_csv(archivo_csv, index=False)
