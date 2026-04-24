import time
import threading
import board
import adafruit_dht
import adafruit_bmp280
import adafruit_mpu6050
from gpiozero import DigitalInputDevice, PWMOutputDevice, Servo, LED

# ==========================================
# SETARI DE CONFIGURARE MANUALA
# ==========================================
ACTIVARE_SENZOR_GAZ = 0      # 1 = Activ, 0 = Ignorat (bun daca il folosesti ca senzor de alcool)
TEMPERATURA_TINTA = 26.0     # Temperatura la care vrei sa ajunga hala
TOLERANTA_TEMP = 1.0         # +/- cate grade incep sa porneasca sistemele

class DigitalTwinHala:
    def __init__(self):
        print("Initializare Creier Digital Twin...")

        self.temp = TEMPERATURA_TINTA
        self.umiditate = 50.0
        self.presiune = 1013.25
        self.calitate_aer_slaba = False 
        self.vibratii = 0.0
        
        self.mesaj_predictie = "Sistem in calibrare..."
        self.alerta = "Niciuna"
        
        # Stari echipamente
        self.geam_deschis = False  
        self.incalzire_activa = False
        self.putere_ventilator = 0.0
        self.culoare_led_rgb = "ALBASTRU" # Placeholder pentru viitorul LED RGB

        self._init_hardware()
        self._verificare_sisteme()

    def _init_hardware(self):
        try: 
            self.dht = adafruit_dht.DHT22(board.D4)
        except Exception as e: 
            print(f"Avertisment DHT22: {e}")
            self.dht = None

        try:
            self.i2c = board.I2C()
            self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c, address=0x76)
            self.mpu = adafruit_mpu6050.MPU6050(self.i2c)
        except Exception as e: 
            print(f"Avertisment I2C (BMP/MPU): {e}")
            self.bmp = self.mpu = None

        try: 
            self.mq135 = DigitalInputDevice(17)
        except Exception as e: 
            print(f"Avertisment MQ-135: {e}")
            self.mq135 = None

        try:
            self.ventilator = PWMOutputDevice(13)
            self.geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.incalzire_rezistente = LED(27) 
            
            # --- ADAUGAT PENTRU LED RGB ---
            # Pin fizic 36 = GPIO 16 (Rosu), Pin fizic 38 = GPIO 20 (Albastru)
            self.led_rosu = LED(16)
            self.led_albastru = LED(20)
            # ------------------------------

            # Stare initiala hardware
            self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None
            self.ventilator.value = 0
            self.incalzire_rezistente.off()
            
            # LED-ul incepe pe albastru (aer curat/normal)
            self.led_rosu.off()
            self.led_albastru.on()
            
        except Exception as e:
            print(f"Eroare Initializare Actuatori: {e}")
            self.ventilator = self.geam_servo = self.incalzire_rezistente = None
            self.led_rosu = self.led_albastru = None

    def _verificare_sisteme(self):
        # Cerinta din Word: Sa verifice la inceput daca merge incalzirea si racirea
        print("Rulare auto-test echipamente (incalzire, servo, ventilator)...")
        if self.incalzire_rezistente: self.incalzire_rezistente.on()
        if self.ventilator: self.ventilator.value = 0.5
        if self.geam_servo: self.geam_servo.max()
        time.sleep(1)
        if self.incalzire_rezistente: self.incalzire_rezistente.off()
        if self.ventilator: self.ventilator.value = 0
        if self.geam_servo: 
            self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None
        print("Auto-test completizat. Sistem gata.")

    def citeste_senzori(self):
        if self.dht:
            try:
                t = self.dht.temperature
                h = self.dht.humidity
                if t is not None: self.temp = round(t, 1)
                if h is not None: self.umiditate = round(h, 1)
            except RuntimeError: pass 

        if self.bmp:
            try: self.presiune = round(self.bmp.pressure, 1)
            except Exception: pass

        if self.mpu:
            try:
                x, y, z = self.mpu.acceleration
                self.vibratii = round(abs(x) + abs(y) + abs(z - 9.8), 2)
            except Exception: pass

        if ACTIVARE_SENZOR_GAZ == 1 and self.mq135:
            self.calitate_aer_slaba = self.mq135.value
        else:
            self.calitate_aer_slaba = False 

    def proceseaza_logica(self):
        # Variabile temporare pentru starea decisa la acest ciclu
        actiune_geam = False
        actiune_incalzire = False
        actiune_ventilator = 0.0
        culoare_rgb_viitor = "ALBASTRU" # Default aer rece/normal
        mesaj = "Parametri in limite optime."
        
        # Calculam diferenta pentru a vedea daca afisam timpul de rezolvare
        diferenta_temp = abs(self.temp - TEMPERATURA_TINTA)
        afiseaza_timp = (diferenta_temp >= 5.0)

        # 1. Verificam intai calitatea aerului (Prioritate maxima)
        if self.calitate_aer_slaba:
            self.alerta = "ALERTA: Calitate aer scazuta!"
            actiune_geam = True       # Se deschide servo
            actiune_incalzire = False # Fara incalzire cand evacuezi aerul
            actiune_ventilator = 1.0  # Ventilator la maxim
            culoare_rgb_viitor = "ALBASTRU"
            mesaj = "Evacuare aer viciat (25 secunde estimat)."
               
        else:
            self.alerta = "Niciuna"
            # 2. Scenariul de RACIRE (Temp creste)
            if self.temp > TEMPERATURA_TINTA + TOLERANTA_TEMP:
                actiune_geam = True        # Servo deschis pentru racire
                actiune_incalzire = False  # Oprim rezistentele
                actiune_ventilator = 1.0   # Pornim ventilatorul
                culoare_rgb_viitor = "ALBASTRU"
                
                if afiseaza_timp:
                    mesaj = f"Racire activa. Se raceste in 20 secunde."
                else:
                    mesaj = "Racire usoara activa."
                    
            # 3. Scenariul de INCALZIRE (Temp scade)
            elif self.temp < TEMPERATURA_TINTA - TOLERANTA_TEMP:
                actiune_geam = False       # Servo RAMANE INCHIS
                actiune_incalzire = True   # Pornim rezistentele la intrare
                actiune_ventilator = 1.0   # Pornim ventilatorul pentru a baga caldura
                culoare_rgb_viitor = "ROSU"
                
                if afiseaza_timp:
                    mesaj = f"Incalzire activa. Se incalzeste in 30 secunde."
                else:
                    mesaj = "Incalzire usoara activa."
            
            # 4. Scenariul de STABILITATE
            else:
                actiune_geam = False
                actiune_incalzire = False
                actiune_ventilator = 0.0
                culoare_rgb_viitor = "ALBASTRU"
                mesaj = f"Sistem stabilizat la tinta de {TEMPERATURA_TINTA} grade."

        # VERIFICARE VIBRATII VENTILATOR (MPU6050)
        if self.vibratii > 5.0 and actiune_ventilator > 0:
            actiune_ventilator = 0.5 # Scade turatiile pentru lifespan 
            mesaj += " [Limitare turatie activata din cauza vibratiilor]"

        # APLICAM STARILE PE HARDWARE
        # Geam (Servo)
        if self.geam_servo and actiune_geam != self.geam_deschis:
            if actiune_geam: self.geam_servo.max()
            else: self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None 
            self.geam_deschis = actiune_geam
             
        # Incalzire (LED/Releu)
        if self.incalzire_rezistente and actiune_incalzire != self.incalzire_activa:
            if actiune_incalzire: self.incalzire_rezistente.on()
            else: self.incalzire_rezistente.off()
            self.incalzire_activa = actiune_incalzire

        # Ventilator
        if self.ventilator:
            self.ventilator.value = actiune_ventilator
            
        # --- NOU: LOGICA LED RGB ---
        if culoare_rgb_viitor == "ROSU":
            if self.led_albastru: self.led_albastru.off()
            if self.led_rosu: self.led_rosu.on()
        else: # Daca e ALBASTRU
            if self.led_rosu: self.led_rosu.off()
            if self.led_albastru: self.led_albastru.on()
        # -----------------------------

        self.putere_ventilator = actiune_ventilator
        self.mesaj_predictie = mesaj
        self.culoare_led_rgb = culoare_rgb_viitor

    def obtine_stare_sistem(self):
        return {
            "temp": self.temp,
            "umiditate": self.umiditate,
            "presiune": self.presiune,
            "vibratii": self.vibratii,
            "aer_viciat": self.calitate_aer_slaba,
            "geam_deschis": self.geam_deschis,
            "incalzire": self.incalzire_activa,
            "ventilator_rpm": int(self.putere_ventilator * 100),
            "predictie": self.mesaj_predictie,
            "alerta": self.alerta,
            "led_rgb": self.culoare_led_rgb
        }

