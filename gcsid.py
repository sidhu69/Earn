from telethon import events
import os
import tempfile


def setup_gcsid(client):
    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.gcsid$'))
    async def get_group_chat_ids(event):
        ids = []
        count = 0

        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                try:
                    ids.append(str(dialog.id))
                    count += 1
                except Exception:
                    pass

        body = "\n".join(ids)
        footer = f"\n\nTotal Groups: {count}"
        full_text = body + footer

        # Telegram safe limit
        if len(full_text) < 3800:
            await event.reply(full_text)
        else:
            # send as file if too long
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as f:
                f.write(body)
                f.write(footer)
                file_path = f.name

            await event.reply(
                "📁 Group IDs list is too long. Sending as file.",
                file=file_path
            )

            os.remove(file_path)
