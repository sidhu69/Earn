import asyncio
from telethon import events

_report_task = None
_stop_flag = False

def setup_scam_report(client):

    @client.on(events.NewMessage(outgoing=True))
    async def scam_report_handler(event):
        global _report_task, _stop_flag

        text = event.raw_text.strip()

        # STOP COMMAND
        if text == ".reportstop":
            _stop_flag = True
            await event.reply("🛑 Reporting stopped")
            return

        # START COMMAND
        if not text.startswith(".report "):
            return

        parts = text.split()

        # Expected:
        # .report @username @channel reason count
        if len(parts) < 5:
            await event.reply(
                "❌ Format:\n"
                ".report @username @channel reason count"
            )
            return

        _, target, channel, reason, count = parts[:5]

        if not count.isdigit():
            await event.reply("❌ Count must be a number")
            return

        count = int(count)

        _stop_flag = False

        # Cancel old task if running
        if _report_task:
            _report_task.cancel()

        status_msg = await event.reply(
            "🚨 Fake reporting started...\n\n"
            f"👤 Target: {target}\n"
            f"📢 Exposed in: {channel}\n"
            f"⚠️ Reason: {reason}\n"
            f"📊 Reports sent: 0/{count}"
        )

        async def fake_report_loop():
            sent = 0

            while sent < count:
                if _stop_flag:
                    return

                sent += 1

                try:
                    await status_msg.edit(
                        "🚨 Reporting in progress...\n\n"
                        f"👤 Target: {target}\n"
                        f"📢 Exposed in: {channel}\n"
                        f"⚠️ Reason: {reason}\n"
                        f"📊 Reports sent: {sent}/{count}"
                    )
                except:
                    pass

                await asyncio.sleep(1)

            await status_msg.edit(
                "✅ Reporting completed!\n\n"
                f"👤 Target: {target}\n"
                f"📢 Exposed in: {channel}\n"
                f"⚠️ Reason: {reason}\n"
                f"📊 Total reports sent: {sent}"
            )

        _report_task = asyncio.create_task(fake_report_loop())
