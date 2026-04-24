import time
import threading
import board
import adafruit_dht
import adafruit_bmp280
import adafruit_mpu6050
from gpiozero import DigitalInputDevice, PWMOutputDevice, Servo, LED

class DigitalTwinHala:
    def __init__(self):
        print("?? Ini?ializare Creier Digital Twin...")

        # --- 1. DATELE SENZORILOR (Input) ---
        self.temp = None # Pornim cu None ca sa ?tim c�nd senzorul a citit prima data cu succes
        self.temp_referinta = None # Aici vom salva temperatura ini?iala (pentru a vedea daca a crescut cu 3 grade)
        self.umiditate = 0.0
        self.presiune = 0.0
        self.calitate_aer = False  
        self.vibratii = 0.0
        
        # --- 2. STAREA SISTEMULUI ?I PREDIC?II (Geamanul Digital) ---
        self.mod_simulare = False
        self.mesaj_predictie = "Sistem ini?ializat. Se a?teapta date."
        self.alerta_critica = None
        
        self.geam_deschis = False  
        self.incalzire_activa = False
        self.putere_ventilator = 0.0
        
        # Variabila pentru a ne asigura ca servomotorul se �nv�rte de 3 ori DOAR O DATA pe eveniment
        self.alarma_temperatura_declansata = False 

        # --- 3. CONECTARE HARDWARE ---
        self._init_hardware()

    def _init_hardware(self):
        try: self.dht = adafruit_dht.DHT22(board.D4)
        except: self.dht = None

        try:
            self.i2c = board.I2C()
            self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c, address=0x76)
            self.mpu = adafruit_mpu6050.MPU6050(self.i2c)
        except: 
            self.bmp, self.mpu = None, None

        try: self.mq135 = DigitalInputDevice(17)
        except: self.mq135 = None

        # Actuatori
        try:
            self.ventilator = PWMOutputDevice(13)
            self.geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.incalzire_led = LED(27)

            # Stare ini?iala de siguran?a
            self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None 
            self.ventilator.value = 0
            self.incalzire_led.off()
        except Exception as e:
            print(f"?? Eroare ini?ializare actuatori (Pinii ar putea fi ocupa?i): {e}")
            self.geam_servo, self.ventilator, self.incalzire_led = None, None, None

    def citeste_senzori(self):
        if self.mod_simulare:
            return

        if self.dht:
            try: 
                t = self.dht.temperature
                h = self.dht.humidity
                
                if t is not None: 
                    self.temp = t
                    # Daca e prima citire, o setam ca referin?a
                    if self.temp_referinta is None:
                        self.temp_referinta = t
                        print(f"? Temperatura de referin?a a fost setata la: {self.temp_referinta}�C")
                        
                if h is not None: 
                    self.umiditate = h
            except RuntimeError as e: 
                print(f"? Senzor DHT eroare de citire (normal): {e}")

        if self.bmp:
            try: self.presiune = self.bmp.pressure
            except Exception: pass

        if self.mpu:
            try:
                x, y, z = self.mpu.acceleration
                self.vibratii = abs(x) + abs(y) + abs(z - 9.8) 
            except Exception: pass

        if self.mq135:
            self.calitate_aer = self.mq135.value

    def proceseaza_logica(self):
        # A?teptam p�na avem o temperatura reala valida de la senzor
        if self.temp is None or self.temp_referinta is None:
            return

        # --- LOGICA NOUA: Cre?terea cu 3 grade ---
        if self.temp >= self.temp_referinta + 3.0:
            self.alerta_critica = "?? CRITIC: Temperatura a crescut cu peste 3 grade!"
            self.mesaj_predictie = "Racire de urgen?a activata!"
            
            # Verificam daca nu a mai fost declan?ata deja (ca sa nu se �nv�rta la infinit)
            if not self.alarma_temperatura_declansata:
                print("?? Se executa rotirea de 3 ori a servomotorului (0 -> 180)...")
                if self.geam_servo:
                    for _ in range(3):
                        self.geam_servo.max()  # 180 grade
                        time.sleep(1)
                        self.geam_servo.min()  # 0 grade
                        time.sleep(1)
                    self.geam_servo.value = None # Scoatem curentul din motor sa nu bazaie
                    
                self.alarma_temperatura_declansata = True
                self.geam_deschis = True
        else:
            self.alerta_critica = None
            self.mesaj_predictie = "Parametri optimi. Monitorizare activa."
            self.geam_deschis = False
            
            # Resetam alarma daca temperatura scade �napoi aproape de normal
            if self.temp <= self.temp_referinta + 1.0:
                self.alarma_temperatura_declansata = False

    def obtine_stare_sistem(self):
        return {
            "temp": round(self.temp, 1) if self.temp else 0.0,
            "umiditate": round(self.umiditate, 1) if self.umiditate else 0.0,
            "presiune": round(self.presiune, 1) if self.presiune else 0.0,
            "vibratii": round(self.vibratii, 2),
            "aer_viciat": self.calitate_aer,
            "geam_deschis": self.geam_deschis,
            "incalzire": self.incalzire_activa,
            "ventilator_rpm": int(self.putere_ventilator * 100),
            "predictie": self.mesaj_predictie,
            "alerta": self.alerta_critica,
            "mod_simulare": self.mod_simulare
        }

twin = DigitalTwinHala()

def ruleaza_geamanul_in_fundal():
    while True:
        twin.citeste_senzori()
        twin.proceseaza_logica()
        time.sleep(1)

thread_twin = threading.Thread(target=ruleaza_geamanul_in_fundal, daemon=True)
thread_twin.start()

# --- ZONA DE TESTARE LOCALA ---
if __name__ == "__main__":
    print("\n?? Mod de testare senzorilor activat. Apasa CTRL+C pentru a opri.")
    try:
        while True:
            date_curente = twin.obtine_stare_sistem()
            print(f"??? Temp: {date_curente['temp']}�C | ?? Umiditate: {date_curente['umiditate']}% | ?? Alerta Aer: {date_curente['aer_viciat']}")
            print("-" * 50) 
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n?? Testare oprita manual.")

