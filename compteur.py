
import json
import os

# Structure: {chat_id: {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}}
compteurs_par_canal = {}

def get_compteurs_fichier(chat_id):
    """Get filename for specific channel counters"""
    return f"compteurs_{abs(chat_id)}.json"

def charger_compteurs_canal(chat_id):
    """Load counters for specific channel"""
    fichier = get_compteurs_fichier(chat_id)
    compteurs_defaut = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}
    
    if os.path.exists(fichier):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    return compteurs_defaut.copy()

def sauvegarder_compteurs_canal(chat_id, compteurs):
    """Save counters for specific channel"""
    fichier = get_compteurs_fichier(chat_id)
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(compteurs, f, ensure_ascii=False)

def get_compteurs(chat_id):
    """Get current counters for channel"""
    if chat_id not in compteurs_par_canal:
        compteurs_par_canal[chat_id] = charger_compteurs_canal(chat_id)
    return compteurs_par_canal[chat_id]

def update_compteurs(chat_id, symbole, count):
    """Update counter for specific symbol in channel"""
    if chat_id not in compteurs_par_canal:
        compteurs_par_canal[chat_id] = charger_compteurs_canal(chat_id)
    
    compteurs_par_canal[chat_id][symbole] += count
    sauvegarder_compteurs_canal(chat_id, compteurs_par_canal[chat_id])

def reset_compteurs_canal(chat_id):
    """Reset all counters for specific channel"""
    compteurs_defaut = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}
    compteurs_par_canal[chat_id] = compteurs_defaut.copy()
    sauvegarder_compteurs_canal(chat_id, compteurs_par_canal[chat_id])

def get_all_channels():
    """Get list of all channels with counters"""
    channels = []
    for fichier in os.listdir("."):
        if fichier.startswith("compteurs_") and fichier.endswith(".json"):
            try:
                chat_id = int(fichier.replace("compteurs_", "").replace(".json", ""))
                channels.append(-chat_id)  # Convert back to negative for channels
            except ValueError:
                continue
    return channels

# Legacy compatibility
compteurs = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}

def sauvegarder_compteurs():
    """Legacy function - do nothing"""
    pass

def charger_compteurs():
    """Legacy function - do nothing"""
    pass

def reset_compteurs():
    """Legacy function - do nothing"""
    pass
