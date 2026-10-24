<div align="center">

# kasys

**A minimalistic, monochromatic way to see your setup.**

Black and white, no colors, no noise. Open it, glance, close it.

![Python](https://img.shields.io/badge/python-3.14%2B-black)
![Platform](https://img.shields.io/badge/platform-Wayland%20%C2%B7%20wlr--layer--shell-black)

</div>

---

<div align="center">

![Screenshot of the kasys Overview page](https://github.com/user-attachments/assets/7003af84-b593-41f7-9597-21dc5fe88f91)

</div>

---

## What it is

kasys is a system viewer for Linux as a
full-screen overlay. Everything is read straight
from `/proc` and `/sys`.

The Overview page shows, in one screen:

- **CPU** — total usage with a 60s graph, model, cores / threads, current total and 60s peak, top 3 processes by CPU
- **Memory** — used / total
- **Disk** — free space per disk
- **Network** — download / upload speed
- **GPU** — utilization with a 60s graph, VRAM, temperature, clock, fan (AMD)
- **Temperatures** — one sensor per chip
- **Processes** — top processes by memory
- **System** — hostname, OS, uptime, OS age, shell and your avatar

---

<div align="center">

![Screenshot of the kasys System page](https://github.com/user-attachments/assets/f5702ec3-04ee-4c38-840f-bb2a2e53f639)

</div>

The System page is about the software side of the machine:

- **Uptime, OS age, last update** — when the system booted, when it was installed, when the last full upgrade finished
- **Boot analysis** — total boot time split into firmware, loader, kernel, initrd and userspace, and the longest stage
- **Recent boots** — boot time of the last 7 startups
- **Startup services** — what held up the boot (systemd's critical chain), slowest first
- **Host information** — OS, kernel, architecture, package count, boot mode, Secure Boot, bootloader
- **Desktop & session** — desktop, display server, shell, resolution and refresh rate

## Design

- **Monochrome.** Black, white and grays. The data is the only thing that stands out.
- **Minimal.** No settings menus, no themes, no animations for show.
- **Glanceable.** It is an overlay: one keybind opens it, the same keybind closes it.

## Who made what

kasys is my first real project, built to learn Python and how Linux exposes
its hardware.

- **Backend (`kasys/collectors/`)** — written by hand by me. Every collector
  reads `/proc` or `/sys`, returns a dataclass, and runs on its own from the
  terminal (`python -m kasys.collectors.cpu`).
- **Frontend (`kasys/bridge.py`, `qml/`, `main.py`)** — written by
  [Claude Code](https://claude.com/claude-code), following my mockups.

## Requirements

| Dependency | Purpose | Arch / CachyOS package |
| --- | --- | --- |
| Python **3.14+** | runtime (the code uses 3.14 syntax) | `python` |
| PySide6 | Qt 6 / QML | `pyside6` |
| layer-shell-qt | the overlay window | `layer-shell-qt` |
| JetBrainsMono Nerd Font | text and icons | `ttf-jetbrains-mono-nerd` |

And a Wayland compositor with **wlr-layer-shell**: Hyprland, Sway, river,
niri, ...

> [!IMPORTANT]
> **The Nerd Font is required.** The font is fixed to `JetBrainsMono Nerd Font`
> and every icon is a Nerd Font glyph. Without it, icons turn into boxes and
> the text falls back to another font, which may not fit the layout.

> [!IMPORTANT]
> **Install PySide6 from your distro, not pip.** `layer-shell-qt` is a Qt
> plugin built against the system Qt; a pip PySide6 ships its own Qt and can
> fail to load it.

```fish
sudo pacman -S python pyside6 layer-shell-qt ttf-jetbrains-mono-nerd
```

## Running

```fish
git clone https://github.com/Roberth-Souza/kasys
cd kasys
python main.py
```

| Key | Action |
| --- | --- |
| `j` / `↓` | Next page |
| `k` / `↑` | Previous page |
| `q` / `Esc` / click outside | Close |

Running `main.py` again while it is open closes it, so one keybind can toggle it:

```lua
-- Hyprland (Lua config)
hl.bind("SUPER + S", hl.dsp.exec_cmd("python /path/to/kasys/main.py"))
```

### Daemon mode (optional)

By default nothing keeps running after the window closes, so the graphs start
empty every time it opens.

With `--daemon`, kasys starts hidden and stays resident, sampling in the
background. Running `python main.py` (no flag) then shows or hides that
window instead of starting a new one, and the graphs already hold the last
minute. Closing the window only hides it; `kill` the process to stop it.

Start it once with your session, e.g. in Hyprland's Lua config:

```lua
hl.on("hyprland.start", function ()
    hl.exec_cmd("python /path/to/kasys/main.py --daemon")
end)
```

and bind your toggle key (or a bar widget) to `python /path/to/kasys/main.py`.

## Avatar

The System card shows an image (png, jpg, jpeg or webp). kasys looks for it
in three steps, once at startup, and stops at the first one that works:

1. **kasys config.** The `avatar` key in `~/.config/kasys/config.toml`:

   ```toml
   # ~/.config/kasys/config.toml
   avatar = "~/Pictures/me.png"
   ```

2. **fastfetch config.** If step 1 gives nothing, kasys reads the image
   fastfetch uses: `logo` (a path) or `logo.source` in
   `~/.config/fastfetch/config.jsonc`.

3. **Placeholder.** If neither gives an image, the card shows a placeholder icon.

kasys never creates `config.toml` for you.

## Limitations

kasys was built and tested on **one machine** (CachyOS, Hyprland, Ryzen 5
5600X, Radeon RX 7800 XT). Anything else is untested.

**General**
- Linux and Wayland only, on a compositor with wlr-layer-shell. No X11, no GNOME.
- Only **Overview** and **System** are built. Processes and Hardware are placeholders.

**GPU**
- **AMD only** (`amdgpu` driver). NVIDIA and Intel GPUs show nothing.
- Only the first AMD card is read.

**CPU and temperatures**
- CPU temperature comes from `k10temp` (AMD) or `coretemp` (Intel) only.
- Cores / threads describe one socket; multi-socket machines are not handled.

**Disk**
- LUKS, LVM and mdraid volumes (`dm-*`) are left out.

**Network**
- Only physical interfaces are counted. VPNs, Docker bridges and other virtual interfaces are ignored.(for now)

**Processes**
- No sorting, filtering or killing yet.

**System page**
- **pacman only.** Package count and last update read pacman's files; other package managers show nothing.
- The bootloader is shown only if it sets the `LoaderInfo` EFI variable (systemd-boot and Limine do; GRUB likely does not).

**Avatar**
- A fastfetch config with comments is not read (it is JSONC, not JSON).
- ASCII logos are not supported, only images.

## Roadmap

The sidebar already has every page; Processes and Hardware are next.

- [x] **Overview** — everything at a glance, on one screen
- [x] **System** — OS, boot, session and the rest of the setup info
- [ ] **Processes** — the full process list, sortable by any column
- [ ] **Hardware** — CPU, GPU, disks, motherboard and sensors in detail
