# Network Application Development

Course project for Network Application Development. This repo has lecture notes and working Python examples covering Web Services, SOAP, and WSDL.

## What's inside

- **Lecture 1** – Intro to Web Services, what SOA is, why interoperability matters
- **Lecture 2** – SOAP protocol, how messages work, the multiply example from class
- **Lecture 3** – WSDL, how service interfaces are described, auto-generating clients

Each lecture folder has a README with notes and an `examples/` folder with runnable code.

## Setup

You need Python 3.10+ and a few libraries:

```bash
pip install -r requirements.txt
```

## How to run

Most Lecture 1 scripts just run on their own. For Lectures 2 and 3 you need to start the server first:

```bash
# terminal 1
python Lecture-02-SOAP-Protocol/examples/soap_server.py

# terminal 2
python Lecture-02-SOAP-Protocol/examples/soap_client.py
```

Check the README in each lecture folder for more details.

## Tech used

- [Spyne](http://spyne.io/) for building SOAP services
- [Zeep](https://docs.python-zeep.org/) for calling them
- lxml for XML stuff
