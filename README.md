# kasys

btop-style system monitor for Linux: Python backend reading `/proc` and `/sys`, QML frontend.
Work in progress, learning project.

## Running

Needs PySide6 (Qt 6), `layer-shell-qt` and a Wayland compositor with the
wlr-layer-shell protocol (Hyprland, Sway, river, niri, ...).

```sh
python main.py
```

kasys is an overlay: open it, glance, close it. `q`, `Escape` or a click
outside the panel closes it; `j`/`k` switch pages. Running `main.py` again
while it is open closes it too, so one keybind can toggle it.

## Daemon mode (optional)

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
