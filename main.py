# Enhanced Telegram Userbot Script with Broadcasting Features + Persistent Pre-added Groups
# New Feature: Groups are saved to a file (added_groups.json) for persistence across restarts.
# Additionally: Pre-add your group IDs directly in the script (no need to .add every time in Termux).

from telethon import TelegramClient, events
import re
import os
import asyncio
import json

# === YOUR CONFIGURATION ===
api_id = 29993225  # Your API ID
api_hash = 'ab74aa76c3851434141419a302028976'  # Your API Hash
session_name = 'userbot_earn_session'

# === PRE-ADD YOUR GROUP/CHANNEL IDs HERE ===
# Put all your supergroup/channel IDs (they start with -100...) in this list.
# Example: pre_added_groups = [-1001234567890, -1009876543210]
pre_added_groups = [-1002442461011, -1001162748137, -1002256145926, -1001734036698, -1001850080445, -1003580441840, -1002674848863, -1001438865759, -1002321303406]  # ←←← ADD YOUR IDs HERE, separated by commas

# File to save added groups persistently
groups_file = 'added_groups.json'

client = TelegramClient(session_name, api_id, api_hash)

# Storage for added groups (set of entity IDs)
added_groups = set()

# Load or initialize groups
if os.path.exists(groups_file):
    try:
        with open(groups_file, 'r') as f:
            added_groups = set(json.load(f))
        print(f"Loaded {len(added_groups)} groups from {groups_file}")
    except:
        added_groups = set()
else:
    added_groups = set()

# Add pre-defined groups (if not already added)
for gid in pre_added_groups:
    if gid not in added_groups:
        added_groups.add(gid)
        print(f"Pre-added group ID: {gid}")

# Save updated list if pre-added were new
if pre_added_groups:
    with open(groups_file, 'w') as f:
        json.dump(list(added_groups), f)

# For auto-sending
auto_task = None
auto_message = None
auto_interval = None

# Regex for .download
link_pattern = re.compile(r'https?://t\.me/(?P<username>[A-Za-z0-9_]+)/?(?P<msg_id>\d+)')

async def resolve_entity(target):
    try:
        if isinstance(target, int) or target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
            return await client.get_entity(int(target))
        elif target.startswith('@') or target.startswith('https://t.me/'):
            return await client.get_entity(target)
        else:
            raise ValueError("Invalid format.")
    except Exception as e:
        raise ValueError(f"Could not resolve: {str(e)}")

# === .download handler (unchanged) ===
@client.on(events.NewMessage(outgoing=True, chats='me'))
async def single_download_handler(event):
    text = event.message.text.strip()
    if not text.startswith('.download '):
        return
    # ... (same as before)

# === .saveall handler (unchanged) ===
# ... (keep your existing .saveall code)

# === .add (now also saves to file) ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.add\s+(.+)'))
async def add_group_handler(event):
    target = event.pattern_match.group(1).strip()
    try:
        entity = await resolve_entity(target)
        added_groups.add(entity.id)
        # Save to file
        with open(groups_file, 'w') as f:
            json.dump(list(added_groups), f)
        await event.reply(f'✅ Added {target} (ID: {entity.id})\nTotal groups: {len(added_groups)}')
    except ValueError as e:
        await event.reply(f'❌ {e}')

# === .text (unchanged) ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.text\s+(.+)'))
async def text_broadcast_handler(event):
    # ... (same as before)

# === .auto (unchanged) ===
async def auto_broadcast_loop():
    # ... (same)

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto\s+(.+)\s+(\d+)'))
async def auto_handler(event):
    # ... (same)

# Optional: Add .list command to see added groups
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.list$'))
async def list_groups(event):
    if not added_groups:
        await event.reply('No groups added.')
        return
    msg = f'**Added Groups ({len(added_groups)}):**\n\n'
    for gid in added_groups:
        try:
            entity = await client.get_entity(gid)
            title = getattr(entity, 'title', 'Unknown')
            msg += f'`{gid}` - {title}\n'
        except:
            msg += f'`{gid}` - (Title unavailable)\n'
    await event.reply(msg)

async def main():
    await client.start()
    print("🚀 Userbot running!")
    print(f"Currently {len(added_groups)} groups loaded (including pre-added).")
    print("Commands: .add, .text, .auto, .download, .saveall, .list")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
