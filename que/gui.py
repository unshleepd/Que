import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import threading
import contextlib
import logging
import sys
from que import (
    get_env_vars,
    process_nations,
    NSSession
)

root = tk.Tk()
root.title("Que - An easy way to process puppets")

script_thread = None  # Track the running thread
selected_file = None  # Track the selected file

# Control variables for switches
create_nation_var = tk.BooleanVar(value=True)  # Moved to the top
change_settings_var = tk.BooleanVar(value=True)
change_flag_var = tk.BooleanVar(value=True)
move_region_var = tk.BooleanVar(value=True)
place_bids_var = tk.BooleanVar(value=True)

# Definition of OnOffSwitch class with two columns
class OnOffSwitch(tk.Frame):
    def __init__(self, master, text, variable, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.text = text

        # Configure columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Column 1: Label for the switch
        label = tk.Label(self, text=self.text)
        label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Column 2: "On" and "Off" buttons in one line without spacing
        button_frame = tk.Frame(self)
        self.on_button = tk.Button(button_frame, text="On", width=5, command=self.activate_on)
        self.off_button = tk.Button(button_frame, text="Off", width=5, command=self.activate_off)
        
        # Place buttons in the same frame
        self.on_button.pack(side=tk.LEFT, padx=0)
        self.off_button.pack(side=tk.LEFT, padx=0)

        # Place the button frame in column 2
        button_frame.grid(row=0, column=1, sticky='e')

        self.update_buttons()
    
    def activate_on(self):
        self.variable.set(True)
        self.update_buttons()
    
    def activate_off(self):
        self.variable.set(False)
        self.update_buttons()
    
    def update_buttons(self):
        if self.variable.get():
            self.on_button.config(bg="green", fg="white")
            self.off_button.config(bg="gray", fg="black")
        else:
            self.on_button.config(bg="gray", fg="black")
            self.off_button.config(bg="red", fg="white")

# Create main frame
main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True)

# Configure grid
main_frame.columnconfigure(0, weight=1)  # Column 0 expands
main_frame.columnconfigure(1, weight=0)  # Column 1 (switches_frame) does not expand
main_frame.rowconfigure(1, weight=1)     # Row 1 (log_window) expands
main_frame.rowconfigure(2, weight=0)     # Row 2 (start_button) does not expand

# Create frame for switches
switches_frame = tk.Frame(main_frame)
switches_frame.grid(row=0, column=1, sticky='ne', padx=10, pady=10)

# Configure the switches_frame to expand
switches_frame.columnconfigure(0, weight=1)

# Create On/Off switches, with "Create Nation" at the top
create_nation_switch = OnOffSwitch(switches_frame, text="Create Nation", variable=create_nation_var)
create_nation_switch.grid(row=0, column=0, sticky='ew', pady=5)

change_settings_switch = OnOffSwitch(switches_frame, text="Change Settings", variable=change_settings_var)
change_settings_switch.grid(row=1, column=0, sticky='ew', pady=5)

change_flag_switch = OnOffSwitch(switches_frame, text="Change Flag", variable=change_flag_var)
change_flag_switch.grid(row=2, column=0, sticky='ew', pady=5)

move_region_switch = OnOffSwitch(switches_frame, text="Move to Region", variable=move_region_var)
move_region_switch.grid(row=3, column=0, sticky='ew', pady=5)

place_bids_switch = OnOffSwitch(switches_frame, text="Place Bids", variable=place_bids_var)
place_bids_switch.grid(row=4, column=0, sticky='ew', pady=5)

# File selection frame
file_frame = tk.Frame(main_frame)
file_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10)

def select_file():
    global selected_file
    filepath = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if filepath:
        selected_file = filepath
        file_label.config(text=f"Selected file: {filepath}")

# File selection label and button within file_frame
file_label = tk.Label(file_frame, text="No file selected")
file_label.grid(row=0, column=0, padx=(0, 5))

select_file_button = tk.Button(file_frame, text="Select Nations File", command=select_file)
select_file_button.grid(row=0, column=1)

# Log window
log_window = scrolledtext.ScrolledText(main_frame, width=80, height=20)
log_window.grid(row=1, column=0, columnspan=2, sticky='nsew')

# Set state to 'disabled' to make the field non-editable
log_window.config(state='disabled')

# Custom logging handler to write logs to the GUI
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Ensure thread-safe GUI updates
        log_window.after(0, self.write_message, msg)

    def write_message(self, msg):
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')

def setup_logging(log_filename="script_log.txt"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%I:%M:%S %p')

    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # GUI handler
    text_handler = TextHandler(log_window)
    text_handler.setFormatter(formatter)
    logger.addHandler(text_handler)

def start_script():
    global script_thread
    if script_thread and script_thread.is_alive():
        messagebox.showwarning("Warning", "The script is already running!")
        return

    if not selected_file:
        messagebox.showwarning("Warning", "Please select a nations file before starting the script.")
        return

    start_button.config(state=tk.DISABLED)
    create_nation = create_nation_var.get()  # Get the value of the create_nation switch
    change_settings = change_settings_var.get()
    change_flag = change_flag_var.get()
    move_region = move_region_var.get()
    place_bids = place_bids_var.get()

    script_thread = threading.Thread(target=run_script, args=(create_nation, change_settings, change_flag, move_region, place_bids))
    script_thread.start()

def run_script(create_nation, change_settings, change_flag, move_region, place_bids):
    global script_thread
    try:
        logging.info("Starting script...")
        env_vars = get_env_vars()
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])
        with open(selected_file, "r") as q:
            pups = q.readlines()
        logging.info("Processing nations...")
        process_nations(session, pups, env_vars, create_nation, change_settings, change_flag, move_region, place_bids)
    except Exception as e:
        error_message = f"An error occurred: {e}"
        logging.error(error_message)
        # Display error dialog
        root.after(0, lambda: messagebox.showerror("Error", error_message))
    else:
        root.after(0, script_completed)
    finally:
        # Re-enable the "Start" button after completion
        root.after(0, lambda: start_button.config(state=tk.NORMAL))
        script_thread = None

def script_completed():
    logging.info("Process completed successfully.")
    # Display dialog
    messagebox.showinfo("Completion", "The process has completed successfully.")

def on_closing():
    if script_thread and script_thread.is_alive():
        if messagebox.askokcancel("Quit", "The script is still running. Do you want to quit?"):
            root.destroy()  # Force quit
    else:
        root.destroy()  # Quit

root.protocol("WM_DELETE_WINDOW", on_closing)

start_button = tk.Button(main_frame, text="Start", command=start_script, width=20)
start_button.grid(row=2, column=0, columnspan=2, pady=10)

setup_logging("script_log.txt")

root.mainloop()
