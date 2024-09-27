import streamlit as st
import requests
import openai
import boto3
import json
import speech_recognition as sr
from io import BytesIO
import base64
import time
import math
import re
import random

# OpenAI API Key
openai.api_key = "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"  # Using Streamlit secrets for API key management

# Initialize Amazon Polly client
polly_client = boto3.Session(
    aws_access_key_id='AKIA3WUCYNZUDTXIV3N6',  # Replace with your AWS Access Key ID
    aws_secret_access_key='hp/xiqHiircDwJ5tx+30MZCxo/999V0VsJaKap2k',
    region_name='us-west-2'  # Use your region
).client('polly')

# Function to clean text before passing to Polly
def clean_text_for_speech(text):
    def replace_dollars(match):
        amount = float(match.group(1))  # Extract the amount (e.g., 25.00)
        return f"{int(amount)} dollars" if amount.is_integer() else f"{amount} dollars"
    
    text = re.sub(r"\$(\d+(\.\d{1,2})?)", replace_dollars, text)
    text = text.replace("\n", " ").strip()
    
    return text

# Fun and random greeting based on time of day
def get_fun_greeting():
    greetings = {
        "morning": [
            "Good morning! Ready to start your day with something delicious?",
            "Hey there! Morning vibes and good food coming your way!",
            "Top of the morning to you! What can I get you today?"
        ],
        "afternoon": [
            "Good afternoon! Let's get you some tasty bites.",
            "Hey, it's lunch o'clock! What's your order today?",
            "Afternoon! I've got the menu all ready for you!"
        ],
        "evening": [
            "Good evening! Hungry yet? Let's get that sorted.",
            "Evening! Perfect time for some great food.",
            "Hi there! Evening's here, and so is some great food!"
        ]
    }

    current_hour = time.localtime().tm_hour
    if 5 <= current_hour < 12:
        return random.choice(greetings["morning"])
    elif 12 <= current_hour < 18:
        return random.choice(greetings["afternoon"])
    else:
        return random.choice(greetings["evening"])

