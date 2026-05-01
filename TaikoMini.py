"""
TaikoMini - Simplified Taiko Game
Main entry point
"""

import pygame
import sys
import gc
from pathlib import Path
import os

# 禁用自动垃圾回收，改为手动控制
gc.disable()
print("[GC] Automatic garbage collection disabled")

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.paths import (
    asset_path,
    resource_dir,
    set_taikomini_root,
    songs_dir,
    taikomini_root,
    taikomini_root_candidates,
)
from lib.tja import TJAParser
from lib.game import TaikoGame
from lib.song_select import SongSelectScreen
from lib.game_settings import GameSettings
# from lib.memory_monitor import get_monitor  # 已禁用 - 影响性能

# Initialize Pygame
pygame.init()
# Initialize mixer with low latency settings
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Enable high DPI support
import ctypes
import locale

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Set environment variables BEFORE pygame.init()
os.environ['SDL_IME_SHOW_UI'] = '0'  # Disable IME UI
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
os.environ['LANG'] = 'C'  # Force C locale
os.environ['LC_ALL'] = 'C'
# 启用垂直同步以消除屏幕撕裂和抖动
os.environ['SDL_RENDER_VSYNC'] = '1'

# Disable IME completely on Windows
try:
    import ctypes
    # Disable IME
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if hwnd:
        ctypes.windll.imm32.ImmAssociateContextEx(hwnd, 0, 0)
except:
    pass

# Window settings (resizable, 9:16 ratio)
BASE_WIDTH = 720   # Base width
BASE_HEIGHT = 1280 # Base height (9:16 ratio)

# Create resizable window with hardware acceleration and vsync
# SCALED: 自动缩放支持
# DOUBLEBUF: 双缓冲
# HWSURFACE: 硬件加速
screen = pygame.display.set_mode(
    (BASE_WIDTH, BASE_HEIGHT), 
    pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF | pygame.HWSURFACE
)
pygame.display.set_caption("TaikoMini - Simplified Taiko")


def _load_startup_font(size):
    font_path = asset_path("lib", "res", "FZPangWaUltra-Regular.ttf")
    if font_path.exists():
        return pygame.font.Font(str(font_path), size)
    return pygame.font.SysFont(None, size)


def _scan_tja_files():
    tja_folder = songs_dir()
    if not tja_folder.exists():
        return tja_folder, []
    return tja_folder, list(tja_folder.glob("**/*.tja"))


def choose_data_root_screen(message):
    title_font = _load_startup_font(42)
    font = _load_startup_font(26)
    small_font = _load_startup_font(20)
    clock = pygame.time.Clock()
    candidates = taikomini_root_candidates()

    while True:
        screen.fill((24, 28, 36))
        screen.blit(title_font.render("选择 TaikoMini 数据目录", True, (255, 255, 255)), (40, 50))
        screen.blit(font.render(message, True, (255, 210, 120)), (40, 110))
        screen.blit(small_font.render("目录结构：taikomini/config.ini、taikomini/songs、taikomini/Resource", True, (210, 210, 210)), (40, 150))

        buttons = []
        y = 205
        for root_path in candidates:
            song_path = root_path / "songs"
            tja_count = len(list(song_path.glob("**/*.tja"))) if song_path.exists() else 0
            exists_text = f"{tja_count} 首" if tja_count else "未找到歌曲"
            color = (62, 142, 88) if tja_count else (82, 92, 110)
            rect = pygame.Rect(40, y, BASE_WIDTH - 80, 70)
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, (230, 230, 230), rect, 2, border_radius=12)
            screen.blit(font.render(str(root_path), True, (255, 255, 255)), (rect.x + 18, rect.y + 12))
            screen.blit(small_font.render(f"songs: {song_path}  ({exists_text})", True, (235, 235, 235)), (rect.x + 18, rect.y + 42))
            buttons.append((rect, root_path))
            y += 84

        rescan_rect = pygame.Rect(40, BASE_HEIGHT - 150, 230, 64)
        quit_rect = pygame.Rect(BASE_WIDTH - 270, BASE_HEIGHT - 150, 230, 64)
        pygame.draw.rect(screen, (50, 110, 170), rescan_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 60, 60), quit_rect, border_radius=12)
        screen.blit(font.render("重新扫描", True, (255, 255, 255)), (rescan_rect.x + 55, rescan_rect.y + 17))
        screen.blit(font.render("退出", True, (255, 255, 255)), (quit_rect.x + 85, quit_rect.y + 17))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_r:
                    candidates = taikomini_root_candidates()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if rescan_rect.collidepoint(pos):
                    candidates = taikomini_root_candidates()
                    continue
                if quit_rect.collidepoint(pos):
                    return None
                for rect, root_path in buttons:
                    if rect.collidepoint(pos):
                        set_taikomini_root(root_path)
                        return root_path

        clock.tick(30)


