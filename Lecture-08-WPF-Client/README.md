# Lecture 8 – Initial Client Application (GUI)

This lab introduces the first graphical client for the Currency Exchange Office
system. In a .NET project this would be a WPF application; here we build the
equivalent using Python's built-in **tkinter** library so that no extra
framework is required.

## What's new compared to Lecture 7

| Feature | Lecture 7 | Lecture 8 |
|---------|-----------|-----------|
| Client type | Script (terminal) | GUI (windowed app) |
| Interaction | Linear demo script | Interactive, event-driven |
| Registration | Hard-coded username | Form with text input |
| Rate display | Printed table | Sortable Treeview widget |
| Trading | Fixed amounts in code | User-entered amounts |
| Portfolio | Printed at end | Live refreshable panel |
| History | Printed at end | Coloured Treeview (buy=green, sell=red) |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               ExchangeApp (tkinter)                 │
│                                                     │
│  ┌──────────┐  ┌────────┐  ┌───────┐  ┌─────────┐  │
│  │Login/Reg │  │ Rates  │  │ Trade │  │ Wallet  │  │
│  │  Tab     │  │  Tab   │  │  Tab  │  │  Tab    │  │
│  └──────────┘  └────────┘  └───────┘  └─────────┘  │
│                     │                               │
│         Background threads (daemon)                 │
│                     │                               │
└─────────────────────┼───────────────────────────────┘
                      │ SOAP / WSDL (Zeep)
                      ▼
           ┌──────────────────────┐
           │  Exchange Office     │
           │  SOAP Service        │
           │  (Lecture 7 server)  │
           └──────────────────────┘
                      │ HTTPS / JSON
                      ▼
               ┌──────────┐
               │  NBP API │
               └──────────┘
```

## Tabs

| Tab | What it does |
|-----|-------------|
| 🔑 Login / Register | Create account or log in; quick PLN deposit |
| 📈 Rates | Live table of all NBP currencies with our buy/sell rates |
| 💰 Trade | Buy or sell foreign currency with live feedback |
| 👜 Wallet | Current balances + estimated total PLN value |
| 📋 History | Full transaction log (colour-coded by type) |

## Running

```bash
# terminal 1 – start the service from Lab 7
python Lecture-07-NBP-Integration/examples/exchange_office_server.py

# terminal 2 – launch the GUI client
python Lecture-08-WPF-Client/examples/gui_client.py
```

The GUI connects automatically on startup. If the service is not running, the
connection indicator (top-right ●) stays **red** and a message appears in the
status bar. You can start the service later — just click **Refresh** on the
Rates tab after it comes up.

> **Note:** tkinter is part of Python's standard library — no `pip install` is
> needed for the GUI itself. Only `zeep` is required (already in
> `requirements.txt`).

## Key concepts introduced

- **Separation of concerns** — the GUI layer knows nothing about SOAP; it just
  calls a thin `Client` wrapper.
- **Threading** — network calls run in daemon threads so the UI stays
  responsive during long API calls.
- **Event-driven programming** — actions are triggered by button clicks, not a
  top-to-bottom script.
- **Immediate feedback** — success/error messages appear inline (not in a
  separate console).

## Previous / Next

[← Lecture 7 – NBP Integration](../Lecture-07-NBP-Integration/)