# ==========================================
# BUCLA PRINCIPALA (TERMINAL)
# ==========================================
if __name__ == "__main__":
    twin = DigitalTwinHala()
    print("\nMonitorizare live inceputa. Apasa Ctrl+C pentru oprire.\n")
    time.sleep(2)

    try:
        while True:
            twin.citeste_senzori()
            twin.proceseaza_logica()
            
            date = twin.obtine_stare_sistem()
            
            status_geam = "DESCHIS" if date['geam_deschis'] else "INCHIS"
            status_inc = "PORNITA" if date['incalzire'] else "OPRITA"
            status_aer = "SLABA (GAZ/ALCOOL)" if date['aer_viciat'] else "CURAT"

            print(f"Temperatura: {date['temp']} C (Tinta: {TEMPERATURA_TINTA} C) | Umiditate: {date['umiditate']}% | Presiune: {date['presiune']} hPa | Vibratii: {date['vibratii']}")
            print(f"Sistem: Ventilator {date['ventilator_rpm']}% | Geam: {status_geam} | Incalzire: {status_inc} | Aer: {status_aer} | LED RGB intrare: {date['led_rgb']}")
            
            if date['alerta'] != "Niciuna":
                print(f"!!! {date['alerta']} !!!")
                
            print(f"Status: {date['predictie']}")
            print("-" * 70)
            
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\nOprire ceruta de utilizator. Oprim echipamentele in siguranta...")
        
        if twin.ventilator: twin.ventilator.value = 0
        if twin.geam_servo:
            twin.geam_servo.min()
            time.sleep(0.5)
            twin.geam_servo.detach()
        if twin.incalzire_rezistente: twin.incalzire_rezistente.off()
        
        # Oprim si LED-urile
        if twin.led_rosu: twin.led_rosu.off()
        if twin.led_albastru: twin.led_albastru.off()
        
        print("Sistem oprit cu succes.")


