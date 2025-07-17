import ctypes
import os
import sys
import threading
import time
import requests
import darkdetect
from tkinter import Tk, Label
from PIL import Image, ImageTk
from idlelib.tooltip import Hovertip
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


class Application:
    def __init__(self):
        self.stop_program = False
        self.state = 0
        self.last_ip = None

        self.root = Tk()
        self.root.overrideredirect(True)

        self.root.title("MyIP Widget")
        self.root.iconbitmap(f"{IMG_DIR}\\icon.ico")

        self.detect_theme()

        self.lab1 = Label(self.root, bg=self.bg_color)
        self.lab1.bind("<Button-3>", self.hide_window)
        self.lab2 = Label(self.root, bd=0, bg=self.bg_color, fg=self.fg_color, highlightthickness=0, borderwidth=0)
        self.lab3 = Label(self.root, bd=0, bg=self.bg_color, fg=self.fg_color, highlightthickness=0, borderwidth=0)

        self.lab1.grid(row=1, column=1)
        self.lab2.grid(row=2, column=1)
        self.lab3.grid(row=3, column=1)

        Hovertip(self.lab1, 'right click to close')

        self.icon = Icon("ping")
        self.icon.icon = Image.open(PIRATE_FLAG)
        self.icon.run_detached()
        self.icon.menu = (
            MenuItem('Quit', lambda: self.quit_window()),
            MenuItem('Show', self.show_window)
        )
        # self.root.wm_attributes("-transparentcolor", self.bg_color)
        self.root.attributes("-alpha", 0.7)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=self.bg_color)
        self.root.bind("<B1-Motion>", self.move_window)

        self.thread2 = threading.Thread(target=self.update_data)
        self.thread2.start()

    def detect_theme(self):
        theme = darkdetect.theme()

        if theme == "Dark":
            self.bg_color = "black"
            self.fg_color = "white"
        else:
            self.bg_color = "white"
            self.fg_color = "black"

    def move_window(self, event):
        self.root.geometry(f'+{event.x_root}+{event.y_root}')

    def quit_window(self):
        self.stop_program = True
        self.icon.icon = None
        self.icon.title = None
        self.icon.stop()
        self.root.destroy()

    def show_window(self):
        self.root.after(0, self.root.deiconify())

    def hide_window(self, event):
        self.root.withdraw()

    def find_ip(self):
        try:
            req = requests.get("http://ip-api.com/json/", timeout=REQUEST_TIMEOUT)
            if req.status_code == 200:
                ip_data = req.json()
                return ip_data
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def update_data(self):
        while not self.stop_program:
            ip = self.find_ip()
            if ip:
                ip_address = ip["query"]
                if ip_address != self.last_ip:
                    self.last_ip = ip_address
                    self.lab1.image = ImageTk.PhotoImage(image=Image.open(f"{IMG_DIR}\\flags\\{ip['countryCode']}.png"))
                    self.lab1.config(image=self.lab1.image)
                    self.lab2.config(text=ip["country"])
                    self.lab3.config(text=ip_address)
                    self.icon.icon = Image.open(f"{IMG_DIR}\\flags\\{ip['countryCode']}.png")
                    self.icon.title = ip_address
            else:
                self.last_ip = None
                self.lab1.image = ImageTk.PhotoImage(file=PIRATE_FLAG)
                self.lab1.config(image=self.lab1.image)
                self.lab2.config(text="No Internet")
                self.lab3.config(text="")
                self.icon.icon = Image.open(PIRATE_FLAG)
            time.sleep(5)

    def run(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # if your windows version >= 8.1
        except:
            ctypes.windll.user32.SetProcessDPIAware()  # win 8.0 or less

        self.root.mainloop()
        os._exit(1)


class Application2:
    def __init__(self):
        # Settings
        self.start_minimized = False

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

        Hovertip(self.lab1, 'Right click to hide')

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

        self.ipApiResolver = IpApiResolver(REQUEST_TIMEOUT)
        self.myIpResolver = MyIpResolver(REQUEST_TIMEOUT)

        self.lab1.image = ImageTk.PhotoImage(file=PIRATE_FLAG)
        self.lab1.config(image=self.lab1.image)
        self.lab2.config(text="No connection")
        self.lab3.config(text="...")
        self.icon.icon = Image.open(PIRATE_FLAG)

        self.x_last = 0
        self.y_last = 0

    def on_left_button_press(self, event):
        self.x_last = event.x_root
        self.y_last = event.y_root

        # ip_info = self.ipApiResolver.get()
        # print(ip_info)
        # ip_info = self.myIpResolver.get()
        # print(ip_info)

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
        # self.icon.menu = (
        #     MenuItem('Hide', self.hide_window),
        #     MenuItem('Quit', self.quit_window)
        # )
        self.icon.update_menu()

        self.root.deiconify()

    def hide_window(self, event):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem('Show', self.show_window) if str(item) == "Hide" else item)
        self.icon.menu = menu_items
        # self.icon.menu = (
        #     MenuItem('Show', self.show_window),
        #     MenuItem('Quit', self.quit_window)
        # )
        self.icon.update_menu()

        self.root.withdraw()

    def quit_window(self, event):
        self.icon.icon = None
        self.icon.title = None
        self.icon.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        os._exit(1)


if __name__ == '__main__':
    Application().run()
    # Application2().run()
