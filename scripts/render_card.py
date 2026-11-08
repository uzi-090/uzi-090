#!/usr/bin/env python3
"""Render the animated discord-github-readme SVG as a browser-captured GIF.

The source project embeds animated Discord assets in an SVG. GitHub freezes those
inside SVG <img> tags, so we render the SVG inline in a Chromium document,
capture frames, and encode a normal GIF with ffmpeg.
"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from playwright.sync_api import sync_playwright
from PIL import Image

SOURCE = 'https://dsc-readme.tsuni.dev/api/user/'


def download_svg(discord_id: str, width: int, theme: str, target: Path) -> None:
    if not re.fullmatch(r'\d{16,22}', discord_id):
        raise ValueError('DISCORD_USER_ID must be a numeric Discord ID.')
    qs = urlencode({'animate': 'true', 'width': str(width), 'theme': theme})
    url = f'{SOURCE}{discord_id}?{qs}'
    r = requests.get(url, timeout=40, headers={'User-Agent': 'uzi-090-animated-discord-card/1.0'})
    r.raise_for_status()
    if len(r.content) > 18_000_000:
        raise RuntimeError('Source SVG too large to safely render.')
    if b'<svg' not in r.content[:2000]:
        raise RuntimeError('The service did not return an SVG. Join the service Discord server and check the user ID.')
    target.write_bytes(r.content)


def capture(svg_path: Path, frames_dir: Path, fps: int, seconds: float, chrome_path: str | None) -> None:
    count = round(fps * seconds)
    with sync_playwright() as p:
        opts = {'headless': True, 'args': ['--disable-dev-shm-usage']}
        if chrome_path:
            opts['executable_path'] = chrome_path
        browser = p.chromium.launch(**opts)
        page = browser.new_page(viewport={'width': 900, 'height': 900}, device_scale_factor=1, reduced_motion='no-preference', java_script_enabled=False)
        # Mount SVG inline in a browser document, NOT as an <img>. The original
        # SVG includes encoded animated assets that can then animate in Chrome.
        source = svg_path.read_text(encoding='utf-8-sig')
        pos = source.find('<svg')
        if pos < 0:
            raise RuntimeError('Source does not contain SVG markup.')
        page.set_content('<!doctype html><html><head><style>body{margin:0;background:transparent}</style>'
                         '</head><body>' + source[pos:] + '</body></html>', wait_until='load')
        svg = page.locator('svg').first
        svg.wait_for(timeout=10000)
        bounds = svg.bounding_box()
        if not bounds or bounds['width'] < 10 or bounds['height'] < 10:
            browser.close()
            raise RuntimeError('SVG image has invalid dimensions.')
        print(f'Captured SVG bounds: {bounds["width"]:.0f} x {bounds["height"]:.0f}')
        page.wait_for_timeout(500)
        start = time.monotonic()
        for i in range(count):
            deadline = start + i / fps
            delay = deadline - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            svg.screenshot(path=str(frames_dir / f'frame_{i:04d}.png'), animations='allow', timeout=15000)
        browser.close()
    print(f'Captured {count} frames at a target {fps} fps')


def encode_gif(frames_dir: Path, fps: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-framerate', str(fps), '-i', str(frames_dir / 'frame_%04d.png'),
        '-filter_complex',
        '[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];'
        '[b][p]paletteuse=dither=bayer:bayer_scale=4',
        '-loop', '0', str(output)
    ]
    subprocess.run(cmd, check=True)
    with Image.open(output) as im:
        print(f'GIF: {im.size[0]} x {im.size[1]}, {getattr(im,"n_frames",1)} frames')
    print(f'Output size: {output.stat().st_size / 1024 / 1024:.2f} MB at {output}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Make an animated GIF of a Discord profile card')
    parser.add_argument('--discord-id', default=os.getenv('DISCORD_USER_ID', '737953430051618839'))
    parser.add_argument('--theme', default='tokyoNight')
    parser.add_argument('--width', type=int, default=480)
    parser.add_argument('--fps', type=int, default=20)
    parser.add_argument('--seconds', type=float, default=5.0)
    parser.add_argument('--chrome-path', default=os.getenv('CHROME_PATH'))
    parser.add_argument('--svg-path', type=Path, help='Optional local SVG for offline testing')
    parser.add_argument('--output', type=Path, default=Path('assets/discord-card.gif'))
    args = parser.parse_args()
    if args.fps not in range(5, 31) or not 1.0 <= args.seconds <= 12.0 or not 240 <= args.width <= 700:
        parser.error('Use fps 5–30, seconds 1–12, width 240–700.')
    with tempfile.TemporaryDirectory(prefix='discord-card-') as t:
        tmp = Path(t)
        source = args.svg_path or tmp / 'card.svg'
        if not args.svg_path:
            download_svg(args.discord_id, args.width, args.theme, source)
        frames = tmp / 'frames'
        frames.mkdir()
        capture(source, frames, args.fps, args.seconds, args.chrome_path)
        encode_gif(frames, args.fps, args.output)


if __name__ == '__main__':
    main()
