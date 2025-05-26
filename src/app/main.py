import src.app.app as app
import tkinter as tk


def main():
    root = tk.Tk()
    app = app.ScanApp(root)
    app.compose()
    app.show_frame()
    root.mainloop()