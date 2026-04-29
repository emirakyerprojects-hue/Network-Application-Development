"""
Lecture 8 - Exchange Office GUI Client

A tkinter-based graphical client application that connects to the
Exchange Office SOAP service (from Lecture 7).

Features:
  - User registration and login
  - PLN deposit
  - Real-time exchange rates (from NBP via service)
  - Buy and sell currencies
  - Portfolio / balance view
  - Transaction history

Start exchange_office_server.py (Lecture 7) first!

needs: pip install zeep
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
from datetime import datetime

try:
    from zeep import Client
    from zeep.exceptions import Fault
except ImportError:
    raise SystemExit("zeep not installed. Run: pip install zeep")

# ── service URL ──────────────────────────────────────────────
SERVICE_WSDL = "http://localhost:8000/?wsdl"

# ── colour palette ────────────────────────────────────────────
BG        = "#0f1117"
CARD      = "#1a1d2e"
ACCENT    = "#6c63ff"
ACCENT2   = "#00d4aa"
DANGER    = "#ff4d6d"
TEXT      = "#e2e8f0"
SUBTEXT   = "#94a3b8"
BORDER    = "#2d3148"
SUCCESS   = "#22c55e"
WARNING   = "#f59e0b"


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def make_button(parent, text, command, color=ACCENT, **kw):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="white", activebackground=color,
        activeforeground="white", relief="flat",
        padx=14, pady=7, cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _lighten(hex_color):
    """Return a slightly lighter shade of a hex colour."""
    r = min(255, int(hex_color[1:3], 16) + 30)
    g = min(255, int(hex_color[3:5], 16) + 30)
    b = min(255, int(hex_color[5:7], 16) + 30)
    return f"#{r:02x}{g:02x}{b:02x}"


def make_entry(parent, placeholder="", show=None, **kw):
    var = tk.StringVar()
    entry = tk.Entry(
        parent, textvariable=var,
        bg=CARD, fg=TEXT, insertbackground=TEXT,
        relief="flat", font=("Segoe UI", 11),
        highlightthickness=1, highlightcolor=ACCENT,
        highlightbackground=BORDER,
        **({"show": show} if show else {}),
        **kw
    )
    if placeholder:
        entry.insert(0, placeholder)
        entry.config(fg=SUBTEXT)

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=TEXT)

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=SUBTEXT)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    return entry, var


def label(parent, text, size=11, bold=False, color=TEXT, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(
        parent, text=text,
        bg=parent["bg"] if hasattr(parent, "__getitem__") else BG,
        fg=color, font=("Segoe UI", size, weight), **kw
    )


# ══════════════════════════════════════════════════════════════
#  Main Application
# ══════════════════════════════════════════════════════════════

class ExchangeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Currency Exchange Office – Lab 8")
        self.geometry("1080x720")
        self.minsize(900, 600)
        self.config(bg=BG)

        # state
        self.client = None
        self.user_id = None
        self.username = None

        # build UI
        self._build_header()
        self._build_status_bar()
        self._build_content()

        # connect in background
        threading.Thread(target=self._connect, daemon=True).start()

    # ── Header ───────────────────────────────────────────────

    def _build_header(self):
        bar = tk.Frame(self, bg=CARD, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(
            bar, text="💱  Currency Exchange Office",
            bg=CARD, fg=TEXT, font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=20, pady=12)

        self.user_label = tk.Label(
            bar, text="Not logged in",
            bg=CARD, fg=SUBTEXT, font=("Segoe UI", 10)
        )
        self.user_label.pack(side="right", padx=20)

        self.conn_dot = tk.Label(bar, text="●", bg=CARD, fg=DANGER,
                                 font=("Segoe UI", 14))
        self.conn_dot.pack(side="right", padx=6)

    # ── Status bar ───────────────────────────────────────────

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Connecting to service…")
        bar = tk.Frame(self, bg="#0a0c14", height=26)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self.status_var,
                 bg="#0a0c14", fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack(side="left", padx=10)

    def set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)

    # ── Content ──────────────────────────────────────────────

    def _build_content(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=CARD, foreground=SUBTEXT,
                        padding=[16, 8], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", TEXT)])

        # tabs
        self.tab_auth    = self._make_tab("🔑  Login / Register")
        self.tab_rates   = self._make_tab("📈  Rates")
        self.tab_trade   = self._make_tab("💰  Trade")
        self.tab_wallet  = self._make_tab("👜  Wallet")
        self.tab_history = self._make_tab("📋  History")

        self._build_auth_tab()
        self._build_rates_tab()
        self._build_trade_tab()
        self._build_wallet_tab()
        self._build_history_tab()

    def _make_tab(self, title):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text=title)
        return frame

    # ── AUTH TAB ─────────────────────────────────────────────

    def _build_auth_tab(self):
        outer = tk.Frame(self.tab_auth, bg=BG)
        outer.place(relx=0.5, rely=0.45, anchor="center")

        card = tk.Frame(outer, bg=CARD, padx=40, pady=36)
        card.pack()

        label(card, "Welcome", 22, bold=True).pack(pady=(0, 4))
        label(card, "Register or log in to start trading",
              10, color=SUBTEXT).pack(pady=(0, 24))

        # username
        label(card, "Username", 10).pack(anchor="w")
        self.auth_user_entry, _ = make_entry(card, width=30)
        self.auth_user_entry.pack(fill="x", pady=(2, 12))

        # password
        label(card, "Password", 10).pack(anchor="w")
        self.auth_pass_entry, _ = make_entry(card, show="•", width=30)
        self.auth_pass_entry.pack(fill="x", pady=(2, 20))

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x")
        make_button(btn_row, "Register",
                    self._register).pack(side="left", expand=True, fill="x", padx=(0, 6))
        make_button(btn_row, "Login",
                    self._login, color=ACCENT2).pack(side="left", expand=True, fill="x")

        # deposit section
        sep = tk.Frame(card, bg=BORDER, height=1)
        sep.pack(fill="x", pady=20)

        label(card, "Quick Deposit (PLN)", 10, bold=True).pack(anchor="w")
        dep_row = tk.Frame(card, bg=CARD)
        dep_row.pack(fill="x", pady=(6, 0))
        self.deposit_entry, _ = make_entry(dep_row, width=18)
        self.deposit_entry.pack(side="left")
        make_button(dep_row, "Deposit",
                    self._deposit, color=SUCCESS).pack(side="left", padx=(8, 0))

    def _register(self):
        username = self.auth_user_entry.get().strip()
        password = self.auth_pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input", "Enter username and password.")
            return
        if not self.client:
            messagebox.showerror("Error", "Not connected to service.")
            return
        try:
            user = self.client.service.register_user(
                username=username, password=password)
            self.user_id = user.user_id
            self.username = user.username
            self._on_login()
            messagebox.showinfo("Registered",
                                f"Account created!\nUser ID: {self.user_id}")
        except Fault as f:
            messagebox.showerror("Registration failed", f.message)

    def _login(self):
        """
        The Lecture 7 service has no login endpoint — registration is
        idempotent for demo purposes. We try register first; if the
        username exists, we search users in-memory (server restart resets
        state). For a real system a login RPC would be needed.
        """
        username = self.auth_user_entry.get().strip()
        password = self.auth_pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input", "Enter username and password.")
            return
        if not self.client:
            messagebox.showerror("Error", "Not connected to service.")
            return
        try:
            user = self.client.service.register_user(
                username=username, password=password)
            self.user_id = user.user_id
            self.username = user.username
            self._on_login()
        except Fault:
            messagebox.showerror(
                "Login",
                "Username already taken (server has in-memory state).\n"
                "Restart the server and try again, or register a new user.")

    def _on_login(self):
        self.user_label.config(
            text=f"👤  {self.username}  (ID: {self.user_id})", fg=ACCENT2)
        self.set_status(f"Logged in as {self.username}")
        self.notebook.select(self.tab_rates)

    def _deposit(self):
        if not self._require_login():
            return
        try:
            amount = float(self.deposit_entry.get())
        except ValueError:
            messagebox.showwarning("Input", "Enter a valid amount.")
            return
        try:
            new_bal = self.client.service.deposit(
                user_id=self.user_id, amount=amount)
            messagebox.showinfo("Deposit OK",
                                f"Deposited {amount:.2f} PLN\n"
                                f"New PLN balance: {new_bal:.2f}")
            self.set_status(f"Deposited {amount:.2f} PLN → balance {new_bal:.2f} PLN")
        except Fault as f:
            messagebox.showerror("Deposit failed", f.message)

    # ── RATES TAB ────────────────────────────────────────────

    def _build_rates_tab(self):
        top = tk.Frame(self.tab_rates, bg=BG)
        top.pack(fill="x", padx=20, pady=16)

        label(top, "Live Exchange Rates", 16, bold=True).pack(side="left")
        make_button(top, "⟳  Refresh", self._load_rates).pack(side="right")

        # table
        cols = ("Code", "Name", "NBP Mid", "Our Buy", "Our Sell", "Spread %", "Date")
        self.rates_tree = ttk.Treeview(
            self.tab_rates, columns=cols, show="headings", height=20)

        widths = [60, 220, 90, 90, 90, 80, 100]
        for col, w in zip(cols, widths):
            self.rates_tree.heading(col, text=col)
            self.rates_tree.column(col, width=w, anchor="center")

        style = ttk.Style()
        style.configure("Treeview",
                        background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=BORDER, foreground=TEXT,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

        sb = ttk.Scrollbar(self.tab_rates, orient="vertical",
                           command=self.rates_tree.yview)
        self.rates_tree.configure(yscrollcommand=sb.set)
        self.rates_tree.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        sb.pack(side="right", fill="y", padx=(0, 20), pady=(0, 16))

    def _load_rates(self):
        if not self.client:
            messagebox.showerror("Error", "Not connected."); return
        self.set_status("Loading rates…")
        threading.Thread(target=self._fetch_rates, daemon=True).start()

    def _fetch_rates(self):
        try:
            currencies = self.client.service.get_available_currencies()
            codes = [c.code for c in currencies] if currencies else []

            # fetch mid rates in bulk
            mid_rates = {}
            if codes:
                chunk = ",".join(codes[:30])          # NBP caps at ~255 entries
                rates = self.client.service.get_multiple_rates(
                    currency_codes=chunk)
                if rates:
                    for r in rates:
                        mid_rates[r.code] = (r.currency, r.mid, r.date)

            rows = []
            for code, (name, mid, date) in mid_rates.items():
                try:
                    eff = self.client.service.get_effective_rate(
                        currency_code=code)
                    buy  = f"{eff.our_buy_rate:.4f}"
                    sell = f"{eff.our_sell_rate:.4f}"
                    sprd = f"{eff.spread_pct:.2f}%"
                except Exception:
                    buy = sell = sprd = "–"
                rows.append((code, name, f"{mid:.4f}", buy, sell, sprd, date))

            # update on main thread
            self.after(0, lambda: self._populate_rates(rows))
            self.after(0, lambda: self.set_status(
                f"Rates loaded – {len(rows)} currencies  "
                f"({datetime.now().strftime('%H:%M:%S')})"))
        except Exception as e:
            self.after(0, lambda: self.set_status(f"Error: {e}"))

    def _populate_rates(self, rows):
        self.rates_tree.delete(*self.rates_tree.get_children())
        for row in rows:
            self.rates_tree.insert("", "end", values=row)

    # ── TRADE TAB ────────────────────────────────────────────

    def _build_trade_tab(self):
        outer = tk.Frame(self.tab_trade, bg=BG)
        outer.place(relx=0.5, rely=0.45, anchor="center")

        # BUY card
        buy_card = tk.Frame(outer, bg=CARD, padx=32, pady=28)
        buy_card.grid(row=0, column=0, padx=16, pady=8)

        label(buy_card, "Buy Currency", 15, bold=True, color=SUCCESS).pack()
        label(buy_card, "Spend PLN, receive foreign currency",
              9, color=SUBTEXT).pack(pady=(2, 18))

        label(buy_card, "Currency Code (e.g. USD)", 10).pack(anchor="w")
        self.buy_code, _ = make_entry(buy_card, width=22)
        self.buy_code.pack(fill="x", pady=(2, 12))

        label(buy_card, "Amount to buy", 10).pack(anchor="w")
        self.buy_amount, _ = make_entry(buy_card, width=22)
        self.buy_amount.pack(fill="x", pady=(2, 18))

        make_button(buy_card, "Buy ▶", self._buy, color=SUCCESS).pack(fill="x")

        self.buy_result = tk.Label(
            buy_card, text="", bg=CARD, fg=ACCENT2,
            font=("Segoe UI", 9), wraplength=260, justify="left")
        self.buy_result.pack(pady=(12, 0))

        # SELL card
        sell_card = tk.Frame(outer, bg=CARD, padx=32, pady=28)
        sell_card.grid(row=0, column=1, padx=16, pady=8)

        label(sell_card, "Sell Currency", 15, bold=True, color=DANGER).pack()
        label(sell_card, "Return foreign currency, receive PLN",
              9, color=SUBTEXT).pack(pady=(2, 18))

        label(sell_card, "Currency Code (e.g. EUR)", 10).pack(anchor="w")
        self.sell_code, _ = make_entry(sell_card, width=22)
        self.sell_code.pack(fill="x", pady=(2, 12))

        label(sell_card, "Amount to sell", 10).pack(anchor="w")
        self.sell_amount, _ = make_entry(sell_card, width=22)
        self.sell_amount.pack(fill="x", pady=(2, 18))

        make_button(sell_card, "◀ Sell", self._sell, color=DANGER).pack(fill="x")

        self.sell_result = tk.Label(
            sell_card, text="", bg=CARD, fg=ACCENT2,
            font=("Segoe UI", 9), wraplength=260, justify="left")
        self.sell_result.pack(pady=(12, 0))

    def _buy(self):
        if not self._require_login(): return
        code = self.buy_code.get().strip().upper()
        try:
            amount = float(self.buy_amount.get())
        except ValueError:
            messagebox.showwarning("Input", "Enter a valid amount."); return
        try:
            res = self.client.service.buy_currency(
                user_id=self.user_id, currency_code=code, amount=amount)
            if res.success == "true":
                self.buy_result.config(
                    fg=SUCCESS,
                    text=f"✔  {res.message}\n"
                         f"PLN left: {res.new_pln_balance:.2f}\n"
                         f"{code} balance: {res.new_currency_balance:.4f}")
                self.set_status(f"Bought {amount} {code} – TX {res.transaction_id}")
            else:
                self.buy_result.config(fg=DANGER, text=f"✖  {res.message}")
        except Fault as f:
            self.buy_result.config(fg=DANGER, text=f"Error: {f.message}")

    def _sell(self):
        if not self._require_login(): return
        code = self.sell_code.get().strip().upper()
        try:
            amount = float(self.sell_amount.get())
        except ValueError:
            messagebox.showwarning("Input", "Enter a valid amount."); return
        try:
            res = self.client.service.sell_currency(
                user_id=self.user_id, currency_code=code, amount=amount)
            if res.success == "true":
                self.sell_result.config(
                    fg=SUCCESS,
                    text=f"✔  {res.message}\n"
                         f"PLN balance: {res.new_pln_balance:.2f}\n"
                         f"{code} left: {res.new_currency_balance:.4f}")
                self.set_status(f"Sold {amount} {code} – TX {res.transaction_id}")
            else:
                self.sell_result.config(fg=DANGER, text=f"✖  {res.message}")
        except Fault as f:
            self.sell_result.config(fg=DANGER, text=f"Error: {f.message}")

    # ── WALLET TAB ───────────────────────────────────────────

    def _build_wallet_tab(self):
        top = tk.Frame(self.tab_wallet, bg=BG)
        top.pack(fill="x", padx=20, pady=16)

        label(top, "My Portfolio", 16, bold=True).pack(side="left")
        make_button(top, "⟳  Refresh", self._load_wallet).pack(side="right")

        cols = ("Currency", "Balance", "Approx. PLN Value")
        self.wallet_tree = ttk.Treeview(
            self.tab_wallet, columns=cols, show="headings", height=15)
        for col in cols:
            self.wallet_tree.heading(col, text=col)
            self.wallet_tree.column(col, width=200, anchor="center")
        self.wallet_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.total_label = label(self.tab_wallet, "", 12, bold=True, color=ACCENT2)
        self.total_label.pack()

    def _load_wallet(self):
        if not self._require_login(): return
        threading.Thread(target=self._fetch_wallet, daemon=True).start()

    def _fetch_wallet(self):
        try:
            balances = self.client.service.get_balance(user_id=self.user_id)
            rows = []
            total_pln = 0.0
            for b in balances:
                if b.currency_code == "PLN":
                    rows.append(("PLN", f"{b.balance:.2f}", f"{b.balance:.2f} PLN"))
                    total_pln += b.balance
                else:
                    try:
                        rate = self.client.service.get_rate(
                            currency_code=b.currency_code)
                        pln_val = b.balance * rate.mid
                        total_pln += pln_val
                        rows.append((
                            b.currency_code,
                            f"{b.balance:.4f}",
                            f"{pln_val:.2f} PLN"
                        ))
                    except Exception:
                        rows.append((b.currency_code, f"{b.balance:.4f}", "?"))
            self.after(0, lambda: self._populate_wallet(rows, total_pln))
        except Exception as e:
            self.after(0, lambda: self.set_status(f"Wallet error: {e}"))

    def _populate_wallet(self, rows, total_pln):
        self.wallet_tree.delete(*self.wallet_tree.get_children())
        for row in rows:
            self.wallet_tree.insert("", "end", values=row)
        self.total_label.config(
            text=f"Total portfolio value ≈ {total_pln:.2f} PLN")

    # ── HISTORY TAB ──────────────────────────────────────────

    def _build_history_tab(self):
        top = tk.Frame(self.tab_history, bg=BG)
        top.pack(fill="x", padx=20, pady=16)

        label(top, "Transaction History", 16, bold=True).pack(side="left")
        make_button(top, "⟳  Refresh", self._load_history).pack(side="right")

        cols = ("ID", "Type", "Currency", "Amount", "Rate", "PLN", "Timestamp")
        self.hist_tree = ttk.Treeview(
            self.tab_history, columns=cols, show="headings", height=22)

        widths = [80, 60, 80, 90, 90, 100, 170]
        for col, w in zip(cols, widths):
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(self.tab_history, orient="vertical",
                           command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=sb.set)
        self.hist_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        sb.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))

    def _load_history(self):
        if not self._require_login(): return
        threading.Thread(target=self._fetch_history, daemon=True).start()

    def _fetch_history(self):
        try:
            txns = self.client.service.get_transaction_history(
                user_id=self.user_id)
            rows = []
            if txns:
                for t in txns:
                    rows.append((
                        t.transaction_id,
                        t.tx_type,
                        t.currency_code,
                        f"{t.amount:.4f}",
                        f"{t.rate:.4f}",
                        f"{t.pln_amount:.2f}",
                        t.timestamp[:19] if t.timestamp else "",
                    ))
            self.after(0, lambda: self._populate_history(rows))
            self.after(0, lambda: self.set_status(
                f"History: {len(rows)} transactions"))
        except Exception as e:
            self.after(0, lambda: self.set_status(f"History error: {e}"))

    def _populate_history(self, rows):
        self.hist_tree.delete(*self.hist_tree.get_children())
        for row in rows:
            tag = "buy" if row[1] == "BUY" else "sell"
            self.hist_tree.insert("", "end", values=row, tags=(tag,))
        self.hist_tree.tag_configure("buy",  foreground=SUCCESS)
        self.hist_tree.tag_configure("sell", foreground=DANGER)

    # ── Connection ───────────────────────────────────────────

    def _connect(self):
        try:
            c = Client(SERVICE_WSDL)
            self.client = c
            self.after(0, self._on_connected)
        except Exception as e:
            self.after(0, lambda: self._on_conn_failed(str(e)))

    def _on_connected(self):
        self.conn_dot.config(fg=SUCCESS)
        self.set_status(f"Connected  →  {SERVICE_WSDL}")
        # auto-load rates
        self._load_rates()

    def _on_conn_failed(self, msg):
        self.conn_dot.config(fg=DANGER)
        self.set_status(f"Cannot reach service: {msg}  "
                        f"(start exchange_office_server.py first)")

    # ── Utility ──────────────────────────────────────────────

    def _require_login(self):
        if not self.user_id:
            messagebox.showinfo("Login required",
                                "Please register or log in first.")
            self.notebook.select(self.tab_auth)
            return False
        return True


# ══════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = ExchangeApp()
    app.mainloop()
