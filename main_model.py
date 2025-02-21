from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import re
import emoji
from unidecode import unidecode
from langdetect import detect
from googletrans import Translator
import requests
import os

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace with your Hugging Face model API URL
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/nmanish10/AI-DRIVEN_HARMFUL_LANGUAGE_DETECTOR"
HEADERS = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_ACCESS_TOKEN')}"}


class MessageInput(BaseModel):
    message: str

translator = Translator()

# Dictionary for common disguised toxic words
slang_dict = {
    "f**k": "fuck", "f#ck": "fuck", "f@ck": "fuck", "fuk": "fuck", "fu*k": "fuck",
    "f*ck": "fuck", "fck": "fuck", "fcuk": "fuck", "phuck": "fuck",

    "b!tch": "bitch", "b1tch": "bitch", "b*tch": "bitch", "bitchh": "bitch",
    "bich": "bitch", "biatch": "bitch", "betch": "bitch",

    "a$$": "ass", "@$$": "ass", "a$s": "ass", "a55": "ass", "4ss": "ass",

    "sh!t": "shit", "sh1t": "shit", "sh*t": "shit", "sht": "shit", "shyt": "shit", "$hit": "shit",

    "d!ck": "dick", "d1ck": "dick", "d*ck": "dick", "dik": "dick", "dikk": "dick", "d!k": "dick",

    "wh0re": "whore", "wh*re": "whore", "wh0r3": "whore", "whor3": "whore", "hore": "whore", "hoar": "whore",

    "f@ggot": "faggot", "f4ggot": "faggot", "f4g": "fag", "fa66ot": "faggot", "fagg0t": "faggot",
    "phaggot": "faggot", "phag": "fag", "fa6": "fag",

    "c*nt": "cunt", "c**t": "cunt", "c@nt": "cunt", "cnt": "cunt", "c_nt": "cunt",

    "sl*t": "slut", "s1ut": "slut", "sl@t": "slut", "s|ut": "slut",

    "b@stard": "bastard", "bast@rd": "bastard", "b@st@rd": "bastard", "basturd": "bastard", "bastid": "bastard",

    "p*ssy": "pussy", "p1ssy": "pussy", "p$ssy": "pussy", "pusy": "pussy", "puss": "pussy", "pu55y": "pussy",

    "dumb@ss": "dumbass", "dumb*ss": "dumbass", "dumba$$": "dumbass", "dumbasss": "dumbass",

    "motherf**ker": "motherfucker", "motherf#cker": "motherfucker", "mothafucka": "motherfucker",
    "motha f*cker": "motherfucker", "mthrfkr": "motherfucker",

    "n!gga": "nigga", "n1gga": "nigga", "ni**a": "nigga", "nigg@": "nigga", "nigguh": "nigga",

    "n!gger": "nigger", "n1gger": "nigger", "ni**er": "nigger", "nigg3r": "nigger", "nigg@r": "nigger",

    "assh0le": "asshole", "a$$hole": "asshole", "@sshole": "asshole", "assh*le": "asshole", "asshol3": "asshole",

    "d!ldo": "dildo", "d1ldo": "dildo", "d!ld0": "dildo", "dildo0": "dildo",

    "jack@ss": "jackass", "jacka$$": "jackass", "jack*ss": "jackass",

    "ret@rd": "retard", "r3tard": "retard", "ret@rded": "retarded", "r3tarded": "retarded",

    "tw@t": "twat", "tw*t": "twat", "tw4t": "twat",
    
    "p*rn": "porn", "po*n": "porn", "por*": "porn",
    
    "n*de": "nude", "nu*e": "nude", "nud*": "nude", "nud3": "nude", "n*d3": "nude", "nu*e": "nude", "nudes": "nude"
}


