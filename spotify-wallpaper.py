#!/usr/bin/env python3
"""
Spotify Wallpaper Updater - Ultimate Edition (v2)
Fixed: Dynamic smart text sizing (no more oversized titles)
"""

import os
import time
import logging
import subprocess
from typing import Optional, Tuple

import dbus
import requests
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageStat

# -------------------
# Config
# -------------------
CACHE_DIR = "album_cache"
FINAL_COVER = "cover.png"
CURRENT_COVER = "current-cover.png"
SCALE_HEIGHT = 0.75

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

os.makedirs(CACHE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------------
# Utility Functions
# -------------------
def sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, '_')
    return name.strip()[:100]


def get_album_cache_path(album: str, artist: str) -> str:
    safe_album = sanitize_filename(album)
    safe_artist = sanitize_filename(artist)
    return os.path.join(CACHE_DIR, f"{safe_album} - {safe_artist}.png")


def get_screen_resolution() -> Tuple[int, int]:
    try:
        output = subprocess.check_output("xrandr --query", shell=True).decode()
        for line in output.splitlines():
            if " connected primary" in line:
                res = line.split()[2].split("+")[0]
                w, h = map(int, res.split("x"))
                return w, h
    except Exception:
        pass
    return 1920, 1080


def send_notification(title: str, message: str, icon: str = ""):
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        interface = dbus.Interface(obj, "org.freedesktop.Notifications")
        interface.Notify("Spotify Wallpaper", 0, icon, title, message, [], {}, 4000)
    except Exception:
        pass  # silent fail


def average_rgb(image_path: str):
    img = Image.open(image_path).convert("RGB").resize((64, 64))
    stat = ImageStat.Stat(img)
    return tuple(int(x) for x in stat.mean)


def complementary_color(rgb):
    return (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])


def is_connected() -> bool:
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.RequestException:
        return False


def get_spotify_metadata() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    try:
        bus = dbus.SessionBus()
        proxy = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")

        title = metadata.get("xesam:title", "Unknown Title")
        artist = ", ".join(metadata.get("xesam:artist", ["Unknown Artist"]))
        album = metadata.get("xesam:album", "Unknown Album")
        art_url = metadata.get("mpris:artUrl", None)

        return title, artist, album, art_url
    except Exception:
        return None, None, None, None


def download_cover(url: str, save_path: str) -> bool:
    try:
        if url.startswith("file://"):
            local = url[7:]
            if os.path.exists(local):
                with open(local, "rb") as f_in, open(save_path, "wb") as f_out:
                    f_out.write(f_in.read())
                return True
            return False

        r = requests.get(url, timeout=6)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        logging.error(f"{RED}Download failed: {e}{RESET}")
        return False


# -------------------
# Improved Wallpaper Creation with Smart Text Sizing
# -------------------
def create_wallpaper(input_path: str, output_path: str, w: int, h: int, title: str, show_text: bool):
    cover = Image.open(input_path).convert("RGB")
    
    # Blurred background
    bg = cover.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(22))
    
    # Scale and center the album cover
    max_h = int(h * SCALE_HEIGHT)
    ratio = cover.width / cover.height
    new_w = min(w, int(max_h * ratio))
    new_h = int(new_w / ratio)

    if new_h > max_h:
        new_h = max_h
        new_w = int(new_h * ratio)

    cover_resized = cover.resize((new_w, new_h), Image.LANCZOS)
    x = (w - new_w) // 2
    y = (h - new_h) // 2
    bg.paste(cover_resized, (x, y))

    # ====================== SMART TEXT SIZING ======================
    if show_text and title:
        draw = ImageDraw.Draw(bg)
        avg_color = average_rgb(input_path)
        text_color = complementary_color(avg_color)

        # Dynamic font sizing - prevent text from being too big
        max_text_width = int(w * 0.88)        # max 88% of screen width
        font_size = max(26, w // 32)          # starting reasonable size

        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, font_size)
            
            # Reduce font size until text fits
            while font_size > 16:
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
                if text_width <= max_text_width:
                    break
                font_size -= 2
                font = ImageFont.truetype(font_path, font_size)
                
        except Exception:
            font = ImageFont.load_default()
            font_size = 20

        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (w - text_width) // 2
        text_y = y + new_h + 40   # a bit of breathing room below the cover

        draw.text((text_x, text_y), title, fill=text_color, font=font)

    bg.save(output_path, quality=95)
    logging.info("Wallpaper created")


def set_wallpaper(path: str, title: str, artist: str):
    abs_path = os.path.abspath(path)
    uri = f"file://{abs_path}"
    
    for key in ["picture-uri", "picture-uri-dark"]:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", key, uri],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    send_notification("Spotify Wallpaper", f"Now playing:\n{title}\nby {artist}", f"file://{abs_path}")
    logging.info(f"{GREEN}Wallpaper updated → {title}{RESET}")


# -------------------
# Main
# -------------------
def main():
    print("♪ Spotify Album Wallpaper Updater - Ultimate v2 ♪\n")

    width, height = get_screen_resolution()
    print(f"Screen resolution: {width}x{height}")

    show_text = input("Show track title on wallpaper? (y/n): ").lower().startswith('y')
    use_cache = input("Enable smart album caching? (y/n): ").lower().startswith('y')

    previous_key = None
    was_offline = False

    print(f"\n{GREEN}Ready! Play something on Spotify 🎵{RESET}\n")

    while True:
        online = is_connected()

        if not online and not was_offline:
            logging.error(f"{RED}No internet — covers won't update until reconnected.{RESET}")
            was_offline = True
        elif online and was_offline:
            logging.info(f"{GREEN}Internet restored.{RESET}")
            was_offline = False

        title, artist, album, art_url = get_spotify_metadata()
        if not title or not art_url:
            time.sleep(1)
            continue

        current_key = f"{album}|{artist}|{title}"

        if current_key == previous_key:
            time.sleep(0.8)
            continue

        logging.info(f"Now playing: {title} — {artist}")

        cache_path = get_album_cache_path(album, artist) if use_cache else CURRENT_COVER

        if not os.path.exists(cache_path):
            if online:
                download_cover(art_url, cache_path)
            elif not os.path.exists(cache_path):
                time.sleep(1)
                continue

        if os.path.exists(cache_path):
            create_wallpaper(cache_path, FINAL_COVER, width, height, title, show_text)
            set_wallpaper(FINAL_COVER, title, artist)
            previous_key = current_key

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Goodbye... Come back whenever you want {RESET}")
    except Exception as e:
        logging.error(f"{RED}Error: {e}{RESET}")
