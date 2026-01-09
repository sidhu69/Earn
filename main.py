# Enhanced Telegram Userbot Script with Broadcasting Features + Persistent Pre-added Groups
# Features:
# - Pre-add groups directly in the script
# - All groups saved to added_groups.json (persistent across restarts)
# - Commands: .add, .text, .auto, .download, .saveall, .list
# - Full media download (.download) and bulk save (.saveall)
# - Safe delays to avoid flood waits

from telethon import TelegramClient, events
import re
import os
import asyncio
import json

# === YOUR CONFIGURATION ===
api_id = 29993225
api_hash = 'ab74aa76c3851434141419a302028976'
session_name = 'userbot_earn_session'

# === PRE-ADD YOUR GROUP/CHANNEL IDs HERE ===
# These should be full supergroup/channel IDs starting with -100
pre_added_groups = [
    -1002442461011,
    -1001162748137,
    -1002256145926,
    -1001734036698,
    -1001850080445,
    -1003580441840,
    -1002674848863,
    -1001438865759,
    -1002321303406
]

# File to store added groups persistently
groups_file = 'added_groups.json'

client = TelegramClient(session_name, api_id, api_hash)

# Runtime storage
added_groups = set()

# Load existing groups from file
if os.path.exists(groups_file):
    try:
        with open(groups_file, 'r') as f:
            loaded = json.load(f)
            added_groups = set(loaded)
        print(f"Loaded {len(added_groups)} groups from {groups_file}")
    except Exception as e:
        print(f"Error loading groups file: {e}")
        added_groups = set()
else:
    added_groups = set()

# Add pre-defined groups if not already present
added_new = False
for gid in pre_added_groups:
    if gid not in added_groups:
        added_groups.add(gid)
        added_new = True
        print(f"Pre-added group ID: {gid}")

# Save if any new pre-added groups
if added_new or not os.path.exists(groups_file):
    with open(groups_file, 'w') as f:
        json.dump(list(added_groups), f)
    print(f"Saved {len(added_groups)} groups to {groups_file}")

# Auto-broadcast variables
auto_task = None
auto_message = None
auto_interval = None

# Regex for .download links
link_pattern = re.compile(r'https?://t\.me/(?P<username>[A-Za-z0-9_]+)/?(?P<msg_id>\d+)')

async def resolve_entity(target):
    try:
        if str(target).lstrip('-').isdigit():
            return await client.get_entity(int(target))
        elif target.startswith('@') or target.startswith('https://t.me/'):
            return await client.get_entity(target)
        else:
            raise ValueError("Invalid format. Use ID (e.g., -100123...), @username, or https://t.me/link")
    except Exception as e:
        raise ValueError(f"Could not resolve entity: {str(e)}")

# === .download - Download media from a message link and send to Saved Messages ===
@client.on(events.NewMessage(outgoing=True, chats='me'))
async def single_download_handler(event):
    text = event.message.text.strip()
    if not text.startswith('.download '):
        return

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply('Usage: `.download <t.me link>`')
        return

    link = parts[1].strip()
    match = link_pattern.match(link)
    if not match:
        await event.reply('Invalid link format. Use a valid t.me message link.')
        return

    username = '@' + match.group('username')
    msg_id = int(match.group('msg_id'))

    try:
        channel = await client.get_entity(username)
        message = await client.get_messages(channel, ids=msg_id)

        if not message or not message.media:
            await event.reply('No media found in that message.')
            return

        status = await event.reply(f'Downloading media from message {msg_id}...')
        file_path = await message.download_media()
        await client.send_file('me', file_path, caption=message.text or '')
        if os.path.exists(file_path):
            os.remove(file_path)
        await status.edit('✅ Media saved to Saved Messages!')
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

