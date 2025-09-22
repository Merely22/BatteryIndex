import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io

def process_txt_file(file_content, filename):
    """
    Procesa el contenido de un archivo .txt para extraer el primer y último mensaje GNBAT.
    """
    lines = file_content.decode("utf-8", errors="ignore").splitlines()
    gnbat_lines = [line for line in lines if "$GNBAT" in line]

    if not gnbat_lines:
        return None
    
    # Primer y último registro
    primer_gnbat = gnbat_lines[0]
    ultimo_gnbat = gnbat_lines[-1]

    # Regex para capturar hora, batería y voltaje
    pattern = r"(\d{2}:\d{2}:\d{2})\.\d+\s+\$GNBAT,(\d+),([\d\.]+)"

    match_inicio = re.search(pattern, primer_gnbat)
    match_fin = re.search(pattern, ultimo_gnbat)

    if match_inicio and match_fin:
        hora_inicio, bateria_in, voltaje_in = match_inicio.groups()
        hora_fin, bateria_fin, voltaje_fin = match_fin.groups()
        mac = filename[-8:-4]  # Extraer MAC del nombre del archivo

        # Extraer fecha del nombre del archivo (serial_YYYYMMDD_....)
        try:
            fecha_str = filename[7:15]
            fecha = datetime.strptime(fecha_str, "%Y%m%d").date()
        except ValueError:
            fecha = None

        return {
            "Fecha": fecha,
            "Hora Inicio": hora_inicio,
            "Hora Fin": hora_fin,
            "MAC": mac,
            "Bateria Inicial (%)": int(bateria_in),
            "Bateria Final (%)": int(bateria_fin),
            "Archivo": filename
        }
    return None

st.set_page_config(page_title="Indicador de Batería", layout="wide")

st.title("🔋 Indicador de Batería")
st.markdown("Sube tus archivos `.txt` para extraer niveles de batería y voltaje al inicio y al final de la grabación.")

uploaded_files = st.file_uploader(
    "Sube tus archivos de texto aquí",
    type="txt",
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 {len(uploaded_files)} archivo(s) seleccionados.")
    data_records = []

    with st.spinner("Procesando archivos..."):
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_content = uploaded_file.read()
            
            result = process_txt_file(file_content, file_name)
            
            if result:
                data_records.append(result)
            else:
                st.warning(f"⚠️ No se pudo extraer datos GNBAT de: {file_name}")

    if data_records:
        df = pd.DataFrame(data_records)
        df_sorted = df.sort_values(by="Fecha", ascending=False)

        st.subheader("Resumen de Datos de Batería")
        st.dataframe(df_sorted)

        # Gráfico comparativo de baterías
        st.subheader("Comparación de Batería Inicial y Final")
        st.line_chart(df_sorted.set_index("MAC")[["Bateria Inicial (%)", "Bateria Final (%)"]], color=["#FF0000", "#0000FF"],)
        
        # Descargar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_sorted.to_excel(writer, index=False, sheet_name='BatteryLevel')
        output.seek(0)

        st.download_button(
            label="Descargar Datos a Excel",
            data=output.getvalue(),
            file_name="battery_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ No se encontraron datos GNBAT válidos en los archivos subidos.")

st.markdown("---")
