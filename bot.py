import os
import io
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# Initialize Flask app
app = Flask(__name__)

# Fetch environment variables from Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") # Provided automatically by Render

# Initialize Telegram Application
tg_app = Application.builder().token(TOKEN).build()

# 1. Logo Generation Engine
def generate_logo(text: str, bg_color="#2C3E50", text_color="#FFFFFF") -> io.BytesIO:
    """Generates a clean, modern square logo with custom text."""
    img = Image.new("RGB", (500, 500), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized geometric background accent
    draw.rectangle([50, 50, 450, 450], outline=text_color, width=8)
    
    # Simple default font handling (Uses system default)
    # For custom fonts, upload a .ttf file to GitHub and use ImageFont.truetype()
    try:
        font = ImageFont.load_default(size=40)
    except TypeError:
        font = ImageFont.load_default() # Fallback for older Pillow versions
        
    # Position text in the center
    # Note: Adjust positioning based on your font size requirements
    draw.text((250, 250), text, fill=text_color, anchor="mm", font=font)
    
    # Save image to memory buffer
    bio = io.BytesIO()
    bio.name = 'logo.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# 2. Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to LogoMakr Bot!\n\n"
        "Just type the **Text** you want on your logo, and I will generate a custom concept for you instantly!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("🎨 Mixing colors and sketching your logo... please wait...")
    
    # Generate the logo
    logo_file = generate_logo(text=user_text)
    
    # Send it back to the user
    await update.message.reply_photo(photo=logo_file, caption=f"✨ Here is your custom logo for '{user_text}'!")

# Register handlers to Telegram app
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 3. Webhook Routing Configuration
@app.route(f"/{TOKEN}", methods=["POST"])
async def respond():
    """Receive updates from Telegram and push them to the bot application."""
    await tg_app.update_queue.put(Update.de_json(request.get_json(force=True), tg_app.bot))
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "LogoMakr Bot is Running!", 200

# Render requires us to initialize the webhook on startup
async def setup_webhook():
    await tg_app.initialize()
    await tg_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# Trigger webhook setup when the script starts
import asyncio
if __name__ != "__main__":
    # When running via Gunicorn, run the webhook setup loop
    asyncio.get_event_loop().run_until_complete(setup_webhook())
