import cv2
import numpy as np
import threading
from playsound import playsound
import pygame



# Global variables
paused = True
play_button_rect = (20, 20, 80, 80)
red_button_rect = (0, 0, 0, 0)
green_button_rect = (0, 0, 0, 0)
speed_up_button_rect = (0, 0, 0, 0)
speed_down_button_rect = (0, 0, 0, 0)

active_segment = (0, (0, 255, 0))
segments = []  # List of (start_frame, end_frame, color)

video_fps = 30
video_frame_count = 1
# playback_speed = 1.0

def draw_toggle_button(frame, paused):
    x1, y1, x2, y2 = play_button_rect
    cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 50, 50), -1)
    if paused:
        pts = [(x1 + 20, y1 + 15), (x1 + 20, y2 - 15), (x2 - 15, y1 + (y2 - y1) // 2)]
        cv2.fillPoly(frame, [np.array(pts)], (0, 255, 0))
    else:
        cv2.rectangle(frame, (x1 + 18, y1 + 15), (x1 + 26, y2 - 15), (0, 0, 255), -1)
        cv2.rectangle(frame, (x1 + 34, y1 + 15), (x1 + 42, y2 - 15), (0, 0, 255), -1)

def calculate_color_durations(current_frame):
    green_time = 0.0
    red_time = 0.0

    for start, end, color in segments:
        duration = (end - start) / video_fps
        if color == (0, 255, 0):
            green_time += duration
        elif color == (0, 0, 255):
            red_time += duration

    if active_segment is not None:
        start, color = active_segment
        duration = (current_frame - start) / video_fps
        if color == (0, 255, 0):
            green_time += duration
        elif color == (0, 0, 255):
            red_time += duration

    return green_time, red_time

def draw_buttons(frame):
    h, w = frame.shape[:2]
    padding = 20
    btn_size = 40
    spacing = 15

    global red_button_rect, green_button_rect, speed_up_button_rect, speed_down_button_rect

    red_button_rect = (w - padding - 4*btn_size - 3*spacing, h - btn_size - 40,
                       w - 3*btn_size - 3*spacing, h - 40)
    green_button_rect = (w - padding - 3*btn_size - 2*spacing, h - btn_size - 40,
                         w - 2*btn_size - 2*spacing, h - 40)
    # speed_down_button_rect = (w - padding - 2*btn_size - spacing, h - btn_size - 40,
    #                           w - btn_size - spacing, h - 40)
    # speed_up_button_rect = (w - btn_size - padding, h - btn_size - 40,
    #                         w - padding, h - 40)

    for rect, color in [(red_button_rect, (0, 0, 255)), (green_button_rect, (0, 255, 0))]:
        cv2.rectangle(frame, rect[:2], rect[2:], (0, 0, 0), -1)
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        cv2.circle(frame, (cx, cy), 12, color, -1)

    # x1, y1, x2, y2 = speed_down_button_rect
    # cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), -1)
    # cv2.putText(frame, '-', (x1 + 12, y2 - 12), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    #
    # x1, y1, x2, y2 = speed_up_button_rect
    # cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), -1)
    # cv2.putText(frame, '+', (x1 + 10, y2 - 12), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

def summarize_usage():
    global segments, active_segment

    if active_segment is not None:
        segments.append((active_segment[0], video_frame_count, active_segment[1]))

def show_summary_screen():
    total_frames = video_frame_count
    green_frames = sum((end - start) for start, end, color in segments if color == (0, 255, 0))
    red_frames = sum((end - start) for start, end, color in segments if color == (0, 0, 255))

    green_percent = (green_frames / total_frames) * 100
    red_percent = (red_frames / total_frames) * 100

    width, height = 600, 400
    summary_img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Title
    cv2.putText(summary_img, "SESSION SUMMARY", (width // 2 - 170, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (50, 50, 50), 3)

    # Green Label + Bar
    cv2.putText(summary_img, f"Green ({green_percent:.1f}%)", (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.rectangle(summary_img, (50, 170), (50 + int(green_percent * 4), 200), (0, 255, 0), -1)

    # Red Label + Bar
    cv2.putText(summary_img, f"Red   ({red_percent:.1f}%)", (50, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.rectangle(summary_img, (50, 270), (50 + int(red_percent * 4), 300), (0, 0, 255), -1)

    # Legend Info (Optional)
    cv2.putText(summary_img, "Press any key to close", (width // 2 - 120, height - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

    cv2.imshow("Summary", summary_img)
    cv2.waitKey(0)


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

def click_event(event, x, y, flags, param):
    global paused, active_segment, segments, playback_speed
    current_frame = param['frame_number']

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    if play_button_rect[0] <= x <= play_button_rect[2] and play_button_rect[1] <= y <= play_button_rect[3]:
        paused = not paused
        if not paused:
            position = current_frame / video_fps
            pygame.mixer.music.stop()  # force fresh playback
            pygame.mixer.music.play(start=position)
        else:
            pygame.mixer.music.pause()
        return

    if green_button_rect[0] <= x <= green_button_rect[2] and green_button_rect[1] <= y <= green_button_rect[3]:
        if active_segment is None:
            active_segment = (current_frame, (0, 255, 0))
        else:
            segments.append((active_segment[0], current_frame, active_segment[1]))
            active_segment = (current_frame, (0, 255, 0))
        return

    if red_button_rect[0] <= x <= red_button_rect[2] and red_button_rect[1] <= y <= red_button_rect[3]:
        if active_segment is None:
            active_segment = (current_frame, (0, 0, 255))
        else:
            segments.append((active_segment[0], current_frame, active_segment[1]))
            active_segment = (current_frame, (0, 0, 255))
        return

    # if speed_down_button_rect[0] <= x <= speed_down_button_rect[2] and speed_down_button_rect[1] <= y <= speed_down_button_rect[3]:
    #     playback_speed = max(0.25, playback_speed - 0.25)
    #     return
    #
    # if speed_up_button_rect[0] <= x <= speed_up_button_rect[2] and speed_up_button_rect[1] <= y <= speed_up_button_rect[3]:
    #     playback_speed = min(4.0, playback_speed + 0.25)
    #     return

def play_video(path):
    global paused, video_fps, video_frame_count

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {path}")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    cv2.namedWindow("Video Player")
    frame_number = 0

    ret, frame = cap.read()
    while ret:
        if not paused:
            ret, frame = cap.read()
            frame_number += 1
            if not ret:
                break

        display_frame = frame.copy()
        draw_toggle_button(display_frame, paused)
        draw_buttons(display_frame)
        draw_progress_bar(display_frame, frame_number)

        cv2.setMouseCallback("Video Player", click_event, param={'frame_number': frame_number})
        green_time, red_time = calculate_color_durations(frame_number)

        cv2.putText(display_frame, f"Green Time: {green_time:.1f}s", (20, frame.shape[0] - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
        cv2.putText(display_frame, f"Red Time: {red_time:.1f}s", (250, frame.shape[0] - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)

        # cv2.putText(display_frame, f"Speed: {playback_speed:.2f}x", (display_frame.shape[1] - 160, 30),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Video Player", display_frame)

        delay = max(1, int(1000 / video_fps))
        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    summarize_usage()
    show_summary_screen()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = r".\\hyperFocus\\assets\\How to Speak So That People Want to Listen _ Julian Treasure _ TED_short.mp4"
    audio_path = r".\\hyperFocus\\assets\\audio.mp3"

    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)

    play_video(video_path)