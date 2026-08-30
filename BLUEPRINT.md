# WALLFORGE — Blueprint Final v1.0

> Dokumen ini adalah **blueprint final** yang dipakai coding agent sebagai acuan
> implementasi. Status: FEASIBLE. Python = core/orchestration/UI; native hanya
> untuk library yang kita *embed* (VLC, WebView2) — bukan kode native yang kita
> tulis sendiri di MVP. GPU renderer boleh naive OpenGL dulu, naik ke DX11
> belakangan kalau perlu.

---

## 0. Status Kelayakan (ringkas)

- **Feasible, full production.** Python 3.12 + PySide6 sanggup jadi core.
- Bagian tersulit bukan fiturnya, tapi **integrasi desktop + resiliensi lifecycle**:
  - nempel di belakang icon desktop (WorkerW),
  - restore wallpaper statis kalau app keluar/crash (biar desktop nggak item),
  - re-attach pas `explorer.exe` restart,
  - DPI per-monitor biar posisi wallpaper nggak meleset di layar scaled.
- Semua itu sudah ada solusi proven (lihat §2). Sisanya tinggal fitur.

---

## 1. Keputusan Arsitektur (aku yang putusin — bisa diganti)

| Topik | Keputusan | Alasan | Alternatif |
|---|---|---|---|
| Video engine | **libVLC** (`python-vlc`) + VLC portable di-bundle | HW decode, audio, `set_hwnd()`, paling sedikit kode | PyAV + OpenGL (lebih kontrol, jauh lebih banyak kode) |
| Web wallpaper | **pywebview `edgechromium`** (WebView2) di-reparent | pakai WebView2 resmi, nggak nambah build C++ | native C++ WebView2 host (lebih robust, nambah toolchain) |
| Interactive / GPU | **PyOpenGL di QWidget** di-reparent | satu event loop (Qt), HWND ada, mudah | native DX11 host |
| Database | **`sqlite3` stdlib + repository layer** (tanpa ORM) | zero dep, migrasi penuh di tangan kita | peewee / SQLAlchemy (tambah dep) |
| Config | **JSON di `%LOCALAPPDATA%/Wallforge`** | simpel, gampang di-migrate | registry (otentik tapi rapuh) |
| Packaging | **PyInstaller `--onedir` + Inno Setup** | start cepat, gampang bundle VLC/WebView2, updater tinggal ganti file | `--onefile` (start lambat, updater ribet) |
| Event bus | **Qt signals + `core/events.py` singleton** | sudah punya loop Qt | pydispatcher (tambah dep) |
| Data dir | `%LOCALAPPDATA%/Wallforge/` (db, logs, config, cache) | standar Windows | — |
| Wallpaper user | `%USERPROFILE%/Documents/Wallforge/Wallpapers/` | user gampang tambah manual | — |

---

## 2. Integrasi Desktop Windows (INI KUNCI — belum ada di draf)

Wallpaper Engine bekerja dengan membuat jendela lalu **menjadikannya child dari
jendela `WorkerW` yang berada di belakang `SysListView32` (icon desktop)**.
Trik proven:

1. Cari `Progman` (`Shell_TrayWnd` → `Progman`).
2. Kirim `SendMessageTimeout(Progman, 0x052C, 0, 0, …)` → Windows spawn `WorkerW`.
3. `EnumWindows`, cari `WorkerW` yang **tidak** punya child `SHELLDLL_DefView`.
   Itu dia target kita (sibling icon, bukan parent icon).
4. `SetParent(render_hwnd, workerW)` + pasang style:
   - `WS_CHILD | WS_VISIBLE`
   - `WS_EX_TOOLWINDOW` (sembunyi dari taskbar/alt-tab)
   - `WS_EX_NOACTIVATE` (jangan curi focus)
   - `SetWindowPos(..., HWND_BOTTOM, ...)` (z-order paling bawah, di atas wallpaper lama)
5. Icon desktop tetap bisa diklik karena dia ada DI ATAS `WorkerW` ini.

```python
# src/wallforge/windows/desktop.py (sudah di-scaffold, inti logikanya):
def find_desktop_worker_window() -> int:
    _spawn_workerw()                      # kirim 0x052C ke Progman
    targets = []
    @WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == "WorkerW":
            if not user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None):
                targets.append(hwnd)
        return True
    user32.EnumWindows(enum_cb, 0)
    return targets[0] if targets else _find_progman()
```

### 2.1 DPI (wajib)
Deklarasikan **Per-Monitor V2** di manifest PyInstaller + panggil
`user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)`
di awal `main.py` SEBELUM window dibuat. Tanpa ini posisi wallpaper meleset di
monitor scaled.

