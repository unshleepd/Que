# -*- coding: utf-8 -*-
import os
from nsdotpy.session import NSSession
from dotenv import load_dotenv
import logging

load_dotenv('config.env')  # take environment variables from .env.

logging.basicConfig(filename='qie.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def get_env_vars():
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
    missing_vars = [k for k, v in env_vars.items() if v is None]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
    return env_vars

def prompt_execution(prompt_message):
    response = input(prompt_message).strip().lower()
    if response == 'y':
        return True
    elif response == 'n':
        print("Skipping operation.")
        return False
    else:
        print("Invalid input, skipping operation.")
        return False

def create_nation(session, nation, env_vars):
    try:
        session.create_nation(
            nation,
            env_vars['password'],
            env_vars['email'],
            env_vars['currency'],
            env_vars['animal'],
            env_vars['slogan']
        )
        logging.info(f"Successfully created nation {nation}")
    except Exception as e:
        logging.error(f"Error creating nation {nation}: {e}")

def change_nation_settings(session, nation, env_vars):
    try:
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
        logging.info(f"Successfully changed settings for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing settings for nation {nation}: {e}")

def change_nation_flag(session, nation, env_vars):
    try:
        session.change_nation_flag(env_vars['flag'])
        logging.info(f"Successfully changed flag for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing flag for nation {nation}: {e}")

def move_to_region(session, nation, env_vars):
    try:
        session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        logging.info(f"Successfully moved nation {nation} to target region")
    except Exception as e:
        logging.error(f"Error moving nation {nation} to target region: {e}")

def process_nations(session, nations, env_vars):
    for each in nations:
        each = each.strip()
        skip_login = False

        if session.can_nation_be_founded(each):
            if prompt_execution(f"Do you want to create {each}? (y/n): "):
                create_nation(session, each, env_vars)
            else:
                skip_login = True

        if not skip_login and session.login(each, env_vars['password']):
            if prompt_execution(f"Do you want to change {each} settings? (y/n): "):
                change_nation_settings(session, each, env_vars)

            if prompt_execution(f"Do you want to change {each} flag? (y/n): "):
                change_nation_flag(session, each, env_vars)

            if prompt_execution(f"Do you want to move {each} to target region? (y/n): "):
                move_to_region(session, each, env_vars)
        elif not skip_login:
            print(f"Could not login with {each}")
            input("Slow down and try again.")

def main():
    try:
        env_vars = get_env_vars()
        session = NSSession("Que", "2.0.1", "Unshleepd", env_vars['UA'])
        with open("que.txt", "r") as q:
            pups = q.readlines()
        
        process_nations(session, pups, env_vars)

    except EnvironmentError as e:
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
