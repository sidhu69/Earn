from telethon import TelegramClient, events
import asyncio

# === CONFIG ===
api_id = 29993225
api_hash = 'ab74aa76c3851434141419a302028976'
session_name = 'main_session'     # One session for everything

INVITE_LINK = "https://t.me/+6yqL9Yx2NZFmNmU1 join"

client = TelegramClient(session_name, api_id, api_hash)

added_groups = set()
auto_task = None
auto_message = None
auto_interval = None

# === Group Broadcasting Part ===
async def resolve_entity(target):
    try:
        return await client.get_entity(target)
    except Exception as e:
        raise ValueError(f"Error: {e}")

# .add, .text, .auto commands (same as before – paste the handlers from gcmsg.py here)

# (Copy the @client.on handlers for .add, .text, .auto, .auto off and the auto_loop here)

# === DM Reply Part ===
@client.on(events.NewMessage(incoming=True))
async def auto_dm_reply(event):
    if not event.is_private:
        return
    sender = await event.get_sender()
    if sender.bot:
        return
    try:
        mutual = await client.get_common_chats(sender.id)
        if len(mutual) > 0:
            await event.reply(INVITE_LINK)
    except:
        pass

async def main():
    await client.start()
    print("🚀 Full Userbot Running! (.add, .text, .auto + DM Reply)")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