def main():
    # 内存监控已禁用以提升性能
    # memory_monitor = get_monitor()
    # memory_monitor.start()
    # memory_monitor.full_report("Program Start")
    
    # 初始化游戏设置
    game_settings = GameSettings()
    
    while True:
        tja_folder, tja_files = _scan_tja_files()
        if tja_files:
            break
        print(f"Error: No .tja files found in {tja_folder}!")
        print(f"Expected structure: {taikomini_root()}/songs/**/*.tja")
        print(f"Resource path: {resource_dir()}")
        selected_root = choose_data_root_screen("没有读取到歌曲，请选择数据目录")
        if selected_root is None:
            return
    
    # Display song list
    print("\n=== Found Songs ===")
    songs = [(tja_file.stem, tja_file) for tja_file in tja_files]
    for i, (title, _) in enumerate(songs, 1):
        try:
            print(f"{i}. {title}")
        except UnicodeEncodeError:
            # Replace problematic characters
            safe_title = title.encode('ascii', errors='replace').decode('ascii')
            print(f"{i}. {safe_title}")
    
    # Main game loop (song selection -> game -> back to selection)
    while True:
        # Show song selection screen
        print("\nOpening Song Selection...")
        selector = SongSelectScreen(screen, songs)
        result = selector.run()
        
        # Check if user quit
        if result is None:
            break
        
        # --- Game loop for a single song (handles restarts) ---
        game_should_run = True
        while game_should_run:
            # Unpack result - now includes category
            if isinstance(result, tuple) and len(result) == 3:
                selected_tja, selected_diff, song_category = result
            else:
                selected_tja, selected_diff = result
                song_category = ""
            try:
                print(f"\nSelected: {selected_tja.stem} [{selected_diff}]")
            except UnicodeEncodeError:
                # Handle problematic characters in song titles
                safe_title = selected_tja.stem.encode('ascii', errors='replace').decode('ascii')
                print(f"\nSelected: {safe_title} [{selected_diff}]")
            
            # Parse TJA with selected difficulty
            # Map difficulty names to numbers
            diff_map = {'Easy': 0, 'Normal': 1, 'Hard': 2, 'Oni': 3, 'Edit': 4}
            diff_num = diff_map.get(selected_diff, 3)  # Default to Oni
            
            # 从设置中获取缩放后的音符距离
            note_distance = game_settings.get_scaled_note_distance()
            parser = TJAParser(selected_tja, start_delay=0, distance=note_distance)
            master_notes, branch_m, branch_e, branch_n = parser.notes_to_position(diff_num)
            
            # Extract metadata
            # 优先使用中文标题，如果没有再使用英文标题
            title = parser.metadata.title.get('cn', '')  # 先尝试中文
            if not title:
                title = parser.metadata.title.get('en', selected_tja.stem)  # 再尝试英文
            bpm = parser.metadata.bpm
            offset = parser.metadata.offset
            
            # Display key info
            print(f"\n=== Chart Info ===")
            try:
                print(f"Title: {title}")
            except UnicodeEncodeError:
                safe_title = title.encode('ascii', errors='replace').decode('ascii')
                print(f"Title: {safe_title}")
            print(f"BPM: {bpm}")
            offset_ms = offset * 1000
            offset_type = "Delayed (Chart lags)" if offset < 0 else "Advanced (Chart leads)" if offset > 0 else "Synced"
            print(f"OFFSET: {offset:.3f}s ({offset_ms:+.0f}ms) - {offset_type}")
            print(f"Notes: {len(master_notes.play_notes)}")
            
            # Create chart data compatible with game
            chart_data = {
                'title': title,
                'bpm': bpm,
                'offset': offset,
                'notes': master_notes,  # Pass NoteList object for branching
                'branch_m': branch_m,
                'branch_e': branch_e,
                'branch_n': branch_n,
                'audio': str(parser.metadata.wave),
                'difficulty': selected_diff,
            }
            
            # Find audio file from TJA's WAVE field or fallback to filename
            audio_file = None
            if chart_data.get('audio') and chart_data['audio'] != 'None':
                # Use WAVE field from TJA (it should be relative to TJA file)
                wave_filename = Path(chart_data['audio']).name  # Just get filename
                wave_path = selected_tja.parent / wave_filename
                if wave_path.exists():
                    audio_file = wave_path
                else:
                    print(f"Warning: WAVE file not found: {wave_path}")
            
            # Fallback: try matching TJA filename
            if not audio_file:
                for ext in ['.ogg', '.wav', '.mp3']:
                    test_path = selected_tja.with_suffix(ext)
                    if test_path.exists():
                        audio_file = test_path
                        break
            
            if not audio_file:
                print(f"Error: Audio file not found")
                if chart_data.get('audio'):
                    print(f"  WAVE field: {chart_data['audio']}")
                print(f"  Tried: {selected_tja.with_suffix('.ogg')}")
                print(f"        {selected_tja.with_suffix('.wav')}")
                print(f"        {selected_tja.with_suffix('.mp3')}")
                continue
            
            # Create and run game (传入TJA路径用于保存成绩)
            game = TaikoGame(screen, chart_data, audio_file, song_category, selected_tja)
            
            # Pass practice mode data if available
            if hasattr(selector, 'practice_audio_paths') and selector.practice_audio_paths:
                game.practice_audio_paths = selector.practice_audio_paths
                game.is_practice_mode = True
            
            game_result = game.run()

            # If game returns 'restart', loop continues. Otherwise, break to song select.
            if game_result != 'restart':
                game_should_run = False
        # --- End of single song loop ---
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
