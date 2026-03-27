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
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# -------------------
# Constants
# -------------------
CURRENT_COVER = "current-cover.png"  # temporary cover
FINAL_COVER = "cover.png"
CACHE_DIR = "album_cache"           # optional cache directory
SCALE_HEIGHT = 0.75  # scale cover to 75% of screen height for better aesthetics

RED = "\033[91m"
RESET = "\033[0m"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------------
# Utility Functions
# -------------------
def get_screen_resolution():
    try:
        output = subprocess.check_output("xrandr --query", shell=True).decode()
        for line in output.splitlines():
            if " connected primary" in line:
                res = line.split()[2].split("+")[0]
                width, height = map(int, res.split('x'))
                return width, height
        # fallback
        return 1920, 1080
    except Exception:
        return 1920, 1080
    
def average_rgb(image_path):
    """
    Calculate the average RGB value of an image.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        tuple: (avg_r, avg_g, avg_b)
    """
    image = Image.open(image_path).convert("RGB")
    pixels = list(image.getdata())
    total_pixels = len(pixels)
    
    sum_r = sum_g = sum_b = 0
    for r, g, b in pixels:
        sum_r += r
        sum_g += g
        sum_b += b
    
    avg_r = round(sum_r / total_pixels)
    avg_g = round(sum_g / total_pixels)
    avg_b = round(sum_b / total_pixels)
    
    return (avg_r, avg_g, avg_b)

def complementary_color(rgb):
    """
    Returns the complementary color for an RGB tuple.
    
    Parameters:
        rgb (tuple): A tuple of three integers (R, G, B), each 0-255.
        
    Returns:
        tuple: Complementary RGB color.
    """
    r, g, b = rgb
    return (255 - r, 255 - g, 255 - b)

def create_centered_cover(input_path: str, output_path: str, final_width: int, final_height: int, track_title: str = "", title_condition: bool = True, screen_width: int = 1366):
    """Create a centered album cover with blurred background and track title below."""
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

    # paste cover on background
    x_offset = (final_width - new_width) // 2
    y_offset = (final_height - new_height) // 2
    background.paste(cover_resized, (x_offset, y_offset))

    # -----------------------
    # Add track title text
    # -----------------------
    if track_title and title_condition:
        draw = ImageDraw.Draw(background)
        avg_color = average_rgb(input_path)
        text_color = complementary_color(avg_color)

        # choose a font and size (you may need a .ttf path)
        try:
            # Use a system font or provide a path to a .ttf file
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_size = screen_width//30  # adjust this to make text bigger or smaller
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            logging.warning("Font file not found, using default font.")
            font = ImageFont.load_default()

        # get text bounding box
        bbox = draw.textbbox((0, 0), track_title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # position text below the cover
        text_x = (final_width - text_width) // 2
        text_y = y_offset + new_height + 25  # 25px below the cover

        draw.text((text_x, text_y), track_title, fill=text_color, font=font)

    background.save(output_path)
    logging.info("Wallpaper created with title: %s", output_path)

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
    previous_title: Optional[str] = None
    last_art_url: Optional[str] = None
    was_offline = False
    width, height = get_screen_resolution()
    logging.info(f"Detected screen resolution: {width}x{height}")
    display_title = input("Display track title on wallpaper? (y/n):\n").strip().lower() == 'y'

    try:
        while True:
            # -------------------------
            # 1️⃣ Check internet connection
            # -------------------------
            online = is_connected()
            if not online and not was_offline:
                logging.error(f"{RED}No internet connection! Album covers won't update.{RESET}")
                was_offline = True
            elif online and was_offline:
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

            # -------------------------
            # 3️⃣ Update wallpaper on new track
            # -------------------------
            if title != previous_title:
                logging.info("Now playing: %s - %s", title, artist)

                # Download album cover if URL changed or missing
                if art_url and (art_url != last_art_url or not os.path.exists(CURRENT_COVER)):
                    if online and download_album_cover(art_url):
                        last_art_url = art_url
                    else:
                        logging.warning(f"{RED}Failed to download album cover or offline.{RESET}")

                # Always create wallpaper with current title if we have a cover
                if os.path.exists(CURRENT_COVER):
                    create_centered_cover(CURRENT_COVER, FINAL_COVER, width, height, title, display_title, width)
                    set_wallpaper()
                else:
                    logging.warning(f"{RED}No cover available to create wallpaper.{RESET}")

                previous_title = title

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Exiting wallpaper updater...\n \033[92mGoodbye!\033[0m")

if __name__ == "__main__":
    main()
