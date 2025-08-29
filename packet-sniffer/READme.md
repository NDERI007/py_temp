# Project Name

## Description

Simple local HTTP Host header sniffer using Scapy
Filename: scapy_http_sniffer.py

Purpose:

- Sniff HTTP requests (port 80/8080) on an interface or from a pcap
- Extract the Host: header from HTTP requests and log them
- Provide basic anomaly detection (rate spikes, missing/malformed Host, many distinct hosts)
- Meant for LOCAL TESTING only (your own machine / lab)

Usage examples:
python3 scapy_http_sniffer.py --pcap sample.pcap --logfile logs/pcap_hosts.log

Test locally with a built-in HTTP server (on the same host):
python3 -m http.server 8000 &
curl -v --header "Host: example.test" http://127.0.0.1:8000/

Notes & safety:

- You must have proper permission to sniff traffic on networks. Only run on networks/hosts you control.
- This sniffer looks at plaintext HTTP only. HTTPS is encrypted and cannot be inspected without interception.

Requires:

- scapy (pip install scapy)

## Setup

```bash
pip install -r requirements.txt
```
