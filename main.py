import os
import sys
import threading
import random
import darkdetect
from tkinter import Tk, Label
from PIL import Image, ImageTk
from pystray import Icon, MenuItem
from resolvers.ip_api import IpApiResolver
from resolvers.myip import MyIpResolver
from models.ip_info import IpInfo


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):  # If running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


REQUEST_TIMEOUT = 5
IMG_DIR = resource_path("assets/images")
PIRATE_FLAG = f"{IMG_DIR}/pirate_flag.png"


class Application2:
    def __init__(self):
        # Settings
        self.start_minimized = False

        self.last_ip = None

        self.root = Tk()
        self.root.overrideredirect(True)
        # self.root.geometry("200x200")

        self.root.iconbitmap(f"{IMG_DIR}\\icon.ico")

        if darkdetect.theme() == "Dark":
            self.bg_color = "black"
            self.fg_color = "white"
        else:
            self.bg_color = "white"
            self.fg_color = "black"

        self.lab1 = Label(self.root, bg=self.bg_color)
        self.lab2 = Label(self.root, bd=0, bg=self.bg_color, fg=self.fg_color, highlightthickness=0, borderwidth=0)
        self.lab3 = Label(self.root, bd=0, bg=self.bg_color, fg=self.fg_color, highlightthickness=0, borderwidth=0)

        self.lab1.grid(row=1, column=1)
        self.lab2.grid(row=2, column=1)
        self.lab3.grid(row=3, column=1)

        self.lab1.bind("<Button-3>", self.hide_window)

        self.icon = Icon("ping")
        self.icon.icon = Image.open(PIRATE_FLAG)
        self.icon.run_detached()

        if self.start_minimized:
            self.icon.menu = (
                MenuItem('Show', self.show_window),
                MenuItem('Quit', self.quit_window)
            )
        else:
            self.icon.menu = (
                MenuItem('Hide', self.hide_window),
                MenuItem('Quit', self.quit_window)
            )
        self.icon.update_menu()

        self.root.attributes('-topmost', True)
        # self.root.attributes("-alpha", 0.7)
        self.root.configure(bg=self.bg_color)

        self.root.bind("<ButtonPress-1>", self.on_left_button_press)
        self.root.bind("<B1-Motion>", self.move_window)
        self.root.bind("<Button-2>", self.quit_window)

        if self.start_minimized:
            self.hide_window(None)

        self.resolvers = [IpApiResolver(REQUEST_TIMEOUT), MyIpResolver(REQUEST_TIMEOUT)]

        self.lab1.image = ImageTk.PhotoImage(file=PIRATE_FLAG)
        self.lab1.config(image=self.lab1.image)
        self.lab2.config(text="No connection")
        self.lab3.config(text="...")
        self.icon.icon = Image.open(PIRATE_FLAG)

        self.x_last = 0
        self.y_last = 0

        self.event = threading.Event()
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()

    def on_left_button_press(self, event):
        self.x_last = event.x_root
        self.y_last = event.y_root

    def move_window(self, event):
        x_delta = event.x_root - self.x_last
        y_delta = event.y_root - self.y_last
        x = self.root.winfo_x() + x_delta
        y = self.root.winfo_y() + y_delta
        self.root.geometry(f"+{x}+{y}")
        self.x_last = event.x_root
        self.y_last = event.y_root

    def show_window(self):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem('Hide', self.hide_window) if str(item) == "Show" else item)
        self.icon.menu = menu_items
        self.icon.update_menu()

        self.root.deiconify()

    def hide_window(self, event):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem('Show', self.show_window) if str(item) == "Hide" else item)
        self.icon.menu = menu_items
        self.icon.update_menu()

        self.root.withdraw()

    def quit_window(self, event):
        self.event.set()
        self.thread.join()

        self.icon.icon = None
        self.icon.title = None
        self.icon.stop()

        self.root.destroy()

    def update_data(self):
        while not self.event.is_set():
            ip_info = self.get_ip_info()
            if not ip_info.is_unknown():
                if ip_info.ip_address != self.last_ip:
                    self.last_ip = ip_info.ip_address
                    self.lab1.image = ImageTk.PhotoImage(
                        image=Image.open(f"{IMG_DIR}\\flags\\{ip_info.country_code}.png"))
                    self.lab1.config(image=self.lab1.image)
                    self.lab2.config(text=ip_info.country_code)
                    self.lab3.config(text=ip_info.ip_address)
                    self.icon.icon = Image.open(f"{IMG_DIR}\\flags\\{ip_info.country_code}.png")
                    self.icon.title = ip_info.ip_address
            else:
                self.last_ip = None
                self.lab1.image = ImageTk.PhotoImage(file=PIRATE_FLAG)
                self.lab1.config(image=self.lab1.image)
                self.lab2.config(text="No connection")
                self.lab3.config(text="...")
                self.icon.icon = Image.open(PIRATE_FLAG)

            self.event.wait(5)

    def get_ip_info(self):
        resolvers_idx = [i for i in range(len(self.resolvers))]
        while len(resolvers_idx) > 0:
            idx = random.randint(0, len(resolvers_idx) - 1)
            resolver = self.resolvers[idx]
            ip_info = resolver.get()
            if ip_info.is_unknown():
                resolvers_idx.remove(idx)
            else:
                return ip_info
        return IpInfo(None, None)

    def run(self):
        self.root.mainloop()
        os._exit(1)


if __name__ == '__main__':
    Application2().run()
