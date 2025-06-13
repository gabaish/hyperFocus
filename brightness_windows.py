import tkinter as tk
import threading
import time
import subprocess
import ctypes
from ctypes import wintypes

def get_brightness_wmi():
    """Get brightness using WMI (Windows Management Instrumentation)"""
    try:
        result = subprocess.run([
            'powershell', 
            'Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness'
        ], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return None

def set_brightness_wmi(brightness):
    """Set brightness using WMI"""
    try:
        subprocess.run([
            'powershell',
            f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {brightness})'
        ], shell=True)
        return True
    except:
        return False

def get_brightness_ddc():
    """Get brightness using DDC/CI (Display Data Channel)"""
    try:
        result = subprocess.run([
            'powershell',
            'Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness'
        ], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return None

def set_brightness_ddc(brightness):
    """Set brightness using DDC/CI"""
    try:
        subprocess.run([
            'powershell',
            f'(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, {brightness})'
        ], shell=True)
        return True
    except:
        return False

def flicker_brightness():
    """Flicker brightness using available methods"""
    try:
        # Try to get current brightness
        original = get_brightness_wmi() or get_brightness_ddc()
        if original is None:
            print("Could not get current brightness, using default value")
            original = 50  # Default to 50%
        
        print(f"Original brightness: {original}%")
        
        # Flicker effect
        for i in range(5):
            print(f"Flicker {i+1}/5")
            
            # Dim
            if set_brightness_wmi(20) or set_brightness_ddc(20):
                print("Set brightness to 20%")
            else:
                print("Failed to dim screen")
            
            time.sleep(0.2)
            
            # Restore
            if set_brightness_wmi(original) or set_brightness_ddc(original):
                print(f"Restored brightness to {original}%")
            else:
                print("Failed to restore brightness")
            
            time.sleep(0.2)
            
    except Exception as e:
        print(f"Error in flicker_brightness: {e}")

def on_click(event):
    threading.Thread(target=flicker_brightness, daemon=True).start()

# Test brightness control methods
def test_methods():
    print("Testing brightness control methods...")
    
    print("\n1. Testing WMI method:")
    brightness = get_brightness_wmi()
    print(f"   Current brightness: {brightness}%")
    
    print("\n2. Testing DDC/CI method:")
    brightness = get_brightness_ddc()
    print(f"   Current brightness: {brightness}%")
    
    print("\n3. Testing set brightness:")
    if set_brightness_wmi(50):
        print("   WMI set brightness successful")
    else:
        print("   WMI set brightness failed")
    
    if set_brightness_ddc(50):
        print("   DDC/CI set brightness successful")
    else:
        print("   DDC/CI set brightness failed")

if __name__ == "__main__":
    # Test methods first
    test_methods()
    
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