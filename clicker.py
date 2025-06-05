import pyautogui
import time

# Enable failsafe: moving the mouse to the top-left corner exits the script.
pyautogui.FAILSAFE = True

# Give yourself 3 seconds to switch to the correct window
time.sleep(3)
try:
    while True:
        x, y = pyautogui.position()
        print(f"Mouse position: x={x}, y={y}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopped.")