### 2.2 Restore on exit / crash (wajib)
Simpan wallpaper statis saat start:
`SystemParametersInfoW(SPI_GETDESKWALLPAPER)`. Di `atexit` + handler
`SetConsoleCtrlHandler`/Qt `aboutToQuit` + `excepthook`, panggil
`SystemParametersInfoW(SPI_SETDESKWALLPAPER, path)` supaya desktop nggak item.

### 2.3 Explorer restart (wajib, sering luput)
Kalau `explorer.exe` crash/restart, `WorkerW` dibuat ulang → window kita
orphan (desktop item / hitam). Mitigasi: poll `IsWindow(worker_hwnd)` tiap
~2 detik; kalau invalid, cari ulang `WorkerW` lalu `SetParent` lagi + re-layout.

---

## 3. Struktur Project (refined dari draf)

```
wallforge/
├── src/wallforge/
│   ├── main.py                 # entry: DPI, excepthook, restore, app.run()
│   ├── core/
│   │   ├── application.py      # orkestrasi subsystem
│   │   ├── config.py           # dataclass Config + load/save JSON
│   │   ├── events.py           # event bus singleton (Qt signals)
│   │   └── logger.py           # rotating file logger
│   ├── ui/
│   │   ├── main_window.py      # QStackedWidget pages + Sidebar
│   │   ├── sidebar.py
│   │   ├── wallpaper_grid.py
│   │   ├── preview.py
│   │   ├── settings.py
│   │   └── dialogs/
│   ├── wallpaper/
│   │   ├── manager.py          # pilih renderer per manifest
│   │   ├── loader.py           # baca manifest + resolve content
│   │   ├── metadata.py
│   │   ├── playlist.py
│   │   └── types/{image,video,web,interactive}.py
│   ├── renderer/
│   │   ├── renderer.py         # ABC: init/start/pause/resume/resize/stop
│   │   ├── video_renderer.py   # VLC
│   │   ├── image_renderer.py
│   │   ├── web_renderer.py     # pywebview edgechromium
│   │   └── interactive_renderer.py  # PyOpenGL + WASAPI loopback
│   ├── windows/
│   │   ├── desktop.py          # WorkerW reparent (NATIVE INTEGRATION)
│   │   ├── monitors.py         # EnumDisplayMonitors
│   │   ├── fullscreen.py       # detect fullscreen/game
│   │   ├── explorer.py         # watch explorer restart
│   │   └── startup.py          # registry Run key
│   ├── performance/
│   │   ├── gpu.py              # PDH "\GPU Engine(*)\Utilization %"
│   │   ├── fps.py              # throttle render loop
│   │   ├── power.py            # GetSystemPowerStatus / WM_POWERBROADCAST
│   │   └── pause_manager.py    # keputusan pause/resume/mute
│   ├── audio/
│   │   ├── player.py           # VLC audio / system
│   │   └── mixer.py            # volume, mute
│   ├── database/
│   │   ├── database.py         # sqlite connection + migration
│   │   └── models.py           # row <-> dataclass
│   ├── tray/system_tray.py     # QSystemTrayIcon + menu
│   └── services/
│       ├── update.py           # version.json, download, verify, spawn updater
│       └── indexing.py         # scan wallpapers dir -> db
├── native/renderer/            # (opsional masa depan) DX11 host
├── assets/
├── wallpapers/
├── tests/
├── installer/Wallforge.iss     # Inno Setup
├── requirements.txt
└── build.spec                  # PyInstaller onedir
```

Penambahan vs draf: `core/events.py`, `windows/desktop.py`, `windows/fullscreen.py`,
`windows/explorer.py`, `performance/gpu.py`, `renderer/renderer.py` ABC, `services/update.py`.
`native/` sengaja dikosongin — cukup PyOpenGL di MVP.

---

## 4. Skema Database (refined)

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE schema_version (version INTEGER NOT NULL);  -- seed: 1

