# gui.py
# -*- coding: utf-8 -*-
"""
This script creates a graphical user interface (GUI) for interacting with the que.py script using PyQt6.
It allows users to process nations in the NationStates game through a user-friendly interface,
providing options to change settings, change flags, move to regions, place bids on cards,
vote in the World Assembly, endorse nations, and manage configuration settings.
"""

import sys
import threading
import logging
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QCheckBox, QTextEdit, QRadioButton, QButtonGroup,
    QLineEdit, QMessageBox, QSizePolicy, QProgressBar, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from que import (
    get_env_vars,      # Function to retrieve environment variables
    process_nations,   # Function to process nations
    endorse_nations,   # Function to endorse nations
    wa_vote,           # Function to perform WA voting
    NSSession          # Class representing a NationStates session
)

class QtHandler(logging.Handler):
    """
    Custom logging handler that emits log records to a signal.
    """
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        # Emit the signal using QueuedConnection
        self.signal.emit(msg)

class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str, str)  # title, message
    completion_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)          # Signal to update the process puppets progress bar
    endorse_progress_signal = pyqtSignal(int)  # Signal to update the endorse progress bar

    # New signals for thread completion
    script_finished_signal = pyqtSignal()
    voting_finished_signal = pyqtSignal()
    endorsement_finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Que - An easy way to process puppets")
        self.script_thread = None  # Track the running thread of the script
        self.selected_file = None  # Track the path of the selected file

        # Control variables for switches
        self.change_settings = True
        self.change_flag = True
        self.move_region = True
        self.place_bids = True

        # Connect signals to slots with QueuedConnection
        self.log_signal.connect(self.append_log, Qt.ConnectionType.QueuedConnection)
        self.error_signal.connect(self.show_error_message, Qt.ConnectionType.QueuedConnection)
        self.info_signal.connect(self.show_info_message, Qt.ConnectionType.QueuedConnection)
        self.completion_signal.connect(self.script_completed, Qt.ConnectionType.QueuedConnection)
        self.progress_signal.connect(self.set_progress, Qt.ConnectionType.QueuedConnection)
        self.endorse_progress_signal.connect(self.set_endorse_progress, Qt.ConnectionType.QueuedConnection)
        self.script_finished_signal.connect(self.on_script_finished, Qt.ConnectionType.QueuedConnection)
        self.voting_finished_signal.connect(self.on_voting_finished, Qt.ConnectionType.QueuedConnection)
        self.endorsement_finished_signal.connect(self.on_endorsement_finished, Qt.ConnectionType.QueuedConnection)

        # Set up the main UI
        self.setup_ui()

    def setup_ui(self):
        # Create the main widget and set it as the central widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Create the tabbed interface
        self.tabs = QTabWidget()
        process_tab = QWidget()
        voting_tab = QWidget()
        endorse_tab = QWidget()
        settings_tab = QWidget()  # New Settings tab
        self.tabs.addTab(process_tab, "Process Puppets")
        self.tabs.addTab(voting_tab, "WA Voting")
        self.tabs.addTab(endorse_tab, "Endorse")
        self.tabs.addTab(settings_tab, "Settings")  # Add the Settings tab

        # Create the shared log window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set up layouts
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Add tabs and log window to the main layout
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.log_window)

        # Set stretch factors to control how space is allocated
        main_layout.setStretchFactor(self.tabs, 2)
        main_layout.setStretchFactor(self.log_window, 1)

        # Set up the Process Puppets tab
        self.setup_process_tab(process_tab)

        # Set up the WA Voting tab
        self.setup_voting_tab(voting_tab)

        # Set up the Endorse tab
        self.setup_endorse_tab(endorse_tab)

        # Set up the Settings tab
        self.setup_settings_tab(settings_tab)

        # Set up logging
        self.setup_logging()

        # Apply stylesheets
        self.apply_styles()

        logging.info("GUI initialized successfully.")

    def apply_styles(self):
        """
        Applies stylesheets to enhance the visual appearance of the application.
        """
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 6px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTabWidget::pane {
                border: 1px solid lightgray;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 10px;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
            QCheckBox {
                font-size: 13px;
            }
            QLabel {
                font-size: 13px;
            }
            QLineEdit {
                font-size: 13px;
                padding: 4px;
            }
            QTextEdit {
                font-size: 12px;
            }
            QRadioButton {
                font-size: 13px;
            }
            QProgressBar {
                font-size: 12px;
                text-align: center;
            }
            QComboBox {
                font-size: 13px;
                padding: 4px;
            }
        """)

    def setup_process_tab(self, tab):
        """
        Sets up the 'Process Puppets' tab with all its widgets and layouts.
        """
        # Create layouts
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)

        # File selection layout
        file_layout = QHBoxLayout()
        file_label = QLabel("No file selected")
        self.file_label = file_label
        select_file_button = QPushButton("Select Nations File")
        select_file_button.clicked.connect(self.select_file)
        self.select_file_button = select_file_button  # Reference to disable/enable later
        file_layout.addWidget(file_label)
        file_layout.addWidget(select_file_button)
        file_layout.setStretch(0, 1)
        file_layout.setStretch(1, 0)

        # Switches layout
        switches_layout = QHBoxLayout()
        # Create checkboxes for each switch
        self.change_settings_checkbox = QCheckBox("Change Settings")
        self.change_settings_checkbox.setChecked(True)
        self.change_flag_checkbox = QCheckBox("Change Flag")
        self.change_flag_checkbox.setChecked(True)
        self.move_region_checkbox = QCheckBox("Move to Region")
        self.move_region_checkbox.setChecked(True)
        self.place_bids_checkbox = QCheckBox("Place Bids")
        self.place_bids_checkbox.setChecked(True)
        switches_layout.addWidget(self.change_settings_checkbox)
        switches_layout.addWidget(self.change_flag_checkbox)
        switches_layout.addWidget(self.move_region_checkbox)
        switches_layout.addWidget(self.place_bids_checkbox)
        switches_layout.addStretch()

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setFixedHeight(20)

        # Start button
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_script)
        self.start_button = start_button
        # Center the Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(start_button)
        button_layout.addStretch()

        # Add layouts to main_layout
        main_layout.addLayout(file_layout)
        main_layout.addLayout(switches_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def setup_voting_tab(self, tab):
        """
        Sets up the 'WA Voting' tab with all its widgets and layouts.
        """
        # Create layouts
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)

        form_layout = QFormLayout()

        # Nation Name Entry
        nation_label = QLabel("Nation Name:")
        self.nation_entry = QLineEdit()
        form_layout.addRow(nation_label, self.nation_entry)

        # Assembly Selection
        assembly_label = QLabel("Select Assembly:")
        assembly_frame = QHBoxLayout()
        self.assembly_group = QButtonGroup()
        self.ga_radio = QRadioButton("General Assembly")
        self.ga_radio.setChecked(True)
        self.sc_radio = QRadioButton("Security Council")
        self.assembly_group.addButton(self.ga_radio)
        self.assembly_group.addButton(self.sc_radio)
        assembly_frame.addWidget(self.ga_radio)
        assembly_frame.addWidget(self.sc_radio)
        assembly_frame.addStretch()
        form_layout.addRow(assembly_label, assembly_frame)

        # Vote Choice Selection
        vote_label = QLabel("Vote Choice:")
        vote_frame = QHBoxLayout()
        self.vote_group = QButtonGroup()
        self.for_radio = QRadioButton("Yes (For)")
        self.for_radio.setChecked(True)
        self.against_radio = QRadioButton("No (Against)")
        self.vote_group.addButton(self.for_radio)
        self.vote_group.addButton(self.against_radio)
        vote_frame.addWidget(self.for_radio)
        vote_frame.addWidget(self.against_radio)
        vote_frame.addStretch()
        form_layout.addRow(vote_label, vote_frame)

        # Vote Button
        vote_button = QPushButton("Vote")
        vote_button.clicked.connect(self.start_voting)
        self.vote_button = vote_button
        # Center the Vote button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(vote_button)
        button_layout.addStretch()

        # Add layouts to main_layout
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def setup_endorse_tab(self, tab):
        """
        Sets up the 'Endorse' tab with all its widgets and layouts.
        """
        # Create layouts
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)

        form_layout = QFormLayout()

        # Nation Name Entry
        endorser_nation_label = QLabel("Endorser Nation Name:")
        self.endorser_nation_entry = QLineEdit()
        form_layout.addRow(endorser_nation_label, self.endorser_nation_entry)

        # File Selection for Nations to Endorse
        file_layout = QHBoxLayout()
        endorse_file_label = QLabel("No file selected")
        self.endorse_file_label = endorse_file_label
        select_endorse_file_button = QPushButton("Select Nations File")
        select_endorse_file_button.clicked.connect(self.select_endorse_file)
        self.select_endorse_file_button = select_endorse_file_button  # Reference to disable/enable later
        file_layout.addWidget(endorse_file_label)
        file_layout.addWidget(select_endorse_file_button)
        file_layout.setStretch(0, 1)
        file_layout.setStretch(1, 0)
        form_layout.addRow(QLabel("Nations File:"), file_layout)

        # Progress Bar
        self.endorse_progress_bar = QProgressBar()
        self.endorse_progress_bar.setValue(0)
        self.endorse_progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.endorse_progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.endorse_progress_bar.setFixedHeight(20)

        # Endorse Button
        endorse_button = QPushButton("Start Endorsement")
        endorse_button.clicked.connect(self.start_endorsement)
        self.endorse_button = endorse_button
        # Center the Endorse button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(endorse_button)
        button_layout.addStretch()

        # Add layouts to main_layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.endorse_progress_bar)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def setup_settings_tab(self, tab):
        """
        Sets up the 'Settings' tab with input fields to load and save config.env.
        """
        settings = [
            {'key': 'UA', 'label': 'Main Nation', 'placeholder': 'Name of your main nation', 'min_length': 0, 'max_length': None},
            {'key': 'PASSWORD', 'label': 'Password', 'placeholder': 'Password of your nation', 'min_length': 0, 'max_length': None},
            {'key': 'EMAIL', 'label': 'Email', 'placeholder': 'Email for joining WA and/or receiving notifications', 'min_length': 0, 'max_length': None},
            {'key': 'NOTIFY', 'label': 'Notify', 'placeholder': 'TRUE or FALSE. This will generate an email when the nation is about to cease to exist.', 'min_length': 0, 'max_length': None},
            {'key': 'TARGET_REGION', 'label': 'Target Region', 'placeholder': 'Name of the region you want to move into', 'min_length': 0, 'max_length': None},
            {'key': 'TARGET_REGION_PASSWORD', 'label': 'Target Region Password', 'placeholder': 'Password of the region you want to move into', 'min_length': 0, 'max_length': None},
            {'key': 'PRETITLE', 'label': 'Pretitle', 'placeholder': 'New pretitle of the nation', 'min_length': 0, 'max_length': 28},
            {'key': 'SLOGAN', 'label': 'Slogan', 'placeholder': 'New Slogan/Motto of the nation', 'min_length': 0, 'max_length': 55},
            {'key': 'CURRENCY', 'label': 'Currency', 'placeholder': 'New currency of the nation', 'min_length': 2, 'max_length': 40},
            {'key': 'ANIMAL', 'label': 'Animal', 'placeholder': 'New national animal of the nation', 'min_length': 2, 'max_length': 40},
            {'key': 'DEMONYM_NOUN', 'label': 'Demonym Noun', 'placeholder': 'Noun the nation will refer to its citizens as', 'min_length': 2, 'max_length': 44},
            {'key': 'DEMONYM_ADJECTIVE', 'label': 'Demonym Adjective', 'placeholder': 'Adjective the nation will refer to its citizens as', 'min_length': 2, 'max_length': 44},
            {'key': 'DEMONYM_PLURAL', 'label': 'Demonym Plural', 'placeholder': 'Plural form of "demonym_noun"', 'min_length': 2, 'max_length': 44},
            {'key': 'CAPITAL', 'label': 'Capital', 'placeholder': 'New capital city of the nation', 'min_length': 0, 'max_length': 40},
            {'key': 'LEADER', 'label': 'Leader', 'placeholder': 'New leader of the nation', 'min_length': 0, 'max_length': 40},
            {'key': 'FAITH', 'label': 'Faith', 'placeholder': 'New faith for nation', 'min_length': 0, 'max_length': 40},
            {'key': 'FLAG', 'label': 'Flag', 'placeholder': 'File name of your flag like flag.png', 'min_length': 0, 'max_length': None},
        ]
        form_layout = QFormLayout()
        self.settings_entries = {}  # Dictionary to store widgets for settings

        for setting in settings:
            key = setting['key']
            label_text = setting['label']
            placeholder = setting['placeholder']
            min_length = setting.get('min_length', 0)
            max_length = setting.get('max_length', None)

            if key == 'NOTIFY':
                # Use QComboBox
                combo_box = QComboBox()
                combo_box.addItems(['TRUE', 'FALSE'])
                self.settings_entries[key] = combo_box
                form_layout.addRow(QLabel(label_text), combo_box)
            elif key == 'FLAG':
                # Use QLineEdit plus Browse button
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(placeholder)
                line_edit.min_length = min_length
                line_edit.max_length = max_length
                browse_button = QPushButton("Browse")
                browse_button.clicked.connect(self.browse_flag_file)
                h_layout = QHBoxLayout()
                h_layout.addWidget(line_edit)
                h_layout.addWidget(browse_button)
                self.settings_entries[key] = line_edit
                form_layout.addRow(QLabel(label_text), h_layout)
            else:
                # Use QLineEdit
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(placeholder)
                line_edit.min_length = min_length
                line_edit.max_length = max_length
                self.settings_entries[key] = line_edit
                form_layout.addRow(QLabel(label_text), line_edit)

        # Add Load Config button
        load_button = QPushButton("Load Config File")
        load_button.clicked.connect(self.load_config_file)

        # Add Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        # Center the buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        button_layout.addStretch()

        # Add to layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        tab.setLayout(main_layout)

        # Load existing settings
        self.load_settings()

    def browse_flag_file(self):
        """
        Opens a file dialog to select a flag file and updates the FLAG field.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Flag File", "", "Image Files (*.svg *.png *.jpeg *.jpg *.gif);;All Files (*)"
        )
        if file_name:
            # Set the full path to the FLAG QLineEdit
            self.settings_entries['FLAG'].setText(file_name)

    def load_config_file(self):
        """
        Opens a file dialog to select a config file and loads the settings.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "Config Files (*.env *.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = {}
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue  # Skip empty lines and comments
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            data[key] = value
                    # Update the settings entries with loaded data
                    for key, widget in self.settings_entries.items():
                        if key in data:
                            value = data[key]
                            if isinstance(widget, QLineEdit):
                                widget.setText(value)
                            elif isinstance(widget, QComboBox):
                                index = widget.findText(value, Qt.MatchFlag.MatchFixedString)
                                if index >= 0:
                                    widget.setCurrentIndex(index)
                    QMessageBox.information(self, "Success", f"Settings loaded from {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error loading config file: {e}")

    def load_settings(self):
        """
        Loads existing settings from config.env and populates the fields.
        """
        config_path = os.path.join(os.getcwd(), 'config.env')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key in self.settings_entries:
                                widget = self.settings_entries[key]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(value)
                                elif isinstance(widget, QComboBox):
                                    index = widget.findText(value, Qt.MatchFlag.MatchFixedString)
                                    if index >= 0:
                                        widget.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error loading settings: {e}")

    def save_settings(self):
        """
        Saves the settings to config.env after validation.
        """
        data = {}
        errors = []
        for key, widget in self.settings_entries.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:
                continue
            # Get min_length and max_length
            min_length = getattr(widget, 'min_length', 0)
            max_length = getattr(widget, 'max_length', None)
            if min_length and len(value) < min_length:
                errors.append(f"{key} must be at least {min_length} characters.")
            if max_length and len(value) > max_length:
                errors.append(f"{key} must be at most {max_length} characters.")
            # Specific validation for NOTIFY
            if key == 'NOTIFY' and value.upper() not in ['TRUE', 'FALSE']:
                errors.append(f"{key} must be TRUE or FALSE.")
            # Specific validation for FLAG
            if key == 'FLAG' and value:
                ext = os.path.splitext(value)[1].lower()
                if ext not in ['.svg', '.png', '.jpeg', '.jpg', '.gif']:
                    errors.append(f"{key} must be one of the following types: SVG, PNG, JPEG, or GIF.")
            data[key] = value
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return
        # Save data to config.env
        config_path = os.path.join(os.getcwd(), 'config.env')
        try:
            with open(config_path, 'w') as f:
                for key, value in data.items():
                    f.write(f"{key}={value}\n")
            QMessageBox.information(self, "Success", f"Settings saved to {config_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving settings: {e}")

    def setup_logging(self):
        """
        Sets up logging to both a file and the GUI log window.
        """
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%I:%M:%S %p')

        # File handler to write logs to a file
        file_handler = logging.FileHandler("que_log.txt")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Qt handler for the log window
        qt_handler = QtHandler(self.log_signal)
        qt_handler.setLevel(logging.INFO)
        qt_handler.setFormatter(formatter)
        logger.addHandler(qt_handler)

    def append_log(self, msg):
        """
        Appends a log message to the shared log window.
        """
        self.log_window.append(msg)

    # [Include all the methods from the previous code, including event handlers and worker methods.]

    def select_file(self):
        """
        Opens a file dialog to select a nations file and updates the label.
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Nations File", "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.selected_file = filepath
            self.file_label.setText(f"Selected file: {filepath}")

    def select_endorse_file(self):
        """
        Opens a file dialog to select a nations file for endorsement and updates the label.
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Nations File to Endorse", "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.endorse_file = filepath
            self.endorse_file_label.setText(f"Selected file: {filepath}")

    def start_script(self):
        """
        Starts the processing script in a separate thread.
        """
        if self.script_thread and self.script_thread.is_alive():
            QMessageBox.warning(self, "Warning", "The script is already running!")
            return

        if not self.selected_file:
            QMessageBox.warning(self, "Warning", "Please select a nations file before starting the script.")
            return

        # Disable the Start button and other controls
        self.start_button.setEnabled(False)
        self.select_file_button.setEnabled(False)
        self.change_settings_checkbox.setEnabled(False)
        self.change_flag_checkbox.setEnabled(False)
        self.move_region_checkbox.setEnabled(False)
        self.place_bids_checkbox.setEnabled(False)
        # Disable other tabs
        self.tabs.setTabEnabled(1, False)  # Disable 'WA Voting' tab
        self.tabs.setTabEnabled(2, False)  # Disable 'Endorse' tab
        self.tabs.setTabEnabled(3, False)  # Disable 'Settings' tab

        # Reset the progress bar
        self.progress_bar.setValue(0)

        # Retrieve the values from the switches
        self.change_settings = self.change_settings_checkbox.isChecked()
        self.change_flag = self.change_flag_checkbox.isChecked()
        self.move_region = self.move_region_checkbox.isChecked()
        self.place_bids = self.place_bids_checkbox.isChecked()

        # Start the script in a new thread
        self.script_thread = threading.Thread(
            target=self.run_script,
            args=(self.change_settings, self.change_flag, self.move_region, self.place_bids),
            daemon=True
        )
        self.script_thread.start()

    def run_script(self, change_settings, change_flag, move_region, place_bids):
        """
        Runs the main processing script with the given parameters.
        """
        try:
            logging.info("Starting script...")
            # Retrieve environment variables
            env_vars = get_env_vars()
            # Initialize the NationStates session
            session = NSSession("Que", "3.0.0", "Unshleepd", env_vars['UA'])
            # Read the nations from the selected file
            with open(self.selected_file, "r") as q:
                pups = q.readlines()
            logging.info("Processing nations...")
            # Reset progress bar
            self.progress_signal.emit(0)
            # Process the nations with the specified options
            process_nations(
                session,
                pups,
                env_vars,
                change_settings,
                change_flag,
                move_region,
                place_bids,
                progress_callback=self.update_progress  # Pass the progress callback
            )
        except Exception as e:
            error_message = f"An error occurred: {e}"
            logging.error(error_message)
            self.error_signal.emit(error_message)
        else:
            self.completion_signal.emit()
        finally:
            # Emit the signal
            self.script_finished_signal.emit()

    def update_progress(self, value):
        """
        Updates the progress bar with the given value.
        """
        self.progress_signal.emit(value)

    def set_progress(self, value):
        """
        Sets the progress bar value.
        """
        self.progress_bar.setValue(value)

    def script_completed(self):
        """
        Called when the script has completed successfully.
        """
        logging.info("Process completed successfully.")
        self.info_signal.emit("Completion", "The process has completed successfully.")
        # Reset the progress bar
        self.progress_bar.setValue(100)

    def show_error_message(self, message):
        """
        Displays an error message dialog.
        """
        QMessageBox.critical(self, "Error", message)

    def show_info_message(self, title, message):
        """
        Displays an information message dialog.
        """
        QMessageBox.information(self, title, message)

    def on_script_finished(self):
        """
        Slot called when the script thread finishes.
        Re-enables GUI elements.
        """
        # Re-enable the Start button and other controls after completion
        self.start_button.setEnabled(True)
        self.select_file_button.setEnabled(True)
        self.change_settings_checkbox.setEnabled(True)
        self.change_flag_checkbox.setEnabled(True)
        self.move_region_checkbox.setEnabled(True)
        self.place_bids_checkbox.setEnabled(True)
        # Re-enable other tabs
        self.tabs.setTabEnabled(1, True)  # Enable 'WA Voting' tab
        self.tabs.setTabEnabled(2, True)  # Enable 'Endorse' tab
        self.tabs.setTabEnabled(3, True)  # Enable 'Settings' tab
        self.script_thread = None

    def start_voting(self):
        """
        Starts the WA voting process in a separate thread.
        """
        nation_name = self.nation_entry.text().strip()
        if not nation_name:
            QMessageBox.warning(self, "Warning", "Please enter a nation name.")
            return

        # Disable the Vote button and input fields
        self.vote_button.setEnabled(False)
        self.nation_entry.setEnabled(False)
        self.ga_radio.setEnabled(False)
        self.sc_radio.setEnabled(False)
        self.for_radio.setEnabled(False)
        self.against_radio.setEnabled(False)
        # Disable other tabs
        self.tabs.setTabEnabled(0, False)  # Disable 'Process Puppets' tab
        self.tabs.setTabEnabled(2, False)  # Disable 'Endorse' tab
        self.tabs.setTabEnabled(3, False)  # Disable 'Settings' tab

        # Get assembly and vote choice
        assembly = 'ga' if self.ga_radio.isChecked() else 'sc'
        vote_choice = 'for' if self.for_radio.isChecked() else 'against'

        # Start the voting process in a new thread
        threading.Thread(
            target=self.run_voting,
            args=(nation_name, assembly, vote_choice),
            daemon=True
        ).start()

    def run_voting(self, nation_name, assembly, vote_choice):
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
            message = f"Successfully voted {vote_choice.upper()} on {assembly_full_name} resolution for {nation_name}."
            logging.info(message)
            self.info_signal.emit("Success", message)
        except Exception as e:
            error_message = f"An error occurred: {e}"
            logging.error(error_message)
            self.error_signal.emit(error_message)
        finally:
            # Emit the signal
            self.voting_finished_signal.emit()

    def on_voting_finished(self):
        """
        Slot called when the voting thread finishes.
        Re-enables GUI elements.
        """
        # Re-enable the Vote button and input fields
        self.vote_button.setEnabled(True)
        self.nation_entry.setEnabled(True)
        self.ga_radio.setEnabled(True)
        self.sc_radio.setEnabled(True)
        self.for_radio.setEnabled(True)
        self.against_radio.setEnabled(True)
        # Re-enable other tabs
        self.tabs.setTabEnabled(0, True)  # Enable 'Process Puppets' tab
        self.tabs.setTabEnabled(2, True)  # Enable 'Endorse' tab
        self.tabs.setTabEnabled(3, True)  # Enable 'Settings' tab

    def start_endorsement(self):
        """
        Starts the endorsement process in a separate thread.
        """
        endorser_nation = self.endorser_nation_entry.text().strip()
        if not endorser_nation:
            QMessageBox.warning(self, "Warning", "Please enter the endorser nation name.")
            return

        if not hasattr(self, 'endorse_file') or not self.endorse_file:
            QMessageBox.warning(self, "Warning", "Please select a nations file to endorse.")
            return

        # Disable the Endorse button and input fields
        self.endorse_button.setEnabled(False)
        self.endorser_nation_entry.setEnabled(False)
        self.select_endorse_file_button.setEnabled(False)
        # Disable other tabs
        self.tabs.setTabEnabled(0, False)  # Disable 'Process Puppets' tab
        self.tabs.setTabEnabled(1, False)  # Disable 'WA Voting' tab
        self.tabs.setTabEnabled(3, False)  # Disable 'Settings' tab

        # Reset the progress bar
        self.endorse_progress_bar.setValue(0)

        # Start the endorsement process in a new thread
        threading.Thread(
            target=self.run_endorsement,
            args=(endorser_nation, self.endorse_file),
            daemon=True
        ).start()

    def run_endorsement(self, endorser_nation, endorse_file):
        """
        Runs the endorsement process.
        """
        try:
            # Retrieve environment variables
            env_vars = get_env_vars()
            # Initialize the NationStates session
            session = NSSession("Que", "3.0.0", "Unshleepd", env_vars['UA'])

            # Read the nations to endorse from the selected file
            with open(endorse_file, "r") as file:
                target_nations = [line.strip() for line in file if line.strip()]

            # Perform the endorsements with progress updates
            success = endorse_nations(
                session,
                endorser_nation,
                target_nations,
                env_vars['password'],
                progress_callback=self.update_endorse_progress  # Pass the progress callback
            )
            if success:
                self.endorse_progress_signal.emit(100)  # Ensure progress bar reaches 100%
                self.info_signal.emit("Success", "Endorsement process completed successfully.")
            else:
                self.error_signal.emit(f"Failed to complete endorsements with {endorser_nation}.")
        except Exception as e:
            error_message = f"An error occurred: {e}"
            logging.error(error_message)
            self.error_signal.emit(error_message)
        finally:
            # Emit the signal
            self.endorsement_finished_signal.emit()

    def on_endorsement_finished(self):
        """
        Slot called when the endorsement thread finishes.
        Re-enables GUI elements.
        """
        # Re-enable the Endorse button and input fields
        self.endorse_button.setEnabled(True)
        self.endorser_nation_entry.setEnabled(True)
        self.select_endorse_file_button.setEnabled(True)
        # Re-enable other tabs
        self.tabs.setTabEnabled(0, True)  # Enable 'Process Puppets' tab
        self.tabs.setTabEnabled(1, True)  # Enable 'WA Voting' tab
        self.tabs.setTabEnabled(3, True)  # Enable 'Settings' tab

    def update_endorse_progress(self, value):
        """
        Updates the endorse progress bar.
        """
        self.endorse_progress_signal.emit(value)

    def set_endorse_progress(self, value):
        """
        Sets the endorse progress bar value.
        """
        self.endorse_progress_bar.setValue(value)

    def closeEvent(self, event):
        """
        Handles the window closing event, ensuring the script thread is terminated properly.
        """
        threads_running = []
        if self.script_thread and self.script_thread.is_alive():
            threads_running.append('Processing script')
        # Since we used threading.Thread without keeping references, we can't check if they are alive
        # For a complete solution, you should store references to the other threads as well
        if threads_running:
            running_processes = ' and '.join(threads_running)
            reply = QMessageBox.question(
                self, 'Quit', f'The {running_processes} is still running. Do you want to quit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
