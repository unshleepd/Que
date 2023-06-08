# -*- coding: utf-8 -*-
import os
from nsdotpy.session import NSSession
from dotenv import load_dotenv
import logging

load_dotenv('config.env')  # take environment variables from .env.

def get_env_vars():
    """
    Load all the environment variables and return them as a dictionary.
    Raises an error if any expected environment variable is missing.
    """
    env_vars = {
        'UA': os.getenv('UA'),
        'password': os.getenv('PASSWORD'),
        'email': os.getenv('EMAIL'),
        'pretitle': os.getenv('PRETITLE'),
        'slogan': os.getenv('SLOGAN'),
        'currency': os.getenv('CURRENCY'),
        'animal': os.getenv('ANIMAL'),
        'demonym_noun': os.getenv('DEMONYM_NOUN'),
        'demonym_adjective': os.getenv('DEMONYM_ADJECTIVE'),
        'demonym_plural': os.getenv('DEMONYM_PLURAL'),
        'target_region': os.getenv('TARGET_REGION'),
        'target_region_password': os.getenv('TARGET_REGION_PASSWORD'),
        'flag': os.getenv('FLAG'),
    }
    # Check all env_vars for any None value, which would indicate a missing environment variable
    missing_vars = [k for k, v in env_vars.items() if v is None]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
    return env_vars

def prompt_execution(prompt_message):
    """
    Prompt the user for a response and return a boolean based on their input.
    """
    response = input(prompt_message).strip().lower()
    if response == 'y':
        return True
    elif response == 'n':
        print("Skipping operation.")
        return False
    else:
        print("Invalid input, skipping operation.")
        return False

def process_nations(session, nations, env_vars):
    """
    Process each nation from the list of nations, prompting the user for each action.
    For each nation, first checks if the nation can be founded, and if so, prompts the user
    to decide whether to found it. If the user chooses not to found the nation, the script
    skips login for this nation and continues to the next.
    If the user chooses to found the nation, or if the nation cannot be founded, the script
    then tries to log in to the nation, prompting the user for each subsequent action.
    """
    for each in nations:
        each = each.strip()  
        skip_login = False  # Add this flag

        if session.can_nation_be_founded(each):
            if prompt_execution(f"Do you want to create {each}? (y/n): "):
                session.create_nation(
                    each,
                    env_vars['password'],
                    env_vars['email'],
                    env_vars['currency'],
                    env_vars['animal'],
                    env_vars['slogan']  # Assuming motto = slogan
                )
            else:
                skip_login = True  # Set the flag to True if user doesn't want to create the nation

        # Then check the flag before logging in
        if not skip_login and session.login(each, env_vars['password']):
            if prompt_execution(f"Do you want to change {each} settings? (y/n): "):
                session.change_nation_settings(
                    email=env_vars['email'],
                    pretitle=env_vars['pretitle'],
                    slogan=env_vars['slogan'],
                    currency=env_vars['currency'],
                    animal=env_vars['animal'],
                    demonym_noun=env_vars['demonym_noun'],
                    demonym_adjective=env_vars['demonym_adjective'],
                    demonym_plural=env_vars['demonym_plural']
                )
                with open("response.html", "w", encoding="utf-8") as f:
                    f.write(session.current_page[1])

            if prompt_execution(f"Do you want to change {each} flag? (y/n): "):
                session.change_nation_flag(env_vars['flag'])

            if prompt_execution(f"Do you want to move {each} to target region? (y/n): "):
                session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        elif not skip_login:
            print(f"Could not login with {each}")
            input("Slow down and try again.")

def main():
    """
    Main function to setup session and process nations.
    First, it loads the environment variables, making sure they're all present.
    Then it creates the session, loads the list of nations, and starts processing each nation.
    """
    try:
        env_vars = get_env_vars()
        session = NSSession("Que", "1.0.0", "Unshleepd", env_vars['UA'])
        with open("que.txt", "r") as q:
            pups = q.readlines()
        
        process_nations(session, pups, env_vars)

    except EnvironmentError as e:
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
