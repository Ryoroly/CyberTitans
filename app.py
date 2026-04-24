import streamlit as st
import time
from logica import twin # Importam instan?a geamanului digital

# Configurare pagina
st.set_page_config(page_title="Hala Inteligenta", layout="wide")

st.title("?? Monitorizare Hala - Digital Twin")
st.write(f"?? Conectat la Raspberry Pi 5")

# Definirea zonelor de afi?are
placeholder = st.empty()

while True:
    # Preluam datele actualizate de la senzori
    date = twin.obtine_stare_sistem()
    
    with placeholder.container():
        # Zona de Alerte
        if date['alerta']:
            st.error(date['alerta'])
        else:
            st.success(f"?? Predic?ie: {date['predictie']}")

        # R�ndul 1: Metrice principale
        col1, col2, col3 = st.columns(3)
        col1.metric("Temperatura", f"{date['temp']} �C")
        col2.metric("Umiditate", f"{date['umiditate']} %")
        col3.metric("Presiune", f"{date['presiune']} hPa")

        # R�ndul 2: Stare Hardware
        st.markdown("### ?? Control Echipamente")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Geam (Servo):** {'? Deschis' if date['geam_deschis'] else '? �nchis'}")
        c2.write(f"**�ncalzire (LED):** {'?? Pornit' if date['incalzire'] else '?? Oprit'}")
        c3.write(f"**Ventilator:** {date['ventilator_rpm']}%")

        # Simulare grafic istoric (op?ional)
        # st.line_chart(...) 

    time.sleep(2) # Refresh la fiecare 2 secunde