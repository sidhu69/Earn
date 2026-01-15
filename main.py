from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantRequest, LeaveChannelRequest
from telethon.tl.types import ChannelParticipantBanned

import re
import os
import asyncio
import json

# IMPORT FEATURES
from auto_reply import setup_auto_reply
from gcsid import setup_gcsid
from scam_report import setup_scam_report

# === YOUR CONFIGURATION ===
api_id = 32887228
api_hash = 'ee517b7c04a76a65a4e659637b1026be'
session_name = 'userbot_earn_session'

# === PRE-ADD GROUPS ===
pre_added_groups = [   
-1001784950038,
-1002570535821,
-1003110483797,
-1002992853627,
-1001374492859,
-1002567432408,
-1003331682270,
-1003614337827,
-1002582954810,
-1002429870137,
-1002427079198,
-1002996308076,
-1002442461011,
-1002885759256,
-1002341708858,
-1001237545447,
-1002887731372,
-1003545832328,
-1002791925052,
-1002685759211,
-1002665929008,
-1002599625280,
-1003013201505,
-1003084626848,
-1002691392153,
-1002135351285,
-1002216963907,
-1002051152325,
-1003383267912,
-1003233545054,
-1003069198737
]

groups_file = 'added_groups.json'
client = TelegramClient(session_name, api_id, api_hash)

# REGISTER FEATURES
setup_auto_reply(client)
setup_scam_report(client)
setup_gcsid(client)

# === LOAD GROUPS ===
added_groups = set()

if os.path.exists(groups_file):
    with open(groups_file, 'r') as f:
        added_groups = set(json.load(f))

for gid in pre_added_groups:
    added_groups.add(gid)

with open(groups_file, 'w') as f:
    json.dump(list(added_groups), f)

# === REGEX ===
link_pattern = re.compile(
    r'https?://t\.me/(?P<username>[A-Za-z0-9_]+)/?(?P<msg_id>\d+)'
)

# === .add ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.add\s+(.+)'))
async def add_group(event):
    target = event.pattern_match.group(1)
    entity = await client.get_entity(target)
    added_groups.add(entity.id)
    with open(groups_file, 'w') as f:
        json.dump(list(added_groups), f)
    await event.reply(f"✅ Added {entity.title}")

# === .list ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.list$'))
async def list_groups(event):
    msg = f"Groups ({len(added_groups)}):\n\n"
    for gid in added_groups:
        try:
            ent = await client.get_entity(gid)
            msg += f"{gid} — {ent.title}\n"
        except Exception:
            msg += f"{gid} — Unknown\n"
    await event.reply(msg)

# === .text ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.text\s+(.+)'))
async def text_broadcast(event):
    text = event.pattern_match.group(1)
    sent = 0
    for gid in added_groups:
        try:
            await client.send_message(gid, text)
            sent += 1
            await asyncio.sleep(1)
        except Exception:
            pass
    await event.reply(f"✅ Sent to {sent} groups")

# === AUTO LOOP ===
auto_task = None
auto_message = None
auto_interval = None

async def auto_loop():
    global auto_message, auto_interval
    try:
        while True:
            for gid in added_groups:
                try:
                    await client.send_message(gid, auto_message)
                    await asyncio.sleep(1)
                except Exception:
                    pass
            await asyncio.sleep(auto_interval * 60)
    except asyncio.CancelledError:
        pass

# === .auto ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto\s+(.+)\s+(\d+)'))
async def auto_start(event):
    global auto_task, auto_message, auto_interval
    auto_message = event.pattern_match.group(1)
    auto_interval = int(event.pattern_match.group(2))
    if auto_task:
        auto_task.cancel()
    auto_task = asyncio.create_task(auto_loop())
    await event.reply("🤖 Auto broadcast started")

# === .auto off ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.auto off$'))
async def auto_stop(event):
    global auto_task
    if auto_task:
        auto_task.cancel()
        auto_task = None
        await event.reply("🛑 Auto broadcast stopped")

# === .download ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.download\s+(.+)'))
async def download(event):
    link = event.pattern_match.group(1)
    m = link_pattern.match(link)
    if not m:
        await event.reply("Invalid link")
        return

    channel = await client.get_entity('@' + m.group('username'))
    msg = await client.get_messages(channel, ids=int(m.group('msg_id')))

    if msg.media:
        file = await msg.download_media()
        await client.send_file('me', file)
        os.remove(file)

# === .saveall ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.saveall\s+(.+)'))
async def save_all(event):
    target = event.pattern_match.group(1)
    channel = await client.get_entity(target)
    count = 0

    async for msg in client.iter_messages(channel):
        if msg.media:
            file = await msg.download_media()
            await client.send_file('me', file)
            os.remove(file)
            count += 1
            await asyncio.sleep(1)

    await event.reply(f"✅ Saved {count} files")

# === .mremove ===
@client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.mremove$'))
async def mremove_handler(event):
    await event.reply("🔍 Checking muted / read-only groups...")

    checked = 0
    left = 0

    async for dialog in client.iter_dialogs():
        if not dialog.is_group and not dialog.is_channel:
            continue

        checked += 1
        try:
            participant = await client(GetParticipantRequest(
                channel=dialog.entity,
                participant='me'
            ))

            p = participant.participant

            if isinstance(p, ChannelParticipantBanned):
                if p.banned_rights and not p.banned_rights.send_messages:
                    await client(LeaveChannelRequest(dialog.entity))
                    left += 1
                    await asyncio.sleep(0.5)

        except Exception:
            continue

    await event.reply(
        f"✅ M-Remove Done\n"
        f"Checked: {checked}\n"
        f"Left muted: {left}"
    )

# === START ===
async def main():
    await client.start()
    print("🚀 Userbot running with auto-reply + gcsid + mremove")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
