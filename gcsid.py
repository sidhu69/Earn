from telethon import events


def setup_gcsid(client):
    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.gcsid$'))
    async def get_group_chat_ids(event):
        msg = "📋 Groups IDs:\n\n"
        count = 0

        async for dialog in client.iter_dialogs():
            # dialog.is_group = groups + supergroups
            # dialog.is_channel = channels (excluded)
            if dialog.is_group:
                try:
                    msg += f"{dialog.id} — {dialog.name}\n"
                    count += 1
                except Exception:
                    pass

        msg += f"\nTotal Groups: {count}"
        await event.reply(msg)
