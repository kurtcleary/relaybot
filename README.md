python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python relay.py
sudo cp relaybot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now relaybot.service
[![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](https://github.com/kurtcleary/relaybot/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-brightgreen.svg)](https://www.python.org/)
[![Build](https://img.shields.io/badge/build-stable-success.svg)](https://github.com/kurtcleary/relaybot)

---

```bash
git clone https://github.com/kurtcleary/relaybot.git
cd relaybot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
nano config.json
python relay.py
md

---

## Status

[![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](https://github.com/kurtcleary/relaybot/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-brightgreen.svg)](https://www.python.org/)
[![Build](https://img.shields.io/badge/build-stable-success.svg)](https://github.com/kurtcleary/relaybot)

---

## Quick Install
 git clone https://github.com/kurtcleary/relaybot.git 
cd relaybot 
python3 -m venv .venv 
source .venv/bin/activate 
pip install -r requirements.txt 
cp config/config.example.json config/config.json 
nano config/config.json 
python src/relay.py

git clone https://github.com/kurtcleary/relaybot.git
cd relaybot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
nano config.json
python relay.py
