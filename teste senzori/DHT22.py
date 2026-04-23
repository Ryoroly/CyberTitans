import time
import board
import adafruit_dht

# --- HARTA PINILOR FIZICI ---
# Firul RO?U   -> Pinul 1 (Alimentare 3.3V) -> Hardware, nu apare �n cod
# Firul NEGRU  -> Pinul 6 (GND / �mpam�ntare) -> Hardware, nu apare �n cod
# Firul VERDE  -> Pinul 7 (Date / Semnal) -> �n Python se nume?te 'board.D4'

print("? Ini?ializare senzor...")

try:
    # Aici spunem placii: "Asculta datele care vin pe Pinul fizic 7 (D4)"
    dht_device = adafruit_dht.DHT22(board.D4)
    print("? Senzor ini?ializat cu succes. A?teptam primele date...")
except Exception as e:
    print(f"? Eroare la ini?ializare: {e}")

# Bucla infinita de citire
while True:
    try:
        # Extragem valorile de pe firul verde
        temperatura = dht_device.temperature
        umiditate = dht_device.humidity
        
        print(f"??? Temp: {temperatura:.1f}�C | ?? Umiditate: {umiditate:.1f}%")
        
    except RuntimeError as error:
        # Erorile de citire sunt foarte comune la DHT22 (dureaza p�na se �ncarca senzorul)
        # Ignoram eroarea ?i �ncercam din nou
        print(f"Eroare temporara de citire (normala pentru DHT22): {error.args[0]}")
        time.sleep(2.0)
        continue
    except Exception as error:
        # O eroare grava (ex: s-a scos un fir accidental)
        dht_device.exit()
        raise error
    
    # DHT22 are un senzor lent, are nevoie de cel pu?in 2 secunde �ntre citiri
    time.sleep(2.0)