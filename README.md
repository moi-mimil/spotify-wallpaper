<div align="center">
  <h2> 🎧 Spotify Wallpaper Updater</h2>
  <p><strong>Beautiful real-time GNOME wallpaper synced with your Spotify music</strong></p>
  
  ![Python](https://img.shields.io/badge/python-3.8+-blue)
  ![License](https://img.shields.io/badge/license-MIT-green)
  ![GitHub issues](https://img.shields.io/github/issues/moi-mimil/spotify-wallpaper)
  <br><br>
  <em>The ultimate version with smart caching, dynamic text sizing & better visuals</em>
</div>

---

## ✨ Features

- 🎵 **Real-time** wallpaper updates via Spotify (MPRIS/DBus)
- 🧠 **Smart Album Caching** — Saves covers locally with clean filenames (`Album - Artist.png`)
- 🖼️ Beautiful blurred background with perfectly centered album art
- 📝 **Smart Text Display** — Shows track title with **dynamic font sizing** (no more overflowing text!)
- 🌈 **Complementary text color** — Automatically picks the best contrasting color
- 🛎️ **Desktop notifications** when the wallpaper updates
- 📺 Automatic screen resolution detection
- 🌐 Smart offline handling with clear feedback
- 💾 Optional smart caching (highly recommended)
- 🛑 Clean & graceful exit with `Ctrl+C`

---

<div align="center">
  <h2> 📸 Preview </h2>
</div>

<div align="center">
  <img src="assets/preview1.png" alt="Preview with title" width="300"/>
  <img src="assets/preview2.png" alt="Preview without title" width="300"/>
</div>

---

## 🎶 Track Title on Wallpaper

The script can display the currently playing track title below the album cover.

- Text **automatically shrinks** if the title is very long (fixed in v3.1)
- Uses **complementary color** for better visibility on any album art
- You can enable/disable it when starting the script

---

## 💡 Why this project?

Most wallpaper tools are static or manual. This project turns your desktop into a live visualizer that reacts to your Spotify listening experience in real time.

---

## ⚙️ Requirements

- Linux with **GNOME** desktop
- Spotify installed via the **official** .deb or Flatpak (Snap version may have DBus issues)
- Python 3.8+
- Internet connection (only needed to download new album covers)

### Python Dependencies
Install all required packages with:
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python3 spotify-wallpaper.py
```
The script will ask you a couple of quick questions when you first run it.

Then just play music on Spotify and enjoy ✨

---

## 📦 Installation

Clone the repo:

```bash
git clone https://github.com/moi-mimil/spotify-wallpaper.git
cd spotify-wallpaper
pip install -r requirements.txt
python3 spotify-wallpaper.py
```
---

## 🧠 How it works

* Fetches current track info using DBus (MPRIS) from Spotify
* Uses smart album-based caching to avoid re-downloading the same album covers
* Creates a blurred background with a nicely centered album art using Pillow
* Automatically adjusts font size so the track title never overflows the screen
* Chooses complementary text color for good contrast on any album cover
* Updates the GNOME wallpaper using gsettings
* Shows a desktop notification when the wallpaper changes

---

## ⚠️ Notes

* Works best on GNOME desktop (uses gsettings)
* Requires Spotify to be actively playing
* Long song titles are now properly handled thanks to dynamic font sizing
* Smart caching makes repeated listens faster and saves your bandwidth
* Internet is only needed when playing a new album for the first time

---

## 📁 Project Structure

```
.
├── spotify-wallpaper.py          # Main script (v2)
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── assets/
    ├── preview1.png
    └── preview2.png
```

---

## 📜 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Feel free to open issues or submit pull requests if you have ideas or improvements!

### Made by [me](https://github.com/moi-mimil)

---
