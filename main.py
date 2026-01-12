from telethon import TelegramClient, events
import re
import os
import asyncio
import json

# IMPORT AUTO-REPLY FEATURE
from auto_reply import setup_auto_reply
from gcsid import setup_gcsid

# === YOUR CONFIGURATION ===
api_id = 29993225
api_hash = 'ab74aa76c3851434141419a302028976'
session_name = 'userbot_earn_session'

# === PRE-ADD GROUPS ===
pre_added_groups = [   
    -1002256145926,
-1002448307258,
-1003560266546,
-1001486096882,
-1001798503017,
-1002570535821,
-1001835473938,
-1002442461011,
-1002948791465,
-1003366845841,
-1002558222911,
-1003013201505,
-1003240208120,
-1001286787674,
-1003119046841,
-1002482258168,
-1001438865759,
-1002148272343,
-1003346448723,
-1002252521652,
-1001725104698,
-1003425279431,
-1003027938036,
-1003530951642,
-1002590778651,
-1001540264500,
-1001850080445,
-1002204953110,
-1003535784019,
-1003691775841,
-1001734036698,
-1001566820340,
-1003231630701,
-1002579282314,
-1002321303406,
-1003259634029,
-1002709607762,
-1003530788291,
-1001814890567,
-1002132960368,
-1003513254543,
-1001762240584,
-1002674848863,
-1003003422594,
-1002350679608,
-1001882636412,
-1003509657457,
-1002469643438,
-1003336057417,
-1003686617178,
-1003436199165,
-1002892502688,
-1002511025954,
-1002142742526,
-1002055557577,
-1002496052988,
-1003204777874,
-1003685469319,
-1001560463100,
-1002216848133,
-1002271327722,
-1002088138420,
-1003116317642,
-1002871328242,
-1003447660527,
-1003027193971,
-5020324507,
-1001311605432,
-4941803256,
-1002257576783,
-1003199416686,
-5077879672,
-5083785676,
-1003199355385,
-1003662915735,
-1003275259709,
-1002056434453,
-1002455283364,
-5088458579,
-1002730562886,
-4780665432
]

groups_file = 'added_groups.json'
client = TelegramClient(session_name, api_id, api_hash)

# REGISTER AUTO-REPLY
setup_auto_reply(client)

# REGISTER SCAM REPORT
from scam_report import setup_scam_report
setup_scam_report(client)

# REGISTER GCSID
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

# === START ===
async def main():
    await client.start()
    print("🚀 Userbot running with auto-reply + gcsid")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
