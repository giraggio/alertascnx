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

        if len(cols) == 4:
            try:
                url_doc = cols[3].find("button")["onclick"].split("'")[1]
            except:
                url_doc = ""

            fila = {
                "Fecha": cols[0].text.strip(),
                "Recursos": cols[1].text.strip(),
                "Estado": cols[2].text.strip(),
                "Documento": f"https://seia.sea.gob.cl{url_doc}"
            }
            filas.append(fila)

    return pd.DataFrame(filas)

def enviar_mail_outlook(nuevos_df):
    remitente = os.environ["OUTLOOK_USER"]
    password = os.environ["OUTLOOK_PASSWORD"]
    destinatarios = [email.strip() for email in os.environ["MAIL_DESTINO"].split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📄 Nuevos documentos en ficha de Recursos Administrativos"
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)

    cuerpo_html = "<h3>Se detectaron nuevos documentos:</h3><ul>"

    for _, fila in nuevos_df.iterrows():
        titulo = fila["Recursos"] or "(sin título)"
        fecha = fila["Fecha"] or "(sin fecha)"
        estado = fila["Estado"] or "(sin estado)"

        if fila["Documento"] == "documento_por_cargar":
            cuerpo_html += f"<li><b>{titulo}</b> – {fecha} – <i>Documento aún no disponible</i></li>"
        else:
            cuerpo_html += f"<li><b>{titulo}</b> – {fecha} – {estado} – <a href='{fila['Documento']}'>Abrir</a></li>"

    cuerpo_html += "</ul>"
    msg.attach(MIMEText(cuerpo_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatarios, msg.as_string())

# ----------------------------- EJECUCIÓN -----------------------------

url = "https://seia.sea.gob.cl/recursos/xhr_principal.php?modo=ficha&id_expediente=2160211381"
df_actual = scrapear_tabla_expediente(url)
print(f"🔍 Documentos encontrados: {df_actual.shape[0]}")

# Crear archivo si no existe
archivo_csv = "test_reclamos.csv"
if not os.path.exists(archivo_csv):
    print("📂 No se encontró archivo anterior. Creando archivo base vacío.")
    df_actual.iloc[:0].to_csv(archivo_csv, index=False)

df_anterior = pd.read_csv(archivo_csv)


# Detectar novedades
nuevos = df_actual[~df_actual["Documento"].isin(df_anterior["Documento"])]
if not nuevos.empty:
    print("⚠️ Nuevos documentos encontrados:")
    print(nuevos[["Recursos", "Fecha", "Documento"]])
    enviar_mail_outlook(nuevos)
else:
    print("✅ Sin cambios en la tabla.")

# Actualizar base
df_actual.to_csv(archivo_csv, index=False)

# cambio random


