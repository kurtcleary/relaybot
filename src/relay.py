import json, asyncio, logging, threading, signal, sys, time, io
import discord
from discord.ext import commands
import telebot

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
cfg = json.load(open("config.json"))

TG_TOKEN = cfg["telegram_token"]
DC_TOKEN = cfg["discord_token"]
MAP = cfg["mappings"]
TG2DC = {int(m["telegram_chat_id"]): int(m["discord_channel_id"]) for m in MAP}
DC2TG = {int(m["discord_channel_id"]): int(m["telegram_chat_id"]) for m in MAP}

ADMIN_IDS = cfg.get("admins", [])  # [] = everyone can use commands
ACTIVE = {int(m["telegram_chat_id"]): True for m in MAP}

tg = telebot.TeleBot(TG_TOKEN, parse_mode="HTML")
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
dc = commands.Bot(command_prefix="!", intents=intents)

stop_flag = False
MAX_TG_UPLOAD = 45 * 1024 * 1024

def handle_sigterm(signum, frame):
    global stop_flag
    stop_flag = True
    logging.info("Signal %s received, shutting down…", signum)
    try: tg.stop_bot()
    except Exception: pass
    try: asyncio.get_event_loop().stop()
    except Exception: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def allowed(uid:int)->bool:
    return (not ADMIN_IDS) or (uid in ADMIN_IDS)

def is_on(chat_id:int)->bool:
    return ACTIVE.get(chat_id, True)

def set_state(chat_id:int, on:bool)->None:
    ACTIVE[chat_id] = on

def _dc_threadsafe(coro):
    return asyncio.run_coroutine_threadsafe(coro, dc.loop).result(timeout=30)

# -------- Telegram admin --------
@tg.message_handler(commands=["status"])
def cmd_status(m):
    if not allowed(m.from_user.id): return
    lines = ["<b>Relay status</b>"]
    for k in sorted(ACTIVE.keys()):
        lines.append(f"{k}: {'ON' if ACTIVE[k] else 'OFF'}")
    tg.reply_to(m, "\n".join(lines), parse_mode="HTML")

@tg.message_handler(commands=["on","off"])
def cmd_toggle(m):
    if not allowed(m.from_user.id): return
    parts = m.text.split()
    # default: affect current chat if no id given
    target = m.chat.id if len(parts) == 1 else int(parts[1])
    set_state(target, m.text.startswith("/on"))
    tg.reply_to(m, f"Relay {'ENABLED' if is_on(target) else 'DISABLED'} for {target}")

# -------- Telegram -> Discord (all gated by ACTIVE) --------
@tg.message_handler(content_types=['text'])
def tg_text(m):
    if not is_on(m.chat.id): return
    chan = TG2DC.get(m.chat.id); 
    if not chan or not m.text: return
    ch = dc.get_channel(chan)
    if ch:
        _dc_threadsafe(ch.send(f"[TG] {m.from_user.first_name}: {m.text}"))

def tg_download(file_id):
    f = tg.get_file(file_id)
    data = tg.download_file(f.file_path)
    name = f.file_path.split('/')[-1]
    return name, data

async def dc_send_bytes(ch: discord.TextChannel, name: str, data: bytes, caption: str | None = None):
    file = discord.File(io.BytesIO(data), filename=name)
    await ch.send(content=caption, file=file) if caption else await ch.send(file=file)

@tg.message_handler(content_types=['photo'])
def tg_photo(m):
    if not is_on(m.chat.id): return
    chan = TG2DC.get(m.chat.id); 
    if not chan: return
    ch = dc.get_channel(chan); 
    if not ch: return
    try:
        ph = m.photo[-1]
        name, data = tg_download(ph.file_id)
        _dc_threadsafe(dc_send_bytes(ch, name if name.endswith('.jpg') else name + '.jpg', data,
                                     f"[TG] {m.from_user.first_name} sent a photo"))
        if m.caption: _dc_threadsafe(ch.send(f"(caption) {m.caption}"))
    except Exception as e:
        logging.exception("TG photo -> DC failed: %s", e)

