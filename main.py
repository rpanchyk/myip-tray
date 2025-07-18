import os
import sys
import threading
import random
from tkinter import Tk, Label
from PIL import Image, ImageTk
from pystray import Icon, MenuItem
from resolvers.ip_api import IpApiResolver
from resolvers.myip import MyIpResolver
from models.ip_info import IpInfo


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):  # If running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


ICONS_DIR = resource_path("assets/icons")
IMAGES_DIR = resource_path("assets/images")
PIRATE_FLAG = f"{IMAGES_DIR}/pirate_flag.png"


class Application:
    def __init__(self):
        # Settings
        self.start_minimized = False
        self.on_top = True
        self.position_x = 1810
        self.position_y = 890
        self.background_color = "aliceblue"  # https://www.plus2net.com/python/tkinter-colors.php
        self.foreground_color = "black"
        self.font_family = "Arial"
        self.font_size = 11
        self.refresh_interval_seconds = 10
        self.refresh_timeout_seconds = 10

        # Runtime
        self.x_last = 0
        self.y_last = 0
        self.last_ip = None
        self.resolvers = [
            IpApiResolver(self.refresh_timeout_seconds),
            MyIpResolver(self.refresh_timeout_seconds)
        ]

        self.root = Tk()
        self.root.overrideredirect(True)
        self.root.iconbitmap(f"{ICONS_DIR}\\icon.ico")
        self.root.attributes("-topmost", self.on_top)
        self.root.configure(bg=self.background_color)

        self.root.bind("<ButtonPress-1>", self.on_left_button_press)
        self.root.bind("<B1-Motion>", self.move_window)
        self.root.bind("<Button-2>", self.quit_window)

        self.lab1 = Label(self.root, bd=0, borderwidth=0, bg=self.background_color)
        self.lab2 = Label(self.root, bd=0, borderwidth=0,
                          bg=self.background_color, fg=self.foreground_color)
        self.lab3 = Label(self.root, bd=0, borderwidth=0,
                          bg=self.background_color, fg=self.foreground_color)

        # self.lab1.grid(row=1, column=1)
        # self.lab2.grid(row=2, column=1)
        # self.lab3.grid(row=3, column=1)
        self.lab1.pack(expand=True)
        self.lab2.pack(expand=True)
        self.lab3.pack(expand=True)

        self.lab1.bind("<Button-3>", self.hide_window)

        self.icon = Icon("myip")
        self.icon.icon = Image.open(PIRATE_FLAG)
        self.icon.run_detached()
        self.icon.menu = (
            MenuItem("Show", None),
            MenuItem("Quit", self.quit_window)
        )

        self.render_window(IpInfo.unknown())
        self.relocate_window()

        if self.start_minimized:
            self.hide_window(None)
        else:
            self.show_window(None)

        self.event = threading.Event()
        self.thread = threading.Thread(target=self.update_data)
        self.thread.start()

    def on_left_button_press(self, event):
        self.x_last = event.x_root
        self.y_last = event.y_root

    def render_window(self, ip_info):
        if ip_info.is_unknown():
            self.last_ip = None
            flag_image = Image.open(PIRATE_FLAG)

            self.icon.icon = flag_image
            self.icon.title = "Unknown IP"

            self.lab1.image = ImageTk.PhotoImage(image=flag_image)
            self.lab1.config(image=self.lab1.image)
            self.lab2.config(text="Unknown IP", font=(self.font_family, self.font_size))
            self.lab3.config(text="000.000.000.000", font=(self.font_family, self.font_size))
        else:
            if ip_info.ip_address != self.last_ip:
                self.last_ip = ip_info.ip_address
                flag_image = Image.open(f"{IMAGES_DIR}\\flags\\{ip_info.country_code}.png")

                self.icon.icon = flag_image
                self.icon.title = ip_info.ip_address

                self.lab1.image = ImageTk.PhotoImage(image=flag_image)
                self.lab1.config(image=self.lab1.image)
                self.lab2.config(text=ip_info.country_code, font=(self.font_family, self.font_size))
                self.lab3.config(text=ip_info.ip_address, font=(self.font_family, self.font_size))

                # self.root.update_idletasks()
                # width = self.lab3.winfo_reqwidth() + 5
                # height = self.root.winfo_height()
                # self.root.geometry(f"{width}x{height}")

                # original_image = Image.open(f"{IMAGES_DIR}\\flags\\{ip_info.country_code}.png")
                # resized_image = original_image.resize((width - 10, original_image.height))
                # self.lab1.image = ImageTk.PhotoImage(resized_image)
                # self.lab1.config(image=self.lab1.image)

    def relocate_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = self.position_x
        y = self.position_y
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
            menu_items.append(MenuItem("Hide", self.hide_window) if str(item) == "Show" else item)
        self.icon.menu = menu_items
        self.icon.update_menu()

        self.root.deiconify()

    def hide_window(self, event):
        menu_items = []
        for item in self.icon.menu:
            menu_items.append(MenuItem("Show", self.show_window) if str(item) == "Hide" else item)
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
        os._exit(1)


if __name__ == "__main__":
    Application().run()
