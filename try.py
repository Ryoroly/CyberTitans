import time
from gpiozero import Servo

# --- HARTA PINILOR ---
# VCC (Ro?u)       -> Pinul 4 (5V)
# GND (Maro)       -> Pinul 14 (GND)
# SIG (Portocaliu) -> Pinul 12 (GPIO 18)

print("? Ini?ializare Servomotor SG90 (Geamul)...")

try:
    # Setam servo-ul pe GPIO 18
    geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
    
    print("? Servomotor pregatit.")
    print("-" * 40)
    
    # Ne asiguram ca plecam de la pozi?ia de baza (�nchis). 
    # �n gpiozero, valoarea variaza de la -1.0 (min) la 1.0 (max)
    geam_servo.value = -1.0
    time.sleep(1) # �i dam o secunda sa se a?eze
    
    print("?? Deschidem geamul lent...")
    # Mergem de la -100 la 100 (�mpar?it la 100 va da de la -1.0 la 1.0)
    for pas in range(-100, 101, 2): # Pa?i din 2 �n 2
        geam_servo.value = pas / 100.0
        time.sleep(0.03) # Pauza mica �ntre pa?i pentru o mi?care lina
        
    print("? Geamul este complet deschis. A?teptam 2 secunde...")
    time.sleep(2)
    
    print("?? �nchidem geamul lent...")
    # Ne �ntoarcem de la 100 �napoi la -100
    for pas in range(100, -101, -2):
        geam_servo.value = pas / 100.0
        time.sleep(0.03)

    print("?? Geam a ajuns la pozi?ia zero (�nchis).")

except KeyboardInterrupt:
    print("\n?? Test oprit for?at de utilizator.")

finally:
    # Blocul 'finally' se executa mereu, indiferent daca programul s-a terminat
    # natural sau a fost oprit cu Ctrl+C.
    geam_servo.min()
    time.sleep(0.5)
    geam_servo.detach() # Oprim semnalul PWM ca sa protejam motorul de supra�ncalzire
    print("?? Motor decuplat �n siguran?a. Test finalizat.")