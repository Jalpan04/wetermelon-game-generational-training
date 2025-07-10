import subprocess
import pyautogui
import pygetwindow as gw
import mss
import cv2
import numpy as np
import time
import threading
import keyboard
import os
import sys

# === CONFIGURATION ===
GAME_SCRIPT = "fruty.py"
GAME_TITLE = "Fruity - Drop Anytime"
UI_HEIGHT = 120
DROP_OFFSET_Y = 60
DROP_INTERVAL = 0.5
X_SCAN_OFFSETS = [-30, -15, 0, 15, 30]
Y_SCAN_OFFSETS = [0, 10, 20]
running = True
locked_x = None
locked_y = None

# All fruit HSV ranges
FRUIT_HSV_RANGES = [
    {"lower": (100, 80, 100), "upper": (130, 255, 255)},  # Blueberry
    {"lower": (0, 100, 100),   "upper": (10, 255, 255)},  # Strawberry/Cherry
    {"lower": (20, 100, 100),  "upper": (40, 255, 255)},  # Peach/Lemon
    {"lower": (40, 50, 100),   "upper": (80, 255, 255)},  # Melon/Lime
    {"lower": (130, 50, 100),  "upper": (160, 255, 255)}, # Purple fruit
]

def listen_for_escape():
    global running
    while running:
        if keyboard.is_pressed("esc"):
            print("🔴 ESC pressed. Stopping...")
            running = False
            break
        time.sleep(0.1)

def start_game():
    print("🎮 Launching game script...")
    if not os.path.exists(GAME_SCRIPT):
        print(f"❌ Game script '{GAME_SCRIPT}' not found.")
        sys.exit(1)
    return subprocess.Popen([sys.executable, GAME_SCRIPT])

def wait_for_game_window(title, timeout=10):
    print("⌛ Waiting for game window...")
    for _ in range(timeout * 10):
        windows = gw.getWindowsWithTitle(title)
        if windows:
            print("✅ Game window found!")
            win = windows[0]
            return {
                "left": win.left + 8,
                "top": win.top + 30,
                "width": 245,
                "height": 382
            }
        time.sleep(0.1)
    print("❌ Could not find game window!")
    return None

def detect_fruits(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for r in FRUIT_HSV_RANGES:
        mask = cv2.inRange(hsv, np.array(r["lower"]), np.array(r["upper"]))
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def count_fruits(image):
    return len(detect_fruits(image))

def fruit_spawned(before_count, after_img):
    return count_fruits(after_img) > before_count

def main():
    global running, locked_x, locked_y

    # Start game
    game_proc = start_game()
    time.sleep(2)

    # Detect window
    game_region = wait_for_game_window(GAME_TITLE)
    if not game_region:
        game_proc.kill()
        return

    drop_y_base = game_region["top"] + UI_HEIGHT + DROP_OFFSET_Y
    drop_x_base = game_region["left"] + game_region["width"] // 2

    threading.Thread(target=listen_for_escape, daemon=True).start()


    print("🤖 AI started. Press ESC to stop.")

    with mss.mss() as sct:
        while running:
            before_img = np.array(sct.grab(game_region))[:, :, :3]
            before_count = count_fruits(before_img)

            if locked_x is not None:
                # ✅ Already found a valid location — only click
                pyautogui.click(locked_x, locked_y)
                time.sleep(DROP_INTERVAL)
                continue

            # 🔍 First-time scan to find valid drop spot
            found = False
            for y_offset in Y_SCAN_OFFSETS:
                for x_offset in X_SCAN_OFFSETS:
                    attempt_x = drop_x_base + x_offset
                    attempt_y = drop_y_base + y_offset
                    pyautogui.moveTo(attempt_x, attempt_y)
                    pyautogui.click()
                    time.sleep(0.25)

                    after_img = np.array(sct.grab(game_region))[:, :, :3]
                    if fruit_spawned(before_count, after_img):
                        print(f"✅ Locked drop location at X={attempt_x}, Y={attempt_y}")
                        locked_x, locked_y = attempt_x, attempt_y
                        found = True
                        break
                if found:
                    break

            if not found:
                print("❌ No fruit detected. Retrying...")
            time.sleep(DROP_INTERVAL)

    print("🛑 AI stopped. Closing game.")
    game_proc.kill()

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    main()
