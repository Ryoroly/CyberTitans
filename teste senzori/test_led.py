from gpiozero import LED
import time

# Pin fizic 29 -> GPIO 5
# Pin fizic 38 -> GPIO 20
led_rosu = LED(5)
led_albastru = LED(20)

print("Testare pini: Rosu (29/GPIO 5) si Albastru (38/GPIO 20)")

try:
    while True:
        print("--> ROSU (Pin 29) aprins")
        led_rosu.on()
        led_albastru.off()
        time.sleep(4)

        print("--> ALBASTRU (Pin 38) aprins")
        led_rosu.off()
        led_albastru.on()
        time.sleep(4)

except KeyboardInterrupt:
    led_rosu.off()
    led_albastru.off()
    print("\nTest oprit.")