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

# Set up basic logging configuration
logging.basicConfig(
    filename='que.log',      # Log file name
    filemode='w',            # Overwrite the log file on each run
    format='%(name)s - %(levelname)s - %(message)s',  # Log message format
    level=logging.DEBUG      # Log level set to DEBUG
)

# Load environment variables from .env files
load_dotenv('config.env')  # Load general configuration variables
load_dotenv('cards.env')   # Load card trading variables

def get_env_vars():
    """
    Extracts and validates environment variables from the loaded .env files.

    Raises:
        EnvironmentError: If any required variables are missing.

    Returns:
        dict: A dictionary mapping environment variable names to their values.
    """
    # Define the environment variables we need and extract them from the environment
    env_vars = {
        # Various nation attributes
        'UA': os.getenv('UA'),  # User Agent string for API requests
        'password': os.getenv('PASSWORD'),  # Nation password
        'email': os.getenv('EMAIL'),  # Email address associated with the nation
        'notify': os.getenv('NOTIFY'),  # Notification settings
        'pretitle': os.getenv('PRETITLE'),  # Nation pretitle (requires population >= 250 million)
        'slogan': os.getenv('SLOGAN'),  # Nation slogan
        'currency': os.getenv('CURRENCY'),  # Nation's currency
        'animal': os.getenv('ANIMAL'),  # National animal
        'demonym_noun': os.getenv('DEMONYM_NOUN'),  # Demonym noun
        'demonym_adjective': os.getenv('DEMONYM_ADJECTIVE'),  # Demonym adjective
        'demonym_plural': os.getenv('DEMONYM_PLURAL'),  # Demonym plural
        'capital': os.getenv('CAPITAL'),  # Capital city
        'leader': os.getenv('LEADER'),  # Leader's name
        'faith': os.getenv('FAITH'),  # National faith
        'target_region': os.getenv('TARGET_REGION'),  # Target region to move to
        'target_region_password': os.getenv('TARGET_REGION_PASSWORD'),  # Password for the target region (if any)
        'flag': os.getenv('FLAG'),  # URL or path to the new flag image

        # Card trading information
        'card_ids': os.getenv('CARD_IDS').split(',') if os.getenv('CARD_IDS') else None,  # List of card IDs
        'seasons': os.getenv('SEASONS').split(',') if os.getenv('SEASONS') else None,     # Corresponding seasons for the cards
        'prices': os.getenv('PRICES').split(',') if os.getenv('PRICES') else None,        # Corresponding prices for the cards
    }
    
    # Check for missing required environment variables
    missing_vars = [k for k, v in env_vars.items() if v is None and k not in ['card_ids', 'seasons', 'prices']]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

    return env_vars

def check_population(session, nation):
    """
    Queries the NationStates API to retrieve the population of a specific nation.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose population is to be checked.

    Returns:
        int: The population of the nation.
    """
    # Make an API request to get the nation's population
    response = session.api_request(api="nation", target=nation, shard="population")
    # The population is returned as a string, convert it to integer
    population = int(response['population'])
    
    return population

def bid_on_cards(session, env_vars):
    """
    Attempts to place bids on a list of cards.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        env_vars (dict): A dictionary of environment variables, which must include 'card_ids',
                         'seasons', and 'prices'.
    """
    # Loop over each card to place a bid
    for card_id, season, price in zip(env_vars['card_ids'], env_vars['seasons'], env_vars['prices']):
        try:
            # Place a bid on the card
            session.bid(price, card_id, season)
            logging.info(f"Successfully placed bid for card {card_id} in season {season} with price {price}")
        except Exception as e:
            logging.error(f"Error placing bid for card {card_id} in season {season} with price {price}: {e}")

