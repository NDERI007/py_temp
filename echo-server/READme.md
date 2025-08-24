# Echo Server (Python)

A simple multi-threaded echo server and client implemented in Python using `socket`, `threading` and `asyncio`.

## Features

- Accepts multiple concurrent clients
- Echoes back whatever data is sent
- Two implementations:
  - **Thread-per-client model** using `socket` + `threading`
  - **Async model** using `asyncio` (efficient with many concurrent clients)
- Configurable buffer size and timeout
- Inactivity timeout (async version)
- Tested with `pytest` and `pytest-asyncio`

## Requirements

- Python 3.9+
- pytest (for running tests)
- pytest-asyncio(for running async tests)

Install dependencies:

```bash
pip install -r requirements.txt
```
