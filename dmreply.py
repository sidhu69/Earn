from telethon import TelegramClient, events
import asyncio

# === CONFIG ===
api_id = 29993225                  # Change to yours
api_hash = 'ab74aa76c3851434141419a302028976'   # Change to yours
session_name = 'dm_session'       # Separate session to avoid conflicts

INVITE_LINK = "https://t.me/+6yqL9Yx2NZFmNmU1 join"

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(incoming=True))
async def auto_dm_reply(event):
    if not event.is_private:
        return
    sender = await event.get_sender()
    if sender.bot:
        return
    try:
        mutual_chats = await client.get_common_chats(sender.id)
        if len(mutual_chats) > 0:
            await event.reply(INVITE_LINK)
            print(f"[DM REPLY] Sent invite to {sender.first_name} ({sender.id})")
    except Exception as e:
        print(f"[DM ERROR] {e}")

async def main():
    await client.start()
    print("DM Reply Userbot Running (Separate Session)")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
