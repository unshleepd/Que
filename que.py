# -*- coding: utf-8 -*-
"""
This script facilitates various operations related to NationStates, including
nation creation, changing nation settings, moving to a different region, and placing
bids on cards.
"""
import os
import logging
from dotenv import load_dotenv
from nsdotpy.session import NSSession
from xml.etree import ElementTree as ET


# Set up basic logging configuration
logging.basicConfig(filename='que.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


# Load environment variables from .env file
load_dotenv('config.env')
load_dotenv('cards.env')


def get_env_vars():
    """
    Extract environment variables from the loaded .env files. Raise an error if any required
    variables are missing.

    Returns:
        dict: A dictionary mapping environment variable names to their values.
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
        'card_ids': os.getenv('CARD_IDS').split(',') if os.getenv('CARD_IDS') else None,
        'seasons': os.getenv('SEASONS').split(',') if os.getenv('SEASONS') else None,
        'prices': os.getenv('PRICES').split(',') if os.getenv('PRICES') else None,
    }
    missing_vars = [k for k, v in env_vars.items() if v is None and k not in ['card_ids', 'seasons', 'prices']]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

    return env_vars


def check_population(session, nation):
    """
    Check the population of a nation.

    Parameters:
        session (NSSession): The current NationStates session.
        nation (str): The name of the nation whose population is to be checked.

    Returns:
        int: The population of the nation.
    """
    data = {"nation": nation, "q": "population"}
    response = session.api_request(data, _auth=None)
    root = ET.fromstring(response.text)
    population = int(root.find('POPULATION').text)
    
    return population


def bid_on_cards(session, env_vars):
    """
    Bid on cards with the given ids, seasons and prices.

    Parameters:
        session (NSSession): The current NationStates session.
        env_vars (dict): A dictionary of environment variables.
    """
    for card_id, season, price in zip(env_vars['card_ids'], env_vars['seasons'], env_vars['prices']):
        try:
            session.bid(price, card_id, season)
            logging.info(f"Successfully placed bid for card {card_id} in season {season} with price {price}")
        except Exception as e:
            logging.error(f"Error placing bid for card {card_id} in season {season} with price {price}: {e}")



def prompt_execution(prompt_message):
    """
    Prompt the user for execution of an operation and handle their response.

    Parameters:
        prompt_message (str): Message to display to the user for the prompt.

    Returns:
        bool: True if the user's response was 'y', otherwise False.
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


def create_nation(session, nation, env_vars):
    """
    Try to create a nation and log the result.

    Parameters:
        session (NSSession): The current NationStates session.
        nation (str): The name of the nation to be created.
        env_vars (dict): A dictionary of environment variables.
    """

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
    """
    Try to change a nation's settings and log the result.

    Parameters:
        session (NSSession): The current NationStates session.
        nation (str): The name of the nation whose settings are to be changed.
        env_vars (dict): A dictionary of environment variables.
    """

    try:
        settings = {
            'email': env_vars['email'],
            'slogan': env_vars['slogan'],
            'currency': env_vars['currency'],
            'animal': env_vars['animal'],
            'demonym_noun': env_vars['demonym_noun'],
            'demonym_adjective': env_vars['demonym_adjective'],
            'demonym_plural': env_vars['demonym_plural']
        }

        # Assuming check_population(session, nation) returns the population of a nation
        population = check_population(session, nation)
        if population >= 250:
            settings['pretitle'] = env_vars['pretitle']
        else:
            print(f"The population of nation {nation} is less than 250 million. Hence, pretitle cannot be changed.")
        
        session.change_nation_settings(**settings)

        with open("response.html", "w", encoding="utf-8") as f:
            f.write(session.current_page[1])
        logging.info(f"Successfully changed settings for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing settings for nation {nation}: {e}")




def change_nation_flag(session, nation, env_vars):
    """
    Try to change a nation's flag and log the result.

    Parameters:
        session (NSSession): The current NationStates session.
        nation (str): The name of the nation whose flag is to be changed.
        env_vars (dict): A dictionary of environment variables.
    """

    try:
        session.change_nation_flag(env_vars['flag'])
        logging.info(f"Successfully changed flag for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing flag for nation {nation}: {e}")


def move_to_region(session, nation, env_vars):
    """
    Try to move a nation to a target region and log the result.

    Parameters:
        session (NSSession): The current NationStates session.
        nation (str): The name of the nation that is to be moved.
        env_vars (dict): A dictionary of environment variables.
    """

    try:
        session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        logging.info(f"Successfully moved nation {nation} to target region")
    except Exception as e:
        logging.error(f"Error moving nation {nation} to target region: {e}")


def process_nations(session, nations, env_vars):
    """
    Process nations from the list, checking if they can be founded, logging in, and performing various actions based on user prompts.

    Parameters:
        session (NSSession): The current NationStates session.
        nations (list): A list of nation names to be processed.
        env_vars (dict): A dictionary of environment variables.
    """

    for each in nations:
        each = each.strip()
        skip_login = False

        # Check if the nation can be founded
        if session.can_nation_be_founded(each):
            if prompt_execution(f"Do you want to create {each}? (y/n): "):
                create_nation(session, each, env_vars)
            else:
                skip_login = True

        # Try to log in to the nation
        if not skip_login and session.login(each, env_vars['password']):
            # Call the settings function
            if prompt_execution(f"Do you want to change {each} settings? (y/n): "):
                change_nation_settings(session, each, env_vars)

            # Call the flag function
            if prompt_execution(f"Do you want to change {each} flag? (y/n): "):
                change_nation_flag(session, each, env_vars)

            # Call the mover function
            if prompt_execution(f"Do you want to move {each} to target region? (y/n): "):
                move_to_region(session, each, env_vars)
                
            # Call the bidding function
            if prompt_execution(f"Do you want to place bids? (y/n): "):
                bid_on_cards(session, env_vars)   
        elif not skip_login:
            print(f"Could not login with {each}")
            input("Slow down and try again.")


def main():
    """
    Entry point for the script. Initializes an NSSession, extracts environment variables,
    reads the list of nations, and processes each nation in turn.

    Exceptions are caught and logged to a file.
    """

    try:
        env_vars = get_env_vars()
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])
        with open("que.txt", "r") as q:
            pups = q.readlines()

        process_nations(session, pups, env_vars)
        

    except EnvironmentError as e:
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
