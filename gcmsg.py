from telethon import TelegramClient, events
import asyncio

# === CONFIG ===
api_id = 29993225
api_hash = 'ab74aa76c3851434141419a302028976'
session_name = 'gc_session'       # Separate session

client = TelegramClient(session_name, api_id, api_hash)

added_groups = set()
auto_task = None
auto_message = None
auto_interval = None

async def resolve_entity(target):
    try:
        return await client.get_entity(target)
    except Exception as e:
        raise ValueError(f"Cannot resolve: {e}")

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.add\s+(.+)'))
async def add_group(event):
    try:
        entity = await resolve_entity(event.pattern_match.group(1).strip())
        added_groups.add(entity.id)
        await event.reply(f'✅ Added {entity.title or "group"} (ID: {entity.id})')
    except Exception as e:
        await event.reply(f'❌ {e}')

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.text\s+(.+)'))
async def text_broadcast(event):
    msg = event.pattern_match.group(1).strip()
    if not added_groups:
        await event.reply('No groups added.')
        return
    status = await event.reply(f'Sending to {len(added_groups)} groups...')
    sent = 0
    for gid in added_groups:
        try:
            await client.send_message(gid, msg)
            sent += 1
            await asyncio.sleep(1)
        except:
            pass
    await status.edit(f'✅ Sent to {sent} groups')

async def auto_loop():
    global auto_message, auto_interval
    while True:
        if added_groups and auto_message:
            for gid in added_groups:
                try:
                    await client.send_message(gid, auto_message)
                    await asyncio.sleep(1)
                except:
                    pass
        await asyncio.sleep(auto_interval * 60 if auto_interval else 60)

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto\s+(.+)\s+(\d+)'))
async def start_auto(event):
    global auto_task, auto_message, auto_interval
    auto_message = event.pattern_match.group(1).strip()
    auto_interval = int(event.pattern_match.group(2))
    if auto_task:
        auto_task.cancel()
    auto_task = asyncio.create_task(auto_loop())
    await event.reply(f'Auto started: "{auto_message}" every {auto_interval} min')

@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto off'))
async def stop_auto(event):
    global auto_task
    if auto_task:
        auto_task.cancel()
        auto_task = None
        await event.reply('Auto stopped.')

async def main():
    await client.start()
    print("Group Messaging Userbot Running (Separate Session)")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
