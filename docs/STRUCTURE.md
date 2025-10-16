# Repository Structure

- `src/` — Python source
  - `relay.py` — main Telegram↔Discord relay (media, multi-mapping, admin cmds)
  - `tg_poll.py` — minimal TG polling tester
  - `get_chat_id.py` — replies with `chat_id` on `/id`
- `config/`
  - `config.example.json` — placeholders for tokens and IDs
  - `config.json` — your real config (not committed)
- `logs/`
  - `relay.log` — service output
- `dist/`
  - `relaybot.zip` — packaged release
- `README.md` — install and usage
- `relaybot.service` — systemd unit (runs `src/relay.py`)
- `requirements.txt` — pinned dependencies
- `LICENSE`, `CLIENT-INSTALL.txt`
