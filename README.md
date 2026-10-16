# Transport & Shipping System

A desktop program (Python + Tkinter) that manages a transport and shipping system using three PostgreSQL databases. The user picks a database and a table, then can read, add, edit, and delete data.

## Requirements

- macOS (the steps below are for Mac)
- Python 3 with Tkinter
- PostgreSQL (Postgres.app)
- Python library `psycopg2-binary`

## Setup and Run

### 1. Install PostgreSQL

### 2. Install Tkinter (Homebrew Python only)

```
brew install python-tk@3.14
```

### 3. Download the project

```
git clone https://github.com/MunirehHosseinzada/transport-shipping-system.git
cd transport-shipping-system
```

### 4. Create a virtual environment and install the library

```
python3 -m venv venv
source venv/bin/activate
pip install psycopg2-binary
```

### 5. Create the databases and dummy data (once)

```
python3 setup_data.py
```

This creates the three databases, the tables, and the sample data. It is safe to run again: existing databases, tables, and data are never changed.

### 6. Start the program

```
python3 main.py
```
