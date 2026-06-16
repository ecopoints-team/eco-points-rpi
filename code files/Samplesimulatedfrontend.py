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

        self.title("EcoPoints Simulation")
        self.geometry("800x480")
        
        # --- THEME COLORS ---
        self.bg_color = "#1e2b15"  
        self.txt_white = "#ffffff"
        self.txt_eco   = "#f1c40f" 
        self.txt_pts   = "#2ecc71" 
        self.btn_color = "#e67e22" 
        self.err_color = "#e74c3c" 
        
        self.configure(bg=self.bg_color)

        # Press ESC to close
        self.bind("<Escape>", lambda e: self.destroy())

        # --- SENSOR VARIABLES ---
        self.total_points = 0
        self.sensor_storage_full = tk.BooleanVar(value=False)
        self.sensor_door_closed = tk.BooleanVar(value=True)
        self.sensor_item_valid = tk.BooleanVar(value=True)

        # --- FONTS ---
        self.header_font = font.Font(family="Segoe UI", size=28, weight="bold")
        self.sub_font = font.Font(family="Segoe UI", size=14)
        self.button_font = font.Font(family="Segoe UI", size=12, weight="bold")
        
        # Welcome Screen Fonts
        self.font_welcome = font.Font(family="Segoe UI", size=24, weight="bold")
        self.font_eco_main = font.Font(family="Segoe UI", size=40, weight="bold")

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
        
        # --- DEBUG PANEL ---
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

# --- SCREENS ---

class ScreenWelcome(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
       
        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=0) 
        self.columnconfigure(2, weight=1) 
        self.rowconfigure(0, weight=1)   
        self.rowconfigure(1, weight=0)   
        self.rowconfigure(2, weight=1)    

       
        inner_box = tk.Frame(self, bg=controller.bg_color)
        inner_box.grid(row=1, column=1)

        # Header 
        header = tk.Frame(inner_box, bg=controller.bg_color)
        header.pack(side="top", pady=(0, 40)) 

        # LOGO
        try:
            self.logo_orig = tk.PhotoImage(file="logo.png")
            if self.logo_orig.width() > 200:
                self.logo_img = self.logo_orig.subsample(2, 2)
            else:
                self.logo_img = self.logo_orig
            
            lbl_logo = tk.Label(header, image=self.logo_img, bg=controller.bg_color)
            lbl_logo.pack(side="left", padx=(0, 20))
        except:
            lbl_logo = tk.Label(header, text="[LOGO]", fg="white", bg=controller.bg_color, font=("Arial", 12))
            lbl_logo.pack(side="left", padx=(0, 20))

        # TEXT
        text_section = tk.Frame(header, bg=controller.bg_color)
        text_section.pack(side="left")

        tk.Label(text_section, text="Welcome to", fg=controller.txt_white, 
                 bg=controller.bg_color, font=controller.font_welcome).pack(anchor="w")

        eco_row = tk.Frame(text_section, bg=controller.bg_color)
        eco_row.pack(anchor="w")
        
        tk.Label(eco_row, text="Eco", fg=controller.txt_eco, bg=controller.bg_color, font=controller.font_eco_main).pack(side="left")
        tk.Label(eco_row, text="Points", fg=controller.txt_pts, bg=controller.bg_color, font=controller.font_eco_main).pack(side="left")

        # Button
        btn = tk.Button(inner_box, text="START TRANSACTION", bg=controller.btn_color, fg="white", 
                        font=controller.button_font, relief="flat", padx=20, pady=8,
                        activebackground="#d35400", activeforeground="white",
                        command=self.check_start)
        btn.pack(side="top")

    def check_start(self):
        if self.controller.sensor_storage_full.get():
            self.controller.show_frame("ScreenStorageFull")
        else:
            self.controller.show_frame("ScreenQR")

