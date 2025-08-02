# Telegram Bot - Render.com Deployment Package

## Files included:
- simple_bot.py: Main Telegram bot
- simple_web.py: Web monitoring interface (port 10000)
- All supporting modules and templates

## Deployment Instructions for Render.com:

1. Upload this ZIP file to your render.com service
2. Set environment variable: TELEGRAM_BOT_TOKEN=your_bot_token
3. The bot will start automatically using the render.yaml configuration
4. Web interface will be available on port 10000

## Environment Variables Required:
- TELEGRAM_BOT_TOKEN: Your Telegram bot token from @BotFather
- PORT: 10000 (automatically set)

## Services:
- Bot Service: Runs the Telegram bot (simple_bot.py)
- Web Service: Monitoring dashboard on port 10000 (simple_web.py)

Generated on: 2025-08-02 00:31:59