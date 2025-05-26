import src.app.scan as scan
import tkinter as tk


def main():
    root = tk.Tk()
    app = scan.ScanApp(root)
    app.compose()
    app.show_frame()
    root.mainloop()