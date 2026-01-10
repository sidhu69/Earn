import asyncio
from telethon import events

# ===== INTERNAL STATE =====
_report_task = None
_stop_flag = False


def setup_scam_report(client):
    """
    FAKE report module
    - No real Telegram reporting
    - Unlimited
    - Safe
    - Instant stop
    """

    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.report\s+(.+)'))
    async def report_handler(event):
        global _report_task, _stop_flag

        parts = event.text.split()
        if len(parts) < 4:
            await event.reply(
                "❌ Usage:\n"
                ".report @username scam 5\n"
                ".report anything anything unlimited"
            )
            return

        target = parts[1]
        total = parts[3]

        _stop_flag = False

        async def fake_report_loop():
            count = 0
            try:
                await event.reply(f"🚨 Started fake reporting: `{target}`")

                while True:
                    if _stop_flag:
                        await event.reply("🛑 Reporting stopped")
                        return

                    count += 1
                    await event.reply(f"✅ Report sent {count} time(s)")
                    await asyncio.sleep(1)  # smooth & safe

            except Exception as e:
                await event.reply(f"❌ Error: {e}")

        if _report_task:
            _report_task.cancel()

        _report_task = asyncio.create_task(fake_report_loop())

    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.reportstop$'))
    async def stop_handler(event):
        global _stop_flag
        _stop_flag = True
        await event.reply("🛑 Reporting stopped")
