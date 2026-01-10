import asyncio
from telethon import events
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonFake,
    InputReportReasonOther
)

# ===== INTERNAL STATE =====
_report_task = None
_stop_flag = False


def _get_reason(reason: str):
    reason = reason.lower()
    if reason == "fake":
        return InputReportReasonFake(), "Fake / impersonation account"
    elif reason == "scam":
        return InputReportReasonOther(), "Scam / fraud activity"
    return InputReportReasonSpam(), "Spam activity"


def setup_scam_report(client):
    """
    Plug-and-play scam report module
    No main.py logic changes required
    """

    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.report\s+(.+)'))
    async def report_handler(event):
        global _report_task, _stop_flag

        parts = event.text.split()
        if len(parts) < 4:
            await event.reply(
                "❌ Usage:\n"
                ".report @username scam 3\n"
                ".report https://t.me/user/123 fake 2"
            )
            return

        target = parts[1]
        reason_obj, reason_text = _get_reason(parts[2])
        total = int(parts[3])
        _stop_flag = False

        async def report_loop():
            count = 0
            try:
                # message link
                if "t.me/" in target and "/" in target:
                    link = target.replace("https://t.me/", "")
                    username, msg_id = link.split("/")
                    entity = await client.get_entity(username)
                    msg_id = int(msg_id)
                else:
                    entity = await client.get_entity(target)
                    msg_id = None

                for _ in range(total):
                    if _stop_flag:
                        break

                    await client(ReportRequest(
                        peer=entity,
                        id=[msg_id] if msg_id else [],
                        reason=reason_obj,
                        message=reason_text
                    ))

                    count += 1
                    await event.reply(f"🚨 Reported {count}/{total}")
                    await asyncio.sleep(15)  # SAFE DELAY

                if not _stop_flag:
                    await event.reply(f"✅ Reporting finished ({count} times)")

            except Exception as e:
                await event.reply(f"❌ Report error: {e}")

        if _report_task:
            _report_task.cancel()

        _report_task = asyncio.create_task(report_loop())

    @client.on(events.NewMessage(outgoing=True, chats='me', pattern=r'^\.reportstop$'))
    async def stop_handler(event):
        global _stop_flag
        _stop_flag = True
        await event.reply("🛑 Reporting stopped")
