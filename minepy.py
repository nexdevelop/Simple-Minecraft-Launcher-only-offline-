import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, subprocess, os, psutil
from minecraft_launcher_lib import install, utils, command

# ================= CONFIG =================
PROFILES = ["Standard", "FPS Boost", "Ultra Optimized"]
MINECRAFT_DIR = os.path.join(os.getcwd(), "minecraft")
os.makedirs(MINECRAFT_DIR, exist_ok=True)

pause_download = False
total_files = 0

# ================= COLORS =================
BG = "#0f1117"
SURFACE = "#161a23"
BORDER = "#222838"
TEXT = "#e6e6e6"
TEXT_MUTED = "#9aa4bf"
ACCENT = "#3fa9f5"
ACCENT_HOVER = "#66bfff"
SUCCESS = "#4caf50"

# ================= FONTS =================
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_TEXT = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 10)

# ================= CALLBACKS =================
def log(msg):
    log_box.configure(state="normal")
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    log_box.configure(state="disabled")
    root.update()

def cb_max(m):
    global total_files
    total_files = m
    progress_var.set(0)
    progress_label.config(text=f"0 / {m}")

def cb_progress(p):
    if total_files:
        percent = int((p / total_files) * 100)
        progress_var.set(percent)
        progress_label.config(text=f"{p} / {total_files} ({percent}%)")
    root.update()

# ================= INSTALL =================
def install_version(version):
    log(f"Installing {version}...")
    version_path = os.path.join(MINECRAFT_DIR, "versions", version)
    if os.path.exists(version_path):
        log(f"{version} already installed ✔")
        return

    def safe_set_status(msg):
        log(msg)
        if pause_download:
            raise Exception("Download paused after current package")

    callbacks = {
        "setStatus": safe_set_status,
        "setMax": cb_max,
        "setProgress": cb_progress
    }

    try:
        install.install_minecraft_version(version, MINECRAFT_DIR, callback=callbacks)
        log(f"{version} installed ✔")
        status_var.set("Ready")
        messagebox.showinfo("Success", f"{version} installed correctly")
    except Exception as e:
        if str(e) == "Download paused after current package":
            log("Download paused ⏸")
            status_var.set("Paused ⏸")
        else:
            messagebox.showerror("Error", str(e))
            status_var.set("Error ❌")

def install_thread():
    threading.Thread(
        target=lambda: install_version(version_var.get()),
        daemon=True
    ).start()

# ================= PAUSE =================
def toggle_pause():
    global pause_download
    pause_download = not pause_download
    pause_btn.config(text="RESUME" if pause_download else "PAUSE")
    status_var.set("Paused ⏸" if pause_download else "Running ▶")

# ================= JVM =================
def get_jvm(profile):
    if profile == "Standard":
        return ["-Xmx2G", "-Xms1G"]

    if profile == "FPS Boost":
        return ["-Xmx4G", "-Xms2G", "-XX:+UseG1GC"]

    ram = psutil.virtual_memory().available // (1024 ** 3)
    max_ram = max(2, min(6, ram - 1))

    return [
        f"-Xmx{max_ram}G",
        f"-Xms{max_ram//2}G",
        "-XX:+UseG1GC",
        "-XX:+UseStringDeduplication",
        "-XX:+OptimizeStringConcat",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:ParallelGCThreads=4"
    ]

# ================= LAUNCH =================
def launch():
    options = {
        "username": username_entry.get().strip() or "OfflinePlayer",
        "uuid": "00000000000000000000000000000000",
        "token": "",
        "jvmArguments": get_jvm(profile_var.get()),
        "fullscreen": True
    }

    try:
        cmd = command.get_minecraft_command(
            version_var.get(), MINECRAFT_DIR, options
        )
        subprocess.Popen(cmd)
        status_var.set("Minecraft launched 🎮")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= FOLDER =================
def open_folder():
    os.startfile(MINECRAFT_DIR)

# ================= UI =================
root = tk.Tk()
root.title("MinePy Launcher")
root.geometry("820x720")
root.configure(bg=BG)
root.resizable(False, False)

style = ttk.Style()
style.theme_use("default")

style.configure("TFrame", background=BG)
style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_TEXT)
style.configure("Header.TLabel", font=FONT_TITLE, foreground=TEXT)

style.configure("TCombobox",
    fieldbackground=SURFACE,
    background=SURFACE,
    foreground=TEXT
)

style.configure("Primary.TButton",
    font=FONT_BTN,
    padding=12,
    background=ACCENT,
    foreground="white"
)

style.map("Primary.TButton",
    background=[("active", ACCENT_HOVER)]
)

style.configure("Ghost.TButton",
    font=FONT_BTN,
    padding=8,
    background=SURFACE,
    foreground=TEXT
)

style.configure("TProgressbar",
    troughcolor=SURFACE,
    background=ACCENT
)

# ================= LAYOUT =================
header = ttk.Label(root, text="MinePy Launcher", style="Header.TLabel")
header.pack(pady=20)

content = ttk.Frame(root)
content.pack()

ttk.Label(content, text="Username").grid(row=0, column=0, sticky="w")
username_entry = tk.Entry(content, width=28, bg=SURFACE, fg=TEXT,
                          insertbackground="white", relief="flat")
username_entry.grid(row=1, column=0, pady=5)

ttk.Label(content, text="Version").grid(row=2, column=0, sticky="w")
versions = [v["id"] for v in utils.get_available_versions(MINECRAFT_DIR)]
version_var = tk.StringVar(value=versions[-1])
ttk.Combobox(content, textvariable=version_var,
             values=versions, state="readonly", width=26).grid(row=3, column=0)

ttk.Label(content, text="Profile").grid(row=4, column=0, sticky="w", pady=(10,0))
profile_var = tk.StringVar(value=PROFILES[0])
ttk.Combobox(content, textvariable=profile_var,
             values=PROFILES, state="readonly", width=26).grid(row=5, column=0)

ttk.Button(root, text="PLAY", style="Primary.TButton",
           command=launch).pack(pady=20)

actions = ttk.Frame(root)
actions.pack()

ttk.Button(actions, text="INSTALL", style="Ghost.TButton",
           command=install_thread).grid(row=0, column=0, padx=5)

pause_btn = ttk.Button(actions, text="PAUSE", style="Ghost.TButton",
                       command=toggle_pause)
pause_btn.grid(row=0, column=1, padx=5)

ttk.Button(actions, text="FOLDER", style="Ghost.TButton",
           command=open_folder).grid(row=0, column=2, padx=5)

status_var = tk.StringVar(value="Ready")
ttk.Label(root, textvariable=status_var,
          foreground=SUCCESS).pack(pady=8)

progress_var = tk.IntVar()
progress_label = ttk.Label(root, text="0 / 0")
progress_label.pack()
ttk.Progressbar(root, length=600,
                variable=progress_var).pack(pady=6)

log_box = scrolledtext.ScrolledText(
    root, height=10, width=95, bg=BG,
    fg=TEXT_MUTED, insertbackground="white",
    font=FONT_MONO, relief="flat", state="disabled"
)
log_box.pack(pady=12)

root.mainloop()
