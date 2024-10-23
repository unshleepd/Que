# gui.py
# -*- coding: utf-8 -*-
"""
This script creates a graphical user interface (GUI) for interacting with the que.py script.
It allows users to process nations in the NationStates game through a user-friendly interface,
providing options to change settings, change flags, move to regions, place bids on cards,
and vote in the World Assembly.
"""

import tkinter as tk  # Import Tkinter library for GUI development
from tkinter import ttk, scrolledtext, messagebox, filedialog  # Import specific widgets and dialogs
import threading  # Import threading to run tasks in separate threads
import logging  # Import logging for logging messages
from que import (
    get_env_vars,      # Function to retrieve environment variables
    process_nations,   # Function to process nations
    wa_vote,           # Function to perform WA voting
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

class OnOffSwitch(tk.Frame):
    """
    Custom widget that represents an On/Off switch with a label.

    Attributes:
        variable (tk.BooleanVar): The control variable associated with the switch.
        text (str): The label text for the switch.
    """
    def __init__(self, master, text, variable, **kwargs):
        """
        Initializes the OnOffSwitch widget.

        Parameters:
            master (tk.Widget): The parent widget.
            text (str): The label text for the switch.
            variable (tk.BooleanVar): The control variable associated with the switch.
            **kwargs: Additional keyword arguments for the Frame.
        """
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

# Create a Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Create frames for each tab
process_tab = tk.Frame(notebook)
voting_tab = tk.Frame(notebook)

# Add tabs to the notebook
notebook.add(process_tab, text='Process Puppets')
notebook.add(voting_tab, text='WA Voting')

# Create the main frame that holds all other widgets in the process_tab
main_frame = process_tab  # Use process_tab as the main_frame

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

# Log window to display output messages in the Process Puppets tab
log_window = scrolledtext.ScrolledText(main_frame, width=80, height=20)  # Create a scrolled text widget
log_window.grid(row=1, column=0, columnspan=2, sticky='nsew')  # Place it in the grid, spanning two columns

# Set state to 'disabled' to make the log window non-editable
log_window.config(state='disabled')  # Prevent user from editing the log content

class TextHandler(logging.Handler):
    """
    Logging handler that directs log messages to a Tkinter Text widget.

    Attributes:
        text_widget (tk.Text): The text widget where logs will be displayed.
    """
    def __init__(self, text_widget):
        """
        Initialize the TextHandler with a reference to a text widget.

        Parameters:
            text_widget (tk.Text): The widget where log messages will be displayed.
        """
        super().__init__()
        self.text_widget = text_widget  # Reference to the text widget

    def emit(self, record):
        """
        Emit a record to the text widget.

        Parameters:
            record (logging.LogRecord): The log record to be emitted.
        """
        try:
            # Ensure that the record message is properly formatted
            msg = self.format(record)
            # Ensure thread-safe GUI updates using after()
            self.text_widget.after(0, self.write_message, msg)
        except Exception:
            self.handleError(record)

    def write_message(self, msg):
        """
        Write a message to the text widget in a thread-safe manner.

        Parameters:
            msg (str): The message to write to the text widget.
        """
        self.text_widget.config(state='normal')  # Make the text widget editable
        self.text_widget.insert(tk.END, msg + '\n')  # Insert the log message at the end
        self.text_widget.see(tk.END)  # Scroll to the end to show the new message
        self.text_widget.config(state='disabled')  # Disable editing again

def setup_logging(log_filename="que_log.txt"):
    """
    Sets up logging to both a file and the GUI log windows.

    Parameters:
        log_filename (str): The name of the log file.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%I:%M:%S %p')

    # File handler to write logs to a file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # GUI handler to write logs to the Process Puppets tab
    text_handler = TextHandler(log_window)
    text_handler.setLevel(logging.INFO)
    text_handler.setFormatter(formatter)  # Ensure formatter is set
    logger.addHandler(text_handler)

    # --- Added code to handle logging in the WA Voting tab ---

    # Log window to display output messages in the WA Voting tab
    voting_log_window = scrolledtext.ScrolledText(voting_tab, width=80, height=20)  # Create a scrolled text widget
    voting_log_window.grid(row=4, column=0, columnspan=2, sticky='nsew')  # Place it in the grid, spanning two columns
    voting_log_window.config(state='disabled')  # Prevent user from editing the log content

    # Configure grid weights for voting_tab
    voting_tab.columnconfigure(0, weight=1)
    voting_tab.columnconfigure(1, weight=1)
    voting_tab.rowconfigure(4, weight=1)  # Make the log window expandable

    # Create a TextHandler for the WA Voting tab
    voting_text_handler = TextHandler(voting_log_window)
    voting_text_handler.setLevel(logging.INFO)
    voting_text_handler.setFormatter(formatter)  # Ensure formatter is set
    logger.addHandler(voting_text_handler)

# Set up logging to file and GUI
setup_logging("que_log.txt")  # Initialize logging handlers

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

    Parameters:
        change_settings (bool): Whether to change nation settings.
        change_flag (bool): Whether to change the nation's flag.
        move_region (bool): Whether to move the nation to a target region.
        place_bids (bool): Whether to place bids on cards.
    """
    global script_thread  # Access the global variable
    try:
        logging.info("Starting script...")  # Log the start of the script
        # Retrieve environment variables
        env_vars = get_env_vars()  # Get environment variables needed for processing
        # Initialize the NationStates session
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])
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

