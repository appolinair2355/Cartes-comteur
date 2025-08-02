import json
import os

messages_traite = set()

def sauvegarder_messages_traite():
    """Save processed messages to JSON file"""
    with open("messages_traite.json", "w") as f:
        json.dump(list(messages_traite), f)

def charger_messages_traite():
    """Load processed messages from JSON file if it exists"""
    global messages_traite
    if os.path.exists("messages_traite.json"):
        with open("messages_traite.json", "r") as f:
            try:
                data = json.load(f)
                messages_traite = set(data)
            except json.JSONDecodeError:
                messages_traite = set()

def add_message_traite(numero):
    """Add a message number to processed messages"""
    messages_traite.add(numero)
    sauvegarder_messages_traite()

def is_message_traite(numero):
    """Check if a message number has been processed"""
    return numero in messages_traite

def get_messages_count():
    """Get count of processed messages"""
    return len(messages_traite)

def reset_messages_traite():
    """Reset processed messages"""
    global messages_traite
    messages_traite.clear()
    sauvegarder_messages_traite()
