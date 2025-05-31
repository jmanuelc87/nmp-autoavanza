import cv2
import time
import threading
import numpy as np
import tkinter as tk

from autoavanza.document import Scanner
from PIL import Image, ImageTk


fps = 25
frame_duration = 1.0 / fps


class ScanApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.running = True
        self.capture = cv2.VideoCapture(0)
        self.scanner = Scanner()
        self.resize_factor = 1280 / 1980

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

    def apply_overlay(self, img, rect_pt1, rect_pt2):
        # Create a dark overlay
        overlay = img.copy()
        overlay[:] = (0, 0, 0)  # Dark color
        alpha = 0.15  # Overlay transparency

        # Draw a white rectangle to cover the area inside the dashed rectangle
        cv2.rectangle(overlay, rect_pt1, rect_pt2, (255, 255, 255), cv2.FILLED)

        # Blend the overlay with the original image
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        return img

    def show_frame(self):
        start_time = time.time()
        ret, self.frame = self.capture.read()
        if ret:
            h, w, _ = self.frame.shape
            box_w, box_h = int(w * 0.7), int(h * 0.7)
            start_x = (w - box_w) // 2
            start_y = (h - box_h) // 2
            end_x = start_x + box_w
            end_y = start_y + box_h

            frame = self.apply_overlay(self.frame, (start_x, start_y), (end_x, end_y))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, None, fx=self.resize_factor, fy=self.resize_factor, interpolation=cv2.INTER_LINEAR)

            img = Image.fromarray(resized)
            imgtk = ImageTk.PhotoImage(image=img)

            # keep the image in memory
            self.label.image = imgtk
            self.label.configure(image=imgtk)

        elapsed = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed)
        self.root.after(int(sleep_time * 1000), self.show_frame)

    def capture_invoice(self):
        if hasattr(self, "frame"):

            def capture():
                final = self.scanner.get_document_from(self.frame)
                # For now we are writing it to disk, but can be sent to a service
                cv2.imwrite("invoice.jpeg", final)
                print("saved correctly...")

            t = threading.Thread(target=capture)
            print("started processing document...")
            t.start()


def main():
    root = tk.Tk()
    app = ScanApp(root)
    app.compose()
    app.show_frame()
    root.mainloop()
