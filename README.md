# Network Application Development

Course project for Network Application Development. This repo has lecture notes and working Python examples covering Web Services, SOAP, WSDL, and a currency exchange office system.

## Course Information

- **Course name:** Network Application Development
- **Project title:** Currency Exchange Office System
- **Description:** A network-based system simulating the functionality of an online currency exchange office, built progressively through laboratory meetings.

## What's inside

- **Lecture 1** – Intro to Web Services, what SOA is, why interoperability matters
- **Lecture 2** – SOAP protocol, how messages work, the multiply example from class
- **Lecture 3** – WSDL, how service interfaces are described, auto-generating clients
- **Lecture 4** – NBP API, building a currency exchange rate service
- **Lecture 5** – Project architecture for the exchange office system
- **Lecture 6** – Currency exchange logic (buy/sell with spread)
- **Lecture 7** – Full NBP API integration (caching, retries, historical rates, statistics)
- **Lecture 8** – GUI client application (tkinter): login, live rates, buy/sell, portfolio, history

Each lecture folder has a README with notes and an `examples/` folder with runnable code.

## Setup

You need Python 3.10+ and a few libraries:

```bash
pip install -r requirements.txt
```

## How to run

Most Lecture 1 scripts just run on their own. For Lectures 2–7 you typically need to start the server first:

```bash
# terminal 1 — start the server
python Lecture-07-NBP-Integration/examples/exchange_office_server.py

# terminal 2 — run the GUI client (Lab 8)
python Lecture-08-WPF-Client/examples/gui_client.py

# or run the script client (Lab 7)
python Lecture-07-NBP-Integration/examples/exchange_office_client.py
```

Some scripts work standalone (no server needed):
```bash
python Lecture-04-NBP-Exchange-Rates/examples/nbp_api_demo.py
python Lecture-06-Exchange-Logic/examples/exchange_logic_demo.py
python Lecture-07-NBP-Integration/examples/nbp_integration_demo.py
```

Check the README in each lecture folder for more details.

## Project structure

```
Network-Application-Development/
├── Lecture-01-Introduction-to-Web-Services/
│   ├── README.md
│   └── examples/
│       ├── web_service_concepts.py
│       ├── soa_demo.py
│       └── interoperability_demo.py
├── Lecture-02-SOAP-Protocol/
│   ├── README.md
│   └── examples/
│       ├── soap_server.py
│       ├── soap_client.py
│       ├── soap_message_anatomy.py
│       └── raw_soap_client.py
├── Lecture-03-WSDL/
│   ├── README.md
│   └── examples/
│       ├── wsdl_anatomy.py
│       ├── wsdl_server.py
│       ├── wsdl_client.py
│       └── wsdl_inspector.py
├── Lecture-04-NBP-Exchange-Rates/
│   ├── README.md
│   └── examples/
│       ├── nbp_api_demo.py
│       ├── exchange_rate_server.py
│       └── exchange_rate_client.py
├── Lecture-05-Project-Architecture/
│   ├── README.md
│   └── examples/
│       ├── models.py
│       ├── exchange_office_server.py
│       └── exchange_office_client.py
├── Lecture-06-Exchange-Logic/
│   ├── README.md
│   └── examples/
│       ├── exchange_logic_demo.py
│       ├── exchange_office_server.py
│       └── exchange_office_client.py
├── Lecture-07-NBP-Integration/
│   ├── README.md
│   └── examples/
│       ├── nbp_client.py
│       ├── nbp_integration_demo.py
│       ├── exchange_office_server.py
│       └── exchange_office_client.py
├── Lecture-08-WPF-Client/
│   ├── README.md
│   └── examples/
│       └── gui_client.py
├── README.md
└── requirements.txt
```

## Tech used

- [Spyne](http://spyne.io/) for building SOAP services
- [Zeep](https://docs.python-zeep.org/) for calling them
- [NBP API](https://api.nbp.pl/) for real exchange rates
- lxml for XML stuff
- requests for HTTP calls
