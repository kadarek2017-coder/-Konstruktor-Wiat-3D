import os
import sys
import time
import socket
import threading
import traceback
import webbrowser

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def show_error(message):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Konstruktor Wiat 3D — błąd uruchamiania", message)
        root.destroy()
    except Exception:
        pass

def free_port():
    s=socket.socket()
    s.bind(("127.0.0.1",0))
    p=s.getsockname()[1]
    s.close()
    return p

try:
    app=resource_path("app.py")
    if not os.path.exists(app):
        raise FileNotFoundError("Nie znaleziono app.py wewnątrz aplikacji.")

    port=free_port()
    url=f"http://127.0.0.1:{port}"

    def open_browser():
        time.sleep(4)
        webbrowser.open(url)

    threading.Thread(target=open_browser,daemon=True).start()

    from streamlit.web import cli as stcli
    sys.argv=[
        "streamlit","run",app,
        "--server.port",str(port),
        "--server.address","127.0.0.1",
        "--server.headless","true",
        "--server.fileWatcherType","none",
        "--browser.gatherUsageStats","false",
    ]
    code=stcli.main()
    sys.exit(code)
except BaseException as e:
    details="".join(traceback.format_exception(type(e),e,e.__traceback__))
    show_error("Program nie mógł się uruchomić.\n\n"+details[-5000:])
    sys.exit(1)