class ScreenStorageFull(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="System Full", bg=controller.bg_color, fg=controller.err_color, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(container, text="Sorry, machine is currently full.\nPlease try again later.",
                 bg=controller.bg_color, fg="white", font=controller.sub_font).pack(pady=20)
        tk.Button(container, text="RETURN HOME", bg="#555", fg="white", font=controller.button_font,
                  command=lambda: controller.show_frame("ScreenWelcome")).pack(pady=30)

class ScreenQR(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="Login Required", bg=controller.bg_color, fg="white", 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(container, text="Scan your QR Code", bg=controller.bg_color, fg="#aaa", 
                 font=controller.sub_font).pack(pady=5)

        # Simulation Input Box
        frame_input = tk.Frame(container, bg=controller.bg_color)
        frame_input.pack(pady=10)
        tk.Label(frame_input, text="Simulate Scan:", fg="white", bg=controller.bg_color).pack()
        self.scanner_input = tk.Entry(frame_input, font=("Arial", 12))
        self.scanner_input.pack(pady=5)
        self.scanner_input.bind("<Return>", self.process_scan)

        self.status_label = tk.Label(container, text="Waiting for scanner...", bg=controller.bg_color, fg="#aaa", font=("Arial", 12))
        self.status_label.pack(pady=20)
        tk.Button(container, text="[Simulate Enter Key]", bg="#333", fg="#888", borderwidth=0, 
                  command=lambda: self.process_scan(None)).pack(pady=5)

    def on_show(self):
        self.status_label.config(text="Waiting for scanner...", fg="#aaa")
        self.scanner_input.delete(0, tk.END)
        self.scanner_input.focus_set()

    def process_scan(self, event):
        data = self.scanner_input.get()
        if data:
            self.status_label.config(text=f"User '{data}' Accepted!", fg=self.controller.txt_pts)
            self.after(1000, lambda: self.controller.show_frame("ScreenInsert"))
        else:
            self.status_label.config(text="Please type something.", fg=self.controller.err_color)

class ScreenInsert(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="Ready to Accept", bg=controller.bg_color, fg="white", 
                 font=controller.header_font).pack(pady=(0, 10))
        tk.Label(container, text="Insert PET bottles into the chute.", bg=controller.bg_color, fg="#aaa",
                 font=controller.sub_font).pack(pady=5)

        try:
            self.original_image = tk.PhotoImage(file="PET_symbol.png")
            tk.Label(container, image=self.original_image, bg=controller.bg_color).pack(pady=20)
        except Exception as e:
            tk.Label(container, text="[pet_symbol.png NOT FOUND]", bg=controller.bg_color, fg="red").pack(pady=40)

        tk.Button(container, text="SIMULATE INSERTION", bg=controller.btn_color, fg="white", font=controller.button_font,
                  padx=20, command=self.attempt_insert).pack(pady=10)

    def attempt_insert(self):
        if not self.controller.sensor_door_closed.get():
            self.controller.show_frame("ScreenDoorAlert")
        else:
            self.controller.show_frame("ScreenVerifying")

class ScreenDoorAlert(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="⚠️ Door Open", bg=controller.bg_color, fg=controller.btn_color, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(container, text="Please close the door to proceed.", bg=controller.bg_color, fg="white",
                 font=controller.sub_font).pack(pady=20)
        tk.Button(container, text="CHECK DOOR STATUS", bg="#555", fg="white", font=controller.button_font,
                  command=self.check_door).pack(pady=30)

    def check_door(self):
        if self.controller.sensor_door_closed.get():
            self.controller.show_frame("ScreenInsert")

class ScreenVerifying(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="Verifying...", bg=controller.bg_color, fg="white", 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(container, text="Analyzing object...", bg=controller.bg_color, fg="#aaa", 
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
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="Transaction Denied", bg=controller.bg_color, fg=controller.err_color, 
                 font=controller.header_font).pack(pady=(0, 20))
        tk.Label(container, text="Invalid Item Detected.\nOnly PET bottles accepted.",
                 bg=controller.bg_color, fg="white", font=controller.sub_font).pack(pady=20)
        tk.Button(container, text="ITEM REMOVED", bg="#c0392b", fg="white", font=controller.button_font,
                  command=lambda: controller.show_frame("ScreenInsert")).pack(pady=40)

class ScreenSuccess(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)
        
        tk.Label(container, text="Success!", bg=controller.bg_color, fg=controller.txt_pts, 
                 font=controller.header_font).pack(pady=(0, 10))
        tk.Label(container, text="+10 Pts", bg=controller.bg_color, fg=controller.txt_eco, 
                 font=("Segoe UI", 60, "bold")).pack(pady=10)
        
        self.total_label = tk.Label(container, text="Total Points: 0", bg=controller.bg_color, fg="white", font=controller.sub_font)
        self.total_label.pack(pady=10)

        # Status Message
        self.status_msg = tk.Label(container, text="", bg=controller.bg_color, fg=controller.err_color, font=("Arial", 12, "bold"))
        self.status_msg.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(container, bg=controller.bg_color)
        btn_frame.pack(pady=10)

        self.btn_again = tk.Button(btn_frame, text="AGAIN", bg=controller.btn_color, fg="white", font=controller.button_font,
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
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        
        container = tk.Frame(self, bg=controller.bg_color)
        container.grid(row=1, column=1)

        tk.Label(container, text="Thank You!", bg=controller.bg_color, fg="white", 
                 font=controller.header_font).pack(pady=(0, 20))
        self.final_label = tk.Label(container, text="Your Total Points: 0", bg=controller.bg_color, 
                                    fg=controller.txt_eco, font=controller.sub_font)
        self.final_label.pack(pady=20)
        tk.Label(container, text="Saving data...", bg=controller.bg_color, fg="#888", font=("Arial", 10)).pack(pady=30)

    def on_show(self):
        self.final_label.config(text=f"Your Total Points: {self.controller.total_points}")
        self.after(3000, self.reset_system)

    def reset_system(self):
        self.controller.total_points = 0
        self.controller.show_frame("ScreenWelcome")

if __name__ == "__main__":
    app = EcoPointsKiosk()
    app.mainloop()