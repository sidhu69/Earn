import asyncio
from telethon import events

_report_task = None
_stop_flag = False

def setup_scam_report(client):

    @client.on(events.NewMessage(outgoing=True))
    async def fake_report_handler(event):
        global _report_task, _stop_flag

        text = event.raw_text.strip()

        # Stop command
        if text == ".reportstop":
            _stop_flag = True
            await event.reply("🛑 Reporting stopped")
            return

        # Start command
        if not text.startswith(".report"):
            return

        _stop_flag = False

        async def fake_loop():
            count = 0
            await event.reply("🚨 auto reporting has been started")

            while True:
                if _stop_flag:
                    return

                count += 1
                await event.reply(f"✅ Report sent {count} time(s)")
                await asyncio.sleep(1)  # safe delay

        # Cancel previous task if running
        if _report_task:
            _report_task.cancel()

        _report_task = asyncio.create_task(fake_loop())
