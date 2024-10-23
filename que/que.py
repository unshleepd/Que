# que.py
# -*- coding: utf-8 -*-
"""
This script facilitates various operations related to NationStates, including
changing nation settings, moving to a different region, and placing bids on cards.

Functions:
- get_env_vars(): Extracts and validates environment variables.
- check_population(session, nation): Retrieves the population of a nation.
- bid_on_cards(session, env_vars): Places bids on specified cards.
- change_nation_settings(session, nation, env_vars): Updates a nation's settings.
- change_nation_flag(session, nation, env_vars): Changes a nation's flag.
- move_to_region(session, nation, env_vars): Moves a nation to a target region.
- process_nations(session, nations, env_vars, change_settings, change_flag, move_region, place_bids): Processes a list of nations.
- main(): Main function to orchestrate nation processing.
"""

import os  # Module for interacting with the operating system
import logging  # Module for logging messages
from dotenv import load_dotenv  # Function to load environment variables from a .env file
from nsdotpy.session import NSSession  # Import NSSession class from nsdotpy library

# Get a logger for this module
logger = logging.getLogger(__name__)
"""
Initializes and returns a logger instance for this module.
"""

# Load environment variables from .env files
load_dotenv('config.env')  # Load general configuration variables from config.env
load_dotenv('cards.env')   # Load card trading variables from cards.env

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
    # Exclude 'card_ids', 'seasons', and 'prices' since they are optional
    missing_vars = [k for k, v in env_vars.items() if v is None and k not in ['card_ids', 'seasons', 'prices']]
    if missing_vars:
        # Raise an error if any required variables are missing
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}.")

    return env_vars  # Return the dictionary of environment variables




def check_population(session, nation):
    """
    Queries the NationStates API to retrieve the population of a specific nation.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose population is to be checked.

    Returns:
        int: The population of the nation in millions.
    """
    # Make an API request to get the nation's population
    response = session.api_request(api="nation", target=nation, shard="population")
    # The population is returned as a string, convert it to an integer
    population = int(response['population'])

    return population  # Return the population value

def bid_on_cards(session, env_vars):
    """
    Attempts to place bids on a list of cards.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        env_vars (dict): A dictionary of environment variables, which must include 'card_ids',
                         'seasons', and 'prices'.

    Logs:
        Info: Successful bid placement.
        Warning: Missing card trading variables.
        Error: Errors encountered during bid placement.
    """
    # Check if card trading variables are available
    if not all([env_vars['card_ids'], env_vars['seasons'], env_vars['prices']]):
        logger.warning("Card trading variables are missing. Skipping card bidding.")
        return

    # Loop over each card to place a bid
    for card_id, season, price in zip(env_vars['card_ids'], env_vars['seasons'], env_vars['prices']):
        try:
            # Place a bid on the card
            session.bid(price, card_id, season)
            logger.info("Successfully placed bid for card %s in season %s with price %s.", card_id, season, price)
        except Exception as e:
            # Log any errors encountered
            logger.error("Error placing bid for card %s in season %s with price %s: %s.", card_id, season, price, e)

