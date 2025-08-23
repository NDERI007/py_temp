#📒 Contact Manager

A simple Python project for managing contacts (name, phone, email) with validation, search, updates, and CSV persistence using pandas.

This project demonstrates:

Dataclasses for clean data modeling

Validation & normalization of input (email format, no empty fields)

CRUD operations (create, read, update, delete) on contacts

Persistence with safe CSV saving/loading using pandas

Tabulated CLI output via tabulate

#🚀 Features

Add and remove contacts

Update existing contacts (name, phone, email only)

Search contacts by name (case-insensitive)

List all contacts

Save to CSV (atomic write → safe from corruption)

Load from CSV with tabulated preview

Automatic UUID assignment per contact

🛠 Installation

Clone this repository and install dependencies:

```
git clone https://github.com/NDERI007/contact_manager.git
cd contact_manager
pip install -r requirements.txt
```

Requirements:

```
Python 3.10+

pandas

tabulate
```
