#!/usr/bin/env python3
"""
Spotify Album Wallpaper Updater - QoL Edition

Features:
- Automatically updates GNOME wallpaper to current Spotify album cover
- Dynamic screen resolution detection
- Red error messages for visibility
- Internet retry every loop, error on each new track if offline
- Graceful exit with Ctrl+C
- Avoids unnecessary downloads if same album cover is already cached
"""

import os
import time
import logging
import subprocess
from typing import Optional, Tuple

import dbus
import requests
from PIL import Image, ImageFilter

# -------------------
# Constants
# -------------------
CURRENT_COVER = "current-cover.png"  # temporary cover
FINAL_COVER = "cover.png"
CACHE_DIR = "album_cache"           # optional cache directory
SCALE_HEIGHT = 0.75

RED = "\033[91m"
RESET = "\033[0m"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------------
# Utility Functions
# -------------------
def get_screen_resolution() -> Tuple[int, int]:
    """Get primary monitor resolution."""
    try:
        output = subprocess.check_output("xrandr | grep '*' | awk '{print $1}'", shell=True)
        resolution = output.decode().split()[0]
        width, height = map(int, resolution.split('x'))
        logging.info("Detected screen resolution: %dx%d", width, height)
        return width, height
    except Exception:
        logging.warning("Failed to detect resolution; using 1366x768")
        return 1366, 768

def create_centered_cover(input_path: str, output_path: str, final_width: int, final_height: int):
    """Create a centered album cover with blurred background."""
    cover = Image.open(input_path).convert("RGB")
    # blurred background
    background = cover.resize((final_width, final_height), Image.LANCZOS)
    background = background.filter(ImageFilter.GaussianBlur(20))
    # scale cover
    max_height = int(final_height * SCALE_HEIGHT)
    ratio = cover.width / cover.height
    canvas_ratio = final_width / max_height
    if ratio > canvas_ratio:
        new_width = min(cover.width, final_width)
        new_height = int(new_width / ratio)
    else:
        new_height = min(cover.height, max_height)
        new_width = int(new_height * ratio)
    cover_resized = cover.resize((new_width, new_height), Image.LANCZOS)
    x_offset = (final_width - new_width) // 2
    y_offset = (final_height - new_height) // 2
    background.paste(cover_resized, (x_offset, y_offset))
    background.save(output_path)
    logging.info("Wallpaper created: %s", output_path)

def get_spotify_metadata() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get currently playing Spotify track info."""
    try:
        bus = dbus.SessionBus()
        spotify = bus.get_object("org.mpris.MediaPlayer2.spotify","/org/mpris/MediaPlayer2")
        props = dbus.Interface(spotify, "org.freedesktop.DBus.Properties")
        metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
        title = metadata.get("xesam:title", "Unknown Title")
        artists = metadata.get("xesam:artist", ["Unknown Artist"])
        art_url = metadata.get("mpris:artUrl", None)
        return title, ", ".join(artists), art_url
    except dbus.exceptions.DBusException:
        logging.error(f"{RED}Spotify not running or DBus error.{RESET}")
        return None, None, None

def download_album_cover(url: str, save_path: str = CURRENT_COVER) -> bool:
    """Download album cover; return True if successful."""
    try:
        if url.startswith("file://"):
            local_path = url[7:]
            if os.path.exists(local_path):
                with open(save_path, "wb") as out_f, open(local_path,"rb") as in_f:
                    out_f.write(in_f.read())
                logging.info("Local cover saved: %s", save_path)
                return True
            else:
                logging.error(f"{RED}Local album cover not found: {local_path}{RESET}")
                return False
        else:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except requests.ConnectionError:
        logging.error(f"{RED}No internet connection! Cannot download album cover.{RESET}")
        return False
    except requests.RequestException as e:
        logging.error(f"{RED}Failed to download album cover: {e}{RESET}")
        return False

def set_wallpaper(image_path: str = FINAL_COVER):
    """Set GNOME wallpaper."""
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        logging.error(f"{RED}Image not found: {abs_path}{RESET}")
        return
    uri = f"file://{abs_path}"
    for key in ["picture-uri","picture-uri-dark"]:
        subprocess.run(["gsettings","set","org.gnome.desktop.background", key, uri])
    logging.info("Wallpaper updated successfully!")


def is_connected() -> bool:
    """Check if there is an active internet connection."""
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.RequestException:
        return False

# -------------------
# Main Loop
# -------------------
def main():
    last_art_url: Optional[str] = None
    last_failed_art_url: Optional[str] = None  # tracks last failed cover
    width, height = get_screen_resolution()
    was_offline = False  # tracks general offline status
    previous_title = None

    try:
        while True:
            # -------------------------
            # 1️⃣ Check internet connection
            # -------------------------
            online = is_connected()
            if not online:
                if not was_offline:
                    logging.error(f"{RED}No internet connection! Album covers won't update.{RESET}")
                    was_offline = True
            else:
                if was_offline:
                    logging.info("\033[92mInternet connection restored. Resuming album cover updates.\033[0m")
                    was_offline = False

            # -------------------------
            # 2️⃣ Get Spotify metadata
            # -------------------------
            title, artist, art_url = get_spotify_metadata()
            if not title:
                # Spotify not running or DBus error
                time.sleep(1)
                continue

            # Log only on track change
            if title != previous_title:
                logging.info("Now playing: %s - %s", title, artist)
                previous_title = title

            # -------------------------
            # 3️⃣ Decide whether to update wallpaper
            # -------------------------
            if art_url and (art_url != last_art_url or not os.path.exists(CURRENT_COVER)):
                if online:
                    success = download_album_cover(art_url)
                    if success:
                        create_centered_cover(CURRENT_COVER, FINAL_COVER, width, height)
                        set_wallpaper()
                        last_art_url = art_url
                        last_failed_art_url = None  # reset failed tracker
                    else:
                        # Download failed; log once per new album
                        if art_url != last_failed_art_url:
                            logging.warning(f"{RED}Failed to download album cover: {art_url}{RESET}")
                            last_failed_art_url = art_url
                else:
                    # Internet is down and album changed → log once per new cover
                    if art_url != last_failed_art_url:
                        logging.warning(f"{RED}Track changed — cover update skipped (no internet).{RESET}")                        last_failed_art_url = art_url

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Exiting wallpaper updater...")

if __name__ == "__main__":
    main()
