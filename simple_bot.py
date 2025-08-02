
#!/usr/bin/env python3
"""
Bot with separated counters per channel
"""
import os
import logging
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from compteur import get_compteurs, update_compteurs, reset_compteurs_canal
from style import afficher_compteurs_canal
import re
import json
import asyncio
from datetime import datetime, timezone, timedelta

# Track processed messages per channel
processed_messages = set()

# Auto report settings per channel
auto_report_settings = {}  # {chat_id: {"interval": minutes, "task": task_object}}

def get_benin_time():
    """Get current time in Benin timezone (UTC+1)"""
    benin_tz = timezone(timedelta(hours=1))
    return datetime.now(benin_tz)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
style_affichage = 1

def save_bot_status(running, message=None, error=None):
    """Save status to file"""
    status = {
        "running": running,
        "last_message": message,
        "error": error
    }
    try:
        with open("bot_status.json", "w") as f:
            json.dump(status, f)
    except:
        pass

def is_message_processed(message_key):
    """Check if message was already processed"""
    return message_key in processed_messages

def mark_message_processed(message_key):
    """Mark message as processed"""
    processed_messages.add(message_key)
    
def load_processed_messages():
    """Load processed messages from file"""
    global processed_messages
    try:
        with open("processed_messages.json", "r") as f:
            processed_messages = set(json.load(f))
    except:
        processed_messages = set()

def save_processed_messages():
    """Save processed messages to file"""
    try:
        with open("processed_messages.json", "w") as f:
            json.dump(list(processed_messages), f)
    except:
        pass

# Dictionary to track pending edited messages
pending_edits = {}  # {message_id: {"chat_id": chat_id, "task": task, "text": text}}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    global style_affichage
    
    # Get message from any source
    msg = update.message or update.channel_post or update.edited_channel_post
    if not msg or not msg.text:
        return
    
    text = msg.text
    chat_id = msg.chat_id
    message_id = msg.message_id
    
    logger.info(f"Channel {chat_id}: {text[:50]}")
    
    # Handle edited messages with delay
    if update.edited_channel_post:
        # Cancel any existing pending task for this message
        if message_id in pending_edits:
            pending_edits[message_id]["task"].cancel()
        
        # Create a new delayed task to process the edited message
        task = asyncio.create_task(
            process_message_after_delay(chat_id, message_id, text, context.bot, 3.0)
        )
        pending_edits[message_id] = {
            "chat_id": chat_id,
            "task": task,
            "text": text
        }
        logger.info(f"Scheduled delayed processing for edited message #{message_id}")
        return
    
    # Process regular messages immediately
    await process_message_content(chat_id, text, msg)

async def process_message_after_delay(chat_id, message_id, text, bot, delay_seconds):
    """Process message after a delay to ensure editing is complete"""
    try:
        await asyncio.sleep(delay_seconds)
        
        # Create a mock message object for processing
        class MockMessage:
            def __init__(self, chat_id, text):
                self.chat_id = chat_id
                self.text = text
                
            async def reply_text(self, response):
                await bot.send_message(chat_id=self.chat_id, text=response)
        
        mock_msg = MockMessage(chat_id, text)
        await process_message_content(chat_id, text, mock_msg)
        
        # Remove from pending edits
        if message_id in pending_edits:
            del pending_edits[message_id]
            
        logger.info(f"Processed edited message #{message_id} after delay")
        
    except asyncio.CancelledError:
        logger.info(f"Cancelled processing for message #{message_id}")
    except Exception as e:
        logger.error(f"Error processing delayed message #{message_id}: {e}")

