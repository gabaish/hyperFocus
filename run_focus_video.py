import threading
import time
import random
import cv2
import numpy as np
import pygame
import time

import concentration
from volume_change import volume_boost
from brightness import flicker_brightness

import logging, random
logger = logging.getLogger(__name__)

# Video path
VIDEO_PATH = "./hyperFocus/assets/How to Speak So That People Want to Listen _ Julian Treasure _ TED_short.mp4"
AUDIO_PATH = "./hyperFocus/assets/audio.mp3"

# Globals
segments = []
active_segment = None
video_fps = 30
video_frame_count = 1
frame_number = 0


def draw_progress_bar(frame, current_frame):
    bar_height = 30
    bar_top = frame.shape[0] - bar_height
    bar_bottom = frame.shape[0]
    width = frame.shape[1]

    cv2.rectangle(frame, (0, bar_top), (width, bar_bottom), (230, 230, 230), -1)

    for start, end, color in segments:
        x1 = int((start / video_frame_count) * width)
        x2 = int((end / video_frame_count) * width)
        cv2.rectangle(frame, (x1, bar_top), (x2, bar_bottom), color, -1)

    if active_segment is not None:
        start, color = active_segment
        x1 = int((start / video_frame_count) * width)
        x2 = int((current_frame / video_frame_count) * width)
        cv2.rectangle(frame, (x1, bar_top), (x2, bar_bottom), color, -1)

    cur_x = int((current_frame / video_frame_count) * width)
    cv2.line(frame, (cur_x, bar_top - 5), (cur_x, bar_bottom + 5), (0, 0, 0), 2)


def show_summary_screen():
    width, height = 600, 400
    summary_img = np.ones((height, width, 3), dtype=np.uint8) * 255

    green_frames = sum(end - start for start, end, color in segments if color == (0, 255, 0))
    red_frames = sum(end - start for start, end, color in segments if color == (0, 0, 255))

    green_percent = (green_frames / video_frame_count) * 100
    red_percent = (red_frames / video_frame_count) * 100

    cv2.putText(summary_img, "SESSION SUMMARY", (width // 2 - 170, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (50, 50, 50), 3)

    cv2.putText(summary_img, f"Focus Time ({green_percent:.1f}%)", (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.rectangle(summary_img, (50, 170), (50 + int(green_percent * 4), 200), (0, 255, 0), -1)

    cv2.putText(summary_img, f"Lost Focus ({red_percent:.1f}%)", (50, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.rectangle(summary_img, (50, 270), (50 + int(red_percent * 4), 300), (0, 0, 255), -1)

    cv2.putText(summary_img, "Press any key to close", (width // 2 - 120, height - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

    cv2.imshow("Summary", summary_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def monitor_focus():
    global active_segment, segments, frame_number
    color= (0, 255, 0) #default color
    while frame_number < video_frame_count:
        time.sleep(1)
        status = concentration.get_focus_status()
        if status == 'focused':
            color = (0, 255, 0)
        elif status == 'out_of_focus':
            color = (0, 0, 255)
            #random.choice([volume_boost, flicker_brightness])()
            # 1. Pick the nudge but don’t run it yet
            action = random.choice([volume_boost, flicker_brightness])

            # 2. Log what we chose (use the function’s __name__ for readability)
            print(f"[NUDGE] Selected: {action.__name__}")

            # 3. Execute the nudge
            action()
        else:
            continue

        if active_segment is not None:
            segments.append((active_segment[0], frame_number, active_segment[1]))
        active_segment = (frame_number, color)


def play_video():
    global frame_number, video_fps, video_frame_count, active_segment
    pygame.mixer.init()
    pygame.mixer.music.load(AUDIO_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ Error opening video.")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    pygame.mixer.music.play()
    frame_number = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        draw_progress_bar(frame, frame_number)
        cv2.imshow("Focus Monitor", frame)

        if cv2.waitKey(int(1000 / video_fps)) & 0xFF == ord('q'):
            break

        frame_number += 1

    if active_segment is not None:
        segments.append((active_segment[0], frame_number, active_segment[1]))

    cap.release()
    pygame.mixer.music.stop()
    show_summary_screen()


# Launch focus tracking and video playback
if __name__ == "__main__":
    ready = threading.Event()
    threading.Thread(target=concentration.main, daemon=True).start()
    threading.Thread(target=monitor_focus, daemon=True).start()
    ready.wait(timeout=30)
    play_video()
