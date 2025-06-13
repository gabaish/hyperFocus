import subprocess

def test_wmi_brightness():
    print("Testing WMI brightness control...")
    
    # Test getting brightness
    try:
        result = subprocess.run([
            'powershell', 
            'Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness'
        ], capture_output=True, text=True, shell=True)
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        print(f"Error: {result.stderr.strip()}")
        
        if result.returncode == 0 and result.stdout.strip():
            brightness = int(result.stdout.strip())
            print(f"Current brightness: {brightness}%")
            return brightness
        else:
            print("Failed to get brightness")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    test_wmi_brightness() 