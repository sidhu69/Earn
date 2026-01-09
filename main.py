from telethon import TelegramClient, events
import re
import os
import asyncio
import json

# ✅ NEW (import auto-reply feature)
from auto_reply import setup_auto_reply

# === YOUR CONFIGURATION ===
api_id = 29993225
api_hash = 'ab74aa76c3851434141419a302028976'
session_name = 'userbot_earn_session'

# === PRE-ADD YOUR GROUP/CHANNEL IDs HERE ===
pre_added_groups = [
    -1002442461011,
    -1001162748137,
    -1002256145926,
    -1001734036698,
    -1001850080445,
    -1003580441840,
    -1002674848863,
    -1001438865759,
    -1002321303406,
    -1001882636412,
    -1001798503017,
    -1003003422594,
    -1001540264500,
    -1001776269030,
    -1003686617178,
    -1002132960368,
    -1002148272343
]

groups_file = 'added_groups.json'
client = TelegramClient(session_name, api_id, api_hash)

# ✅ Register auto-reply (ONE LINE)
setup_auto_reply(client)

# ================= EXISTING CODE BELOW (UNCHANGED) =================

added_groups = set()

if os.path.exists(groups_file):
    with open(groups_file, 'r') as f:
        added_groups = set(json.load(f))

for gid in pre_added_groups:
    added_groups.add(gid)

with open(groups_file, 'w') as f:
    json.dump(list(added_groups), f)

link_pattern = re.compile(r'https?://t\.me/(?P<username>[A-Za-z0-9_]+)/?(?P<msg_id>\d+)')

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.list$'))
async def list_groups(event):
    msg = f"Groups ({len(added_groups)}):\n"
    for gid in added_groups:
        try:
            entity = await client.get_entity(gid)
            msg += f"{gid} — {entity.title}\n"
        except:
            msg += f"{gid} — Unknown\n"
    await event.reply(msg)

async def main():
    await client.start()
    print("🚀 Userbot is running!")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
