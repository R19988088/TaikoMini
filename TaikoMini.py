"""
TaikoMini - Simplified Taiko Game
Main entry point
"""

import pygame
import sys
import gc
from pathlib import Path

# 禁用自动垃圾回收，改为手动控制
gc.disable()
print("[GC] Automatic garbage collection disabled")

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

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
import os
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

def select_songs_directory():
    """
    For Android: Allow user to select songs directory at startup
    For PC: Use default 'songs' folder
    """
    # Check if we're on Android
    if 'ANDROID_BOOTSTRAP' in os.environ or 'ANDROID_ARGUMENT' in os.environ:
        # For Android, we would implement directory selection here
        # This is a simplified version - in reality, we would use Android-specific APIs
        print("Android detected. Please ensure songs are placed in the appropriate directory.")
        return Path("songs")
    else:
        # Standard PC behavior
        return Path("songs")

def main():
    # 内存监控已禁用以提升性能
    # memory_monitor = get_monitor()
    # memory_monitor.start()
    # memory_monitor.full_report("Program Start")
    
    # 初始化游戏设置
    game_settings = GameSettings()
    
    # Find songs folder
    tja_folder = select_songs_directory()
    if not tja_folder.exists():
        print("Error: 'songs' folder not found!")
        print("Please create a 'songs' folder and add .tja files with .ogg audio")
        return
    
    # Find all tja files (including subfolders)
    tja_files = list(tja_folder.glob("**/*.tja"))
    
    if not tja_files:
        print(f"Error: No .tja files found in {tja_folder}!")
        print(f"Search path: {tja_folder.absolute()}")
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