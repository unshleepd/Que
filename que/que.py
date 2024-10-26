# que.py
# -*- coding: utf-8 -*-
"""
Module for automating various NationStates operations.

This script provides functions to interact with the NationStates API for automating tasks such as changing nation settings, moving nations to different regions, placing bids on cards, voting in the World Assembly, and endorsing nations.

Functions:
- get_env_vars(): Extracts and validates required environment variables.
- check_population(session, nation): Retrieves the population of a nation.
- bid_on_cards(session, env_vars): Places bids on specified cards using provided environment variables.
- change_nation_settings(session, nation, env_vars): Updates a nation's settings with provided environment variables.
- change_nation_flag(session, nation, env_vars): Changes a nation's flag.
- move_to_region(session, nation, env_vars): Moves a nation to a target region.
- endorse_nations(session, endorser_nation, target_nations, password, progress_callback=None): Endorses a list of nations using an endorser nation.
- process_nations(session, nations, env_vars, change_settings, change_flag, move_region, place_bids, progress_callback=None): Processes a list of nations, performing specified actions.
- wa_vote(session, nation_name, assembly, vote_choice): Casts a vote in the World Assembly.
- main(): Main function to orchestrate nation processing.
"""

import os
import logging
from dotenv import load_dotenv
from nsdotpy.session import NSSession

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env files
load_dotenv('config.env')  # Load general configuration variables
load_dotenv('cards.env')   # Load card trading variables

def get_env_vars():
    """
    Extracts and validates required environment variables from loaded .env files.

    Expected environment variables include:

    - UA: User agent string for API requests.
    - PASSWORD: Nation password.
    - EMAIL: Email address associated with the nation.
    - NOTIFY: Notification settings.
    - PRETITLE: Nation pretitle (requires population >= 250 million).
    - SLOGAN: Nation slogan.
    - CURRENCY: Nation's currency.
    - ANIMAL: National animal.
    - DEMONYM_NOUN: Demonym noun.
    - DEMONYM_ADJECTIVE: Demonym adjective.
    - DEMONYM_PLURAL: Demonym plural.
    - CAPITAL: Capital city.
    - LEADER: Leader's name.
    - FAITH: National faith.
    - TARGET_REGION: Target region to move to.
    - TARGET_REGION_PASSWORD: Password for the target region (if any).
    - FLAG: URL or path to the new flag image.

    Optional environment variables for card trading:

    - CARD_IDS: Comma-separated list of card IDs.
    - SEASONS: Comma-separated list of corresponding seasons for the cards.
    - PRICES: Comma-separated list of corresponding prices for the cards.

    Returns:
        dict: A dictionary mapping environment variable names to their values.

    Raises:
        EnvironmentError: If any required environment variables are missing.
    """
    # Extract environment variables
    env_vars = {
        'UA': os.getenv('UA'),
        'password': os.getenv('PASSWORD'),
        'email': os.getenv('EMAIL'),
        'notify': os.getenv('NOTIFY'),
        'pretitle': os.getenv('PRETITLE'),
        'slogan': os.getenv('SLOGAN'),
        'currency': os.getenv('CURRENCY'),
        'animal': os.getenv('ANIMAL'),
        'demonym_noun': os.getenv('DEMONYM_NOUN'),
        'demonym_adjective': os.getenv('DEMONYM_ADJECTIVE'),
        'demonym_plural': os.getenv('DEMONYM_PLURAL'),
        'capital': os.getenv('CAPITAL'),
        'leader': os.getenv('LEADER'),
        'faith': os.getenv('FAITH'),
        'target_region': os.getenv('TARGET_REGION'),
        'target_region_password': os.getenv('TARGET_REGION_PASSWORD'),
        'flag': os.getenv('FLAG'),
        'card_ids': os.getenv('CARD_IDS').split(',') if os.getenv('CARD_IDS') else None,
        'seasons': os.getenv('SEASONS').split(',') if os.getenv('SEASONS') else None,
        'prices': os.getenv('PRICES').split(',') if os.getenv('PRICES') else None,
    }

    # Identify missing required environment variables (excluding optional card trading variables)
    required_vars = [
        'UA', 'password', 'email', 'notify', 'slogan', 'currency', 'animal',
        'demonym_noun', 'demonym_adjective', 'demonym_plural', 'capital',
        'leader', 'faith', 'target_region', 'flag'
    ]
    missing_vars = [k for k in required_vars if env_vars.get(k) is None]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}.")

    return env_vars

def check_population(session, nation):
    """
    Retrieves the population of a specified nation from the NationStates API.

    Args:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose population is to be retrieved.

    Returns:
        int: The population of the nation, in millions.
    """
    # Make an API request to get the nation's population
    response = session.api_request(api="nation", target=nation, shard="population")
    population = int(response['population'])
    return population

def bid_on_cards(session, env_vars):
    """
    Places bids on specified cards using provided environment variables.

    Args:
        session (NSSession): An authenticated NationStates session.
        env_vars (dict): A dictionary of environment variables, must include 'card_ids', 'seasons', and 'prices'.

    Logs:
        - Info: Successful bid placements.
        - Warning: Missing card trading variables.
        - Error: Errors encountered during bid placement.
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
            logger.error("Error placing bid for card %s in season %s with price %s: %s.", card_id, season, price, e)

def change_nation_settings(session, nation, env_vars):
    """
    Updates a nation's settings with provided environment variables.

    Args:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose settings are to be changed.
        env_vars (dict): A dictionary of environment variables containing the new settings.

    Logs:
        - Info: Successful settings change.
        - Error: Errors encountered during settings change.
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
            logger.info("The population of nation %s is less than 250 million. Pretitle cannot be changed.", nation)

        # Apply the new settings to the nation
        session.change_nation_settings(**settings)
        logger.info("Successfully changed settings for nation %s.", nation)
    except Exception as e:
        logger.error("Error changing settings for nation %s: %s.", nation, e)

