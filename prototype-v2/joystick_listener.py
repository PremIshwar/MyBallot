import serial
import threading
import time
import pyautogui
import glob

_running = False
_thread = None
ser = None


def find_arduino_port():
    """
    Find Arduino UNO serial port on Raspberry Pi / Linux
    """
    ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    return ports[0] if ports else None


def _listen():
    global ser, _running

    port = find_arduino_port()
    if not port:
        print("❌ Arduino not found")
        return

    print(f"✅ Arduino connected on {port}")
    ser = serial.Serial(port, 9600, timeout=1)

    # Allow Arduino to reset
    time.sleep(2)

    while _running:
        try:
            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            print(f"🎮 {line}")

            if line == "LEFT":
                pyautogui.press("left")
            elif line == "RIGHT":
                pyautogui.press("right")
            elif line == "UP":
                pyautogui.press("up")
            elif line == "DOWN":
                pyautogui.press("down")
            elif line == "ENTER":
                pyautogui.press("enter")

        except Exception as e:
            print("❌ Serial error:", e)
            break

    if ser:
        ser.close()
        ser = None


def start():
    global _running, _thread

    if _running:
        return

    _running = True
    _thread = threading.Thread(target=_listen, daemon=True)
    _thread.start()
    print("Joystick listener started")


def stop():
    global _running
    _running = False