def change_nation_settings(session, nation, env_vars):
    """
    Attempts to change a nation's settings.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose settings are to be changed.
        env_vars (dict): A dictionary of environment variables containing the new settings.

    Logs:
        Info: Successful settings change.
        Error: Errors encountered during settings change.
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
            # If population is sufficient, include 'pretitle' in settings
            settings['pretitle'] = env_vars['pretitle']
        else:
            # Otherwise, log that pretitle cannot be changed
            logger.info("The population of nation %s is less than 250 million. Pretitle cannot be changed.", nation)

        # Apply the new settings to the nation
        session.change_nation_settings(**settings)
        logger.info("Successfully changed settings for nation %s.", nation)
    except Exception as e:
        # Log any errors that occur during the process
        logger.error("Error changing settings for nation %s: %s.", nation, e)

def change_nation_flag(session, nation, env_vars):
    """
    Attempts to change a nation's flag.
    """
    try:
        # Change the nation's flag using the provided flag data
        session.change_nation_flag(env_vars['flag'])
        logger.info("Successfully changed flag for nation %s.", nation)
    except Exception as e:
        # Log any errors that occur during the flag change
        logger.error("Error changing flag for nation %s: %s.", nation, e)

def move_to_region(session, nation, env_vars):
    """
    Attempts to move a nation to a specified region.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation that is to be moved.
        env_vars (dict): A dictionary of environment variables containing the target region and password.

    Logs:
        Info: Successful region move.
        Error: Errors encountered during region move.
    """
    try:
        # Move the nation to the target region, using a password if necessary
        session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        logger.info("Successfully moved nation %s to %s.", nation, env_vars['target_region'])
    except Exception as e:
        # Log any errors that occur during the move
        logger.error("Error moving nation %s to %s: %s.", nation, env_vars['target_region'], e)

def process_nations(session, nations, env_vars, change_settings, change_flag, move_region, place_bids):
    """
    Processes a list of nations, performing operations based on the provided flags.

    Parameters:
        session (NSSession): An authenticated NationStates session.
        nations (list): A list of nation names to process.
        env_vars (dict): A dictionary of environment variables.
        change_settings (bool): Whether to change nation settings.
        change_flag (bool): Whether to change the nation's flag.
        move_region (bool): Whether to move the nation to a target region.
        place_bids (bool): Whether to place bids on cards.

    Logs:
        Warning: If unable to log in to a nation.
    """
    for each in nations:
        each = each.strip()  # Remove any leading/trailing whitespace
        skip_login = False  # Flag to determine if login should be skipped

        # Check if the nation can be founded (i.e., if the name is available)
        if session.can_nation_be_founded(each):
            # Since the nation doesn't exist, skip login
            skip_login = True
            logger.warning("Nation %s does not exist. Skipping.", each)

        # Try to log in to the nation if not skipping login
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
            logger.warning("Could not log in with %s.", each)



def wa_vote(session, nation_name, assembly, vote_choice):
    """
    Casts a vote in the World Assembly (WA) on behalf of a nation.
    Returns True on success, False otherwise.
    """
    # Retrieve environment variables
    env_vars = get_env_vars()
    # Log in to the nation
    if session.login(nation_name, env_vars['password']):
        try:
            logging.info("Starting WA voting for nation: %s", nation_name)
            # Perform the vote
            session.wa_vote(assembly, vote_choice)
            # If no exception, vote was successful
            assembly_full_name = "General Assembly" if assembly.lower() == 'ga' else "Security Council"
            logger.info("Successfully voted %s on %s resolution for nation %s.", vote_choice.upper(), assembly_full_name, nation_name)
            return True
        except Exception as e:
            logger.error("Failed to vote for nation %s: %s", nation_name, e)
            return False
    else:
        logger.error("Could not log in with nation %s.", nation_name)
        return False


def main():
    """
    Main function that orchestrates the processing of nations.

    It retrieves environment variables, initializes the session, reads the list of nations,
    and calls process_nations() with the appropriate flags.

    Logs:
        Error: Configuration errors or unexpected exceptions.
    """
    try:
        # Retrieve environment variables
        env_vars = get_env_vars()

        # Initialize the NationStates session with appropriate user agent
        session = NSSession("Que", "3.0.0", "Unshleepd", env_vars['UA'])

        # Read the list of nations from a file named 'que.txt'
        with open("que.txt", "r") as q:
            pups = q.readlines()  # Read all lines (nation names)

        # Process the nations with the specified operations
        process_nations(
            session,
            pups,
            env_vars,
            change_settings=True,  # Set to True to change nation settings
            change_flag=True,      # Set to True to change nation flag
            move_region=True,      # Set to True to move nation to a region
            place_bids=True        # Set to True to place bids on cards
        )

    except EnvironmentError as e:
        # Handle missing environment variables
        logger.error("Configuration error: %s.", e)
    except Exception as e:
        # Handle any other unexpected errors
        logger.error("An unexpected error occurred: %s.", e)

if __name__ == "__main__":
    main()  # Call the main function when the script is executed directly