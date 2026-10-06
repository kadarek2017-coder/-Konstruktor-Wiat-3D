import os
import sys
import time
import socket
import threading
import webbrowser
from streamlit.web import cli as stcli

def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

port = free_port()
url = f"http://127.0.0.1:{port}"

def open_browser():
    time.sleep(2.5)
    webbrowser.open(url)

threading.Thread(target=open_browser, daemon=True).start()
sys.argv = [
    "streamlit", "run", resource_path("app.py"),
    "--server.port", str(port),
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false",
]
sys.exit(stcli.main())
