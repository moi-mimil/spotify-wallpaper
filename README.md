<div align="center">
  <h2> 🎧 Spotify Wallpaper </h2>

  Automatically updates your GNOME wallpaper with the currently playing Spotify album cover.
  <br>
  ![Python](https://img.shields.io/badge/python-3.8+-blue)
  ![License](https://img.shields.io/badge/license-MIT-green)
  ![GitHub issues](https://img.shields.io/github/issues/moi-mimil/spotify-wallpaper)
  ---
</div>

## ✨ Features

* 🎵 Syncs wallpaper with Spotify in real time (via MPRIS / DBus)
* 🖼️ Generates a blurred background with centered album art
* 📝 Optionally displays the currently playing track title below the album cover
* 📺 Adapts to your screen resolution automatically
* 🌐 Handles offline mode gracefully
* 🧠 Clean logging with useful status messages
* 🛑 Safe exit with ``Ctrl+C``

---

<div align="center">
  <h2> 📸 Preview </h2>
</div>

<div align="center">
  <img src="assets/preview1.png" alt="Preview 1" width="300"/>
  <img src="assets/preview2.png" alt="Preview 2" width="300"/>
</div>

---
## 🎶 Track Title on Wallpaper
The updater can optionally display the currently playing track title on your wallpaper, positioned just below the album art.
* You will be prompted when starting the script:
```
Display track title on wallpaper? (y/n):
```
* The text color is automatically chosen to contrast with the album cover for readability.
* Works with long titles by centering them under the cover.
* Can be toggled off if you prefer a clean wallpaper without text.

  
## ⚙️ Requirements

* Sudo privileges are ***not*** required (unless missing key dependencies)
* Linux (GNOME desktop)
* Spotify must be **running** and installed via the ***official*** package (Snap versions may block DBus access)
* DBus is required (usually pre-installed on modern GNOME desktops)
* Python 3.8+

### Python dependencies

> These Python packages are not included by default. Install them with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python3 spotify-wallpaper.py
```

That’s it. The wallpaper will automatically update when the track changes.

---

## 📦 Installation

Clone the repo:

```bash
git clone https://github.com/moi-mimil/spotify-wallpaper.git
cd spotify-wallpaper
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python3 spotify-wallpaper.py
```

---

## 🧠 How it works

* Uses **MPRIS (DBus)** to fetch Spotify metadata
* Downloads the current album cover
* Applies a blur + scaling effect using Pillow
* Sets it as the GNOME wallpaper via `gsettings`

---

## ⚠️ Notes

* Works on **GNOME** (uses `gsettings`)
* Requires Spotify to be running
* Internet is needed to fetch album covers (unless cached locally)

---

## 📁 Project Structure

```
.
├── spotify-wallpaper.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── assets/
```

---

## 📜 License

This project is licensed under the MIT License.

---

## 💡 Future ideas

* CLI options (blur strength, update interval, etc.)
* Support for KDE / other desktops
* Packaging as a pip installable tool
* Systemd service integration

---

## 🤝 Contributing

Feel free to open issues or submit pull requests if you have ideas or improvements!

### Made by [me](https://github.com/moi-mimil)

---