toxic_non_english = {
    # Hindi Cuss Words
    "chutiya": "idiot",
    "bhosdike": "stupid",
    "मादरचोद": "motherfucker",
    "मदारचोद": "motherfucker",
    "मदार्चोद": "motherfucker",
    "मदरचोद": "motherfucker",
    "भोसड़ी के": "stupid",
    "लवड़ा": "stupid",
    "lavda": "stupid",
    "lavde": "stupid",
    "lawda": "stupid",
    "lawde": "stupid",
    "laude": "stupid",
    "lauda": "stupid",
    "gandu": "asshole",
    "gaand mara": "offensive",
    "behenchod": "sisterfucker",
    "bhenchod": "sisterfucker",
    "behenchodh": "sisterfucker",
    "bhenchodh": "sisterfucker",
    "benchodh": "sisterfucker",
    "benchod": "sisterfucker",
    "lund": "penis",
    "pennis" : "penis",
    "lund chus": "suck dick",
    "gaand": "ass",
    "randi": "prostitute",
    "rundi": "prostitute",
    "haraami": "bastard",
    "kuttiya": "bitch",
    "kutti": "bitch",
    "chut": "vagina",
    "chuth": "vagina",
    "chutad": "ass",
    "chodna": "f***ing",
    "chod diya": "f***ed",
    "bhadwa": "pimp",
    "bhadve": "pimp",
    "tatti": "shit",
    "gand" : "ass",
    "gaandfat": "ass burst",
    "gaand phat gayi": "scared as shit",
    "gaand mara": "screwed",
    "chut ke dhakkan": "stupid",
    "tera dimag kharab hai": "your mind is bad",
    "teri maa ki chut": "your mother's vagina",
    "teri behen ki chut": "your sister’s vagina",
    "teri gaand": "your ass",
    "launde": "boy insult",
    "kamina": "mean person",
    "nalayak": "useless",
    
    # Telugu Cuss Words
    "poda patti": "dog insult",
    "puka": "vagina",
    "pooka": "vagina",
    "pooku": "ass",
    "puka lanti": "like a vagina",
    "nee amma": "your mother stupid",
    "nee yamma": "your mother stupid",
    "nee ayya": "your father stupid",
    "nee abba": "your father stupid",
    "nee yabba": "your father stupid",
    "ni amma": "your mother stupid",
    "ni yamma": "your mother stupid",
    "ni ayya": "your father stupid",
    "ni abba": "your father stupid",
    "ni yabba": "your father stupid",
    "yedhava": "you stupid",
    "dengudu": "sex",
    "dengutha": "sex",
    "denguthe": "sex",
    "dobbey": "fuck off",
    "dengey": "fuck off",
    "me pooku": "your ass",
    "madda" : "penis",
    "munda" : "prostitute",
    "gozza" : "gay",
    "kozza" : "gay",
    "gojja" : "gay",
    "kojja" : "gay",
    "gozja" : "gay",
    "kozja" : "gay",
    "goja" : "gay",
    "koja" : "gay",
    "lanja" : "prostitute",
    "lanjakodaka" : "son of a prostitute",
    "lanza" : "prostitute",
    "lanzakodaka" : "son of a prostitute",
    "pacha pooku": "rotten ass",
    "pachi pooku": "rotten ass",
    "guddha": "asshole",
    "pirralu" : "ass",
    "piralu" : "ass",
    "pirall" : "ass",
    "piral" : "ass",
    "kukka kodaka": "son of a dog",
    "pandhi kodaka": "son of a pig",
    "pandhi" : "pig",
    "pandi" : "pig",
    "kukka" : "dog",
    "kuka" : "dog",
    "bokka": "useless",
    "boku": "stupid",
    "madarchod": "motherfucker",
    "madarchodh": "motherfucker",
    "dengudu pooku": "fucking vagina",
    "nee kukka": "your dog (offensive)",
    "telu kodaka": "bastard",
    "gobbemma kodaka": "son of an idiot",
    "nee batuku": "your life (insult)",
    "taluka": "fool",
    "nee guddha": "your ass",
    "nee chetta": "your shit",
    "nee jaathi": "your caste (insult)",
    "champutha" : "kill",
    "champestha" : "kill",
    "champuta" : "kill",
    "champesta" : "kill",
    "champadam" : "kill",
    "champutham" : "kill",
    "champudam" : "kill",
    "champetha" : "kill",
    "chempetha" : "kill",
    "chemputha" : "kill",
    "chempestha" : "kill",
    "champeta" : "kill",
    "chempeta" : "kill",
    "chemputa" : "kill",
    "chempesta" : "kill",
    "chempadam" : "kill",
    "chemputham" : "kill",
    "chempudam" : "kill",
    "godava" : "fight",
    "katthi" : "knife",
    "kathi" : "knife",
    "tho" : "with",
    "podustha" : "kill",
    "podusth" : "kill",
    "podusta" : "kill",
    "podusutha" : "kill",
    "podusuta" : "kill",
    "what is your price?" : "prostitute",
    "what is your price" : "prostitute",
    "your price?" : "prostitute",
    "your price" : "prostitute",
    "what your price?" : "prostitute",
    "what your price" : "prostitute",
    "send nudes": "prostitute",
    "nudes" : "prostitute",
    "nude" : "prostitute"
}

# List of offensive emojis
bad_emojis = [
    "🖕", "🤬", "💩", "😡", "😠", "🤮", "👿", "😾", "😤", "👎", "💔", 
    "😓", "😖", "😣", "😞", "😕", "😬", "😰", "😵", "🥵", "🥶",
    "🤕", "🤒", "😷", "🤢", "🥴", "😿", "💀", "☠️", "👹", "👺",
    "💣", "🔪", "🩸", "🔞", "🚫", "⛔", "❌", "‼️", "😾", "💢", "🤯"
]

# Preprocessing function to clean the text
def preprocess_message(text):
    # Convert to lowercase
    text = text.lower()
    
    # Normalize disguised words
    for word, replacement in slang_dict.items():
        text = text.replace(word, replacement)
    
    # Convert leetspeak (replace common symbols)
    leet_dict = {"@": "a", "!": "i", "$": "s", "0": "o", "3": "e", "1": "i", "5": "s"}
    for char, replacement in leet_dict.items():
        text = text.replace(char, replacement)
    
    # Detect and reduce repeated characters (e.g., "fuuuuuuckkk" -> "fuck")
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # Language detection and translation
    try:
        lang = detect(text)
        if lang not in ["en"] and lang in ["hi", "te"]:  # Translate Hindi/Telugu
            translated_text = translator.translate(text, src=lang, dest='en').text
            text = translated_text.lower()
    except Exception as e:
        print(f"Language detection/translation error: {e}")

    # Replace toxic non-English words
    for word, replacement in toxic_non_english.items():
        text = text.replace(word, replacement)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

@app.post("/check_harmful")
async def check_harmful(input_data: MessageInput):
    cleaned_message = preprocess_message(input_data.message)

    # Check for offensive emojis
    if any(emoji in cleaned_message for emoji in bad_emojis):
        return {"harmful": True, "reason": "Contains offensive emoji"}

    # Send to Hugging Face API for toxicity classification
    response = requests.post(HUGGINGFACE_API_URL, headers=HEADERS, json={"inputs": cleaned_message})

    try:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            is_harmful = any(label["label"] == "toxic" and label["score"] > 0.8 for label in data[0])
            if is_harmful:
                return {"harmful": True, "reason": "Detected toxic language"}
        return {"harmful": False}
    except Exception as e:
        print(f"Error in Hugging Face API response: {e}")
        return {"harmful": False}


