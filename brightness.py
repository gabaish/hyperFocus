import time
import screen_brightness_control as sbc

# def flicker_brightness():
#     try:
#         original = sbc.get_brightness(display=0)[0]
#         for _ in range(5):
#             sbc.set_brightness(20)
#             time.sleep(0.2)
#             sbc.set_brightness(original)
#             time.sleep(0.2)
#     except Exception as e:
#         print("Error adjusting brightness:", e)


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