import os
import random
import sys
import threading
import winreg
from tkinter import Tk, Label

from PIL import Image, ImageTk
from distutils.util import strtobool
from dotenv import load_dotenv
from pystray import Icon, Menu, MenuItem

from models.ip_info import IpInfo
from resolvers.ip_api import IpApiResolver
from resolvers.myip import MyIpResolver


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):  # If running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


IMAGES_DIR = resource_path("assets/images")
PIRATE_FLAG = f"{IMAGES_DIR}/pirate_flag.png"
EXPECTED_FLAG = f"{IMAGES_DIR}/expected_flag.png"
UNEXPECTED_FLAG = f"{IMAGES_DIR}/unexpected_flag.png"
APP_NAME = "myip-tray"
RUNTIME_FILE = ".run"


class Application:
    def __init__(self):
        load_dotenv()

        # Docs
        # Colors - https://www.plus2net.com/python/tkinter-colors.php

        # Settings
        self.start_minimized = strtobool(os.getenv("START_MINIMIZED", "false"))
        self.run_on_boot = strtobool(os.getenv("RUN_ON_BOOT", "false"))
        self.on_top = strtobool(os.getenv("ON_TOP", "true"))
        self.position_absolute = strtobool(os.getenv("POSITION_ABSOLUTE", "false"))
        self.position_x = int(os.getenv("POSITION_X", "0"))  # 1800
        self.position_y = int(os.getenv("POSITION_Y", "0"))  # 890
        self.background_color = os.getenv("BACKGROUND_COLOR", "aliceblue")
        self.foreground_color = os.getenv("FOREGROUND_COLOR", "black")
        self.font_family = os.getenv("FONT_FAMILY", "Arial")
        self.font_size = int(os.getenv("FONT_SIZE", "11"))
        self.refresh_interval_seconds = int(os.getenv("REFRESH_INTERVAL_SECONDS", "60"))
        self.refresh_timeout_seconds = int(os.getenv("REFRESH_TIMEOUT_SECONDS", "10"))
        self.expected_ip = os.getenv("EXPECTED_IP", "").strip()

        # Runtime
        self.x_last = 0
        self.y_last = 0
        self.last_ip = None
        self.resolvers = [
            IpApiResolver(self.refresh_timeout_seconds),
            MyIpResolver(self.refresh_timeout_seconds)
        ]

        self.manage_autostart()

        self.root = Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", self.on_top)
        self.root.configure(bg=self.background_color)

        self.root.bind("<ButtonPress-1>", self.on_left_button_press)
        self.root.bind('<ButtonRelease-1>', self.on_left_button_release)
        self.root.bind("<B1-Motion>", self.move_window)
        self.root.bind("<Button-2>", self.quit_window)

        self.lab1 = Label(self.root, bd=0, borderwidth=0, bg=self.background_color)
        self.lab2 = Label(self.root, bd=0, borderwidth=0,
                          bg=self.background_color, fg=self.foreground_color)
        self.lab3 = Label(self.root, bd=0, borderwidth=0,
                          bg=self.background_color, fg=self.foreground_color)

        self.lab1.pack(expand=True)
        self.lab2.pack(expand=True)
        self.lab3.pack(expand=True)

        self.lab1.bind("<Button-3>", self.hide_window)

        self.icon = Icon(APP_NAME)
        self.icon.icon = Image.open(PIRATE_FLAG)
        self.icon.menu = Menu(
            MenuItem("Hide", self.hide_window, default=True),
            MenuItem("Quit", self.quit_window)
        )
        self.icon.run_detached()

        self.render_window(IpInfo.unknown())
        self.relocate_window()

        if self.start_minimized:
            self.hide_window(None)

        self.event = threading.Event()
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()

    def manage_autostart(self):
        if sys.platform == "win32":
            self.manage_windows_startup()
        elif sys.platform == "linux":
            self.manage_linux_startup()

    def manage_windows_startup(self):
        file = sys.executable if getattr(sys, 'frozen', False) else __file__
        filepath = os.path.realpath(file)
        filepath = filepath if getattr(sys, 'frozen', False) else "python " + filepath
        key_name = winreg.HKEY_CURRENT_USER
        key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key_name, key_value, 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                if self.run_on_boot:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, filepath)
                else:
                    winreg.DeleteValue(key, APP_NAME)
            except WindowsError as e:
                print("Registry error:", e)
            finally:
                winreg.CloseKey(key)

    def manage_linux_startup(self):
        file = sys.executable if getattr(sys, 'frozen', False) else __file__
        filepath = os.path.realpath(file)
        filepath = filepath if getattr(sys, 'frozen', False) else "python " + filepath
        directory = os.path.join(os.path.expanduser("~"), ".config/autostart")
        config_path = os.path.join(directory, APP_NAME + ".desktop")
        if self.run_on_boot:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.path.isfile(config_path):
                with open(config_path, "w") as f:
                    f.write("""[Desktop Entry]
Type=Application
StartupNotify=false
Terminal=false
Name=""" + APP_NAME + """
Exec=""" + filepath)
        else:
            if os.path.isfile(config_path):
                os.remove(config_path)

    def on_left_button_press(self, event):
        self.x_last = event.x_root
        self.y_last = event.y_root

    def on_left_button_release(self, event):
        x_delta = event.x_root - self.x_last
        y_delta = event.y_root - self.y_last
        x = self.root.winfo_x() + x_delta
        y = self.root.winfo_y() + y_delta
        with open(RUNTIME_FILE, "w") as file:
            file.write(str(x) + " " + str(y))

    def render_window(self, ip_info):
        # ip_info.ip_address = "172.20.10.50"
        # ip_info.country_code = "AU"
        if ip_info.is_unknown():
            self.last_ip = None
            flag_image = Image.open(PIRATE_FLAG)

            self.icon.icon = flag_image
            self.icon.title = "Unknown"

            self.lab1.image = ImageTk.PhotoImage(image=flag_image)
            self.lab1.config(image=self.lab1.image)
            self.lab2.config(text="Unknown", font=(self.font_family, self.font_size))
            self.lab3.config(text="000.000.000.000", font=(self.font_family, self.font_size))
        else:
            if ip_info.ip_address != self.last_ip:
                self.last_ip = ip_info.ip_address
                flag_image = Image.open(f"{IMAGES_DIR}\\flags\\{ip_info.country_code}.png")
                if len(self.expected_ip) > 0:
                    if self.expected_ip == ip_info.ip_address:
                        flag_image = Image.open(EXPECTED_FLAG)
                    else:
                        flag_image = Image.open(UNEXPECTED_FLAG)

                self.icon.icon = flag_image
                self.icon.title = ip_info.ip_address

                self.lab1.image = ImageTk.PhotoImage(image=flag_image)
                self.lab1.config(image=self.lab1.image)
                self.lab2.config(text=ip_info.country_code, font=(self.font_family, self.font_size))
                self.lab3.config(text=" " + ip_info.ip_address + " ", font=(self.font_family, self.font_size))

    def relocate_window(self):
        x = self.position_x
        y = self.position_y
        if not self.position_absolute and os.path.isfile(RUNTIME_FILE):
            with open(RUNTIME_FILE, "r") as file:
                items = file.read().split(" ")
                if len(items) == 2:
                    x = int(items[0])
                    y = int(items[1])

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def move_window(self, event):
        x_delta = event.x_root - self.x_last
        y_delta = event.y_root - self.y_last
        x = self.root.winfo_x() + x_delta
        y = self.root.winfo_y() + y_delta
        self.root.geometry(f"+{x}+{y}")
        self.x_last = event.x_root
        self.y_last = event.y_root

    def show_window(self, event):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem("Hide", self.hide_window, default=True) if str(item) == "Show" else item)
        self.icon.menu = Menu(*menu_items)
        self.icon.update_menu()

        self.root.deiconify()

    def hide_window(self, event):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem("Show", self.show_window, default=True) if str(item) == "Hide" else item)
        self.icon.menu = Menu(*menu_items)
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
            self.render_window(self.get_ip_info())
            self.event.wait(self.refresh_interval_seconds)

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
        return IpInfo.unknown()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Interrupted by user")
        sys.exit()


if __name__ == "__main__":
    Application().run()
