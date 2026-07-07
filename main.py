"""Android/Buildozer entry point."""

from pathlib import Path
import os
import sys
import traceback


def _crash_log_candidates():
    names = ["TaikoMini-crash.txt", "taikomini_crash.txt"]
    roots = []
    for env_name in ("ANDROID_ARGUMENT", "ANDROID_PRIVATE"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value))
    roots.extend(
        [
            Path("/sdcard"),
            Path("/sdcard/Download"),
            Path("/sdcard/Documents"),
            Path("/sdcard/taikomini"),
            Path("/storage/emulated/0"),
            Path("/storage/emulated/0/Download"),
            Path("/storage/emulated/0/Documents"),
            Path("/storage/emulated/0/taikomini"),
            Path.cwd(),
        ]
    )
    return [root / name for root in roots for name in names]


def _write_crash_log(text):
    for path in _crash_log_candidates():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except Exception:
            continue


def _show_crash_screen(text):
    try:
        import pygame

        pygame.init()
        screen = pygame.display.set_mode((720, 1280), pygame.FULLSCREEN | pygame.SCALED)
        font = pygame.font.SysFont(None, 28)
        lines = [
            "TaikoMini startup failed.",
            "Crash log: TaikoMini-crash.txt",
            "",
            *text.splitlines()[-18:],
        ]
        clock = pygame.time.Clock()
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 20000:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return
            screen.fill((24, 24, 28))
            y = 36
            for line in lines:
                try:
                    rendered = font.render(line[:96], True, (240, 240, 240))
                    screen.blit(rendered, (24, y))
                except Exception:
                    pass
                y += 34
            pygame.display.flip()
            clock.tick(30)
    except Exception:
        pass


def main():
    try:
        from TaikoMini import main as run_game

        run_game()
    except BaseException:
        text = traceback.format_exc()
        print(text)
        _write_crash_log(text)
        _show_crash_screen(text)
        raise


if __name__ == "__main__":
    main()
