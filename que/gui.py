import tkinter as tk  # Import Tkinter library for GUI development
from tkinter import scrolledtext, messagebox, filedialog  # Import specific widgets and dialogs
import threading  # Import threading to run tasks in separate threads
import logging  # Import logging for logging messages
from que import (
    get_env_vars,      # Function to retrieve environment variables
    process_nations,   # Function to process nations
    NSSession          # Class representing a NationStates session
)

# Initialize the main application window
root = tk.Tk()  # Create the main window instance
root.title("Que - An easy way to process puppets")  # Set the window title

script_thread = None  # Track the running thread of the script
selected_file = None  # Track the path of the selected file

# Control variables for switches (BooleanVars for Tkinter)
change_settings_var = tk.BooleanVar(value=True)  # Variable for 'Change Settings' switch
change_flag_var = tk.BooleanVar(value=True)      # Variable for 'Change Flag' switch
move_region_var = tk.BooleanVar(value=True)      # Variable for 'Move to Region' switch
place_bids_var = tk.BooleanVar(value=True)       # Variable for 'Place Bids' switch

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
        self.columnconfigure(0, weight=1)  # Column 0 (label) expands
        self.columnconfigure(1, weight=0)  # Column 1 (buttons) does not expand

        # Column 1: Label for the switch
        label = tk.Label(self, text=self.text)  # Create a label widget
        label.grid(row=0, column=0, padx=10, pady=5, sticky="w")  # Place the label in the grid

        # Column 2: "On" and "Off" buttons side by side without spacing
        button_frame = tk.Frame(self)  # Create a frame to hold the buttons
        self.on_button = tk.Button(button_frame, text="On", width=5, command=self.activate_on)  # 'On' button
        self.off_button = tk.Button(button_frame, text="Off", width=5, command=self.activate_off)  # 'Off' button
        
        # Place buttons in the same frame
        self.on_button.pack(side=tk.LEFT, padx=0)  # Pack 'On' button to the left
        self.off_button.pack(side=tk.LEFT, padx=0)  # Pack 'Off' button to the right of 'On'

        # Place the button frame in column 2
        button_frame.grid(row=0, column=1, sticky='e')  # Place the button frame in the grid

        self.update_buttons()  # Initialize button states
    
    def activate_on(self):
        """
        Activates the 'On' state and updates button appearances.
        """
        self.variable.set(True)  # Set the variable to True
        self.update_buttons()    # Update the button colors
    
    def activate_off(self):
        """
        Activates the 'Off' state and updates button appearances.
        """
        self.variable.set(False)  # Set the variable to False
        self.update_buttons()     # Update the button colors
    
    def update_buttons(self):
        """
        Updates the button colors based on the current state.
        """
        if self.variable.get():
            # If the switch is 'On', set the 'On' button to green
            self.on_button.config(bg="green", fg="white")
            self.off_button.config(bg="gray", fg="black")
        else:
            # If the switch is 'Off', set the 'Off' button to red
            self.on_button.config(bg="gray", fg="black")
            self.off_button.config(bg="red", fg="white")

# Create the main frame that holds all other widgets
main_frame = tk.Frame(root)  # Create a frame inside the main window
main_frame.pack(fill='both', expand=True)  # Allow the frame to expand in both directions

# Configure grid weights to control widget resizing behavior
main_frame.columnconfigure(0, weight=1)  # Column 0 (file selection and log window) expands
main_frame.columnconfigure(1, weight=0)  # Column 1 (switches_frame) does not expand
main_frame.rowconfigure(1, weight=1)     # Row 1 (log_window) expands vertically
main_frame.rowconfigure(2, weight=0)     # Row 2 (start_button) does not expand

# Create frame for switches on the right side
switches_frame = tk.Frame(main_frame)  # Create a frame for the switches
switches_frame.grid(row=0, column=1, sticky='ne', padx=10, pady=10)  # Place it in the grid

# Configure the switches_frame to expand
switches_frame.columnconfigure(0, weight=1)  # Allow the switches to fill the frame

# Create On/Off switches, each in one row with label and buttons
change_settings_switch = OnOffSwitch(switches_frame, text="Change Settings", variable=change_settings_var)
change_settings_switch.grid(row=0, column=0, sticky='ew', pady=5)  # Place the switch in the grid

change_flag_switch = OnOffSwitch(switches_frame, text="Change Flag", variable=change_flag_var)
change_flag_switch.grid(row=1, column=0, sticky='ew', pady=5)  # Next row

move_region_switch = OnOffSwitch(switches_frame, text="Move to Region", variable=move_region_var)
move_region_switch.grid(row=2, column=0, sticky='ew', pady=5)  # Next row

place_bids_switch = OnOffSwitch(switches_frame, text="Place Bids", variable=place_bids_var)
place_bids_switch.grid(row=3, column=0, sticky='ew', pady=5)  # Next row

# File selection frame on the left side
file_frame = tk.Frame(main_frame)  # Create a frame for file selection widgets
file_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10)  # Place it in the grid

def select_file():
    """
    Opens a file dialog to select a nations file and updates the label.
    """
    global selected_file  # Use the global variable
    filepath = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]  # Specify file types
    )
    if filepath:
        selected_file = filepath  # Update the selected file path
        file_label.config(text=f"Selected file: {filepath}")  # Update the label to show the selected file

# File selection label and button within file_frame
file_label = tk.Label(file_frame, text="No file selected")  # Label to display selected file
file_label.grid(row=0, column=0, padx=(0, 5))  # Place the label in the grid

