from tkinter import Tk, Label, Entry, Button
from nsdotpy.session import NSSession
from dotenv import load_dotenv
import os

def change_nation_settings():
    # Code to change nation settings
    pass

def change_nation_flag():
    # Code to change nation flag
    pass

def move_to_region():
    # Code to move nation to the target region
    pass

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Access environment variables
    UA = os.getenv("UA")
    password = os.getenv("PASSWORD")
    email = os.getenv("EMAIL")
    tregion = os.getenv("TARGET_REGION")
    tregpassword = os.getenv("TARGET_REGION_PASSWORD")

    def on_submit():
        # Get input values from the GUI
        ua = user_agent_entry.get()
        password = password_entry.get()
        email = email_entry.get()
        tregion = target_region_entry.get()
        tregpassword = target_region_password_entry.get()

        # Create an NSSession object
        session = NSSession("Que", "1.0.0", "Unshleepd", ua)

        try:
            with open("que.txt", "r") as q:
                pups = q.readlines()

            for each in pups:
                each = each.strip()
                if session.login(each, password):
                    # Change nation settings if selected
                    if change_settings_var.get() == 1:
                        change_nation_settings()
                        print("Nation settings changed.")

                    with open("response.html", "w", encoding="utf-8") as f:
                        f.write(session.current_page[1])

                    # Change nation flag if selected
                    if change_flag_var.get() == 1:
                        change_nation_flag()
                        print("Nation flag changed.")

                    # Move nation to the target region if selected
                    if move_region_var.get() == 1:
                        move_to_region()
                        print("Nation moved to the target region.")

                else:
                    print("Slow down and try again.")

        except Exception as e:
            # Handle exceptions
            print(f"An error occurred: {str(e)}")

    # Create the GUI
    root = Tk()
    root.title("Nation App")

    user_agent_label = Label(root, text="User agent:")
    user_agent_label.pack()
    user_agent_entry = Entry(root)
    user_agent_entry.pack()

    password_label = Label(root, text="Password:")
    password_label.pack()
    password_entry = Entry(root, show="*")
    password_entry.pack()

    email_label = Label(root, text="Email:")
    email_label.pack()
    email_entry = Entry(root)
    email_entry.pack()

    target_region_label = Label(root, text="Target region:")
    target_region_label.pack()
    target_region_entry = Entry(root)
    target_region_entry.pack()

    target_region_password_label = Label(root, text="Target region password:")
    target_region_password_label.pack()
    target_region_password_entry = Entry(root, show="*")
    target_region_password_entry.pack()

    change_settings_var = IntVar()
    change_settings_checkbox = Checkbutton(root, text="Change nation settings", variable=change_settings_var)
    change_settings_checkbox.pack()

    change_flag_var = IntVar()
    change_flag_checkbox = Checkbutton(root, text="Change nation flag", variable=change_flag_var)
    change_flag_checkbox.pack()

    move_region_var = IntVar()
    move_region_checkbox = Checkbutton(root, text="Move nation to target region", variable=move_region_var)
    move_region_checkbox.pack()

    submit_button = Button(root, text="Submit", command=on_submit)
    submit_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
