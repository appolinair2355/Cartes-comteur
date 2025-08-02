def afficher_compteurs_canal(compteurs, style=1):
    """Display counters for a specific channel with chosen style"""
    if not compteurs:
        compteurs = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}

    if style == 1:
        return f"❤️: {compteurs.get('❤️', 0)}\n♦️: {compteurs.get('♦️', 0)}\n♣️: {compteurs.get('♣️', 0)}\n♠️: {compteurs.get('♠️', 0)}"
    elif style == 2:
        return f"❤️ {compteurs.get('❤️', 0)} | ♦️ {compteurs.get('♦️', 0)} | ♣️ {compteurs.get('♣️', 0)} | ♠️ {compteurs.get('♠️', 0)}"
    elif style == 3:
        return f"Cœurs: {compteurs.get('❤️', 0)} - Carreaux: {compteurs.get('♦️', 0)} - Trèfles: {compteurs.get('♣️', 0)} - Piques: {compteurs.get('♠️', 0)}"
    elif style == 4:
        return f"[❤️ {compteurs.get('❤️', 0)}] [♦️ {compteurs.get('♦️', 0)}] [♣️ {compteurs.get('♣️', 0)}] [♠️ {compteurs.get('♠️', 0)}]"
    else:  # style 5
        total = sum(compteurs.values())
        return f"Total: {total} (❤️{compteurs.get('❤️', 0)} ♦️{compteurs.get('♦️', 0)} ♣️{compteurs.get('♣️', 0)} ♠️{compteurs.get('♠️', 0)})"

def get_all_styles():
    """Return all available display styles"""
    return {
        1: "Style vertical simple",
        2: "Style horizontal avec séparateurs",
        3: "Style avec noms complets",
        4: "Style avec crochets",
        5: "Style avec total"
    }

def afficher_compteurs(compteurs=None, style=1):
    """Format and display counters in different styles"""
    if compteurs is None:
        compteurs = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}

    if style == 1:
        # Simple vertical list
        return f"""📊 **Compteur de Cartes**

❤️ Cœurs: {compteurs['❤️']}
♦️ Carreaux: {compteurs['♦️']}
♣️ Trèfles: {compteurs['♣️']}
♠️ Piques: {compteurs['♠️']}

🔢 Total: {sum(compteurs.values())}"""

    elif style == 2:
        # Compact horizontal
        total = sum(compteurs.values())
        return f"🃏 ❤️{compteurs['❤️']} ♦️{compteurs['♦️']} ♣️{compteurs['♣️']} ♠️{compteurs['♠️']} | Total: {total}"

    elif style == 3:
        # With percentages
        total = sum(compteurs.values())
        if total == 0:
            return "📊 **Compteurs vides**\n❤️♦️♣️♠️ 0 | 0 | 0 | 0"

        result = "📊 **Statistiques**\n"
        for symbole, count in compteurs.items():
            pct = (count / total * 100) if total > 0 else 0
            result += f"{symbole} {count} ({pct:.1f}%)\n"
        result += f"\n🔢 Total: {total}"
        return result

    elif style == 4:
        # Visual bars
        total = sum(compteurs.values())
        max_count = max(compteurs.values()) if compteurs.values() else 1
        result = "📊 **Graphique**\n\n"

        for symbole, count in compteurs.items():
            bars = "█" * min(10, int((count / max_count * 10)) if max_count > 0 else 0)
            result += f"{symbole} {count:2d} {bars}\n"

        result += f"\n🔢 Total: {total}"
        return result

    elif style == 5:
        # Detailed with emojis
        total = sum(compteurs.values())
        result = "🎴 **Rapport Détaillé**\n\n"

        symbols_names = {
            "❤️": "Cœurs",
            "♦️": "Carreaux", 
            "♣️": "Trèfles",
            "♠️": "Piques"
        }

        for symbole, count in compteurs.items():
            name = symbols_names.get(symbole, symbole)
            result += f"🔸 {symbole} **{name}**: {count}\n"

        result += f"\n📈 **Total général**: {total} cartes"
        return result

    else:
        # Default to style 1
        return afficher_compteurs(compteurs, 1)