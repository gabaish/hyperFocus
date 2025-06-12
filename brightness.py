import tkinter as tk
import threading
import time
import screen_brightness_control as sbc

def flicker_brightness():
    try:
        original = sbc.get_brightness(display=0)[0]
        for _ in range(5):
            sbc.set_brightness(20)    # Dim quickly
            time.sleep(0.2)
            sbc.set_brightness(original)  # Restore
            time.sleep(0.2)
    except Exception as e:
        print("Error adjusting brightness:", e)

def on_click(event):
    threading.Thread(target=flicker_brightness, daemon=True).start()

# GUI setup
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.geometry("120x50+50+50")

canvas = tk.Canvas(root, width=120, height=50, bg="black", highlightthickness=0)
canvas.pack()

button = canvas.create_rectangle(10, 10, 110, 40, fill="yellow", outline="white", width=2)
label = canvas.create_text(60, 25, text="Flicker", font=('Helvetica', 12, 'bold'), fill='black')

canvas.tag_bind(button, "<Button-1>", on_click)
canvas.tag_bind(label, "<Button-1>", on_click)

root.mainloop()
