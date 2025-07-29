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

def enviar_mail_outlook(nuevos_df):
    remitente = os.environ["OUTLOOK_USER"]
    password = os.environ["OUTLOOK_PASSWORD"]
    destinatarios = [email.strip() for email in os.environ["MAIL_DESTINO"].split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📄 Nuevos documentos en expediente SEIA"
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)  # para mostrar todos en el encabezado

    cuerpo_html = "<h3>Se detectaron nuevos documentos:</h3><ul>"
    for _, fila in nuevos_df.iterrows():
        cuerpo_html += f"<li><b>{fila['titulo']}</b> – {fila['fecha']} – <a href='{fila['url_documento']}'>Abrir</a></li>"
    cuerpo_html += "</ul>"

    msg.attach(MIMEText(cuerpo_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatarios, msg.as_string())


url = "https://seia.sea.gob.cl/expediente/xhr_expediente2.php?id_expediente=2160211381"
df_actual = scrapear_tabla_expediente(url)

print(df_actual.shape)
# Si no existe archivo anterior, crear uno vacío
archivo_csv = "ultimo_expediente.csv"
if not os.path.exists(archivo_csv):
    print("No se encuentra archivo")
    df_actual.iloc[:0].to_csv(archivo_csv, index=False)
    

df_anterior = pd.read_csv(archivo_csv)
# df_anterior = df_anterior[:300]
# Comparar
nuevos = df_actual[~df_actual["url_documento"].isin(df_anterior["url_documento"])]

if not nuevos.empty:
    print("⚠️ Nuevos documentos encontrados:")
    print(nuevos[["identificador", "titulo", "fecha", "url_documento"]])
    enviar_mail_outlook(nuevos)
else:
    print("✅ Sin cambios en la tabla.")

# Guardar nuevo estado
df_actual.to_csv(archivo_csv, index=False)
