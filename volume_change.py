import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import comtypes

def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(level):
    volume = get_volume_interface()
    volume.SetMasterVolumeLevelScalar(level, None)

def get_current_volume():
    volume = get_volume_interface()
    return volume.GetMasterVolumeLevelScalar()

def volume_boost():
    comtypes.CoInitialize()
    original_volume = get_current_volume()
    peak_volume = min(original_volume + 0.3, 1.0)
    steps = 10
    pause = 0.1

    for _ in range(3):  # wave 3 times
        for i in range(1, steps + 1):
            level = original_volume + (peak_volume - original_volume) * (i / steps)
            set_volume(level)
            time.sleep(pause)
        for i in range(1, steps + 1):
            level = peak_volume - (peak_volume - original_volume) * (i / steps)
            set_volume(level)
            time.sleep(pause)

    set_volume(original_volume)
