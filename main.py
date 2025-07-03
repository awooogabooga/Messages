import discord
import os
import asyncio
import logging
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logger.error("TOKEN environment variable is required!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True  # Requires enabling in Discord Developer Portal

client = discord.Client(intents=intents)

SOURCE_CHANNEL_ID = 1311671727763361866  # Replace with your source channel ID
TARGET_CHANNEL_ID = 1067479368823210028  # Replace with your target channel ID

@client.event
async def on_ready():
    logger.info(f"🤖 Bot successfully connected as {client.user}")
    logger.info(f"📊 Connected to {len(client.guilds)} servers")
    
    # Verify channels exist
    source_channel = client.get_channel(SOURCE_CHANNEL_ID)
    target_channel = client.get_channel(TARGET_CHANNEL_ID)
    
    if source_channel:
        logger.info(f"✅ Source channel found: #{source_channel.name} in {source_channel.guild.name}")
    else:
        logger.error(f"❌ Source channel not found with ID: {SOURCE_CHANNEL_ID}")
    
    if target_channel:
        logger.info(f"✅ Target channel found: #{target_channel.name} in {target_channel.guild.name}")
    else:
        logger.error(f"❌ Target channel not found with ID: {TARGET_CHANNEL_ID}")
    
    # Set bot status
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"you"
    )
    await client.change_presence(activity=activity)

@client.event
async def on_message(message):
    # Skip messages from the bot itself to prevent loops
    if message.author == client.user:
        return
    
    if message.channel.id == SOURCE_CHANNEL_ID:
        target = client.get_channel(TARGET_CHANNEL_ID)
        
        if not target:
            logger.error(f"Target channel {TARGET_CHANNEL_ID} not found")
            return
        
        # Get or create webhook for the target channel
        webhook = await get_or_create_webhook(target)
        
        if not webhook:
            logger.warning(f"Failed to create webhook for {target.name}, falling back to normal message")
            # Fallback to normal message if webhook fails
            content = f"**{message.author.display_name}**: {message.content}" if message.content else f"**{message.author.display_name}** sent an attachment"
            try:
                if message.attachments:
                    files = await download_attachments(message.attachments)
                    await target.send(content=content, files=files)
                else:
                    await target.send(content=content)
                logger.info(f"📤 Forwarded message from {message.author.display_name} (fallback mode)")
            except Exception as e:
                logger.error(f"Failed to send fallback message: {e}")
            return
        
        # Prepare message content (without author prefix since webhook will show as the user)
        content = message.content if message.content else None
        
        # Handle attachments (images, files, etc.)
        files = await download_attachments(message.attachments)
        
        # Send message via webhook to impersonate the user
        try:
            await webhook.send(
                content=content,
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
                files=files
            )
            logger.info(f"📤 Forwarded message from {message.author.display_name} via webhook")
        except Exception as e:
            logger.error(f"Failed to send webhook message: {e}")

async def download_attachments(attachments):
    """Download attachments and return discord.File objects"""
    files = []
    for attachment in attachments:
        try:
            file_data = await attachment.read()
            discord_file = discord.File(
                fp=BytesIO(file_data),
                filename=attachment.filename
            )
            files.append(discord_file)
            logger.debug(f"Downloaded attachment: {attachment.filename}")
        except Exception as e:
            logger.warning(f"Failed to download attachment {attachment.filename}: {e}")
    return files

async def get_or_create_webhook(channel):
    """Get existing webhook or create a new one for the channel"""
    try:
        # Check if webhook already exists
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == "Message Forwarder":
                logger.debug(f"Using existing webhook for {channel.name}")
                return webhook
        
        # Create new webhook if none exists
        webhook = await channel.create_webhook(name="Message Forwarder")
        logger.info(f"✅ Created new webhook for {channel.name}")
        return webhook
    except discord.Forbidden:
        logger.error(f"❌ Missing 'Manage Webhooks' permission in {channel.name}")
        return None
    except Exception as e:
        logger.error(f"Error managing webhook: {e}")
        return None

@client.event
async def on_error(event, *args, **kwargs):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error in {event}", exc_info=True)

@client.event
async def on_disconnect():
    """Called when the bot disconnects"""
    logger.warning("🔌 Bot disconnected from Discord")

@client.event
async def on_resumed():
    """Called when connection is resumed"""
    logger.info("🔄 Connection resumed")

# Add reconnection logic
async def run_bot():
    """Run bot with automatic reconnection"""
    while True:
        try:
            await client.start(TOKEN)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("🔄 Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)

# Run the bot with automatic reconnection
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.info("Bot will restart automatically")
