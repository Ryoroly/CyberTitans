import time
import board
import adafruit_mpu6050

print("? Ini?ializare senzor de vibra?ii MPU6050...")

try:
    # Ne conectam la magistrala I2C (Pinii 3 ?i 5)
    i2c = board.I2C()
    
    # Gasim senzorul MPU6050 pe aceasta magistrala
    mpu = adafruit_mpu6050.MPU6050(i2c)
    print("? Senzor MPU6050 ini?ializat cu succes!")
except ValueError as e:
    print("? Eroare I2C: Nu gasesc senzorul. Verifica firele! Ai pus SCL/SDA corect pe pinii 5 ?i 3?")
    exit()
except Exception as e:
    print(f"? Eroare la ini?ializare: {e}")
    exit()

print("-" * 40)
print("?? Test: Lovi?i u?or masa sau senzorul pentru a vedea cum cresc vibra?iile!")
print("-" * 40)

while True:
    try:
        # Citim accelera?ia pe cele 3 axe (�n m/s^2)
        # Acestea ne vor ajuta sa detectam "vibra?iile" utilajului nostru
        accel_x, accel_y, accel_z = mpu.acceleration
        
        # MPU6050 are ?i giroscop (cite?te rota?ia), dar pentru detectarea uzurii motorului,
        # accelera?ia liniara (vibra?ia fizica) este cea mai importanta.
        
        print(f"?? Vibra?ii (m/s�): X: {accel_x:5.2f} | Y: {accel_y:5.2f} | Z: {accel_z:5.2f}")
        
    except Exception as error:
        print(f"?? Eroare de citire: {error}")
    
    # Citim foarte rapid ca sa nu ratam ?ocurile (0.2 secunde)
    time.sleep(0.2)