def change_nation_flag(session, nation, env_vars):
    """
    Changes a nation's flag using the provided flag data.

    Args:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation whose flag is to be changed.
        env_vars (dict): A dictionary of environment variables containing the flag information.

    Logs:
        - Info: Successful flag change.
        - Error: Errors encountered during flag change.
    """
    try:
        # Change the nation's flag
        session.change_nation_flag(env_vars['flag'])
        logger.info("Successfully changed flag for nation %s.", nation)
    except Exception as e:
        logger.error("Error changing flag for nation %s: %s.", nation, e)

def move_to_region(session, nation, env_vars):
    """
    Moves a nation to a specified target region.

    Args:
        session (NSSession): An authenticated NationStates session.
        nation (str): The name of the nation to move.
        env_vars (dict): A dictionary of environment variables containing the target region and password.

    Logs:
        - Info: Successful region move.
        - Error: Errors encountered during region move.
    """
    try:
        # Move the nation to the target region
        session.move_to_region(env_vars['target_region'], env_vars['target_region_password'])
        logger.info("Successfully moved nation %s to %s.", nation, env_vars['target_region'])
    except Exception as e:
        logger.error("Error moving nation %s to %s: %s.", nation, env_vars['target_region'], e)

def endorse_nations(session, endorser_nation, target_nations, password, progress_callback=None):
    """
    Endorses a list of target nations using the endorser nation.

    Args:
        session (NSSession): An authenticated NationStates session.
        endorser_nation (str): The nation that will perform the endorsements.
        target_nations (list): A list of nations to be endorsed.
        password (str): The password for the endorser nation.
        progress_callback (callable, optional): Function to call with progress updates.

    Returns:
        bool: True if endorsements were successful, False otherwise.

    Logs:
        - Info: Successful endorsements.
        - Error: Errors encountered during endorsements.
    """
    try:
        if session.login(endorser_nation, password):
            total_nations = len(target_nations)
            for index, target_nation in enumerate(target_nations):
                try:
                    session.endorse(target_nation)
                    logger.info("%s has endorsed %s.", endorser_nation, target_nation)
                except Exception as e:
                    logger.error("An error occurred while endorsing %s with %s: %s", target_nation, endorser_nation, e)
                # Update progress
                if progress_callback:
                    progress = int(((index + 1) / total_nations) * 100)
                    progress_callback(progress)
            return True
        else:
            logger.error("Could not log in with nation %s.", endorser_nation)
            return False
    except Exception as e:
        logger.error("An error occurred during endorsements with %s: %s", endorser_nation, e)
        return False

def wa_vote(session, nation_name, assembly, vote_choice):
    """
    Casts a vote in the World Assembly (WA) on behalf of a nation.

    Args:
        session (NSSession): An authenticated NationStates session.
        nation_name (str): The name of the nation casting the vote.
        assembly (str): 'ga' for General Assembly or 'sc' for Security Council.
        vote_choice (str): 'for' or 'against'.

    Returns:
        bool: True if the vote was successful, False otherwise.

    Logs:
        - Info: Successful vote.
        - Error: Errors encountered during voting.
    """
    # Retrieve environment variables
    env_vars = get_env_vars()
    # Log in to the nation
    if session.login(nation_name, env_vars['password']):
        try:
            logger.info("Starting WA voting for nation: %s", nation_name)
            # Perform the vote
            session.wa_vote(assembly, vote_choice)
            assembly_full_name = "General Assembly" if assembly.lower() == 'ga' else "Security Council"
            logger.info("Successfully voted %s on %s resolution for nation %s.", vote_choice.upper(), assembly_full_name, nation_name)
            return True
        except Exception as e:
            logger.error("Failed to vote for nation %s: %s", nation_name, e)
            return False
    else:
        logger.error("Could not log in with nation %s.", nation_name)
        return False

def process_nations(session, nations, env_vars, change_settings, change_flag, move_region, place_bids, progress_callback=None):
    """
    Processes a list of nations, performing operations based on provided flags.

    Args:
        session (NSSession): An authenticated NationStates session.
        nations (list): A list of nation names to process.
        env_vars (dict): A dictionary of environment variables.
        change_settings (bool): Whether to change nation settings.
        change_flag (bool): Whether to change the nation's flag.
        move_region (bool): Whether to move the nation to a target region.
        place_bids (bool): Whether to place bids on cards.
        progress_callback (callable, optional): A callback function to update progress.

    Logs:
        - Warning: If unable to log in to a nation.
        - Info: Progress updates.
        """
    total_nations = len(nations)
    for index, each in enumerate(nations):
        each = each.strip()
        skip_login = False

        # Check if the nation can be founded (i.e., if the name is available)
        if session.can_nation_be_founded(each):
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
            logger.warning("Could not log in with %s.", each)

        # Update progress
        if progress_callback:
            progress = int(((index + 1) / total_nations) * 100)
            progress_callback(progress)

def main():
    """
    Main function that orchestrates the processing of nations.

    It retrieves environment variables, initializes the session, reads the list of nations,
    and calls process_nations() or endorse_nations() with the appropriate flags.

    Logs:
        - Error: Configuration errors or unexpected exceptions.
    """
    try:
        # Retrieve environment variables
        env_vars = get_env_vars()

        # Initialize the NationStates session with appropriate user agent
        session = NSSession("Que", "3.5.0", "Unshleepd", env_vars['UA'])

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
        logger.error("Configuration error: %s.", e)
    except Exception as e:
        logger.error("An unexpected error occurred: %s.", e)

if __name__ == "__main__":
    main()
