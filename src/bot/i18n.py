import json
import os

# Load translations from the JSON file
translations = {}
file_path = os.path.join(os.path.dirname(__file__), "i18n.json")
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        translations = json.load(f)

def t(key, lang="en"):
    """
    Translates a given key into the specified language.
    Falls back to the key itself if the translation is not found.
    """
    return translations.get(lang, {}).get(key, key)