CREATE TABLE wallpapers (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    author      TEXT,
    type        TEXT NOT NULL,            -- image|video|web|interactive
    path        TEXT NOT NULL,            -- abs path ke folder wallpaper
    thumbnail   TEXT,                     -- abs path thumbnail.jpg
    preview     TEXT,
    favorite    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE collections (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE collection_items (
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    wallpaper_id  INTEGER NOT NULL REFERENCES wallpapers(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, wallpaper_id)
);

CREATE TABLE playlists (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE playlist_items (
    playlist_id  INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    wallpaper_id INTEGER NOT NULL REFERENCES wallpapers(id) ON DELETE CASCADE,
    position     INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, wallpaper_id)
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE monitor_profiles (
    monitor_id  TEXT NOT NULL,            -- device name dari EnumDisplayMonitors
    wallpaper_id INTEGER REFERENCES wallpapers(id) ON DELETE SET NULL,
    settings     TEXT                     -- JSON: fps, audio, sync, dst rect
);
```

Migrasi: baca `schema_version`; terapkan forward migration satu per satu
(`ALTER` / `CREATE`) sampai versi target. Jangan drop kolom — tambah kolom baru.

---

## 5. Wallpaper Plugin & Manifest

Folder wallpaper (user bisa taruh manual di `Documents/Wallforge/Wallpapers/`):

```
<wallpaper>/
├── manifest.json
├── preview.jpg
├── thumbnail.jpg
└── content/...          # video.mp4 | index.html | assets | scene.py
```

`manifest.json` (v1):

```json
{
  "name": "Cyber City",
  "author": "Dika",
  "type": "video",
  "version": "1.0",
  "resolution": "1920x1080",
  "fps": 60,
  "audio": true,
  "entry": "content/video.mp4",
  "tags": ["cyberpunk", "neon"]
}
```

`loader.py` baca manifest → `manager.py` pilih subclass `Renderer` by `type`
→ `renderer.init(hwnd, rect)` → `start()`. Thumbnail dibuat otomatis oleh
`indexing.py` (Pillow untuk image, VLC snapshot untuk video, screenshot untuk web).

---

## 6. Renderer per Tipe (ABC di `renderer/renderer.py`)

```python
class Renderer(ABC):
    @abstractmethod
    def init(self, hwnd: int, rect: tuple): ...
    @abstractmethod
    def start(self): ...
    @abstractmethod
    def pause(self): ...
    @abstractmethod
    def resume(self): ...
    @abstractmethod
    def set_volume(self, v: float): ...
    @abstractmethod
    def resize(self, rect: tuple): ...
    @abstractmethod
    def stop(self): ...
    def handle_input(self, event): ...   # override untuk interactive
```

- **image**: `QWidget` + `QPixmap` scaled ke rect (atau quad OpenGL). Sangat ringan.
- **video**: `vlc.Instance()` + `media_player_new()`; `player.set_hwnd(hwnd)`;
  `player.set_media(path)`; `player.play()`. Audio lewat VLC.
- **web**: `webview.create_window(..., gui='edgechromium')`; ambil
  `window._native_window` (HWND) → `desktop.attach_to_desktop(hwnd)`.
  Input mouse/key di-handle WebView2 sendiri.
- **interactive**: `QOpenGLWidget` di QWidget → reparent; loop render pakai
  `QTimer`/`QElapsedTimer`. Mouse dari event Qt. Audio-reactive: capture
  system audio via **WASAPI loopback** (`soundcard` lib) → FFT → uniform shader.

Semua renderer adalah QWidget yang `winId()`-nya di-reparent ke `WorkerW`.

---

## 7. Multi-Monitor

`monitors.get_monitors()` (`EnumDisplayMonitors`) → tiap monitor dapat 1 instance
`Renderer` → `attach_to_desktop` di rect monitor tsb.

- **Per-monitor**: tiap `monitor_id` di `monitor_profiles` menunjuk wallpaper beda.
- **Synchronize**: satu source di-clone ke N renderer (video: N VLC player sama;
  web: N webview sama; interactive: share state).
- **Hotplug**: poll `EnumDisplayMonitors` tiap ~2s / tangkap `WM_DISPLAYCHANGE`;
  kalau jumlah/rect monitor berubah → re-layout semua renderer.

---

## 8. Performance Manager

- **FPS limit** (`fps.py`): throttle loop interactive; video biarkan native,
  tapi bisa `player.set_rate()` kalau perlu. Opsi: 30/60/120/unlimited.
- **Fullscreen/game detect** (`fullscreen.py`):
  `GetForegroundWindow` → `GetWindowRect` vs `MonitorFromWindow` rect;
  + `DwmGetWindowAttribute(DWMWA_CLOAKED)`; + cek style `WS_POPUP`/`WS_MAXIMIZE`.
  Jika rect == monitor rect dan bukan desktop/window kita → fullscreen/game.
- **Battery** (`power.py`): `GetSystemPowerStatus` (ACLineStatus, BatteryLifePercent)
  + `WM_POWERBROADCAST`.
- **GPU %** (`gpu.py`): PDH counter `\GPU Engine(*)\Utilization Percentage`
  filter by PID kita (fallback: `psutil` CPU/RAM).
- **Aksi** (`pause_manager.py`): `keep` | `pause` | `pause + mute`.
  Pause = `renderer.pause()`; Mute = `audio.set_volume(0)`.

UI setting (§9 Performance page):
```
When fullscreen:  ( ) keep   (•) pause   ( ) pause + mute
```

---

## 9. UI Utama (PySide6)

`MainWindow` = `QHBoxLayout(Sidebar | QStackedWidget)`. Pages:
Home, Library, Favorites, Collections, Editor (M7), Displays, Performance, Settings.

- **Sidebar**: tombol nav + ikon (pakai `qtawesome` opsional).
- **WallpaperGrid**: `QGridLayout` dari `QPushButton` ber-thumbnail (Pillow resize).
- **Preview** (klik): dialog dengan live preview + `[Apply]` `[Favorite ☆]`.
- **Settings**: FPS, fullscreen behavior, startup, audio default.
- **Displays**: peta monitor, drag-assign wallpaper per monitor, checkbox sync.
- **Tray**: `QSystemTrayIcon` → Show / Pause / Resume / Next / Prev / Performance / Exit.

---

## 10. System Tray, Startup, Auto-Updater

- **Tray**: app minimal ke tray saat di-close (bukan quit). Menu di §9.
- **Startup** (`startup.py`): tulis `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
  → `"Wallforge"="C:\...\Wallforge.exe --minimized"`. Mode: normal | minimized | hidden.
- **Updater** (`services/update.py`):
  1. GET `https://.../version.json` `{ "version": "1.2.3", "url": "...", "sha256": "..." }`.
  2. Kalau `version > current` → download zip → verifikasi SHA256.
  3. Spawn `updater.exe` (atau `Wallforge.exe --update`), quit.
  4. Updater tunggu main exit, ganti file, restart. (Butuh process terpisah
     karena exe yang jalan nggak bisa overwrite dirinya sendiri.)

---

## 11. Build & Packaging

- **PyInstaller** (`build.spec`, `--onedir`, `--windowed`):
  - `datas`: `assets/`, `wallpapers/` (contoh), `build.spec` untuk VLC/WebView2.
  - `hiddenimports`: `PySide6.*`, `vlc`, `pywebview`, `soundcard`, `psutil`.
  - Bundle **VLC portable** & **WebView2 fixed runtime** ke folder output.
- **Inno Setup** (`installer/Wallforge.iss`):
  - copy `dist/Wallforge/*`, VLC, WebView2 runtime.
  - Start Menu shortcut, uninstall, optional "run at startup".
  - `AppId` tetap untuk upgrade-in-place.

---

## 12. Milestone (acceptance criteria)

- **M1 Foundation** — *done when*: app boot, tray jalan, config+log+db init,
  window minimal bisa buka/tutup ke tray. (Scaffold sudah ada.)
- **M2 Wallpaper Engine** — *done when*: image & video tampil DI BELAKANG icon
  di 1+ monitor, restore-on-exit work, multi-monitor assign work.
- **M3 Performance** — *done when*: fullscreen/game → auto pause; battery →
  pause; FPS limit effect; GPU% terbaca di UI.
- **M4 Library** — *done when*: indexing folder, collections, favorites,
  search/filter, playlist play.
- **M5 Web** — *done when*: wallpaper HTML/CSS/JS jalan di desktop via WebView2.
- **M6 Interactive** — *done when*: mouse particle + clock + audio-reactive
  (WASAPI loopback) jalan.
- **M7 Editor** — *done when*: canvas + layers + timeline + assets + export ke
  manifest wallpaper.
- **M8 Production** — *done when*: `Wallforge-Setup.exe` ter-install bersih,
  auto-update work, crash recovery (desktop nggak item), log+backup+migrasi setting.

---

## 13. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| Desktop item/hitam pas crash | restore `SPI_SETDESKWALLPAPER` di excepthook + atexit |
| Explorer restart orphan | poll `IsWindow(worker_hwnd)`, re-attach |
| Posisi meleset di monitor scaled | Per-Monitor V2 DPI + set di manifest |
| VLC/WebView2 nggak kebundle | masukin ke datas Inno + PyInstaller |
| WebView2 reparent flaky | fallback native C++ host (M5) |
| GPU% nggak akurat | PDH per-PID, fallback psutil |
| Audio-reactive latency | WASAPI loopback + ring buffer kecil |
| Updater nimpa exe jalan | process updater terpisah |

---

## 14. Konvensi Koding (untuk agent)

- Type hints di semua signature.
- Satu module = satu tanggung jawab.
- Jangan block UI thread: render loop di thread/Qt timer terpisah.
- Semua HWND terpusat di `windows/desktop.py` + `monitors.py`.
- Path selalu lewat `core/config.py` (`DATA_DIR`), jangan hardcode.
- Log ke file rotating; jangan `print` untuk production.
- Test: `pytest` di `tests/`, minimal smoke test per renderer + db migration.

---

## 15. Next Step

Scaffold M1 sudah dibuat (`config.py`, `logger.py`, `application.py`,
`windows/desktop.py`, `windows/monitors.py`, `requirements.txt`, `build.spec`).
Lanjut ke **M1 selesai** (tray + window + db init) lalu **M2** (image/video ke
desktop). Bilang aja "lanjut" ke aku.
