# TMP-Network Panel

A lightweight desktop control panel for managing multiple Minecraft servers from a single interface.

---

## 🚀 Features

- Start / Stop / Restart individual servers
- Start / Stop ALL servers at once
- Live console per server tab
- Command input per server
- Server status monitoring (ONLINE / OFFLINE / STARTING)
- Config-driven server system (no hardcoding required)
- Supports multiple Paper-based servers
- Lightweight Swing GUI
- Now coded in Python (5/7/2026)

---

## ⚙️ Configuration

All servers are defined in 'config.json':

```json
{
"servers": {
    "<name>": {
      "folder": "<folder name (CASE SENSATIVE)>",
      "jar": "<Jar name>"
    }
    }
  }
```
# 🧠 How It Works
The panel reads config.json
Each server is loaded into its own tab
Each server runs as a separate Java process
Console output is streamed into the UI in real time
Commands are sent directly to the server process input
Background monitoring checks server status periodically

---

# ⚠️ Notes
- You **NEED** need Python installed
- This panel does **NOT** include Minecraft server files
- Users must provide their own server jars and worlds
- Designed for local or private hosting environments
- No remote access or authentication system included
- To install follow the instructions in `installation-guide.txt`

---

# 📜 License
This project is intended for personal and educational use. You are free to modify and expand it.

---

# 👤 Author
TMP-Network
