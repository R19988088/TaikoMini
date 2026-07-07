# TaikoMini

Python/Pygame Taiko rhythm game prototype.

## Build APK

Release builds run on GitHub Actions:

1. Open the repository Actions tab.
2. Run **Build Releases**.
3. Download the needed artifact:
   - `TaikoMini-android-debug.apk`
   - `TaikoMini-windows.exe`
   - `TaikoMini-macos.dmg`

The repository intentionally does not include the local song library. Put songs on the device under one of these folders:

- `/sdcard/taikomini/songs`
- `/sdcard/Download/taikomini/songs`
- another folder selected from the in-app data directory screen

Expected structure:

```text
taikomini/
  Resource/
  songs/
    category/
      song.tja
      song.ogg
```

## Desktop Test

```bat
run.bat
```
