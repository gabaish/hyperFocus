import cv2
import numpy as np

# Global variables
paused = True
play_button_rect = (20, 20, 80, 80)
red_button_rect = (500, 460, 550, 500)
green_button_rect = (560, 460, 610, 500)

active_segment = None  # (start_frame, color)
segments = []  # List of (start_frame, end_frame, color)

video_fps = 30
video_frame_count = 1


def draw_toggle_button(frame, paused):
    x1, y1, x2, y2 = play_button_rect
    cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 50, 50), -1)
    if paused:
        pts = [(x1 + 20, y1 + 15), (x1 + 20, y2 - 15), (x2 - 15, y1 + (y2 - y1) // 2)]
        cv2.fillPoly(frame, [np.array(pts)], (0, 255, 0))
    else:
        cv2.rectangle(frame, (x1 + 18, y1 + 15), (x1 + 26, y2 - 15), (0, 0, 255), -1)
        cv2.rectangle(frame, (x1 + 34, y1 + 15), (x1 + 42, y2 - 15), (0, 0, 255), -1)


def draw_buttons(frame):
    cv2.rectangle(frame, red_button_rect[:2], red_button_rect[2:], (0, 0, 255), -1)
    cv2.rectangle(frame, green_button_rect[:2], green_button_rect[2:], (0, 255, 0), -1)


def draw_progress_bar(frame, current_frame):
    bar_top = 440
    bar_bottom = 450
    width = frame.shape[1]

    # Background
    cv2.rectangle(frame, (0, bar_top), (width, bar_bottom), (200, 200, 200), -1)

    # Colored segments
    for start, end, color in segments:
        x1 = int((start / video_frame_count) * width)
        x2 = int((end / video_frame_count) * width)
        cv2.rectangle(frame, (x1, bar_top), (x2, bar_bottom), color, -1)

    # Ongoing segment
    if active_segment is not None:
        start, color = active_segment
        x1 = int((start / video_frame_count) * width)
        x2 = int((current_frame / video_frame_count) * width)
        cv2.rectangle(frame, (x1, bar_top), (x2, bar_bottom), color, -1)

    # Current position marker
    cur_x = int((current_frame / video_frame_count) * width)
    cv2.line(frame, (cur_x, bar_top - 5), (cur_x, bar_bottom + 5), (0, 0, 0), 2)


def click_event(event, x, y, flags, param):
    global paused, active_segment, segments
    current_frame = param['frame_number']

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # Play/Pause button
    if play_button_rect[0] <= x <= play_button_rect[2] and play_button_rect[1] <= y <= play_button_rect[3]:
        paused = not paused
        return

    # Green button
    if green_button_rect[0] <= x <= green_button_rect[2] and green_button_rect[1] <= y <= green_button_rect[3]:
        if active_segment is None:
            active_segment = (current_frame, (0, 255, 0))  # Start new green segment
        else:
            # Close current and start green
            segments.append((active_segment[0], current_frame, active_segment[1]))
            active_segment = (current_frame, (0, 255, 0))
        return

    # Red button
    if red_button_rect[0] <= x <= red_button_rect[2] and red_button_rect[1] <= y <= red_button_rect[3]:
        if active_segment is None:
            active_segment = (current_frame, (0, 0, 255))  # Start red
        else:
            segments.append((active_segment[0], current_frame, active_segment[1]))
            active_segment = (current_frame, (0, 0, 255))
        return


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
        cv2.imshow("Video Player", display_frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    video_path = r"C:\Users\gomea\Documents\GitHub\Hackathon2025\hyperFocus\assets\How to Speak So That People Want to Listen _ Julian Treasure _ TED.mp4"
    play_video(video_path)