# === .saveall - Save all media from a channel ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.saveall\s+(.+)'))
async def bulk_save_handler(event):
    raw = event.pattern_match.group(1).strip()
    parts = raw.split()
    target = parts[0]
    limit = 100
    if len(parts) > 1:
        try:
            limit = int(parts[1])
            if limit <= 0:
                limit = None
        except:
            await event.reply('Limit must be a number.')
            return

    try:
        channel = await client.get_entity(target)
        status = await event.reply(f'Saving media from {target} (limit: {limit or "all recent"})...')
        count = 0
        async for msg in client.iter_messages(channel, limit=limit, min_id=0, wait_time=1):
            if msg.media:
                try:
                    file = await msg.download_media()
                    if file:
                        await client.send_file('me', file, caption=msg.text or '')
                        os.remove(file)
                        count += 1
                        if count % 10 == 0:
                            await status.edit(f'Saved {count} items...')
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"Save error: {e}")
        await status.edit(f'✅ Done! Saved {count} media items.')
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

# === .add - Add a group/channel ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.add\s+(.+)'))
async def add_group_handler(event):
    target = event.pattern_match.group(1).strip()
    try:
        entity = await resolve_entity(target)
        added_groups.add(entity.id)
        with open(groups_file, 'w') as f:
            json.dump(list(added_groups), f)
        await event.reply(f'✅ Added **{getattr(entity, "title", target)}** (ID: `{entity.id}`)\nTotal: {len(added_groups)} groups')
    except ValueError as e:
        await event.reply(f'❌ {e}')

# === .text - Broadcast message now ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.text\s+(.+)'))
async def text_broadcast_handler(event):
    message = event.pattern_match.group(1).strip()
    if not added_groups:
        await event.reply('❌ No groups added yet.')
        return

    status = await event.reply(f'📤 Sending to {len(added_groups)} groups...')
    sent = 0
    failed = []

    for gid in list(added_groups):
        try:
            entity = await client.get_entity(gid)
            await client.send_message(entity, message)
            sent += 1
            await asyncio.sleep(1)
        except Exception as e:
            failed.append(f"{gid}: {str(e)}")

    result = f'✅ Sent to **{sent}/{len(added_groups)}** groups.'
    if failed:
        result += '\n\nFailed:\n' + '\n'.join(failed)
    await status.edit(result)

# === Auto broadcast loop ===
async def auto_broadcast_loop():
    global auto_message, auto_interval
    while True:
        if not added_groups or not auto_message:
            await asyncio.sleep(60)
            continue
        sent = 0
        for gid in list(added_groups):
            try:
                entity = await client.get_entity(gid)
                await client.send_message(entity, auto_message)
                sent += 1
                await asyncio.sleep(1)
            except:
                pass
        print(f"[AUTO] Sent '{auto_message}' to {sent} groups")
        await asyncio.sleep(auto_interval * 60)

# === .auto - Start auto broadcast ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto\s+(.+)\s+(\d+)'))
async def auto_handler(event):
    global auto_task, auto_message, auto_interval
    auto_message = event.pattern_match.group(1).strip()
    auto_interval = int(event.pattern_match.group(2))

    if auto_interval < 1:
        await event.reply('Interval must be ≥ 1 minute.')
        return

    if auto_task:
        auto_task.cancel()

    auto_task = asyncio.create_task(auto_broadcast_loop())
    await event.reply(f'🤖 Auto-broadcast started!\nMessage: `{auto_message}`\nEvery {auto_interval} minutes\nTo {len(added_groups)} groups')

# === .auto off - Stop auto ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto off$'))
async def stop_auto(event):
    global auto_task, auto_message, auto_interval
    if auto_task:
        auto_task.cancel()
        auto_task = None
        auto_message = None
        auto_interval = None
        await event.reply('🛑 Auto-broadcast stopped.')
    else:
        await event.reply('No auto-broadcast running.')

# === .list - Show all added groups ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.list$'))
async def list_groups(event):
    if not added_groups:
        await event.reply('No groups added.')
        return
    msg = f'**Added Groups ({len(added_groups)}):**\n\n'
    for gid in sorted(added_groups):
        try:
            entity = await client.get_entity(gid)
            title = entity.title or 'Unknown'
            msg += f'`{gid}` — {title}\n'
        except:
            msg += f'`{gid}` — (Title unavailable)\n'
    await event.reply(msg)

# === Start the bot ===
async def main():
    await client.start()
    print("🚀 Userbot is running!")
    print(f"Loaded {len(added_groups)} groups (pre-added + saved)")
    print("Available commands: .add | .text | .auto | .auto off | .download | .saveall | .list")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
