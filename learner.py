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

# All fruit RGB color references (from your game definition)
fruit_types = [
    {"color": (74, 144, 226)},
    {"color": (255, 107, 107)},
    {"color": (192, 57, 43)},
    {"color": (255, 140, 66)},
    {"color": (255, 217, 61)},
    {"color": (170, 0, 255)},
    {"color": (255, 165, 0)},
    {"color": (0, 184, 148)},
    {"color": (253, 203, 110)},
    {"color": (108, 92, 231)},
    {"color": (46, 204, 113)},
]


def listen_for_escape():
    global running
    while running:
        if keyboard.is_pressed("esc"):
            print("\U0001F534 ESC pressed. Stopping...")
            running = False
            break
        time.sleep(0.1)


def start_game():
    print("\U0001F3AE Launching game script...")
    if not os.path.exists(GAME_SCRIPT):
        print(f"\u274C Game script '{GAME_SCRIPT}' not found.")
        sys.exit(1)
    return subprocess.Popen([sys.executable, GAME_SCRIPT])


def wait_for_game_window(title, timeout=10):
    print("\u231B Waiting for game window...")
    for _ in range(timeout * 10):
        windows = gw.getWindowsWithTitle(title)
        if windows:
            print("\u2705 Game window found!")
            win = windows[0]
            return {
                "left": win.left + 8,
                "top": win.top + 30,
                "width": 245,
                "height": 382
            }
        time.sleep(0.1)
    print("\u274C Could not find game window!")
    return None


def detect_fruits(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 30, 30), (180, 255, 255))  # simple brightness mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def count_fruits(image):
    return len(detect_fruits(image))


def fruit_spawned(before_count, after_img):
    return count_fruits(after_img) > before_count


def detect_fruit_type_from_ui(game_region):
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(game_region))[:, :, :3]

    current_region = screenshot[UI_HEIGHT:UI_HEIGHT+60, game_region["width"] // 2 - 30:game_region["width"] // 2 + 30]
    next_region = screenshot[50:100, game_region["width"] - 120:game_region["width"] - 40]

    def dominant_color(region):
        region = cv2.resize(region, (1, 1), interpolation=cv2.INTER_AREA)
        return tuple(int(x) for x in region[0, 0])

    def match_fruit_type(rgb):
        best_match = None
        lowest_dist = float('inf')
        for idx, ft in enumerate(fruit_types):
            dist = np.linalg.norm(np.array(ft["color"]) - np.array(rgb))
            if dist < lowest_dist:
                best_match = idx
                lowest_dist = dist
        return best_match

    current_rgb = dominant_color(current_region)
    next_rgb = dominant_color(next_region)

    current_type = match_fruit_type(current_rgb)
    next_type = match_fruit_type(next_rgb)

    print(f"\U0001F3AF Current Fruit RGB: {current_rgb} → Type {current_type}")
    print(f"\U0001F52E Next Fruit RGB: {next_rgb} → Type {next_type}")
    return current_type, next_type


def main():
    global running, locked_x, locked_y

    game_proc = start_game()
    time.sleep(2)

    game_region = wait_for_game_window(GAME_TITLE)
    if not game_region:
        game_proc.kill()
        return

    drop_y_base = game_region["top"] + UI_HEIGHT + DROP_OFFSET_Y
    drop_x_base = game_region["left"] + game_region["width"] // 2

    threading.Thread(target=listen_for_escape, daemon=True).start()
    print("\U0001F916 AI started. Press ESC to stop.")

    with mss.mss() as sct:
        while running:
            before_img = np.array(sct.grab(game_region))[:, :, :3]
            before_count = count_fruits(before_img)

            # Detect current and next fruit types (optional logic hook)
            current_type, next_type = detect_fruit_type_from_ui(game_region)

            if locked_x is not None:
                pyautogui.click(locked_x, locked_y)
                time.sleep(DROP_INTERVAL)
                continue

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
                        print(f"\u2705 Locked drop location at X={attempt_x}, Y={attempt_y}")
                        locked_x, locked_y = attempt_x, attempt_y
                        found = True
                        break
                if found:
                    break

            if not found:
                print("\u274C No fruit detected. Retrying...")
            time.sleep(DROP_INTERVAL)

    print("\U0001F6D1 AI stopped. Closing game.")
    game_proc.kill()


if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    main()