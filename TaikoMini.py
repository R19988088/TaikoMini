"""
TaikoMini - Simplified Taiko Game
Main entry point
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

# 早期日志函数 - 在任何导入失败时也能记录
def early_log(message, log_path="/sdcard/taikomini_early.log"):
    """早期日志，用于记录导入阶段的错误"""
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
        print(message)
    except:
        # 如果主路径失败，尝试备用路径
        try:
            fallback_path = "/sdcard/taikomini_early.log"
            with open(fallback_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
                f.flush()
        except:
            pass
        print(message)

early_log("=" * 70)
early_log("TaikoMini 启动开始")
early_log("=" * 70)
early_log(f"Python版本: {sys.version}")
early_log(f"Python路径: {sys.executable}")

try:
    early_log("[1/10] 导入基础模块...")
    import pygame
    import gc
    early_log("✓ 基础模块导入成功")
    
    # 禁用自动垃圾回收，改为手动控制
    gc.disable()
    early_log("[GC] Automatic garbage collection disabled")
    
    # Add lib to path
    sys.path.insert(0, str(Path(__file__).parent))
    early_log(f"库路径: {sys.path[0]}")
    
    early_log("[2/10] 导入Android适配器...")
    # Import Android adapter BEFORE pygame.init()
    from lib.android_adapter import get_adapter, is_android
    early_log("✓ Android适配器导入成功")
    
    # Initialize adapter
    early_log("[3/10] 初始化Android适配器...")
    adapter = get_adapter()
    early_log(f"✓ Android适配器初始化成功 (is_android={is_android()})")

except Exception as e:
    early_log(f"✗ 早期初始化失败: {e}")
    early_log(traceback.format_exc())
    sys.exit(1)

try:
    early_log("[4/10] 导入日志模块...")
    # Initialize logger with platform-specific settings
    from lib.logger import init_logger, get_logger, close_logger
    if is_android():
        base_path = adapter.get_base_path()
        logger = init_logger(is_android=True, base_path=base_path)
    else:
        logger = init_logger(is_android=False)
    early_log("✓ 日志系统初始化成功")
    
    logger.info("=" * 70)
    logger.info("TaikoMini 启动 / TaikoMini Starting")
    logger.info("=" * 70)
    logger.info(f"平台 / Platform: {'Android' if is_android() else 'Desktop'}")
    logger.info(f"Python版本 / Python Version: {sys.version}")
    logger.info(f"Pygame版本 / Pygame Version: {pygame.version.ver}")
    
    early_log("[5/10] 导入游戏模块...")
    from lib.tja import TJAParser
    from lib.game import TaikoGame
    from lib.song_select import SongSelectScreen
    from lib.game_settings import GameSettings
    early_log("✓ 游戏模块导入成功")
    
except Exception as e:
    early_log(f"✗ 模块导入失败: {e}")
    early_log(traceback.format_exc())
    sys.exit(1)

# Initialize Pygame
try:
    early_log("[6/10] 初始化Pygame...")
    logger.info("初始化Pygame / Initializing Pygame...")
    pygame.init()
    logger.info("✓ Pygame初始化成功")
    early_log("✓ Pygame初始化成功")
except Exception as e:
    early_log(f"✗ Pygame初始化失败: {e}")
    logger.exception(f"✗ Pygame初始化失败: {e}")
    early_log(traceback.format_exc())
    sys.exit(1)

# Initialize mixer with platform-specific buffer size
try:
    early_log("[7/10] 初始化音频系统...")
    buffer_size = adapter.get_audio_buffer_size()
    logger.info(f"初始化音频系统 / Initializing audio with buffer size: {buffer_size}")
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=buffer_size)
    logger.info(f"✓ 音频系统初始化成功")
    early_log("✓ 音频系统初始化成功")
except Exception as e:
    early_log(f"✗ 音频系统初始化失败: {e}")
    logger.exception(f"✗ 音频系统初始化失败: {e}")
    early_log(traceback.format_exc())
    sys.exit(1)

# Enable high DPI support (Windows only)
if not is_android():
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

# Set environment variables
import os
if not is_android():
    os.environ['SDL_IME_SHOW_UI'] = '0'  # Disable IME UI
    os.environ['LANG'] = 'C'  # Force C locale
    os.environ['LC_ALL'] = 'C'

os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
os.environ['SDL_RENDER_VSYNC'] = '1'  # 启用垂直同步

# Disable IME completely on Windows
if not is_android():
    try:
        import ctypes
        # Disable IME
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd:
            ctypes.windll.imm32.ImmAssociateContextEx(hwnd, 0, 0)
    except:
        pass

# Window settings (platform-specific)
BASE_WIDTH = 720   # Base width
BASE_HEIGHT = 1280 # Base height (9:16 ratio)

# Create window with platform-specific settings
try:
    early_log("[8/10] 创建窗口...")
    logger.info(f"创建窗口 / Creating window ({BASE_WIDTH}x{BASE_HEIGHT})...")
    screen_size, screen_flags = adapter.get_screen_mode(BASE_WIDTH, BASE_HEIGHT)
    logger.info(f"屏幕模式 / Screen mode: {screen_size}, flags: {screen_flags}")
    screen = pygame.display.set_mode(screen_size, screen_flags)
    pygame.display.set_caption("TaikoMini - Simplified Taiko")
    logger.info(f"✓ 窗口创建成功 / Window created: {screen.get_size()}")
    early_log(f"✓ 窗口创建成功: {screen.get_size()}")
except Exception as e:
    early_log(f"✗ 窗口创建失败: {e}")
    logger.exception(f"✗ 窗口创建失败: {e}")
    early_log(traceback.format_exc())
    sys.exit(1)

# Apply Android-specific settings (screen always on, immersive mode, etc.)
if is_android():
    try:
        early_log("[9/10] 应用Android设置...")
        logger.info("应用Android特定设置 / Applying Android settings...")
        adapter.apply_platform_settings()
        logger.info("✓ Android设置应用成功")
        early_log("✓ Android设置应用成功")
    except Exception as e:
        early_log(f"✗ Android设置失败: {e}")
        logger.exception(f"✗ Android设置应用失败: {e}")
        early_log(traceback.format_exc())

def main():
    try:
        # 初始化游戏设置
        logger.info("初始化游戏设置 / Initializing game settings...")
        game_settings = GameSettings()
        logger.info("✓ 游戏设置初始化成功")
    except Exception as e:
        logger.exception(f"✗ 游戏设置初始化失败: {e}")
        return
    
    # Find songs folder (platform-specific)
    # Note: On Android, the directory structure is auto-created in android_adapter._init_android()
    try:
        tja_folder = adapter.get_songs_folder()
        logger.info(f"歌曲文件夹路径 / Songs folder: {tja_folder}")
    except Exception as e:
        logger.exception(f"✗ 获取歌曲文件夹失败: {e}")
        return
    
    # 验证歌曲文件夹存在（理论上Android平台已经在adapter初始化时创建）
    if not tja_folder.exists():
        logger.error(f"歌曲文件夹不存在 / Songs folder not found: {tja_folder}")
        
        # Android: 显示详细的路径说明
        if is_android():
            print("=" * 60)
            print("首次启动说明 / First Launch Instructions:")
            print("=" * 60)
            print(f"请将歌曲文件放到以下目录：")
            print(f"Please place song files in:")
            print(f"  {tja_folder}")
            print(f"")
            print(f"需要的文件格式：")
            print(f"Required file formats:")
            print(f"  - .tja files (譜面文件)")
            print(f"  - .ogg/.wav/.mp3 files (音乐文件)")
            print(f"")
            print(f"目录结构示例：")
            print(f"Example directory structure:")
            print(f"  /sdcard/taikomini/")
            print(f"    ├── config.ini (配置文件)")
            print(f"    ├── Resource/ (分类背景图片)")
            print(f"    └── songs/")
            print(f"        ├── 1 流行音乐/")
            print(f"        │   ├── song1.tja")
            print(f"        │   └── song1.ogg")
            print(f"        └── 2 VOCALOID音乐/")
            print(f"            ├── song2.tja")
            print(f"            └── song2.ogg")
            print("=" * 60)
        else:
            print("Please create the folder and add .tja files with .ogg audio")
        
        return
    
    # Find all tja files (including subfolders)
    try:
        logger.info(f"搜索.tja文件 / Searching for .tja files in {tja_folder}...")
        tja_files = list(tja_folder.glob("**/*.tja"))
        logger.info(f"找到 {len(tja_files)} 个.tja文件 / Found {len(tja_files)} .tja files")
    except Exception as e:
        logger.exception(f"✗ 搜索.tja文件失败: {e}")
        return
    
    if not tja_files:
        logger.error(f"未找到.tja文件 / No .tja files found in {tja_folder}!")
        logger.error(f"搜索路径 / Search path: {tja_folder.absolute()}")
        
        # Android: 显示更详细的说明
        if is_android():
            print("")
            print("=" * 60)
            print("未找到歌曲文件 / No Songs Found")
            print("=" * 60)
            print(f"歌曲目录已创建，但里面没有歌曲文件。")
            print(f"Song directory exists but contains no song files.")
            print(f"")
            print(f"请将歌曲文件（.tja 和对应的 .ogg）放入：")
            print(f"Please add song files (.tja and .ogg) to:")
            print(f"  {tja_folder}")
            print(f"")
            print(f"然后重新启动应用。")
            print(f"Then restart the app.")
            print("=" * 60)
        
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
            
            # Create and run game
            game = TaikoGame(screen, chart_data, audio_file, song_category)
            
            # Pass practice mode data if available
            if hasattr(selector, 'practice_audio_paths') and selector.practice_audio_paths:
                game.practice_audio_paths = selector.practice_audio_paths
                game.is_practice_mode = True
            
            game_result = game.run()

            # If game returns 'restart', loop continues. Otherwise, break to song select.
            if game_result != 'restart':
                game_should_run = False
        # --- End of single song loop ---
    
    logger.info("游戏正常退出 / Game exiting normally")
    pygame.quit()
    close_logger()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"程序异常退出 / Program crashed: {e}")
        close_logger()
        raise

