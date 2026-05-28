import threading
from socket import *
from datetime import datetime
from customtkinter import *

BG_DARK      = "#0f1117"
BG_MID       = "#16181f"
BG_CARD      = "#1e2130"
ACCENT       = "#5b8cff"
ACCENT_HOVER = "#7aa3ff"
ACCENT_DIM   = "#2a3a6e"
TEXT_PRIMARY = "#e8eaf0"
TEXT_SECOND  = "#8b90a8"
TEXT_TIME    = "#555a72"
ONLINE_DOT   = "#3dd68c"
ERROR_RED    = "#ff5f5f"
BORDER       = "#2a2d3e"


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.title("💬 Chat")
        self.geometry("760x520")
        self.minsize(600, 420)
        self.configure(fg_color=BG_DARK)

        self.username        = "Danil"
        self.connected       = False
        self._sidebar_w      = 0.0
        self._sidebar_target = 0
        self._animating      = False

        self._build_layout()
        self._connect()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Главный контейнер — делит окно на сайдбар и правую часть
        self.root_frame = CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.root_frame.pack(fill="both", expand=True)

        # Sidebar (фиксированная ширина, меняется через configure)
        self.sidebar = CTkFrame(self.root_frame, fg_color=BG_MID,
                                corner_radius=0, width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text="👤",
                 font=("Segoe UI Emoji", 26),
                 text_color=TEXT_PRIMARY).pack(pady=(52, 2))

        self.name_label = CTkLabel(self.sidebar, text=self.username,
                                   font=("Segoe UI", 13, "bold"),
                                   text_color=TEXT_PRIMARY)
        self.name_label.pack()

        self.status_dot = CTkLabel(self.sidebar, text="● Offline",
                                   font=("Segoe UI", 10), text_color=ERROR_RED)
        self.status_dot.pack(pady=(0, 10))

        CTkFrame(self.sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=12, pady=4)

        CTkLabel(self.sidebar, text="ІМ'Я КОРИСТУВАЧА",
                 font=("Segoe UI", 9, "bold"),
                 text_color=TEXT_SECOND).pack(padx=12, pady=(10, 3), anchor="w")

        self.name_entry = CTkEntry(self.sidebar,
                                   placeholder_text="Нове ім'я…",
                                   fg_color=BG_CARD, border_color=BORDER,
                                   text_color=TEXT_PRIMARY,
                                   placeholder_text_color=TEXT_SECOND,
                                   corner_radius=8, height=34)
        self.name_entry.pack(padx=12, fill="x")
        self.name_entry.insert(0, self.username)
        self.name_entry.bind("<Return>", lambda _e: self._apply_username())

        CTkButton(self.sidebar, text="Застосувати",
                  fg_color=ACCENT, hover_color=ACCENT_HOVER,
                  text_color=TEXT_PRIMARY, corner_radius=8, height=32,
                  font=("Segoe UI", 12),
                  command=self._apply_username).pack(padx=12, pady=(6, 4), fill="x")

        CTkFrame(self.sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=12, pady=6)

        CTkButton(self.sidebar, text="🔄  Перепідключитись",
                  fg_color=ACCENT_DIM, hover_color=ACCENT,
                  text_color=TEXT_PRIMARY, corner_radius=8, height=32,
                  font=("Segoe UI", 11),
                  command=self._connect).pack(padx=12, fill="x")

        # Правая часть — chat + input, через pack (без place вообще)
        self.right_frame = CTkFrame(self.root_frame, fg_color=BG_DARK,
                                    corner_radius=0)
        self.right_frame.pack(side="left", fill="both", expand=True)

        # Toggle button поверх всего (place только для него)
        self.toggle_btn = CTkButton(self, text="☰",
                                    width=36, height=36, corner_radius=8,
                                    fg_color=BG_CARD, hover_color=ACCENT_DIM,
                                    text_color=TEXT_PRIMARY,
                                    font=("Segoe UI", 14),
                                    command=self._toggle_menu)
        self.toggle_btn.place(x=6, y=6)
        self.toggle_btn.lift()

        # Chat area
        self.chat_outer = CTkFrame(self.right_frame, fg_color=BG_MID,
                                   corner_radius=12)
        self.chat_outer.pack(fill="both", expand=True, padx=(4, 4), pady=(4, 4))

        topbar = CTkFrame(self.chat_outer, fg_color=BG_CARD,
                          corner_radius=8, height=44)
        topbar.pack(fill="x", padx=8, pady=(8, 0))
        topbar.pack_propagate(False)

        CTkLabel(topbar, text="💬  Загальний чат",
                 font=("Segoe UI", 13, "bold"),
                 text_color=TEXT_PRIMARY).pack(side="left", padx=12)

        self.conn_indicator = CTkLabel(topbar, text="● Не підключено",
                                       font=("Segoe UI", 10),
                                       text_color=ERROR_RED)
        self.conn_indicator.pack(side="right", padx=12)

        self.chat_field = CTkTextbox(self.chat_outer,
                                     font=("Consolas", 13),
                                     fg_color=BG_DARK, text_color=TEXT_PRIMARY,
                                     corner_radius=8, border_width=0,
                                     state="disabled", wrap="word")
        self.chat_field.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat_field.tag_config("time",   foreground=TEXT_TIME)
        self.chat_field.tag_config("me",     foreground=ACCENT)
        self.chat_field.tag_config("other",  foreground=ONLINE_DOT)
        self.chat_field.tag_config("system", foreground=TEXT_SECOND)
        self.chat_field.tag_config("error",  foreground=ERROR_RED)

        # Input row
        self.input_row = CTkFrame(self.right_frame, fg_color=BG_CARD,
                                  corner_radius=10, height=54)
        self.input_row.pack(fill="x", padx=4, pady=(0, 4))
        self.input_row.pack_propagate(False)

        self.message_entry = CTkEntry(self.input_row,
                                      placeholder_text="Введіть повідомлення…",
                                      fg_color=BG_MID, border_color=BORDER,
                                      text_color=TEXT_PRIMARY,
                                      placeholder_text_color=TEXT_SECOND,
                                      corner_radius=8, height=36,
                                      font=("Segoe UI", 13))
        self.message_entry.pack(side="left", fill="x", expand=True,
                                padx=(10, 6), pady=9)
        self.message_entry.bind("<Return>", lambda _e: self._send_message())

        CTkButton(self.input_row, text="➤",
                  width=44, height=36, corner_radius=8,
                  fg_color=ACCENT, hover_color=ACCENT_HOVER,
                  text_color="white", font=("Segoe UI", 15, "bold"),
                  command=self._send_message).pack(side="right", padx=(0, 10), pady=9)

    # ── Menu animation ────────────────────────────────────────────────────────

    def _toggle_menu(self):
        if self._sidebar_target == 0:
            self._sidebar_target = 210
            self.toggle_btn.configure(text="✕")
        else:
            self._sidebar_target = 0
            self.toggle_btn.configure(text="☰")
        if not self._animating:
            self._animating = True
            self._animate_step()

    def _animate_step(self):
        diff = self._sidebar_target - self._sidebar_w
        if abs(diff) < 1.5:
            self._sidebar_w = float(self._sidebar_target)
            self._animating = False
            self.sidebar.configure(width=int(self._sidebar_w))
            return
        self._sidebar_w += diff * 0.22
        self.sidebar.configure(width=int(self._sidebar_w))
        self.after(14, self._animate_step)

    # ── Username ──────────────────────────────────────────────────────────────

    def _apply_username(self):
        new = self.name_entry.get().strip()
        if not new or new == self.username:
            return
        old = self.username
        self.username = new
        self.name_label.configure(text=new)
        self._add_message(f"Ім'я змінено: {old} → {new}", tag="system")
        if self.connected:
            try:
                self.sock.sendall(
                    f"TEXT@[SYSTEM]@{old} змінив(ла) ім'я на {new}\n".encode())
            except Exception:
                pass

    # ── Network ───────────────────────────────────────────────────────────────

    def _connect(self):
        if self.connected:
            return
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('2.tcp.eu.ngrok.io', 16172))
            self.connected = True
            self._set_status(True)
            self.sock.send(
                f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась)!\n"
                .encode("utf-8"))
            threading.Thread(target=self._recv_loop, daemon=True).start()
        except Exception as e:
            self.connected = False
            self._set_status(False)
            self._add_message(f"Не вдалося підключитися: {e}", tag="error")

    def _set_status(self, online: bool):
        c = ONLINE_DOT if online else ERROR_RED
        self.status_dot.configure(
            text="● Online" if online else "● Offline", text_color=c)
        self.conn_indicator.configure(
            text="● Підключено" if online else "● Не підключено", text_color=c)

    def _recv_loop(self):
        buf = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self._handle_line(line.strip())
            except Exception:
                break
        self.connected = False
        self.after(0, lambda: self._set_status(False))
        self.sock.close()

    def _handle_line(self, line: str):
        if not line:
            return
        parts = line.split("@", 3)
        if parts[0] == "TEXT" and len(parts) >= 3:
            a, m = parts[1], parts[2]
            self.after(0, lambda a=a, m=m:
                       self._add_message(f"{a}: {m}", tag="other"))
        elif parts[0] == "IMAGE" and len(parts) >= 4:
            a, f = parts[1], parts[2]
            self.after(0, lambda a=a, f=f:
                       self._add_message(f"{a} надіслав(ла) зображення: {f}", tag="system"))
        else:
            self.after(0, lambda l=line: self._add_message(l, tag="system"))

    # ── Messages ──────────────────────────────────────────────────────────────

    def _add_message(self, text: str, tag: str = "other"):
        ts = datetime.now().strftime("%H:%M")
        self.chat_field.configure(state="normal")
        self.chat_field.insert("end", f"[{ts}] ", ("time",))
        self.chat_field.insert("end", text + "\n", (tag,))
        self.chat_field.configure(state="disabled")
        self.chat_field.see("end")

    def _send_message(self):
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self._add_message(f"{self.username}: {msg}", tag="me")
        if self.connected:
            try:
                self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
            except Exception:
                self._add_message("Помилка надсилання.", tag="error")
        self.message_entry.delete(0, "end")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()