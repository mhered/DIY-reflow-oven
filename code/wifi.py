import network
import time
from secrets import SSID, PASSWORD

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        for _ in range(10):
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print('Connected. IP:', wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        raise RuntimeError("Wi-Fi connection failed")
