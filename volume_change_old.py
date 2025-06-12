import tkinter as tk
import threading
import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import comtypes

# Volume functions
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(level):
    volume = get_volume_interface()
    volume.SetMasterVolumeLevelScalar(level, None)  # level between 0.0 and 1.0

def get_current_volume():
    volume = get_volume_interface()
    return volume.GetMasterVolumeLevelScalar()

def volume_boost():
    comtypes.CoInitialize()
    original_volume = get_current_volume()
    peak_volume = min(original_volume + 0.3, 1.0)  # Don't go above 1.0
    steps = 10  # Number of steps to rise/fall
    pause = 0.1  # Time between steps in seconds

    # Go up
    for i in range(1, steps + 1):
        level = original_volume + (peak_volume - original_volume) * (i / steps)
        set_volume(level)
        time.sleep(pause)

    # Go down
    for i in range(1, steps + 1):
        level = peak_volume - (peak_volume - original_volume) * (i / steps)
        set_volume(level)
        time.sleep(pause)

    # Repeat two more times
    for _ in range(2):
        for i in range(1, steps + 1):
            level = original_volume + (peak_volume - original_volume) * (i / steps)
            set_volume(level)
            time.sleep(pause)
        for i in range(1, steps + 1):
            level = peak_volume - (peak_volume - original_volume) * (i / steps)
            set_volume(level)
            time.sleep(pause)

    # Restore original volume
    set_volume(original_volume)



# GUI
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "pink")
root.geometry("150x150+50+50")  # Corner floating button

canvas = tk.Canvas(root, width=150, height=150, bg="pink", highlightthickness=0)
canvas.pack()

# Create a clickable circle
circle = canvas.create_oval(25, 25, 125, 125, fill="red", outline="white", width=4)
label = canvas.create_text(75, 75, text="LOUD", font=('Helvetica', 12, 'bold'), fill='white')

# Click event
def on_click(event):
    threading.Thread(target=volume_boost, daemon=True).start()

canvas.tag_bind(circle, "<Button-1>", on_click)
canvas.tag_bind(label, "<Button-1>", on_click)

root.mainloop()
