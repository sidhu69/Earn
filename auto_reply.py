import os
import json
from telethon import events
from telethon.tl.functions.messages import GetCommonChatsRequest

def setup_auto_reply(client):

    AUTO_REPLY_TEXT = "https://t.me/+NnVEoV5beT45Yzk9\nJoin"
    FILE = "auto_replied_users.json"

    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            replied = set(json.load(f))
    else:
        replied = set()

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if not event.is_private:
            return

        sender = await event.get_sender()
        me = await client.get_me()

        if sender.bot or sender.id == me.id:
            return
        if sender.contact:
            return
        if str(sender.id) in replied:
            return

        common = await client(GetCommonChatsRequest(
            user_id=sender.id,
            max_id=0,
            limit=5
        ))

        if not common.chats:
            return

        await event.reply(AUTO_REPLY_TEXT)

        replied.add(str(sender.id))
        with open(FILE, "w") as f:
            json.dump(list(replied), f)
