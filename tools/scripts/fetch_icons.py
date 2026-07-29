"""
Simple script to fetch hero icons from a configurable base URL into `ui/assets/`.
Usage:
    python fetch_icons.py --base https://example.com/hero-icons --out ui/assets/icons
If no base is provided, it will try `https://example.com/hero-icons` as placeholder.

This script avoids external dependencies by using urllib.
"""
import os
import json
import argparse
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERO_FILE = os.path.join(ROOT, 'engine', 'heroes_config.json')


def main(base_url, out_dir):
    if not os.path.exists(HERO_FILE):
        print(f"heroes file not found: {HERO_FILE}")
        return
    os.makedirs(out_dir, exist_ok=True)
    with open(HERO_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    summary = []
    for name in data.keys():
        filename = f"{name.lower().replace(' ', '_')}.png"
        encoded_name = quote_plus(name)
        url = f"{base_url.rstrip('&')}&name={encoded_name}&background=random&color=fff&size=128&font-size=0.4"
        dest = os.path.join(out_dir, filename)
        try:
            req = Request(url, headers={'User-Agent': 'RedWar-Fetcher/1.0'})
            with urlopen(req, timeout=10) as resp, open(dest, 'wb') as out:
                out.write(resp.read())
            summary.append((name, True, dest))
            print(f"Fetched {name} -> {dest}")
        except (HTTPError, URLError) as e:
            summary.append((name, False, str(e)))
            print(f"Failed {name}: {e}")
    print('\nSummary:')
    for name, ok, info in summary:
        print(f"- {name}: {'OK' if ok else 'ERR'} -> {info}")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base', default='https://ui-avatars.com/api/?', help='Base URL for avatars API')
    p.add_argument('--out', default=os.path.join('ui','assets'), help='Output directory')
    args = p.parse_args()
    main(args.base, args.out)