def create_nation(session, nation, env_vars):
    """
    Attempts to create a new nation using the provided session and details.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation to be created.
        env_vars (dict): A dictionary of environment variables containing nation details.
    """
    try:
        # Attempt to create a new nation with the given details
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
    Attempts to change a nation's settings.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose settings are to be changed.
        env_vars (dict): A dictionary of environment variables containing the new settings.
    """
    try:
        # Prepare the settings to be updated
        settings = {
            'email': env_vars['email'],
            'notify': env_vars['notify'],
            'slogan': env_vars['slogan'],
            'currency': env_vars['currency'],
            'animal': env_vars['animal'],
            'demonym_noun': env_vars['demonym_noun'],
            'demonym_adjective': env_vars['demonym_adjective'],
            'demonym_plural': env_vars['demonym_plural'],
            'capital': env_vars['capital'],
            'leader': env_vars['leader'],
            'faith': env_vars['faith']
        }

        # Check if the nation's population allows changing the pretitle
        population = check_population(session, nation)
        if population >= 250:
            settings['pretitle'] = env_vars['pretitle']
        else:
            print(f"The population of nation {nation} is less than 250 million. Hence, pretitle cannot be changed.")
        
        # Apply the new settings to the nation
        session.change_nation_settings(**settings)

        logging.info(f"Successfully changed settings for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing settings for nation {nation}: {e}")

def change_nation_flag(session, nation, env_vars):
    """
    Attempts to change a nation's flag.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose flag is to be changed.
        env_vars (dict): A dictionary of environment variables containing the new flag.
    """
    try:
        # Change the nation's flag using the provided flag data
        session.change_nation_flag(env_vars['flag'])
        logging.info(f"Successfully changed flag for nation {nation}")
    except Exception as e:
        logging.error(f"Error changing flag for nation {nation}: {e}")

def move_to_region(session, nation, env_vars):
    """
    Attempts to move a nation to a specified region.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation that is to be moved.
        env_vars (dict): A dictionary of environment variables containing the target region and password.
    """
    try:
        # Move the nation to the target region, using a password if necessary
        session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        logging.info(f"Successfully moved nation {nation} to target region")
    except Exception as e:
        logging.error(f"Error moving nation {nation} to target region: {e}")

def process_nations(session, nations, env_vars,new_nation, change_settings, change_flag, move_region, place_bids):
    """
    Processes a list of nations, performing operations based on the provided flags.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nations (list): A list of nation names to process.
        env_vars (dict): A dictionary of environment variables.
        new_nation (bool): Wheter to craete a new nation.
        change_settings (bool): Whether to change nation settings.
        change_flag (bool): Whether to change the nation's flag.
        move_region (bool): Whether to move the nation to a target region.
        place_bids (bool): Whether to place bids on cards.
    """
    for each in nations:
        each = each.strip()  # Remove any leading/trailing whitespace
        skip_login = False

        # Check if the nation can be founded (e.g., if the name is available)
        if session.can_nation_be_founded(each):
            if new_nation:
                create_nation(session, each, env_vars)
            else:
                skip_login = True  # Skip login since the nation doesn't exist yet

        # Try to log in to the nation
        if not skip_login and session.login(each, env_vars['password']):
            # Perform actions based on the provided flags
            if change_settings:
                change_nation_settings(session, each, env_vars)
            if change_flag:
                change_nation_flag(session, each, env_vars)
            if move_region:
                move_to_region(session, each, env_vars)
            if place_bids:
                bid_on_cards(session, env_vars)
        elif not skip_login:
            # Unable to log in to the nation
            print(f"Could not login with {each}")

def main():
    """
    Main function that orchestrates the processing of nations.
    """
    try:
        # Retrieve environment variables
        env_vars = get_env_vars()
        # Initialize the NationStates session
        session = NSSession("Que", "2.2.0", "Unshleepd", env_vars['UA'])
        # Read the list of nations from a file
        with open("que.txt", "r") as q:
            pups = q.readlines()

        # Process the nations with the specified operations
        process_nations(
            session,
            pups,
            env_vars,
            new_nation=True,
            change_settings=True,
            change_flag=True,
            move_region=True,
            place_bids=True
        )

    except EnvironmentError as e:
        # Handle missing environment variables
        logging.error(f"Configuration error: {e}")
    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
