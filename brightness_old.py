import tkinter as tk
import threading
import time
import subprocess

def get_brightness():
    """Get current brightness using PowerShell WMI"""
    try:
        result = subprocess.run([
            'powershell', 
            'Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness'
        ], capture_output=True, text=True, shell=True)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except:
        pass
    return None

def set_brightness(brightness):
    """Set brightness using PowerShell WMI"""
    try:
        subprocess.run([
            'powershell',
            f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {brightness})'
        ], shell=True)
        return True
    except:
        return False

def flicker_brightness():
    try:
        original = get_brightness()
        if original is None:
            print("Could not get current brightness, using default value")
            original = 50  # Default to 50%
        
        print(f"Original brightness: {original}%")
        
        for _ in range(3):
            set_brightness(20)    # Dim quickly
            time.sleep(0.2)
            set_brightness(original)  # Restore
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
