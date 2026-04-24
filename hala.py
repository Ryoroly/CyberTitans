import time
import board
import adafruit_dht
import adafruit_bmp280
import adafruit_mpu6050
from gpiozero import DigitalInputDevice, PWMOutputDevice, Servo, LED

# ==========================================
# ?? SETARI DE CONFIGURARE MANUALA
# ==========================================
# 1 = Senzorul MQ-135 este citit ?i influen?eaza logica
# 0 = Senzorul MQ-135 este ignorat (consideram aer curat permanent)
ACTIVARE_SENZOR_GAZ = 1  

class DigitalTwinHala:
    def __init__(self):
        print("?? Ini?ializare Creier Digital Twin (Mod Terminal)...")

        self.temp = 22.0
        self.umiditate = 50.0
        self.presiune = 1013.25
        self.calitate_aer = False 
        self.vibratii = 0.0
        
        self.mesaj_predictie = "Sistem �n calibrare..."
        self.alerta_critica = None
        self.geam_deschis = False  
        self.incalzire_activa = False
        self.putere_ventilator = 0.0

        self._init_hardware()

    def _init_hardware(self):
        try: self.dht = adafruit_dht.DHT22(board.D4)
        except Exception as e: 
            print(f"?? Eroare DHT22: {e}")
            self.dht = None

        try:
            self.i2c = board.I2C()
            self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c, address=0x76)
            self.mpu = adafruit_mpu6050.MPU6050(self.i2c)
        except Exception as e: 
            print(f"?? Eroare I2C (BMP/MPU): {e}")
            self.bmp = self.mpu = None

        try: self.mq135 = DigitalInputDevice(17)
        except Exception as e: 
            print(f"?? Eroare MQ-135: {e}")
            self.mq135 = None

        try:
            self.ventilator = PWMOutputDevice(13)
            self.geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.incalzire_led = LED(27) 
            
            self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None
            self.ventilator.value = 0
            self.incalzire_led.off()
        except Exception as e:
            print(f"?? Eroare Ini?ializare Actuatori: {e}")

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
            self.calitate_aer = self.mq135.value
        else:
            self.calitate_aer = False 

    def proceseaza_logica(self):
        t_geam = False
        t_incalzire = False
        t_ventilator = 0.0
        predictie = "Sistem stabil."

        if self.calitate_aer:
            self.alerta_critica = "?? ALERTA: Aer Viciat Detectat!"
            t_geam = True
            t_incalzire = False
            t_ventilator = 1.0 
            predictie = "Evacuare gaze. Aerul se cura?a �n 25 sec."
        else:
            self.alerta_critica = None
            if self.temp > 28.0:
                t_geam = True
                t_incalzire = False
                t_ventilator = 1.0
                predictie = "Racire activa. Timp estimat: 20 sec."
            elif self.temp < 18.0:
                t_geam = False
                t_incalzire = True
                t_ventilator = 1.0
                predictie = "�ncalzire activa. Timp estimat: 30 sec."
            else:
                t_geam = False
                t_incalzire = False
                t_ventilator = 0.0

        if self.vibratii > 5.0 and t_ventilator > 0:
            t_ventilator = 0.5 
            predictie += " (Tura?ie redusa automat vs Uzura)"

        if t_geam != self.geam_deschis:
            if t_geam: self.geam_servo.max()
            else: self.geam_servo.min()
            time.sleep(0.5)
            self.geam_servo.value = None 
            self.geam_deschis = t_geam
             
        if t_incalzire != self.incalzire_activa:
            if t_incalzire: self.incalzire_led.on()
            else: self.incalzire_led.off()
            self.incalzire_activa = t_incalzire

        self.ventilator.value = t_ventilator
        self.putere_ventilator = t_ventilator
        self.mesaj_predictie = predictie

    def obtine_stare_sistem(self):
        return {
            "temp": self.temp,
            "umiditate": self.umiditate,
            "presiune": self.presiune,
            "vibratii": self.vibratii,
            "aer_viciat": self.calitate_aer,
            "geam_deschis": self.geam_deschis,
            "incalzire": self.incalzire_activa,
            "ventilator_rpm": int(self.putere_ventilator * 100),
            "predictie": self.mesaj_predictie,
            "alerta": self.alerta_critica
        }

# ==========================================
# BUCLA PRINCIPALA (TERMINAL)
# ==========================================
if __name__ == "__main__":
    twin = DigitalTwinHala()
    print("\n?? Sistem pornit. Citim datele live... (Apasa Ctrl+C pentru oprire)\n")
    time.sleep(2)

    try:
        while True:
            # 1. Citim ?i procesam
            twin.citeste_senzori()
            twin.proceseaza_logica()
            
            # 2. Extragem datele
            date = twin.obtine_stare_sistem()
            
            # 3. Formatam mesajele pentru consola
            status_geam = "DESCHIS" if date['geam_deschis'] else "�NCHIS"
            status_inc = "PORNITA" if date['incalzire'] else "OPRITA"
            status_aer = "?? VICIAT" if date['aer_viciat'] else "? CURAT"

            # 4. Printam pe ecran
            print(f"???  Temp: {date['temp']}�C | ?? Umid: {date['umiditate']}% | ?? Presiune: {date['presiune']} hPa | ?? Vibra?ii: {date['vibratii']}")
            print(f"??  Hardware: Vent {date['ventilator_rpm']}% | Geam {status_geam} | �ncalzire {status_inc} | Aer {status_aer}")
            
            if date['alerta']:
                print(f"??  {date['alerta']}")
                
            print(f"??  {date['predictie']}")
            print("-" * 65)
            
            # O mica pauza ca sa nu inundam ecranul
            time.sleep(1.5)

    except KeyboardInterrupt:
        # Codul de aici ruleaza DOAR c�nd ape?i Ctrl+C
        print("\n?? Oprire for?ata de utilizator. Securizare actuatori...")
        
        # Oprim ventilatorul
        twin.ventilator.value = 0
        # �nchidem geamul ?i taiem semnalul
        twin.geam_servo.min()
        time.sleep(0.5)
        twin.geam_servo.detach()
        # Oprim �ncalzirea
        twin.incalzire_led.off()
        
        print("?? Hardware oprit �n siguran?a. O zi buna!")

