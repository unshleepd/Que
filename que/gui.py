import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import threading
import logging
from que import (
    get_env_vars,
    process_nations,
    NSSession
)

# Initialize the main application window
root = tk.Tk()
root.title("Que - An easy way to process puppets")

script_thread = None  # Track the running thread
selected_file = None  # Track the selected file path

# Control variables for switches (BooleanVars for Tkinter)
new_nation_var = tk.BooleanVar(value=True)
change_settings_var = tk.BooleanVar(value=True)
change_flag_var = tk.BooleanVar(value=True)
move_region_var = tk.BooleanVar(value=True)
place_bids_var = tk.BooleanVar(value=True)

# Definition of OnOffSwitch class with two columns
class OnOffSwitch(tk.Frame):
    """
    Custom widget that represents an On/Off switch with a label.
    """
    def __init__(self, master, text, variable, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable  # Control variable (BooleanVar)
        self.text = text  # Label text for the switch

        # Configure columns for the switch layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Column 1: Label for the switch
        label = tk.Label(self, text=self.text)
        label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Column 2: "On" and "Off" buttons side by side without spacing
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
        """
        Activates the 'On' state and updates button appearances.
        """
        self.variable.set(True)
        self.update_buttons()
    
    def activate_off(self):
        """
        Activates the 'Off' state and updates button appearances.
        """
        self.variable.set(False)
        self.update_buttons()
    
    def update_buttons(self):
        """
        Updates the button colors based on the current state.
        """
        if self.variable.get():
            self.on_button.config(bg="green", fg="white")
            self.off_button.config(bg="gray", fg="black")
        else:
            self.on_button.config(bg="gray", fg="black")
            self.off_button.config(bg="red", fg="white")

# Create the main frame that holds all other widgets
main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True)

# Configure grid weights to control widget resizing behavior
main_frame.columnconfigure(0, weight=1)  # Column 0 expands (file selection and log)
main_frame.columnconfigure(1, weight=0)  # Column 1 (switches_frame) does not expand
main_frame.rowconfigure(1, weight=1)     # Row 1 (log_window) expands vertically
main_frame.rowconfigure(2, weight=0)     # Row 2 (start_button) does not expand

# Create frame for switches on the right side
switches_frame = tk.Frame(main_frame)
switches_frame.grid(row=0, column=1, sticky='ne', padx=10, pady=10)

# Configure the switches_frame to expand
switches_frame.columnconfigure(0, weight=1)

# Create On/Off switches, each in one row with label and buttons
new_nation_switch = OnOffSwitch(switches_frame, text="Create Nation", variable=new_nation_var)
new_nation_switch.grid(row=0, column=0, sticky='ew', pady=5)

change_settings_switch = OnOffSwitch(switches_frame, text="Change Settings", variable=change_settings_var)
change_settings_switch.grid(row=1, column=0, sticky='ew', pady=5)

change_flag_switch = OnOffSwitch(switches_frame, text="Change Flag", variable=change_flag_var)
change_flag_switch.grid(row=2, column=0, sticky='ew', pady=5)

move_region_switch = OnOffSwitch(switches_frame, text="Move to Region", variable=move_region_var)
move_region_switch.grid(row=3, column=0, sticky='ew', pady=5)

place_bids_switch = OnOffSwitch(switches_frame, text="Place Bids", variable=place_bids_var)
place_bids_switch.grid(row=4, column=0, sticky='ew', pady=5)

# File selection frame on the left side
file_frame = tk.Frame(main_frame)
file_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10)

def select_file():
    """
    Opens a file dialog to select a nations file and updates the label.
    """
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

# Log window to display output messages
log_window = scrolledtext.ScrolledText(main_frame, width=80, height=20)
log_window.grid(row=1, column=0, columnspan=2, sticky='nsew')

# Set state to 'disabled' to make the log window non-editable
log_window.config(state='disabled')

# Custom logging handler to write logs to the GUI
class TextHandler(logging.Handler):
    """
    Logging handler that directs log messages to a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        """
        Emit a record to the text widget.
        """
        msg = self.format(record)
        # Ensure thread-safe GUI updates using after()
        log_window.after(0, self.write_message, msg)

    def write_message(self, msg):
        """
        Write a message to the text widget in a thread-safe manner.
        """
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)  # Scroll to the end
        self.text_widget.config(state='disabled')

def setup_logging(log_filename="script_log.txt"):
    """
    Sets up logging to both a file and the GUI log window.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%I:%M:%S %p')

    # File handler to write logs to a file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # GUI handler to write logs to the GUI
    text_handler = TextHandler(log_window)
    text_handler.setFormatter(formatter)
    logger.addHandler(text_handler)

def start_script():
    """
    Starts the processing script in a separate thread.
    """
    global script_thread
    if script_thread and script_thread.is_alive():
        messagebox.showwarning("Warning", "The script is already running!")
        return

    if not selected_file:
        messagebox.showwarning("Warning", "Please select a nations file before starting the script.")
        return

    # Disable the Start button to prevent multiple runs
    start_button.config(state=tk.DISABLED)
    # Retrieve the values from the switches
    new_nation = new_nation_var.get()
    change_settings = change_settings_var.get()
    change_flag = change_flag_var.get()
    move_region = move_region_var.get()
    place_bids = place_bids_var.get()
    # Start the script in a new thread to keep the GUI responsive
    script_thread = threading.Thread(target=run_script, args=(new_nation, change_settings, change_flag, move_region, place_bids))
    script_thread.start()

def run_script(new_nation, change_settings, change_flag, move_region, place_bids):
    """
    Runs the main processing script with the given parameters.
    """
    global script_thread
    try:
        logging.info("Starting script...")
        # Retrieve environment variables
        env_vars = get_env_vars()
        # Initialize the NationStates session
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])
        # Read the nations from the selected file
        with open(selected_file, "r") as q:
            pups = q.readlines()
        logging.info("Processing nations...")
        # Process the nations with the specified options
        process_nations(session, pups, env_vars,new_nation, change_settings, change_flag, move_region, place_bids)
    except Exception as e:
        error_message = f"An error occurred: {e}"
        logging.error(error_message)
        # Display error dialog in the GUI
        root.after(0, lambda: messagebox.showerror("Error", error_message))
    else:
        # If successful, call script_completed in the main thread
        root.after(0, script_completed)
    finally:
        # Re-enable the "Start" button after completion
        root.after(0, lambda: start_button.config(state=tk.NORMAL))
        script_thread = None

def script_completed():
    """
    Called when the script has completed successfully.
    """
    logging.info("Process completed successfully.")
    # Display completion dialog
    messagebox.showinfo("Completion", "The process has completed successfully.")

def on_closing():
    """
    Handles the window closing event, ensuring the script thread is terminated properly.
    """
    if script_thread and script_thread.is_alive():
        if messagebox.askokcancel("Quit", "The script is still running. Do you want to quit?"):
            root.destroy()  # Force quit the application
    else:
        root.destroy()  # Quit the application

# Set the protocol for handling window close events
root.protocol("WM_DELETE_WINDOW", on_closing)

# Create the Start button to initiate the script
start_button = tk.Button(main_frame, text="Start", command=start_script, width=20)
start_button.grid(row=2, column=0, columnspan=2, pady=10)

# Set up logging to file and GUI
setup_logging("script_log.txt")

# Start the Tkinter event loop
root.mainloop()