async def process_message_content(chat_id, text, msg):
    """Process the actual message content and count cards"""
    # Check for confirmation symbols - required for ALL messages
    confirmation_symbols = ['✅', '🔰']
    has_confirmation = any(symbol in text for symbol in confirmation_symbols)
    
    if not has_confirmation:
        logger.info(f"Message does not contain confirmation symbols (✅ or 🔰), skipping")
        return
    
    # Check for message number to avoid duplicates
    match_numero = re.search(r"#n(\d+)", text)
    if match_numero:
        numero = int(match_numero.group(1))
        # Create unique key for this channel and message number
        message_key = f"{chat_id}_{numero}"
        
        # Check if already processed
        if is_message_processed(message_key):
            logger.info(f"Message #{numero} already processed for channel {chat_id}")
            return
        
        # Mark as processed
        mark_message_processed(message_key)
    
    # Find FIRST parentheses only
    match = re.search(r'\(([^()]*)\)', text)
    if not match:
        logger.info("No parentheses found")
        return
    
    content = match.group(1)
    logger.info(f"Channel {chat_id} - Content: '{content}'")
    
    # Count ALL card symbols in the content (including both heart symbols)
    cards_found = {}
    total_cards = 0
    
    # Check for hearts (both symbols)
    heart_count = content.count("❤️") + content.count("♥️")
    if heart_count > 0:
        update_compteurs(chat_id, "❤️", heart_count)
        cards_found["❤️"] = heart_count
        total_cards += heart_count
    
    # Check other symbols
    for symbol in ["♦️", "♣️", "♠️"]:
        count = content.count(symbol)
        if count > 0:
            update_compteurs(chat_id, symbol, count)
            cards_found[symbol] = count
            total_cards += count
    
    if not cards_found:
        logger.info(f"No card symbols found in: '{content}'")
        return
    
    logger.info(f"Channel {chat_id} - Cards counted: {cards_found}")
    
    save_bot_status(True, f"Channel {chat_id}: {cards_found}")
    
    try:
        # Get updated counters and send response
        compteurs_updated = get_compteurs(chat_id)
        response = afficher_compteurs_canal(compteurs_updated, style_affichage)
        await msg.reply_text(response)
        logger.info(f"Response sent to channel {chat_id}")
    except Exception as e:
        logger.error(f"Send error: {e}")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset command"""
    if not update.message:
        return
        
    chat_id = update.message.chat_id
    reset_compteurs_canal(chat_id)
    
    # Cancel auto report if active
    if chat_id in auto_report_settings and auto_report_settings[chat_id].get("task"):
        auto_report_settings[chat_id]["task"].cancel()
        del auto_report_settings[chat_id]
    
    # Cancel all pending edited messages for this channel
    global pending_edits
    to_cancel = []
    for message_id, edit_info in pending_edits.items():
        if edit_info["chat_id"] == chat_id:
            edit_info["task"].cancel()
            to_cancel.append(message_id)
    
    for message_id in to_cancel:
        del pending_edits[message_id]
    
    # Clear processed messages for this channel
    global processed_messages
    processed_messages = {key for key in processed_messages if not key.startswith(f"{chat_id}_")}
    save_processed_messages()
    
    await update.message.reply_text(
        "✅ **Reset effectué pour ce canal**\n\n"
        "📊 Compteurs remis à zéro\n"
        "⏰ Bilans automatiques arrêtés\n"
        "🔄 Historique des messages effacé\n"
        "⏳ Éditions en attente annulées"
    )
    save_bot_status(True, f"Reset completed for channel {chat_id}")

async def deposer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create deployment package and send it"""
    if not update.message:
        return
    
    try:
        await update.message.reply_text("📦 Création du package de déploiement en cours...")
        
        # Import and run the deployment package creation
        from create_deploy_package import create_deployment_package
        zip_filename = create_deployment_package()
        
        # Check if file exists
        if os.path.exists(zip_filename):
            # Send the ZIP file
            await update.message.reply_document(
                document=open(zip_filename, 'rb'),
                filename=zip_filename,
                caption="✅ Package de déploiement créé avec succès !\n🚀 Prêt pour upload sur render.com"
            )
            logger.info(f"ZIP file sent: {zip_filename}")
        else:
            await update.message.reply_text("❌ Erreur : fichier ZIP non trouvé")
        
        save_bot_status(True, "Deployment package sent")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")
        logger.error(f"Error in deposer command: {e}")

