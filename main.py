# Enhanced Telegram Userbot Script with Broadcasting Features
# Commands (all in Saved Messages):
# - .add <group_id or @username or link> : Add a group/channel to the broadcast list (e.g., .add -1001234567890 or .add @mygroup)
# - .text <message> : Send the <message> immediately to all added groups/channels
# - .auto <message> <interval_in_minutes> : Start auto-sending <message> every X minutes to all added groups (replaces previous auto if any)
#
# Includes previous .download and .saveall commands.
#
# Notes:
# - Groups are stored in memory (lost on restart). For persistence, you could save to a file.
# - Use responsibly: Automated messaging can violate Telegram's TOS if used for spam.
# - For private groups without username, use the full ID (e.g., -1001234567890).

from telethon import TelegramClient, events
import re
import os
import asyncio

# Replace with your values
api_id = 29993225  # Your API ID
api_hash = 'ab74aa76c3851434141419a302028976'  # Your API Hash
session_name = 'userbot_session'

client = TelegramClient(session_name, api_id, api_hash)

# Storage for added groups (set of entity IDs for uniqueness)
added_groups = set()

# For auto-sending: Current task and message/interval
auto_task = None
auto_message = None
auto_interval = None

# Regex for single message links (for .download)
link_pattern = re.compile(r'https?://t\.me/(?P<username>[A-Za-z0-9_]+)/?(?P<msg_id>\d+)')

# Extract username or ID from input
async def resolve_entity(target):
    try:
        if isinstance(target, int) or target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
            entity = await client.get_entity(int(target))
        elif target.startswith('@') or target.startswith('https://t.me/'):
            entity = await client.get_entity(target)
        else:
            raise ValueError("Invalid group format.")
        return entity
    except Exception as e:
        raise ValueError(f"Could not resolve entity: {str(e)}")

# === Single message download (.download) ===
@client.on(events.NewMessage(outgoing=True, chats='me'))
async def single_download_handler(event):
    text = event.message.text.strip()
    
    if not text.startswith('.download '):
        return
    
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply('Usage: `.download <link>`')
        return
    
    link = parts[1].strip()
    match = link_pattern.match(link)
    if not match:
        await event.reply('Invalid link format.')
        return
    
    username = '@' + match.group('username')
    msg_id = int(match.group('msg_id'))
    
    try:
        channel = await client.get_entity(username)
        message = await client.get_messages(channel, ids=msg_id)
        
        if not message or not message.media:
            await event.reply('No media found in that message.')
            return
        
        status = await event.reply(f'Processing message {msg_id} from {username}...')
        file_path = await message.download_media()
        await client.send_file('me', file_path, caption=message.text or '')
        if os.path.exists(file_path):
            os.remove(file_path)
        await status.edit('Media saved to Saved Messages!')
        
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

# === Bulk save all media (.saveall) ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.saveall\s+(.+)'))
async def bulk_save_handler(event):
    raw_input = event.pattern_match.group(1).strip()
    parts = raw_input.split()
    
    # Extract username (supports @username or https://t.me/username)
    username_raw = parts[0]
    if username_raw.startswith('https://t.me/'):
        username = username_raw.split('/')[-1]
        if username.isdigit():
            username = int('-100' + username)  # For private channel links like t.me/c/123456
        else:
            username = '@' + username
    elif username_raw.startswith('@'):
        username = username_raw
    else:
        await event.reply('Invalid channel format. Use @username or https://t.me/username')
        return
    
    # Optional: limit
    limit = 100  # default
    if len(parts) > 1:
        try:
            limit = int(parts[1])
            if limit <= 0:
                limit = None
        except ValueError:
            await event.reply('Limit must be a number.')
            return
    
    try:
        channel = await client.get_entity(username)
        
        status = await event.reply(f'Starting to save media from {username} (limit: {limit or "all recent"})...')
        
        count = 0
        async for message in client.iter_messages(channel, limit=limit, min_id=0, wait_time=1):
            if message.media:
                try:
                    file_path = await message.download_media()
                    if file_path:
                        await client.send_file('me', file_path, caption=message.text or '')
                        os.remove(file_path)
                        count += 1
                        if count % 10 == 0:
                            await status.edit(f'Saved {count} media items so far...')
                        await asyncio.sleep(1)
                except Exception as inner_e:
                    print(f"Error: {inner_e}")
                    continue
        
        await status.edit(f'Done! Saved {count} media items.')
        
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

# === Add group (.add) ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.add\s+(.+)'))
async def add_group_handler(event):
    target = event.pattern_match.group(1).strip()
    
    try:
        entity = await resolve_entity(target)
        added_groups.add(entity.id)
        await event.reply(f'Added group/channel {target} (ID: {entity.id}) to broadcast list.')
    except ValueError as e:
        await event.reply(str(e))

# === Send text to all groups (.text) ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.text\s+(.+)'))
async def text_broadcast_handler(event):
    message = event.pattern_match.group(1).strip()
    
    if not added_groups:
        await event.reply('No groups added yet. Use .add first.')
        return
    
    status = await event.reply(f'Broadcasting message "{message}" to {len(added_groups)} groups...')
    sent_count = 0
    failed = []
    
    for group_id in list(added_groups):
        try:
            entity = await client.get_entity(group_id)
            await client.send_message(entity, message)
            sent_count += 1
            await asyncio.sleep(1)  # Delay to avoid flood
        except Exception as e:
            failed.append(f"{group_id}: {str(e)}")
    
    reply = f'Broadcast complete: Sent to {sent_count}/{len(added_groups)} groups.'
    if failed:
        reply += '\nFailures:\n' + '\n'.join(failed)
    await status.edit(reply)

# === Auto-send (.auto) ===
async def auto_broadcast_loop():
    global auto_message, auto_interval
    while True:
        if not added_groups or not auto_message:
            break
        sent_count = 0
        for group_id in list(added_groups):
            try:
                entity = await client.get_entity(group_id)
                await client.send_message(entity, auto_message)
                sent_count += 1
                await asyncio.sleep(1)
            except:
                pass
        print(f'Auto-broadcast: Sent "{auto_message}" to {sent_count} groups.')
        await asyncio.sleep(auto_interval * 60)  # Minutes to seconds

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto\s+(.+)\s+(\d+)'))
async def auto_handler(event):
    global auto_task, auto_message, auto_interval
    
    auto_message = event.pattern_match.group(1).strip()
    auto_interval = int(event.pattern_match.group(2))
    
    if auto_interval < 1:
        await event.reply('Interval must be at least 1 minute.')
        return
    
    if auto_task:
        auto_task.cancel()
        await event.reply('Previous auto-broadcast stopped.')
    
    auto_task = asyncio.create_task(auto_broadcast_loop())
    await event.reply(f'Auto-broadcast started: Sending "{auto_message}" every {auto_interval} minutes to {len(added_groups)} groups.')

async def main():
    await client.start()
    print("Userbot running! Commands in Saved Messages: .add, .text, .auto, .download, .saveall")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
