import time
from gpiozero import Servo

# --- CONFIGURARE ---
# SIG (Semnal) -> Pinul 12 (GPIO 18)
# min_pulse_width si max_pulse_width setate pentru SG90
print("?? Pornire ciclu comutare: 180� <--> 90�")
print("? Pauza: 5 secunde in fiecare pozitie. Apasa Ctrl+C pentru oprire.")

try:
    geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)

    while True:
        # --- POZITIA: 180 GRADE (INCHIS) ---
        print("?? Mutare la 180� (Inchis)...")
        geam_servo.max()
        time.sleep(0.6)          # Timp suficient pentru ca bratul sa ajunga fizic
        geam_servo.value = None  # Taiem curentul pentru a opri tremuratul
        print("?? Stationare 5 secunde la 180�.")
        time.sleep(4.4)          # Restul timpului pana la 5 secunde

        # --- POZITIA: 90 GRADE (DESCHIS PARTIAL) ---
        print("?? Mutare la 90� (Mijloc)...")
        geam_servo.mid()
        time.sleep(0.6)          # Timp miscare
        geam_servo.value = None  # Taiem curentul
        print("?? Stationare 5 secunde la 90�.")
        time.sleep(4.4)          # Restul timpului pana la 5 secunde

except KeyboardInterrupt:
    print("\n?? Program oprit de utilizator.")

finally:
    # Inchidem curat pentru a nu lasa motorul sub tensiune
    geam_servo.detach()
    print("?? Servomotor deconectat.")