import discord
import asyncio
import logging
import requests
import nest_asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Apply workaround for running Discord bot in an interactive environment
nest_asyncio.apply()

# API Endpoint from environment variable
API_URL = os.getenv("API_URL")

# Discord bot token from environment variable
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Ensure token and API URL are set
if not API_URL or not DISCORD_TOKEN:
    raise ValueError("Missing API_URL or DISCORD_TOKEN. Check your .env file.")

# Create a Discord client instance
intents = discord.Intents.default()
intents.message_content = True  # Ensure bot can read message content
client = discord.Client(intents=intents)

bot_active = True  # Flag to control bot activity
GROUP_LEADER_ID = int(os.getenv("GROUP_LEADER_ID", "0"))  # Ensure ID is integer

toxic_message_counts = {}
muted_users = {}

# List of offensive emojis
bad_emojis = [
    "🖕", "🤬", "💩", "😡", "😠", "🤮", "👿", "😾", "😤", "👎", "💔", 
    "😓", "😖", "😣", "😞", "😕", "😬", "😰", "😵", "🥵", "🥶",
    "🤕", "🤒", "😷", "🤢", "🥴", "😿", "💀", "☠️", "👹", "👺",
    "💣", "🔪", "🩸", "🔞", "🚫", "⛔", "❌", "‼️", "😾", "💢", "🤯"
]

# Event: Bot has connected to Discord
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    print(f'Bot ID: {client.user.id}')  # Confirm bot is connected

# Event: When a message is sent in the server
@client.event
async def on_message(message):
    global bot_active

    if message.author == client.user:
        return
    
    if message.author.id == GROUP_LEADER_ID:
        if message.content.lower() == 'bot on':
            bot_active = True
            await message.channel.send("Bot is now **ON** and monitoring messages.")
            return

        elif message.content.lower() == 'bot off':
            bot_active = False
            await message.channel.send("Bot is now **OFF** and not monitoring messages.")
            return
    
    if not bot_active:
        return

    try:
        user_id = message.author.id

        # Check for bad emojis
        if any(emoji in message.content for emoji in bad_emojis):
            await message.delete()
            await message.channel.send(f"Warning: {message.author}, your message contained inappropriate content (emoji).")
            increment_toxic_count(message, user_id)
            return

        # Send the message to API for toxicity prediction
        response = requests.post(API_URL, json={"message": message.content})
        if response.status_code == 200:
            prediction = response.json()
            logging.debug(f"API response: {prediction}")

            if prediction["harmful"]:  # Delete harmful messages
                await message.delete()
                await message.channel.send(f"Warning: {message.author}, your message was flagged as harmful.")
                increment_toxic_count(message, user_id)

        else:
            logging.error(f"Error from API: {response.status_code}, {response.text}")

    except Exception as e:
        logging.error(f"Error in on_message: {e}")

async def mute_user(member, duration):
    if member.id == GROUP_LEADER_ID:
        return
    muted_role = discord.utils.get(member.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await member.guild.create_role(name="Muted")
        for channel in member.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False)
    await member.add_roles(muted_role)
    await asyncio.sleep(duration)
    await member.remove_roles(muted_role)

async def kick_user(member):
    if member.id == GROUP_LEADER_ID:
        return
    await member.kick(reason="Repeated toxic messages.")

def increment_toxic_count(message, user_id):
    if user_id == GROUP_LEADER_ID:  # Prevent actions on group leader
        return
    
    if user_id not in toxic_message_counts:
        toxic_message_counts[user_id] = 0

    toxic_message_counts[user_id] += 1
    logging.debug(f"User {message.author} has {toxic_message_counts[user_id]} toxic messages.")

    if toxic_message_counts[user_id] == 5 and user_id not in muted_users:
        muted_users[user_id] = True
        asyncio.create_task(mute_user(message.author, 10))  # 10-second mute
        asyncio.create_task(message.channel.send(f"{message.author} has been muted for 10 seconds due to repeated toxic messages."))

    elif toxic_message_counts[user_id] >= 10:
        asyncio.create_task(kick_user(message.author))
        asyncio.create_task(message.channel.send(f"{message.author} has been kicked for repeated toxic messages."))
        toxic_message_counts.pop(user_id, None)
        muted_users.pop(user_id, None)

# Run the bot
client.run(DISCORD_TOKEN)
