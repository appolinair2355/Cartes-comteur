#!/usr/bin/env python3
"""
Simple web interface for the card counting bot
"""
import json
import os
from flask import Flask, render_template, jsonify, request
from compteur import get_compteurs, reset_compteurs
from historique import get_messages_count, reset_messages_traite
from style import get_all_styles

app = Flask(__name__)
current_style = 1

def get_bot_status():
    """Get bot status from JSON file"""
    try:
        with open("bot_status.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"running": False, "last_message": "Bot not started", "error": None}
    except json.JSONDecodeError:
        return {"running": False, "last_message": "Error reading status", "error": "JSON decode error"}

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API: Get current status"""
    status = get_bot_status()
    # Get counters for all channels or default empty
    try:
        # Try to load from file directly
        import json
        with open("compteurs_global.json", "r") as f:
            counters = json.load(f)
    except:
        counters = {"❤️": 0, "♦️": 0, "♣️": 0, "♠️": 0}
    
    messages_count = get_messages_count()
    styles = get_all_styles()
    
    return jsonify({
        'bot_status': status,
        'counters': counters,
        'messages_processed': messages_count,
        'current_style': current_style,
        'styles': styles
    })

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """API: Reset counters and history"""
    try:
        # Reset all channel counters
        import os
        import glob
        for file in glob.glob("compteurs_*.json"):
            os.remove(file)
        reset_messages_traite()
        return jsonify({'success': True, 'message': 'Reset completed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/style', methods=['POST'])
def api_style():
    """API: Change display style"""
    global current_style
    try:
        data = request.get_json()
        new_style = int(data.get('style', 1))
        if 1 <= new_style <= 5:
            current_style = new_style
            return jsonify({'success': True, 'message': f'Style {new_style} selected'})
        else:
            return jsonify({'success': False, 'error': 'Style must be 1-5'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Starting web interface...")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)