async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set auto report interval command"""
    if not update.message:
        return
    
    chat_id = update.message.chat_id
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "⏰ **Commande /time**\n\n"
            "Définit l'intervalle pour les bilans automatiques.\n\n"
            "📝 **Usage :** /time [minutes]\n"
            "📊 **Exemple :** /time 15\n\n"
            "⏱️ **Intervalle autorisé :** 5 à 32 minutes\n\n"
            "💡 **Note :** Le bilan sera envoyé automatiquement "
            "et les compteurs seront remis à zéro après chaque bilan."
        )
        return
    
    interval = int(context.args[0])
    
    if interval < 5 or interval > 32:
        await update.message.reply_text(
            "❌ **Erreur d'intervalle**\n\n"
            "L'intervalle doit être entre 5 et 32 minutes.\n"
            f"Vous avez saisi : {interval} minutes"
        )
        return
    
    # Cancel existing auto report task if any
    if chat_id in auto_report_settings and auto_report_settings[chat_id].get("task"):
        auto_report_settings[chat_id]["task"].cancel()
    
    # Create new auto report task
    task = asyncio.create_task(auto_report_cycle(chat_id, interval, context.bot))
    auto_report_settings[chat_id] = {"interval": interval, "task": task}
    
    await update.message.reply_text(
        f"✅ **Bilan automatique configuré**\n\n"
        f"⏰ **Intervalle :** {interval} minutes\n"
        f"🕐 **Prochaine execution :** dans {interval} minutes\n\n"
        "📊 Le bilan sera envoyé automatiquement avec l'heure du Bénin,\n"
        "puis les compteurs seront remis à zéro."
    )
    
    save_bot_status(True, f"Auto report set to {interval}min for channel {chat_id}")

async def auto_report_cycle(chat_id, interval_minutes, bot):
    """Auto report cycle for a specific channel"""
    try:
        while True:
            # Wait for the specified interval
            await asyncio.sleep(interval_minutes * 60)
            
            # Get current counters
            compteurs = get_compteurs(chat_id)
            benin_time = get_benin_time()
            
            # Format the automatic report
            report_msg = (
                "📊 **Bilan automatique du compteur**\n\n"
                f"🕐 **Heure :** {benin_time.strftime('%H:%M:%S')} (heure du Bénin)\n\n"
                f"♣️ **Trèfle :** {compteurs['♣️']} ✅\n"
                f"♦️ **Carreau :** {compteurs['♦️']} ✅\n"
                f"♠️ **Pique :** {compteurs['♠️']} ✅\n"
                f"❤️ **Coeur :** {compteurs['❤️']} ✅\n\n"
                "🔄 **Compteurs remis à zéro pour le prochain cycle**"
            )
            
            # Send the report
            await bot.send_message(chat_id=chat_id, text=report_msg)
            
            # Reset counters after sending report
            reset_compteurs_canal(chat_id)
            
            # Clear processed messages for this channel
            global processed_messages
            processed_messages = {key for key in processed_messages if not key.startswith(f"{chat_id}_")}
            save_processed_messages()
            
            logger.info(f"Auto report sent and counters reset for channel {chat_id}")
            
    except asyncio.CancelledError:
        logger.info(f"Auto report cancelled for channel {chat_id}")
    except Exception as e:
        logger.error(f"Error in auto report cycle for channel {chat_id}: {e}")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    welcome_msg = (
        "🤖 **Bot de Comptage de Cartes** 🃏\n\n"
        "Bonjour ! Je compte les cartes séparément pour chaque canal.\n\n"
        "📝 **Comment ça marche :**\n"
        "• Envoyez un message avec des cartes entre parenthèses\n"
        "• Exemple : Résultat du tirage (❤️♦️♣️♠️)\n"
        "• Je compterai automatiquement chaque symbole\n\n"
        "🎯 **Symboles reconnus :**\n"
        "❤️ Cœurs • ♦️ Carreaux • ♣️ Trèfles • ♠️ Piques\n\n"
        "💡 **Commandes disponibles :**\n"
        "• /reset - Réinitialiser les compteurs\n"
        "• /time [minutes] - Configurer bilans automatiques (5-32min)\n"
        "• /deposer - Créer package de déploiement\n\n"
        "⚡ Je suis maintenant actif et prêt à compter !"
    )
    await update.message.reply_text(welcome_msg)
    chat_id = update.message.chat_id
    save_bot_status(True, f"Bot started in channel {chat_id}")

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a group or channel"""
    # Check if the bot itself was added
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            welcome_msg = (
                "👋 **Salut tout le monde !** 🃏\n\n"
                "Je suis le **Bot de Comptage de Cartes** !\n\n"
                "🎯 **Ma mission :**\n"
                "Je vais compter automatiquement tous les symboles de cartes "
                "que vous mettez entre parenthèses dans vos messages.\n\n"
                "📋 **Les compteurs sont séparés par canal !**\n"
                "Chaque canal aura ses propres totaux.\n\n"
                "🃏 **Cartes reconnues :**\n"
                "❤️ Cœurs • ♦️ Carreaux • ♣️ Trèfles • ♠️ Piques\n\n"
                "⚡ **Je suis maintenant actif !**\n\n"
                "💡 **Commandes utiles :**\n"
                "• /reset - Réinitialiser les compteurs de ce canal\n"
                "• /time [minutes] - Bilans automatiques (5-32min)\n"
                "• /start - Revoir ce message d'aide"
            )
            
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=welcome_msg
            )
            chat_id = update.message.chat_id
            save_bot_status(True, f"Bot added to channel {chat_id}")
            logger.info(f"Bot added to chat: {chat_id}")
            break

def main():
    """Main function"""
    # Get token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        save_bot_status(False, error="No token")
        sys.exit(1)
    
    # Load processed messages
    load_processed_messages()
    
    logger.info("Starting bot...")
    save_bot_status(True, "Starting...")
    
    # Create app
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("deposer", deposer_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    logger.info("Bot ready")
    save_bot_status(True, "Bot online")
    
    # Run
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Cancel all auto report tasks
        for chat_id, settings in auto_report_settings.items():
            if settings.get("task"):
                settings["task"].cancel()
        
        # Cancel all pending edit tasks
        for message_id, edit_info in pending_edits.items():
            edit_info["task"].cancel()
        
        save_bot_status(False, "Stopped")
    except Exception as e:
        # Cancel all auto report tasks
        for chat_id, settings in auto_report_settings.items():
            if settings.get("task"):
                settings["task"].cancel()
        
        # Cancel all pending edit tasks
        for message_id, edit_info in pending_edits.items():
            edit_info["task"].cancel()
        
        save_bot_status(False, error=str(e))
        logger.error(f"Error: {e}")