# Function to fetch restaurant data with caching and a spinner
@st.cache_data(ttl=3600, show_spinner=True)
def fetch_restaurant_data(restaurant_id):
    with st.spinner("Fetching the menu..."):
        url = "https://www.dfoeindia.com/fri/php_api/get_stadium_menu_item.php"
        payload = {
            "availability": "",
            "category_id": "",
            "deviceDateTime": "",
            "restaurant_id": restaurant_id,
            "stall_id": "0",
            "sub_category_id": ""
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error("Error fetching restaurant data")
            return None

# Function to parse menu items
def parse_menu_items(items):
    parsed_items = {}
    for item in items:
        category = item.get("category_name", "Uncategorized")
        if category not in parsed_items:
            parsed_items[category] = []
        parsed_items[category].append({
            "name": item.get("name", "Unknown"),
            "price": item["menuPriceData"][0].get("menu_price", "Unknown") if item.get("menuPriceData") else "Unknown",
            "id": item.get("id", "Unknown"),
            "menu_price_id": item["menuPriceData"][0].get("menu_price_id", "Unknown") if item.get("menuPriceData") else "Unknown",
            "image_url": item.get("image_url", None)
        })
    return parsed_items

# Function to format parsed menu items into categories for dropdowns
def format_parsed_menu(parsed_items):
    return parsed_items  # Return parsed items directly

# Function to send messages to the assistant with error handling
def send_message_to_assistant(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        response_text = response['choices'][0]['message']['content'].strip()
        return response_text
    except Exception as e:
        st.error("Error sending message to assistant")
        return None

# Speech-to-text using SpeechRecognition with enhanced error handling
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        st.info("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            user_input = recognizer.recognize_google(audio)
            st.success(f"You said: {user_input}")
            return user_input
        except sr.UnknownValueError:
            st.warning("Sorry, I didn't catch that. Please try again.")
            return None
        except sr.RequestError as e:
            st.error(f"Request error: {e}")
            return None
        except sr.WaitTimeoutError:
            st.warning("Listening timed out. Please try again.")
            return None

# Text-to-speech using Amazon Polly and autoplay with HTML
def speak_text(text, voice_id):
    try:
        clean_text = clean_text_for_speech(text)
        response = polly_client.synthesize_speech(
            Text=clean_text,
            OutputFormat='mp3',
            VoiceId=voice_id
        )
        audio_stream = response.get("AudioStream")
        audio_data = BytesIO(audio_stream.read())
        audio_stream.close()
        audio_base64 = base64.b64encode(audio_data.read()).decode('utf-8')
        audio_html = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error("Error with Polly TTS")

# Initialize session state for conversation and listening state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.conversation = []

if "listening_active" not in st.session_state:
    st.session_state.listening_active = False

# Web app layout with columns for better structure
st.title("FRI Chatbot Voice Demo")

# Dropdown for selecting Polly voice
voice_id = st.selectbox("Select Polly Voice", options=[
    "Joanna", "Matthew", "Kimberly", "Salli", "Ivy", "Kendra", "Justin", "Joey"
], index=0)

restaurant_id = st.text_input("Enter the restaurant ID", key="restaurant_id")

if restaurant_id and st.button("Fetch Menu"):
    restaurant_data = fetch_restaurant_data(restaurant_id)
    if restaurant_data:
        menu_items = restaurant_data.get("restaurant_menu", [])
        parsed_menu = parse_menu_items(menu_items)
        st.session_state.parsed_menu = parsed_menu

        # Split into two columns: left for menu, right for listening status and voice interaction mode
        col1, col2 = st.columns([3, 1])

        with col1:
            # Display the dropdown for each category
            st.write(f"Here is the menu for restaurant {restaurant_id}:")
            for category, items in parsed_menu.items():
                with st.expander(category, expanded=False):  # Use expander for each category
                    for item in items:
                        st.write(f"- {item['name']} (${item['price']})")
                        if item.get('image_url'):
                            st.image(item['image_url'], width=50)

        with col2:
            # Display conversation and listening status
            st.markdown("### Voice Interaction")
            # Show conversation
            if st.session_state.conversation:
                st.write("Conversation:")
                for line in st.session_state.conversation:
                    st.write(line)

            # Show listening status
            if st.session_state.listening_active:
                st.info("Listening... please speak.")

            # Welcome message plays after fetching the menu
            welcome_message = f"{get_fun_greeting()} How may I assist you today?"
            speak_text(welcome_message, voice_id)

            # Disable listening during response playback
            st.session_state.listening_active = False
            estimated_playback_time = math.ceil(len(welcome_message.split()) / 2.5)
            time.sleep(estimated_playback_time)
            st.session_state.listening_active = True
    else:
        st.write("Failed to retrieve restaurant data.")

# Continuous voice interaction loop with "exit" control
if "parsed_menu" in st.session_state:
    while True:
        if st.session_state.listening_active:
            user_input = recognize_speech()

            if user_input and user_input.lower() == "exit":
                st.write("Exiting the conversation.")
                speak_text("Alright, I’ll leave you to your food dreams. See you soon!", voice_id)
                break

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.conversation.append(f"You: {user_input}")
                response_text = send_message_to_assistant(st.session_state.messages)

                if response_text:
                    st.session_state.conversation.append(f"Assistant: {response_text}")
                    st.write(f"Assistant: {response_text}")
                    st.session_state.listening_active = False
                    speak_text(response_text, voice_id)
                    estimated_playback_time = math.ceil(len(response_text.split()) / 2.5)
                    time.sleep(estimated_playback_time + 1)
                    st.session_state.listening_active = True
                else:
                    break
        else:
            time.sleep(1)

# User-friendly exit option
if st.button("Exit Conversation"):
    st.write("Exiting the conversation.")
    speak_text("Alright, I’ll leave you to your food dreams. See you soon!", voice_id)
