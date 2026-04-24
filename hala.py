import time
import threading
import board
import math
import adafruit_dht
import adafruit_bmp280
import adafruit_mpu6050
from gpiozero import DigitalInputDevice, PWMOutputDevice, Servo, LED, Button

# ==========================================
# SETARI DE CONFIGURARE INITIALE
# ==========================================
ACTIVARE_SENZOR_GAZ = 0      
TEMPERATURA_TINTA_INITIALA = 26.0     
TOLERANTA_TEMP = 1.0         

class DigitalTwinHala:
    def __init__(self):
        print("Initializare Creier Digital Twin...")

        # Date Senzori
        self.temp = TEMPERATURA_TINTA_INITIALA
        self.temperatura_tinta = TEMPERATURA_TINTA_INITIALA # NOU: Tinta controlabila
        self.umiditate = 50.0
        self.presiune = 1013.25
        self.calitate_aer_slaba = False 
        self.vibratii = 0.0
        
        # Stari Sistem
        self.mesaj_predictie = "Sistem in pornire..."
        self.alerta = "Niciuna"
        self.geam_deschis = False  
        self.incalzire_activa = False
        self.culoare_led = "ALBASTRU"
        self.alerta_vibratii = False
        
        # PWM Fluid 
        self.target_ventilator = 0.0
        self.putere_curenta_ventilator = 0.0
        
        # Mod Manual Web
        self.mod_auto = True         
        self.manual_vent = 0.0       
        self.manual_geam = False     
        self.manual_inc = False      
        
        # Override Vechi (pentru terminal)
        self.override_temp = None
        self.override_servo = None
        self.override_timp_expirare = 0.0
        
        # Buton Fizic
        self.mod_aer_combinat = False

        self._init_hardware()
        threading.Thread(target=self._worker_pwm_fluid, daemon=True).start()
        self._verificare_sisteme()

    def _init_hardware(self):
        try: self.dht = adafruit_dht.DHT22(board.D4)
        except: self.dht = None

        try:
            self.i2c = board.I2C()
            self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c, address=0x76)
            self.mpu = adafruit_mpu6050.MPU6050(self.i2c)
        except: self.bmp = self.mpu = None

        try: self.mq135 = DigitalInputDevice(17)
        except: self.mq135 = None

        try:
            self.ventilator = PWMOutputDevice(13)
            self.geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.incalzire_rezistente = LED(27) 
            
            self.led_rosu = LED(5)      
            self.led_albastru = LED(20) 
            self.led_galben = LED(6)    
            
            self.buton_fizic = Button(26, pull_up=True, bounce_time=0.2)
            self.buton_fizic.when_pressed = self.toggle_buton_fizic

            self.geam_servo.max()
            time.sleep(0.5)
            self.geam_servo.value = None 
            self.geam_deschis = False
            
            self.ventilator.value = 0
            self.incalzire_rezistente.off()
            
            self.led_rosu.off()
            self.led_albastru.on()
            self.led_galben.off()
        except Exception as e:
            print(f"Eroare Hardware: {e}")

    def _worker_pwm_fluid(self):
        pas_crestere = 0.05   
        pas_scadere = 0.015   
        while True:
            if self.ventilator:
                if self.putere_curenta_ventilator < self.target_ventilator:
                    self.putere_curenta_ventilator += pas_crestere
                    if self.putere_curenta_ventilator > self.target_ventilator:
                        self.putere_curenta_ventilator = self.target_ventilator
                elif self.putere_curenta_ventilator > self.target_ventilator:
                    self.putere_curenta_ventilator -= pas_scadere
                    if self.putere_curenta_ventilator < self.target_ventilator:
                        self.putere_curenta_ventilator = self.target_ventilator
                try:
                    val_sigura = max(0.0, min(1.0, self.putere_curenta_ventilator))
                    self.ventilator.value = val_sigura
                except: pass
            time.sleep(0.1)

    def toggle_buton_fizic(self):
        self.mod_aer_combinat = not self.mod_aer_combinat
        stare_str = "ACTIVAT" if self.mod_aer_combinat else "DEZACTIVAT"
        print(f"\n[!] Buton fizic apasat: Mod Aer Combinat {stare_str} [!]\n")

    def _verificare_sisteme(self):
        print("Auto-test: Verificare hardware in curs...")
        if self.incalzire_rezistente: self.incalzire_rezistente.on()
        if self.led_rosu: self.led_rosu.on()
        if self.led_galben: self.led_galben.on()
        self.target_ventilator = 0.5
        time.sleep(1.5)
        if self.incalzire_rezistente: self.incalzire_rezistente.off()
        if self.led_rosu: self.led_rosu.off()
        if self.led_galben: self.led_galben.off()
        self.target_ventilator = 0.0
        print("Auto-test finalizat.")

    def citeste_senzori(self):
        if self.dht:
            try:
                t = self.dht.temperature
                h = self.dht.humidity
                if t is not None: self.temp = round(t, 1)
                if h is not None: self.umiditate = round(h, 1)
            except: pass 

        if self.bmp:
            try: self.presiune = round(self.bmp.pressure, 1)
            except: pass

        if self.mpu:
            try:
                x, y, z = self.mpu.acceleration
                val_vibratie = math.sqrt(x**2 + y**2 + z**2)
                self.vibratii = round(abs(val_vibratie - 9.8), 2)
            except: pass

        if ACTIVARE_SENZOR_GAZ == 1 and self.mq135:
            self.calitate_aer_slaba = self.mq135.value
        else:
            self.calitate_aer_slaba = False 
            
        if time.time() < self.override_timp_expirare and self.override_temp is not None:
            self.temp = self.override_temp

    def proceseaza_logica(self):
        act_geam = False   
        act_inc = False
        target_vent_nou = 0.0 
        culoare = "ALBASTRU"
        msg = "Hala in parametri optimi."
        alerta_vibratie = False
        
        diff = abs(self.temp - self.temperatura_tinta)

        # 1. VERIFICARE BUTON FIZIC
        if self.mod_aer_combinat:
            self.alerta = "MOD AER COMBINAT (Manual Fizic)"
            act_geam = False   
            act_inc = False    
            target_vent_nou = 0.0  
            culoare = "AMBELE" 
            msg = "[OVERRIDE FIZIC] Asteptare aer combinat. Se opreste lent."
            
        # 2. MOD MANUAL DIN WEB
        elif not self.mod_auto:
            self.alerta = "MOD MANUAL"
            act_geam = self.manual_geam
            act_inc = self.manual_inc
            target_vent_nou = self.manual_vent
             
            if act_inc: culoare = "ROSU"
            elif target_vent_nou > 0 or act_geam: culoare = "ALBASTRU"
            else: culoare = "GALBEN"
            
            msg = "[MANUAL] Echipamente controlate de utilizator."
            
            if self.vibratii > 3.0:
                alerta_vibratie = True 
                if target_vent_nou > 0:       
                    target_vent_nou = 0.5
                    msg += " [ATENTIE: Turatie redusa din cauza vibratiilor!]"

        # 3. LOGICA NORMALA (AUTO)
        else:
            if self.calitate_aer_slaba:
                self.alerta = "ALERTA: Aer Viciat!"
                act_geam = True
                target_vent_nou = 1.0
                msg = "Evacuare aer viciat."
            else:
                self.alerta = "Niciuna"
                if self.temp > self.temperatura_tinta + TOLERANTA_TEMP:
                    act_geam = True  
                    target_vent_nou = 1.0
                    msg = "Racire activa."
                elif self.temp < self.temperatura_tinta - TOLERANTA_TEMP:
                    act_geam = False 
                    act_inc = True
                    target_vent_nou = 1.0
                    culoare = "ROSU"
                    msg = "Incalzire activa."
                else:
                    act_geam = False 
                    msg = "Temperatura optima atinsa."

            if self.vibratii > 3.0:
                alerta_vibratie = True 
                msg += " [ALERTA VIBRATII]"
                if target_vent_nou > 0:       
                    target_vent_nou = 0.5
                    msg += " -> Turatie redusa!"

            if time.time() < self.override_timp_expirare and self.override_servo is not None:
                act_geam = self.override_servo

        # --- EXECUTIE HARDWARE ---
        if self.geam_servo and act_geam != self.geam_deschis:
            if act_geam: self.geam_servo.mid() 
            else: self.geam_servo.max() 
            time.sleep(0.5)               
            self.geam_servo.value = None  
            self.geam_deschis = act_geam
             
        if self.incalzire_rezistente:
            if act_inc: self.incalzire_rezistente.on()
            else: self.incalzire_rezistente.off()
            self.incalzire_activa = act_inc

        self.target_ventilator = target_vent_nou
            
        if culoare == "ROSU":
            if self.led_albastru: self.led_albastru.off()
            if self.led_rosu: self.led_rosu.on()
        elif culoare == "ALBASTRU":
            if self.led_rosu: self.led_rosu.off()
            if self.led_albastru: self.led_albastru.on()
        elif culoare == "AMBELE":
            if self.led_rosu: self.led_rosu.on()
            if self.led_albastru: self.led_albastru.on()
        else:
            if self.led_rosu: self.led_rosu.off()
            if self.led_albastru: self.led_albastru.off()

        if self.led_galben:
            if alerta_vibratie: self.led_galben.on()
            else: self.led_galben.off()

        self.mesaj_predictie = msg
        self.culoare_led = culoare
        self.alerta_vibratii = alerta_vibratie

    def obtine_stare(self):
        return {
            "t": self.temp, "u": self.umiditate, "p": self.presiune,
            "v": self.vibratii, "aer": self.calitate_aer_slaba,
            "g": self.geam_deschis, "inc": self.incalzire_activa,
            "vnt": int(self.putere_curenta_ventilator * 100),
            "msg": self.mesaj_predictie, "led": self.culoare_led,
            "alert_vib": self.alerta_vibratii,
            "auto": self.mod_auto,
            "tinta": self.temperatura_tinta, 
            "toleranta": TOLERANTA_TEMP
        }

