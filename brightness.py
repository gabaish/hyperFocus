import time
import screen_brightness_control as sbc

def flicker_brightness():
    try:
        original = sbc.get_brightness(display=0)[0]
        for _ in range(5):
            sbc.set_brightness(20)
            time.sleep(0.2)
            sbc.set_brightness(original)
            time.sleep(0.2)
    except Exception as e:
        print("Error adjusting brightness:", e)
