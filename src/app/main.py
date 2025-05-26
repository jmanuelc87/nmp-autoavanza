import src.app.app as application
import tkinter as tk


def main():
    root = tk.Tk()
    app = application.ScanApp(root)
    app.compose()
    app.show_frame()
    root.mainloop()