# main.py
from tkinter import Tk
from interfaz import EmotionDashboard

if __name__ == "__main__":
    root = Tk()
    app = EmotionDashboard(root)
    root.mainloop()