# ------------------------ WA Voting Tab ------------------------

# Nation Name Entry
nation_label = tk.Label(voting_tab, text="Nation Name:")
nation_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')

nation_entry = tk.Entry(voting_tab, width=30)
nation_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

# Assembly Selection
assembly_label = tk.Label(voting_tab, text="Select Assembly:")
assembly_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')

assembly_var = tk.StringVar(value='ga')  # Default to General Assembly
assembly_options = [('General Assembly', 'ga'), ('Security Council', 'sc')]

assembly_frame = tk.Frame(voting_tab)
assembly_frame.grid(row=1, column=1, padx=10, pady=5, sticky='w')

for text, value in assembly_options:
    tk.Radiobutton(assembly_frame, text=text, variable=assembly_var, value=value).pack(side='left')

# Vote Choice Selection
vote_label = tk.Label(voting_tab, text="Vote Choice:")
vote_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')

vote_var = tk.StringVar(value='for')  # Default to 'for'
vote_options = [('Yes (For)', 'for'), ('No (Against)', 'against')]

vote_frame = tk.Frame(voting_tab)
vote_frame.grid(row=2, column=1, padx=10, pady=5, sticky='w')

for text, value in vote_options:
    tk.Radiobutton(vote_frame, text=text, variable=vote_var, value=value).pack(side='left')

# Start Voting Button
vote_button = tk.Button(
    voting_tab,
    text="Vote",
    command=lambda: start_voting(nation_entry.get(), assembly_var.get(), vote_var.get()),
    width=20
)
vote_button.grid(row=3, column=0, columnspan=2, pady=10)

logging.info("GUI initialized successfully.")  # Log that the GUI has been initialized

def start_voting(nation_name, assembly, vote_choice):
    """
    Starts the WA voting process in a separate thread.
    """
    if not nation_name:
        messagebox.showwarning("Warning", "Please enter a nation name.")
        return

    # Disable the Vote button to prevent multiple clicks
    vote_button.config(state=tk.DISABLED)

    # Disable the input fields
    nation_entry.config(state=tk.DISABLED)
    for child in assembly_frame.winfo_children():
        child.config(state=tk.DISABLED)
    for child in vote_frame.winfo_children():
        child.config(state=tk.DISABLED)

    # Start the voting process in a new thread
    threading.Thread(
        target=run_voting,
        args=(nation_name, assembly, vote_choice)
    ).start()

def run_voting(nation_name, assembly, vote_choice):
    """
    Runs the WA voting process.
    """
    try:
        # Retrieve environment variables
        env_vars = get_env_vars()
        # Initialize the NationStates session
        session = NSSession("Que", "3.0.0", "Unshleepd", env_vars['UA'])

        # Perform the voting
        wa_vote(session, nation_name, assembly, vote_choice)

        # Notify the user upon success
        assembly_full_name = "General Assembly" if assembly.lower() == 'ga' else "Security Council"
        root.after(0, lambda: messagebox.showinfo("Success", "Successfully voted %s on %s resolution for %s." % (vote_choice.upper(), assembly_full_name, nation_name)))
    except Exception as e:
        error_message = "An error occurred: %s" % e
        logging.error(error_message)
        root.after(0, lambda: messagebox.showerror("Error", error_message))
    finally:
        # Re-enable the Vote button and input fields after completion
        root.after(0, lambda: vote_button.config(state=tk.NORMAL))
        root.after(0, lambda: nation_entry.config(state=tk.NORMAL))
        root.after(0, lambda: [child.config(state=tk.NORMAL) for child in assembly_frame.winfo_children()])
        root.after(0, lambda: [child.config(state=tk.NORMAL) for child in vote_frame.winfo_children()])


# Start the Tkinter event loop
root.mainloop()  # Begin the GUI's main event loop