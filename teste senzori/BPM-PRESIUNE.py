import time
import board
import adafruit_bmp280

# --- HARTA PINILOR FIZICI (I2C) ---
# VCC -> Pinul 17 (3.3V)
# GND -> Pinul 9 (GND)
# SCL -> Pinul 5 (GPIO 3) -> Semnalul de "ceas" (Clock)
# SDA -> Pinul 3 (GPIO 2) -> Datele efective

print("? Ini?ializare senzor BMP280...")

try:
    # 1. Cream conexiunea I2C. 'board.I2C()' folose?te automat pinii 3(SDA) ?i 5(SCL)
    i2c = board.I2C()
    
    # 2. Conectam senzorul la aceasta magistrala
    bmp_device = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    
    # Op?ional: Setam presiunea de la nivelul marii (hPa) pentru a calcula altitudinea corect
    # Valoarea medie este 1013.25, dar o po?i ajusta dupa vremea reala din Bra?ov
    bmp_device.sea_level_pressure = 1013.25 
    
    print("? Senzor BMP280 ini?ializat cu succes!")
except ValueError as e:
    print(f"? Eroare I2C: Nu gasesc senzorul. Verifica firele SDA/SCL! ({e})")
    exit()
except Exception as e:
    print(f"? Eroare la ini?ializare: {e}")
    exit()

# Bucla de citire
while True:
    try:
        # Senzorul BMP280 cite?te ?i temperatura, pe l�nga presiune!
        temp = bmp_device.temperature
        presiune = bmp_device.pressure
        altitudine = bmp_device.altitude
        
        # Afi?am datele formatate frumos
        print(f"??? Temp: {temp:.1f}�C | ?? Presiune: {presiune:.1f} hPa | ?? Altitudine: {altitudine:.1f} m")
        
    except Exception as error:
        print(f"?? Eroare de citire: {error}")
    
    # BMP280 e un senzor rapid, dar punem o secunda pauza pentru a nu inunda ecranul
    time.sleep(1.0)