def asculta_terminal(twin):
    while True:
        try:
            c = input().strip().lower()
            if c.startswith("temp "):
                twin.override_temp = float(c.split()[1])
                twin.override_timp_expirare = time.time() + 10.0
            elif c == "servo deschis":
                twin.override_servo = True
                twin.override_timp_expirare = time.time() + 10.0
            elif c == "servo inchis":
                twin.override_servo = False
                twin.override_timp_expirare = time.time() + 10.0
        except: pass

def ruleaza_sistem(twin):
    print("\nSistem Activ. Comenzi TTY: 'temp [val]', 'servo deschis', 'servo inchis'\n")
    try:
        while True:
            twin.citeste_senzori()
            twin.proceseaza_logica()
            s = twin.obtine_stare()
            str_led = s['led']
            if s['alert_vib']: str_led += " + GALBEN"
            print(f"[{str_led}] Temp: {s['t']}C | Vib: {s['v']} | Pres: {s['p']}")
            print(f"Vent: {s['vnt']}% | Geam: {'DESCHIS' if s['g'] else 'INCHIS'} | Rezistente: {'DA' if s['inc'] else 'NU'} | Mod: {'AUTO' if s['auto'] else 'MANUAL'}")
            print(f"Status: {s['msg']}")
            print("-" * 65)
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\nInchidere securizata... Oprim hardware-ul in siguranta.")
        if twin.ventilator: twin.ventilator.value = 0
        if twin.incalzire_rezistente: twin.incalzire_rezistente.off()
        if twin.led_rosu: twin.led_rosu.off()
        if twin.led_albastru: twin.led_albastru.off()
        if twin.led_galben: twin.led_galben.off()
        if twin.geam_servo:
            twin.geam_servo.max() 
            time.sleep(1)
            twin.geam_servo.detach()
        print("Sistem oprit complet.")

if __name__ == "__main__":
    twin = DigitalTwinHala()
    t_cmd = threading.Thread(target=asculta_terminal, args=(twin,), daemon=True)
    t_cmd.start()
    ruleaza_sistem(twin)
   

