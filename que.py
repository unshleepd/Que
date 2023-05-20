# -*- coding: utf-8 -*-
from nsdotpy.session import NSSession
from dotenv import load_dotenv
import os

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Access environment variables
    UA = os.getenv("UA")
    password = os.getenv("PASSWORD")
    email = os.getenv("EMAIL")
    tregion = os.getenv("TARGET_REGION")
    tregpassword = os.getenv("TARGET_REGION_PASSWORD")
    
# Create an NSSession object
    session = NSSession("Que", "1.0.0", "Unshleepd", UA)
    try:
        # Read lines from que.txt
        with open("que.txt", "r") as q:
            pups = q.readlines()

        # Iterate over each line in que.txt
        for each in pups:
            each = each.strip()
            if session.login(each, password):
                # Prompt user if they want to change nation settings
                change_settings = input("Do you want to change the nation settings? (y/n): ")
                if change_settings.lower() == "y":
                    # Change nation settings
                    session.change_nation_settings(
                        email=email,
                        pretitle=os.getenv("PRETITLE"),
                        slogan=os.getenv("SLOGAN"),
                        currency=os.getenv("CURRENCY"),
                        animal=os.getenv("ANIMAL"),
                        demonym_noun=os.getenv("DEMONYM_NOUN"),
                        demonym_adjective=os.getenv("DEMONYM_ADJECTIVE"),
                        demonym_plural=os.getenv("DEMONYM_PLURAL")
                    )
                    print("Nation settings changed.")
                else:
                    print("Skipping nation settings change.")

                # Write current page response to response.html
                with open("response.html", "w", encoding="utf-8") as f:
                    f.write(session.current_page[1])
                
                # Prompt user if they want to change the nation flag
                change_flag = input("Do you want to change the nation flag? (y/n): ")
                if change_flag.lower() == "y":
                    session.change_nation_flag("flag.jpg")
                    print("Nation flag changed.")
                else:
                    print("Skipping nation flag change.")
                
                # Prompt user if they want to move the nation to the target region
                move_region = input("Do you want to move the nation to the target region? (y/n): ")
                if move_region.lower() == "y":
                    session.move_to_region(tregion, tregpassword)
                    print("Nation moved to the target region.")
                else:
                    print("Skipping nation move to the target region.")
                    
            else:
                input("Sloooooooooooooooooooooooooooooow down and try again.")
    except Exception as e:
        # Handle exceptions
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
