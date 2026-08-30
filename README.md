# Wallforge

Wallpaper Engine-class desktop wallpaper application — Python core (PySide6)
with native-media integration (libVLC video, WebView2 web, PyOpenGL interactive).

See **BLUEPRINT.md** for the full architecture, milestones and conventions.

## Quick start (dev)
```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -c "from src.wallforge.windows.monitors import get_monitors; print(get_monitors())"
```

## Layout
- `src/wallforge/` — application source (see BLUEPRINT §3)
- `native/renderer/` — optional future native DX11 host
- `installer/` — Inno Setup script
- `build.spec` — PyInstaller onedir spec
- `BLUEPRINT.md` — the authoritative plan