@tg.message_handler(content_types=['document'])
def tg_doc(m):
    if not is_on(m.chat.id): return
    chan = TG2DC.get(m.chat.id); 
    if not chan: return
    ch = dc.get_channel(chan); 
    if not ch: return
    try:
        name, data = tg_download(m.document.file_id)
        _dc_threadsafe(dc_send_bytes(ch, m.document.file_name or name, data,
                                     f"[TG] {m.from_user.first_name} sent a file"))
        if m.caption: _dc_threadsafe(ch.send(f"(caption) {m.caption}"))
    except Exception as e:
        logging.exception("TG doc -> DC failed: %s", e)

@tg.message_handler(content_types=['video','audio','voice','sticker'])
def tg_misc(m):
    if not is_on(m.chat.id): return
    chan = TG2DC.get(m.chat.id); 
    if not chan: return
    ch = dc.get_channel(chan); 
    if not ch: return
    try:
        if getattr(m,'sticker',None):
            st = m.sticker
            if st.is_animated or st.is_video:
                _dc_threadsafe(ch.send(f"[TG] {m.from_user.first_name} sent a sticker {st.emoji or ''} (animated/video not previewed)"))
            else:
                name, data = tg_download(st.file_id)
                _dc_threadsafe(dc_send_bytes(ch, name if name.endswith('.webp') else name + '.webp', data,
                                             f"[TG] {m.from_user.first_name} sent a sticker {st.emoji or ''}"))
            return
        file_id = (getattr(m,'video',None) or getattr(m,'audio',None) or getattr(m,'voice',None)).file_id
        name, data = tg_download(file_id)
        _dc_threadsafe(dc_send_bytes(ch, name, data, f"[TG] {m.from_user.first_name} sent media"))
        if getattr(m,'caption',None): _dc_threadsafe(ch.send(f"(caption) {m.caption}"))
    except Exception as e:
        logging.exception("TG media -> DC failed: %s", e)

# -------- Discord -> Telegram (gated by ACTIVE) --------
@dc.event
async def on_message(msg: discord.Message):
    if msg.author == dc.user: 
        return
    tg_chat = DC2TG.get(msg.channel.id)
    if tg_chat is None or not is_on(tg_chat):
        return

    if msg.content:
        try: tg.send_message(tg_chat, f"[DC] {msg.author.display_name}: {msg.content}")
        except Exception as e: logging.exception("DC text -> TG failed: %s", e)

    for a in msg.attachments:
        try:
            if a.size and a.size > MAX_TG_UPLOAD:
                tg.send_message(tg_chat, f"[DC] {msg.author.display_name} sent '{a.filename}' ({a.size//1024//1024}MB) over limit. Skipped.")
                continue
            b = await a.read()
            bio = io.BytesIO(b); bio.name = a.filename
            if a.content_type and a.content_type.startswith("image/"):
                tg.send_photo(tg_chat, bio, caption=f"[DC] {msg.author.display_name} sent an image")
            else:
                tg.send_document(tg_chat, bio, caption=f"[DC] {msg.author.display_name} sent a file")
        except Exception as e:
            logging.exception("DC file -> TG failed: %s", e)

    await dc.process_commands(msg)

@dc.event
async def on_ready():
    logging.info("Discord ready as %s", dc.user)
    for dc_chan_id in DC2TG.keys():
        ch = dc.get_channel(dc_chan_id)
        if ch: await ch.send("Relay online (admin controls).")
    for tg_chat_id in TG2DC.keys():
        try: tg.send_message(tg_chat_id, "Relay online (admin controls).")
        except Exception: pass

def start_tg():
    try: tg.delete_webhook(drop_pending_updates=True)
    except Exception: pass
    logging.info("Starting Telegram polling")
    while not stop_flag:
        try:
            tg.infinity_polling(timeout=60, long_polling_timeout=50, skip_pending=True)
        except Exception as e:
            logging.exception("Polling crash: %s", e)
            time.sleep(5)

threading.Thread(target=start_tg, daemon=True).start()

async def heartbeat():
    while not stop_flag:
        await asyncio.sleep(60)
        logging.info("heartbeat alive: %s", {k: 'ON' if v else 'OFF' for k,v in ACTIVE.items()})

async def main():
    asyncio.create_task(heartbeat())
    await dc.start(DC_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_sigterm(signal.SIGINT, None)
