# reverse-proxy-check

An interactive CLI tool I wrote to check if a website is using a reverse proxy (such as nginx) or CDN (such as Cloudflare or Fastly) to serve its content.

In general, the approach used by this tool is to check if the domain and its IPv4 address(es) produce the same (or closely similar) website.

Note that answers are not always 100% accurate because websites do not necessarily serve the same webpage twice, so it instead will produce a percentage (which is usually close to either 0% or 100%).

Inconclusive results near the middle should be checked manually by entering the domain and an IP address known to be used by the domain into two web browser windows and comparing the resulting webpages.

This utility is not guaranteed to work 100% of the time. Use your own judgement in production environments.

## Usage

To use it, enter a domain name (or a space-separated list of domains). The tool will then tell you which domains are and are not behind a reverse proxy or CDN.

## Setup

Install dependencies:

```
python3 -m venv ./venv/
source ./venv/bin/activate
pip install -r requirements.txt
```

And run:

```
python3 ./main.py
```

## Examples

Sites that should be behind a reverse proxy include:
- leoapagano.com
- stackoverflow.com
- nytimes.com

Sites that should NOT be behind a reverse proxy include:
- github.com
- google.com
- uconn.edu