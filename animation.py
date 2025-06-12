import tkinter as tk
import random

# Create transparent fullscreen window
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.0)  # fully transparent background

# Get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Overlay window with a color-key-based transparent canvas
overlay = tk.Toplevel(root)
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor", "pink")  # pink will be transparent
overlay.geometry(f"{screen_width}x{screen_height}+0+0")

# Canvas setup
canvas = tk.Canvas(overlay, width=screen_width, height=screen_height, bg='pink', highlightthickness=0)
canvas.pack()

# List of colors to pick from
colors = ['cyan', 'magenta', 'yellow', 'lime', 'orange', 'white', 'red', 'blue', 'purple']

# Create text
text = canvas.create_text(100, 100, text="FOCUS", font=('Helvetica', 32, 'bold'), fill=random.choice(colors))

# Initial position and speed
x_speed = 4
y_speed = 3
x_pos = random.randint(100, screen_width - 100)
y_pos = random.randint(100, screen_height - 100)

# Direction flags
x_dir = 1
y_dir = 1

def move_text():
    global x_pos, y_pos, x_speed, y_speed, x_dir, y_dir

    canvas.move(text, x_speed * x_dir, y_speed * y_dir)
    x_pos += x_speed * x_dir
    y_pos += y_speed * y_dir

    left, top, right, bottom = canvas.bbox(text)

    hit_wall = False

    # Bounce logic
    if right >= screen_width or left <= 0:
        x_dir *= -1
        hit_wall = True
    if bottom >= screen_height or top <= 0:
        y_dir *= -1
        hit_wall = True

    # Change color on bounce
    if hit_wall:
        canvas.itemconfig(text, fill=random.choice(colors))

    root.after(20, move_text)

# Start animation
move_text()

# Auto-close after 10 seconds (optional)
root.after(10000, lambda: (overlay.destroy(), root.destroy()))

root.mainloop()
