import re

import pandas as pd
from loguru import logger
from google.cloud import speech

from utils import read_json


config = read_json("config.json")
menu_df = pd.read_csv(config['menu_csv_path'])


def recognize_speech(file):
    content = file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US',
    )
    stt_client = speech.SpeechClient()
    response = stt_client.recognize(config=config, audio=audio)
    return ' '.join([result.alternatives[0].transcript for result in response.results])


def process_audio(file):
    order_text = recognize_speech(file)

    for wake_word in config['wake_words']:
        if wake_word in order_text:
            start_index = order_text.find(wake_word) + len(wake_word)
            order_text = order_text[start_index:].strip()
            break

    logger.info(f"Order text recognized = {order_text}")

    return order_text


def parse_order(recognized_text):
    match = re.search(r'(\d+)\s*(.*)', recognized_text)
    if match:
        quantity = int(match.group(1))
        item_name = match.group(2).strip()
    else:
        quantity = 1
        item_name = recognized_text

    return quantity, item_name


def get_menu_item_variants(item_name):
    matching_items = menu_df.loc[menu_df['Menu Item'].str.lower() == item_name.lower()]
    if  len(matching_items) != 0:
        match = True
        variants = matching_items[['Type 1', 'Type 2', 'Type 3']].values[0].tolist()
        variants = [variant for variant in variants if not pd.isna(variant)]
    else:
        match = False
        variants = []

    return match, variants


def process_order_step_one(order_text):
    items = [item.strip() for item in re.split(r'\band\b', order_text, flags=re.IGNORECASE)]

    founditems = []
    for item_text in items:
        logger.info(f"Handling individual item. item text = {item_text}")
        quantity, item_name = parse_order(item_text)
        match, variants = get_menu_item_variants(item_name)
        if match:
            message = f"we have several type of variants for {item_name}: {', '.join(variants)}. Which one would you like ?"
        else:
            message = f"We don't have any variants for {item_name}."

        iteminfo = {
            "item": item_name,
            "quantity": quantity,
            "variantflag": match,
            "possiblevariants": variants,
            "message": message
        }
        founditems.append(iteminfo)

    return founditems


def get_closest_variant(user_choice, variants):
    user_choice_normalized = user_choice.lower().strip()
    for variant in variants:
        if variant.lower() in user_choice_normalized:
            return True, variant
    return False, "NA"
