import cv2
import time
import threading
import numpy as np
import tkinter as tk

from src.app.document import Invoice
from PIL import Image, ImageTk


fps = 25
frame_duration = 1.0 / fps


class ScanApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.running = True
        self.capture = cv2.VideoCapture(0)
        self.invoice = Invoice()

    def compose(self):
        self.root.title("Scan App")

        self.label = tk.Label(self.root)
        self.label.pack()

        self.capture_btn = tk.Button(
            self.root, text="📸 Capture Invoice", command=self.capture_invoice
        )
        self.capture_btn.pack(pady=10)

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1980)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    def show_frame(self):
        start_time = time.time()
        ret, frame = self.capture.read()
        if ret:
            h, w, _ = frame.shape
            box_w, box_h = int(w * 0.70), int(h * 0.8)
            start_x = (w - box_w) // 2
            start_y = (h - box_h) // 2
            end_x = start_x + box_w
            end_y = start_y + box_h

            # save a complete frame
            self.image = frame

            copy = frame.copy()
            cv2.rectangle(copy, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
            rgb = cv2.cvtColor(copy, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # keep the image in memory
            self.label.image = imgtk
            self.label.configure(image=imgtk)

        elapsed = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed)
        self.root.after(int(sleep_time * 1000), self.show_frame)

    def capture_invoice(self):
        if hasattr(self, "image"):
            final = self.invoice.process(self.image)
            cv2.imwrite("invoice.jpeg", final)


def main():
    root = tk.Tk()
    app = ScanApp(root)
    app.compose()
    app.show_frame()
    root.mainloop()
