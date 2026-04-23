import time
from gpiozero import PWMOutputDevice

# Ini?ializam ventilatorul pe GPIO 13 (Pinul fizic 33)
# PWMOutputDevice permite setarea valorilor �ntre 0.0 (oprit) ?i 1.0 (putere maxima)
ventilator = PWMOutputDevice(13)

print("?? �ncepem testul PWM pentru ventilator...")

try:
    while True:
        print("?? Accelerare (0% -> 100%) �n 10 secunde...")
        
        # Facem 100 de pa?i. 100 pa?i * 0.1 secunde = 10 secunde
        for putere in range(0, 101):
            ventilator.value = putere / 100.0
            time.sleep(0.1) 

        print("?? Viteza maxima atinsa!")
        time.sleep(1) # �l ?inem la viteza maxima timp de 1 secunda pentru efect

        print("?? Decelerare (100% -> 0%) �n 10 secunde...")
        
        # Numaram invers, de la 100 la 0
        for putere in range(100, -1, -1):
            ventilator.value = putere / 100.0
            time.sleep(0.1)
            
        print("?? Ventilatorul s-a oprit.")
        time.sleep(2) # Pauza de 2 secunde �nainte de a relua ciclul

except KeyboardInterrupt:
    # C�nd ape?i Ctrl+C pentru a opri scriptul, ne asiguram ca ventilatorul se opre?te complet
    print("\n?? Test oprit de utilizator. Oprim ventilatorul.")
    ventilator.value = 0