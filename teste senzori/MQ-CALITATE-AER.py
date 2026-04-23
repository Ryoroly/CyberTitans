import time
from gpiozero import DigitalInputDevice

# --- HARTA PINILOR ---
# VCC -> Pinul 2 (5V) 
# GND -> Pinul 39 (GND) 
# DO  -> Pinul 11 (GPIO 17) -> Semnalul Digital

print("? Ini?ializare senzor de gaz MQ-135...")

try:
    # Setam GPIO 17 ca pin de intrare
    senzor_gaz = DigitalInputDevice(17)
    
    print("? Senzor pregatit. Afi?am datele live (apasa?i Ctrl+C pentru oprire)...\n")

    while True:
        # Extragem valoarea bruta din senzor (va fi True sau False)
        valoare_bruta = senzor_gaz.value
        
        # Afi?am exact ce vede Raspberry Pi-ul
        if valoare_bruta == True: # True �nseamna 1 / HIGH
            print(f"Valoare pin: {valoare_bruta} (1) -> ?? ALERTA: Gaz Detectat!")
        else:                     # False �nseamna 0 / LOW
            print(f"Valoare pin: {valoare_bruta} (0) -> ? Aer Curat.")
            
        # O pauza de o secunda ca sa putem citi u?or ce scrie pe ecran
        time.sleep(1)

except KeyboardInterrupt:
    print("\n?? Test oprit de utilizator.")