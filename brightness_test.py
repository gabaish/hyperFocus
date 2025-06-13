import screen_brightness_control as sbc
import sys

def test_brightness_control():
    print("Testing brightness control...")
    print(f"Python version: {sys.version}")
    
    try:
        # List monitors
        monitors = sbc.list_monitors()
        print(f"Detected monitors: {monitors}")
        
        # Try to get current brightness
        print("Attempting to get current brightness...")
        brightness = sbc.get_brightness()
        print(f"Current brightness: {brightness}")
        
        # Try to set brightness
        print("Attempting to set brightness to 50%...")
        sbc.set_brightness(50)
        print("Brightness set successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try alternative methods
        print("\nTrying alternative methods...")
        try:
            # Try with specific display
            brightness = sbc.get_brightness(display=0)
            print(f"Brightness with display=0: {brightness}")
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")

if __name__ == "__main__":
    test_brightness_control() 