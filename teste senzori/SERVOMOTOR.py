import time
from gpiozero import Servo

# --- HARTA PINILOR ---
# VCC (Ro?u)       -> Pinul 4 (5V)
# GND (Maro)       -> Pinul 14 (GND)
# SIG (Portocaliu) -> Pinul 12 (GPIO 18)

print("? Ini?ializare Servomotor SG90 (Fara Jitter)...")

try:
    geam_servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
    
    print("? Servomotor pregatit. Secven?a: 0� ?? 90� ?? 180�")
    print("-" * 40)
    
    # --- POZI?IA 1: 0 GRADE ---
    print("?? Pozi?ia 1: 0� (�NCHIS)")
    geam_servo.min()
    time.sleep(0.5)          # �i dam 0.5 secunde sa faca mi?carea fizica
    geam_servo.value = None  # Oprim semnalul (TAIEM TREMURATUL)
    time.sleep(2.5)          # A?teptam restul de 2.5 secunde �n lini?te totala
    
    # --- POZI?IA 2: 90 GRADE ---
    print("?? Pozi?ia 2: 90� (JUMATATE)")
    geam_servo.mid()         # Motorul se "treze?te" automat c�nd prime?te o comanda noua
    time.sleep(0.5)          # Timp pentru mi?care
    geam_servo.value = None  # Oprim semnalul
    time.sleep(2.5)          # A?teptam �n lini?te
    
    # --- POZI?IA 3: 180 GRADE ---
    print("?? Pozi?ia 3: 180� (DESCHIS COMPLET)")
    geam_servo.max()
    time.sleep(0.5)          # Timp pentru mi?care
    geam_servo.value = None  # Oprim semnalul
    time.sleep(2.5)          # A?teptam �n lini?te

    print("? Test finalizat cu succes. Zero tremurat!")

except KeyboardInterrupt:
    print("\n?? Test oprit for?at de utilizator.")

finally:
    print("?? Readucem geamul la 0� (�NCHIS) pentru siguran?a...")
    geam_servo.min()
    time.sleep(0.5)
    geam_servo.detach() # Opre?te totul definitiv
    print("?? Motor decuplat �n siguran?a.")