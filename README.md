# MBH Proxy Rotator v2.0

A lightweight, multithreaded proxy checker and rotator built with Python.

MBH Proxy Rotator allows you to validate proxy servers, measure response latency, rotate between working proxies, and monitor connection statistics through a simple command-line interface.

## Features

- **Proxy Scanner** — Validate multiple proxies concurrently using multithreading.
- **Proxy Rotation** — Automatically rotate through available proxies using round-robin.
- **IP Checker** — Display the public IP address used by each proxy.
- **Latency Testing** — Measure proxy response times in milliseconds.
- **Automatic Filtering** — Separate working proxies from failed ones.
- **Proxy Export** — Save validated proxies to `working_proxies.txt`, sorted by latency.
- **Statistics** — Track connection attempts, successes, failures, and success rates.
- **Multiple Protocols** — Support for HTTP, HTTPS, SOCKS5, and SOCKS5H.
- **Error Handling** — Handle timeouts, unreachable servers, and invalid proxy entries.

## Requirements

- Python 3.9+
- Requests library
- PySocks (for SOCKS proxy support)

Install dependencies:

```bash
python -m pip install "requests[socks]"
```

## Installation

1. Download or clone the repository.
2. Install the required dependencies.
3. Create a `proxies.txt` file in the project directory.
4. Add your proxy addresses, one per line.
5. Run the application:

```bash
python main.py
```

## Proxy Configuration

Add proxies to `proxies.txt` using the following formats:

```text
http://127.0.0.1:8080
http://127.0.0.1:3128
socks5h://127.0.0.1:1080
```

The addresses above are examples.

Supported formats:

- `http://host:port`
- `https://host:port`
- `socks5://host:port`
- `socks5h://host:port`
- `http://username:password@host:port`

Entries without a protocol automatically default to HTTP.

## Usage

Launch the application to access the interactive menu:

```text
[1] SCAN ALL PROXIES
[2] CHECK CURRENT PROXY IP
[3] AUTO ROTATE PROXIES
[4] EXPORT WORKING PROXIES
[5] STATISTICS
[6] RELOAD PROXY LIST
[0] EXIT
```

### Proxy Scanner

Select option `1` to test every proxy in your list.

The scanner performs concurrent connection tests, identifies responsive proxies, and records their response times.

Working proxies are automatically exported to `working_proxies.txt`.

### Automatic Rotation

Select option `3` to configure automatic proxy rotation.

You can specify:

-
