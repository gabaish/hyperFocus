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
    comtypes.CoInitialize()  # <-- add this line
    current = get_current_volume()
    set_volume(current+0.2)  # Max volume
    time.sleep(3)
    set_volume(current)
    comtypes.CoUninitialize()  # <-- optional, for cleanup

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
