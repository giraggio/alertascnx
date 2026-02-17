import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def scrapear_tabla_expediente(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "html.parser")

    filas = []
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")

        # Caso completo (8 columnas)
        if len(cols) == 8:
            try:
                url_doc = cols[7].find("button")["onclick"].split("'")[1]
            except Exception:
                url_doc = ""

            fila = {
                "n_fila": cols[0].get_text(strip=True),
                "oficio": cols[1].get_text(strip=True),
                "identificador": cols[2].get_text(strip=True),
                "titulo": cols[3].get_text(strip=True),
                "emisor": cols[4].get_text(strip=True),
                "receptor": cols[5].get_text(strip=True),
                "fecha": cols[6].get_text(strip=True),
                "url_documento": url_doc
            }
            filas.append(fila)

        # Caso incompleto con "Documento por cargar"
        elif any("documento por cargar" in col.get_text(strip=True).lower() for col in cols):
            texto = " ".join(col.get_text(strip=True) for col in cols)
            fila = {
                "n_fila": "",
                "oficio": "",
                "identificador": "",
                "titulo": texto,
                "emisor": "",
                "receptor": "",
                "fecha": "",
                "url_documento": "documento_por_cargar"
            }
            filas.append(fila)

    return pd.DataFrame(filas)

def enviar_mail_outlook(nuevos_df):
    remitente = os.environ["OUTLOOK_USER"]
    password = os.environ["OUTLOOK_PASSWORD"]
    destinatarios = [email.strip() for email in os.environ["MAIL_DESTINO"].split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📄 Nuevos documentos en expediente SEIA"
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)

    cuerpo_html = "<h3>Se detectaron nuevos documentos:</h3><ul>"

    for _, fila in nuevos_df.iterrows():
        titulo = fila["titulo"] or "(sin título)"
        fecha = fila["fecha"] or "(sin fecha)"

        if fila["url_documento"] == "documento_por_cargar":
            cuerpo_html += f"<li><b>{titulo}</b> – {fecha} – <i>Documento aún no disponible</i></li>"
        else:
            cuerpo_html += f"<li><b>{titulo}</b> – {fecha} – <a href='{fila['url_documento']}'>Abrir</a></li>"

    cuerpo_html += "</ul>"
    msg.attach(MIMEText(cuerpo_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatarios, msg.as_string())

# ----------------------------- EJECUCIÓN -----------------------------

url = "https://seia.sea.gob.cl/expediente/xhr_expediente2.php?id_expediente=2165803565"
df_actual = scrapear_tabla_expediente(url)
print(f"🔍 Documentos encontrados: {df_actual.shape[0]}")

# Crear archivo si no existe
archivo_csv = "ultimo_expediente_tovaku.csv"
if not os.path.exists(archivo_csv):
    print("📂 No se encontró archivo anterior. Creando archivo base vacío.")
    df_actual.iloc[:0].to_csv(archivo_csv, index=False)

df_anterior = pd.read_csv(archivo_csv)

df_actual["clave_unica"] = df_actual["identificador"] + "|" + df_actual["url_documento"].fillna("")
df_anterior["clave_unica"] = df_anterior["identificador"] + "|" + df_anterior["url_documento"].fillna("")

# Detectar novedades
nuevos = df_actual[~df_actual["clave_unica"].isin(df_anterior["clave_unica"])]

if not nuevos.empty:
    print("⚠️ Nuevos documentos encontrados:")
    print(nuevos[["titulo", "fecha", "url_documento"]])
    enviar_mail_outlook(nuevos)
else:
    print("✅ Sin cambios en la tabla.")

# Actualizar base
df_actual.to_csv(archivo_csv, index=False)

# cambio random