select_file_button = tk.Button(file_frame, text="Select Nations File", command=select_file)  # Button to open file dialog
select_file_button.grid(row=0, column=1)  # Place the button next to the label

# Log window to display output messages
log_window = scrolledtext.ScrolledText(main_frame, width=80, height=20)  # Create a scrolled text widget
log_window.grid(row=1, column=0, columnspan=2, sticky='nsew')  # Place it in the grid, spanning two columns

# Set state to 'disabled' to make the log window non-editable
log_window.config(state='disabled')  # Prevent user from editing the log content

# Custom logging handler to write logs to the GUI
class TextHandler(logging.Handler):
    """
    Logging handler that directs log messages to a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget  # Reference to the text widget

    def emit(self, record):
        """
        Emit a record to the text widget.
        """
        msg = self.format(record)  # Format the log message
        # Ensure thread-safe GUI updates using after()
        log_window.after(0, self.write_message, msg)  # Schedule the message to be written in the main thread

    def write_message(self, msg):
        """
        Write a message to the text widget in a thread-safe manner.
        """
        self.text_widget.config(state='normal')  # Make the text widget editable
        self.text_widget.insert(tk.END, msg + '\n')  # Insert the log message at the end
        self.text_widget.see(tk.END)  # Scroll to the end to show the new message
        self.text_widget.config(state='disabled')  # Disable editing again

def setup_logging(log_filename="script_log.txt"):
    """
    Sets up logging to both a file and the GUI log window.
    """
    logger = logging.getLogger()  # Get the root logger
    logger.setLevel(logging.INFO)  # Set the logging level to INFO
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%I:%M:%S %p')  # Define the log message format

    # File handler to write logs to a file
    file_handler = logging.FileHandler(log_filename)  # Create a handler for the log file
    file_handler.setFormatter(formatter)  # Set the formatter for the file handler
    logger.addHandler(file_handler)  # Add the file handler to the logger

    # GUI handler to write logs to the GUI
    text_handler = TextHandler(log_window)  # Create a handler for the GUI log window
    text_handler.setFormatter(formatter)  # Set the formatter for the text handler
    logger.addHandler(text_handler)  # Add the text handler to the logger

def start_script():
    """
    Starts the processing script in a separate thread.
    """
    global script_thread  # Access the global variable
    if script_thread and script_thread.is_alive():
        # If the script is already running, show a warning message
        messagebox.showwarning("Warning", "The script is already running!")
        return

    if not selected_file:
        # If no file has been selected, prompt the user to select one
        messagebox.showwarning("Warning", "Please select a nations file before starting the script.")
        return

    # Disable the Start button to prevent multiple runs
    start_button.config(state=tk.DISABLED)
    # Retrieve the values from the switches
    change_settings = change_settings_var.get()  # Get the state of 'Change Settings' switch
    change_flag = change_flag_var.get()          # Get the state of 'Change Flag' switch
    move_region = move_region_var.get()          # Get the state of 'Move to Region' switch
    place_bids = place_bids_var.get()            # Get the state of 'Place Bids' switch

    # Start the script in a new thread to keep the GUI responsive
    script_thread = threading.Thread(
        target=run_script,
        args=(change_settings, change_flag, move_region, place_bids)
    )
    script_thread.start()  # Start the new thread

def run_script(change_settings, change_flag, move_region, place_bids):
    """
    Runs the main processing script with the given parameters.
    """
    global script_thread  # Access the global variable
    try:
        logging.info("Starting script...")  # Log the start of the script
        # Retrieve environment variables
        env_vars = get_env_vars()  # Get environment variables needed for processing
        # Initialize the NationStates session
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])  # Create a session object
        # Read the nations from the selected file
        with open(selected_file, "r") as q:
            pups = q.readlines()  # Read all lines (nations) from the file
        logging.info("Processing nations...")  # Log that nation processing is starting
        # Process the nations with the specified options
        process_nations(
            session,
            pups,
            env_vars,
            change_settings,
            change_flag,
            move_region,
            place_bids
        )
    except Exception as e:
        error_message = f"An error occurred: {e}"  # Prepare the error message
        logging.error(error_message)  # Log the error
        # Display error dialog in the GUI
        root.after(0, lambda: messagebox.showerror("Error", error_message))  # Show error message box
    else:
        # If successful, call script_completed in the main thread
        root.after(0, script_completed)
    finally:
        # Re-enable the "Start" button after completion
        root.after(0, lambda: start_button.config(state=tk.NORMAL))
        script_thread = None  # Reset the script thread variable

def script_completed():
    """
    Called when the script has completed successfully.
    """
    logging.info("Process completed successfully.")  # Log completion message
    # Display completion dialog to the user
    messagebox.showinfo("Completion", "The process has completed successfully.")  # Show info message box

def on_closing():
    """
    Handles the window closing event, ensuring the script thread is terminated properly.
    """
    if script_thread and script_thread.is_alive():
        # If the script is running, confirm if the user wants to quit
        if messagebox.askokcancel("Quit", "The script is still running. Do you want to quit?"):
            root.destroy()  # Destroy the window and exit the application
    else:
        root.destroy()  # Destroy the window and exit the application

# Set the protocol for handling window close events
root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the on_closing function to window close event

# Create the Start button to initiate the script
start_button = tk.Button(
    main_frame,
    text="Start",
    command=start_script,
    width=20
)  # Create a Start button widget
start_button.grid(row=2, column=0, columnspan=2, pady=10)  # Place the Start button in the grid

# Set up logging to file and GUI
setup_logging("script_log.txt")  # Initialize logging handlers

# Start the Tkinter event loop
root.mainloop()  # Begin the GUI's main event loop
