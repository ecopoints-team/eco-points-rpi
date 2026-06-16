import tkinter as tk
from tkinter import font
import time

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class EcoPointsKiosk(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("EcoPoints Simulation [Graphic Design Mode]")
        self.geometry("800x550")
        
        # --- THEME COLORS ---
        self.bg_color = "#F3F4E0" 
        self.txt_primary = "#000000" 
        self.txt_eco   = "#16502d"  
        self.txt_pts   = "#e25822"  
        self.btn_bg    = "#ffffff" 
        self.btn_fg    = "#000000"   
        self.err_color = "#c0392b"  
        
        self.configure(bg=self.bg_color)

        self.bind("<Escape>", lambda e: self.destroy())

        # --- SENSOR VARIABLES ---
        self.total_points = 0
        self.sensor_storage_full = tk.BooleanVar(value=False)
        self.sensor_door_closed = tk.BooleanVar(value=True)
        self.sensor_item_valid = tk.BooleanVar(value=True)

        # --- FONTS ---
        self.header_font = font.Font(family="Arial", size=28, weight="bold")
        self.sub_font = font.Font(family="Arial", size=14)
        self.button_font = font.Font(family="Arial", size=11, weight="bold")
        
        self.font_welcome = font.Font(family="Arial", size=26, weight="bold")
        self.font_eco_main = font.Font(family="Arial", size=48, weight="bold")

        # --- MAIN CONTAINER ---
        self.container = tk.Frame(self, bg=self.bg_color)
        self.container.pack(side="top", fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # --- INITIALIZE SCREENS ---
        self.frames = {}
        for F in (ScreenWelcome, ScreenStorageFull, ScreenQR, ScreenInsert,
                  ScreenDoorAlert, ScreenVerifying, ScreenInvalid, ScreenSuccess, ScreenEnd):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ScreenWelcome")
        self.create_debug_panel()

    def create_debug_panel(self):
        debug_frame = tk.LabelFrame(self, text=" SENSOR SIMULATION ",
                                    bg="#333", fg="#0f0", font=("Arial", 8, "bold"), bd=1)
        debug_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        style = {"bg": "#333", "fg": "white", "selectcolor": "#555", 
                 "activebackground": "#333", "activeforeground": "white", "font": ("Arial", 10)}

        tk.Checkbutton(debug_frame, text="Storage Full", variable=self.sensor_storage_full, **style).pack(side="left", padx=10)
        tk.Checkbutton(debug_frame, text="Door Closed", variable=self.sensor_door_closed, **style).pack(side="left", padx=10)
        tk.Checkbutton(debug_frame, text="Valid Item", variable=self.sensor_item_valid, **style).pack(side="left", padx=10)

        tk.Button(debug_frame, text="EXIT APP", command=self.destroy, bg="#c0392b", fg="white",
                  font=("Arial", 9, "bold")).pack(side="right", padx=10, pady=2)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

# --- BASE SCREEN ---
class BaseScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bg=controller.bg_color)
        self.canvas.pack(fill="both", expand=True)

        try:
           self.bg_img = tk.PhotoImage(file="bg.png")
           self.canvas.create_image(400, 240, image=self.bg_img, anchor="center")
        except:
            pass 

        self.centered_frame = tk.Frame(self.canvas, bg=controller.bg_color)
        
        self.canvas.create_window(400, 240, window=self.centered_frame, anchor="center")

# --- SCREENS ---

class ScreenWelcome(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        # LOGO 
        try:
            self.logo_orig = tk.PhotoImage(file="logo.png")
            if self.logo_orig.width() > 100:
                self.logo_img = self.logo_orig.subsample(3, 3)
            else:
                self.logo_img = self.logo_orig
            self.canvas.create_image(750, 50, image=self.logo_img, anchor="center")
        except:
            pass

        # CUSTOM TEXT ON CANVAS
        self.canvas.create_text(400, 140, text="Welcome to", fill="black", font=controller.font_welcome)
        self.canvas.create_text(340, 220, text="Eco", fill=controller.txt_eco, font=controller.font_eco_main, anchor="e")
        self.canvas.create_text(340, 220, text="Points", fill=controller.txt_pts, font=controller.font_eco_main, anchor="w")

        # BUTTON
        btn = tk.Button(self, text="START TRANSACTION", bg="white", fg="black", 
                        font=controller.button_font, relief="raised", padx=20, pady=10,
                        activebackground="#eee", command=self.check_start)
        self.canvas.create_window(400, 350, window=btn)

    def check_start(self):
        if self.controller.sensor_storage_full.get():
            self.controller.show_frame("ScreenStorageFull")
        else:
            self.controller.show_frame("ScreenQR")


class ScreenStorageFull(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="System Full", bg=controller.bg_color, fg=controller.err_color, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(self.centered_frame, text="Sorry, machine is currently full.\nPlease try again later.",
                 bg=controller.bg_color, fg="black", font=controller.sub_font).pack(pady=20)
        tk.Button(self.centered_frame, text="RETURN HOME", bg="#555", fg="white", font=controller.button_font,
                  command=lambda: controller.show_frame("ScreenWelcome")).pack(pady=30)

class ScreenQR(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Login Required", bg=controller.bg_color, fg="black", 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(self.centered_frame, text="Please scan your QR Code", bg=controller.bg_color, fg="#555", 
                 font=controller.sub_font).pack(pady=5)

        # Simulation Input Box
        frame_input = tk.Frame(self.centered_frame, bg=controller.bg_color)
        frame_input.pack(pady=10)
        tk.Label(frame_input, text="Simulate Scan:", fg="black", bg=controller.bg_color).pack()
        self.scanner_input = tk.Entry(frame_input, font=("Arial", 12))
        self.scanner_input.pack(pady=5)
        self.scanner_input.bind("<Return>", self.process_scan)

        self.status_label = tk.Label(self.centered_frame, text="Waiting for scanner...", bg=controller.bg_color, fg="#555", font=("Arial", 12))
        self.status_label.pack(pady=20)
        
        tk.Button(self.centered_frame, text="[Simulate Enter Key]", bg="#ddd", fg="black", borderwidth=1, 
                  command=lambda: self.process_scan(None)).pack(pady=5)

    def on_show(self):
        self.status_label.config(text="Waiting for scanner...", fg="#555")
        self.scanner_input.delete(0, tk.END)
        self.scanner_input.focus_set() 

    def process_scan(self, event):
        data = self.scanner_input.get()
        if data:
            self.status_label.config(text=f"User '{data}' Accepted!", fg=self.controller.txt_eco)
            self.after(1000, lambda: self.controller.show_frame("ScreenInsert"))
        else:
            self.status_label.config(text="Please type something.", fg=self.controller.err_color)

class ScreenInsert(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Ready to Accept", bg=controller.bg_color, fg="black", 
                 font=controller.header_font).pack(pady=(0, 10))
        tk.Label(self.centered_frame, text="Insert PET bottles into the chute.", bg=controller.bg_color, fg="#555",
                 font=controller.sub_font).pack(pady=5)

        try:
            self.original_image = tk.PhotoImage(file="PET_symbol.png")
            tk.Label(self.centered_frame, image=self.original_image, bg=controller.bg_color).pack(pady=20)
        except Exception as e:
            tk.Label(self.centered_frame, text="[pet_symbol.png NOT FOUND]", bg=controller.bg_color, fg="red").pack(pady=40)

        tk.Button(self.centered_frame, text="SIMULATE INSERTION", bg=controller.txt_pts, fg="white", font=controller.button_font,
                  padx=20, command=self.attempt_insert).pack(pady=10)

    def attempt_insert(self):
        if not self.controller.sensor_door_closed.get():
            self.controller.show_frame("ScreenDoorAlert")
        else:
            self.controller.show_frame("ScreenVerifying")

class ScreenDoorAlert(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="⚠️ Door Open", bg=controller.bg_color, fg=controller.txt_pts, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(self.centered_frame, text="Please close the door to proceed.", bg=controller.bg_color, fg="black",
                 font=controller.sub_font).pack(pady=20)
        tk.Button(self.centered_frame, text="CHECK DOOR STATUS", bg="#555", fg="white", font=controller.button_font,
                  command=self.check_door).pack(pady=30)

    def check_door(self):
        if self.controller.sensor_door_closed.get():
            self.controller.show_frame("ScreenInsert")

class ScreenVerifying(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Verifying...", bg=controller.bg_color, fg="black", 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(self.centered_frame, text="Analyzing object...", bg=controller.bg_color, fg="#555", 
                 font=controller.sub_font).pack()

    def on_show(self):
        self.after(2000, self.finish_verification)

    def finish_verification(self):
        if self.controller.sensor_item_valid.get():
            self.controller.total_points += 10
            self.controller.show_frame("ScreenSuccess")
        else:
            self.controller.show_frame("ScreenInvalid")

class ScreenInvalid(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Transaction Denied", bg=controller.bg_color, fg=controller.err_color, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(self.centered_frame, text="Invalid Item Detected.\nOnly PET bottles accepted.",
                 bg=controller.bg_color, fg="black", font=controller.sub_font).pack(pady=20)
        tk.Button(self.centered_frame, text="ITEM REMOVED", bg="#c0392b", fg="white", font=controller.button_font,
                  command=lambda: controller.show_frame("ScreenInsert")).pack(pady=40)

class ScreenSuccess(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Success!", bg=controller.bg_color, fg=controller.txt_eco, 
                 font=controller.header_font).pack(pady=(0, 10))
        tk.Label(self.centered_frame, text="+10 Pts", bg=controller.bg_color, fg=controller.txt_pts, 
                 font=("Arial", 60, "bold")).pack(pady=10)
        
        self.total_label = tk.Label(self.centered_frame, text="Total Points: 0", bg=controller.bg_color, fg="black", font=controller.sub_font)
        self.total_label.pack(pady=10)

        self.status_msg = tk.Label(self.centered_frame, text="", bg=controller.bg_color, fg=controller.err_color, font=("Arial", 12, "bold"))
        self.status_msg.pack(pady=5)

        btn_frame = tk.Frame(self.centered_frame, bg=controller.bg_color)
        btn_frame.pack(pady=10)

        self.btn_again = tk.Button(btn_frame, text="AGAIN", bg=controller.txt_pts, fg="white", font=controller.button_font,
                  width=10, command=self.check_again)
        self.btn_again.pack(side="left", padx=15)

        self.btn_finish = tk.Button(btn_frame, text="FINISH", bg="#555", fg="white", font=controller.button_font,
                  width=10, command=self.finish_session)
        self.btn_finish.pack(side="left", padx=15)

    def on_show(self):
        self.total_label.config(text=f"Total Points: {self.controller.total_points}")
        self.status_msg.config(text="") 
        self.btn_again.config(state="normal")

    def check_again(self):
        if self.controller.sensor_storage_full.get():
            self.status_msg.config(text="⚠️ Storage Full! Finalizing...")
            self.btn_again.config(state="disabled")
            self.after(2000, self.finish_session)
        else:
            self.controller.show_frame("ScreenInsert")

    def finish_session(self):
        self.controller.show_frame("ScreenEnd")

class ScreenEnd(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        tk.Label(self.centered_frame, text="Thank You!", bg=controller.bg_color, fg="black", 
                 font=controller.header_font).pack(pady=(0, 20))
        self.final_label = tk.Label(self.centered_frame, text="Your Total Points: 0", bg=controller.bg_color, 
                                    fg=controller.txt_eco, font=controller.sub_font)
        self.final_label.pack(pady=20)
        tk.Label(self.centered_frame, text="Saving data...", bg=controller.bg_color, fg="#888", font=("Arial", 10)).pack(pady=30)

    def on_show(self):
        self.final_label.config(text=f"Your Total Points: {self.controller.total_points}")
        self.after(3000, self.reset_system)

    def reset_system(self):
        self.controller.total_points = 0
        self.controller.show_frame("ScreenWelcome")

if __name__ == "__main__":
    app = EcoPointsKiosk()
    app.mainloop()