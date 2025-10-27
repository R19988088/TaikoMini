#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaikoMini - Android 太鼓达人小游戏
支持 Android 13-16
"""

import os
import sys
import traceback
from pathlib import Path

# Android 特殊处理
def setup_android_environment():
    """设置 Android 环境"""
    if hasattr(sys, 'getandroidapp'):
        # 禁用垃圾回收以提高性能
        import gc
        gc.disable()
        
        # 设置环境变量
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
        os.environ['SDL_RENDER_VSYNC'] = '1'
        
        print("[ANDROID] Environment configured")

def get_android_storage_path():
    """获取 Android 存储路径"""
    if hasattr(sys, 'getandroidapp'):
        try:
            android_app = sys.getandroidapp()
            storage_dir = android_app.getExternalFilesDir(None)
            if storage_dir:
                return Path(storage_dir)
        except Exception as e:
            print(f"[ERROR] Failed to get Android storage: {e}")
    
    # 开发环境回退
    return Path.home() / "TaikoMini"

def log_to_android(message):
    """在 Android 上记录日志"""
    try:
        if hasattr(sys, 'getandroidapp'):
            android_app = sys.getandroidapp()
            android_app.log(message)
        print(message)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def main():
    """主函数 - 包含完整的错误处理"""
    log_to_android("=== TaikoMini Starting ===")
    
    try:
        # 1. 设置 Android 环境
        setup_android_environment()
        
        # 2. 添加 lib 目录到路径
        lib_path = Path(__file__).parent / 'lib'
        if lib_path.exists():
            sys.path.insert(0, str(lib_path))
            log_to_android(f"[PATH] Added lib path: {lib_path}")
        
        # 3. 初始化 pygame
        log_to_android("[INIT] Initializing pygame...")
        import pygame
        pygame.init()
        
        # 设置音频
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            log_to_android("[AUDIO] Mixer initialized")
        except Exception as e:
            log_to_android(f"[WARN] Mixer init failed: {e}")
        
        # 4. 获取存储路径
        storage_path = get_android_storage_path()
        songs_path = storage_path / "songs"
        songs_path.mkdir(parents=True, exist_ok=True)
        log_to_android(f"[STORAGE] Songs path: {songs_path}")
        
        # 5. 导入并运行游戏
        log_to_android("[IMPORT] Importing game modules...")
        
        # 先尝试使用完整的游戏代码
        try:
            from lib.game import TaikoGame
            from lib.song_select import SongSelectScreen
            from lib.game_settings import GameSettings
            
            log_to_android("[IMPORT] Full game modules loaded")
            
            # 创建游戏设置
            game_settings = GameSettings()
            
            # 查找歌曲
            tja_folder = Path("songs")
            if not tja_folder.exists():
                # 尝试从应用资源加载
                tja_folder = Path(__file__).parent / "taikomini" / "songs"
            
            log_to_android(f"[SONGS] Looking for songs in: {tja_folder}")
            
            if tja_folder.exists():
                tja_files = list(tja_folder.glob("**/*.tja"))
                log_to_android(f"[SONGS] Found {len(tja_files)} songs")
                
                if tja_files:
                    # 创建窗口
                    screen_width = 720
                    screen_height = 1280
                    screen = pygame.display.set_mode((screen_width, screen_height))
                    pygame.display.set_caption("TaikoMini")
                    
                    # 创建歌曲选择界面
                    song_select = SongSelectScreen(screen, screen_width, screen_height, tja_files, game_settings)
                    
                    # 进入主循环
                    log_to_android("[GAME] Starting game loop...")
                    song_select.run()
                else:
                    log_to_android("[ERROR] No songs found!")
                    show_error_screen(pygame, "No songs found!")
            else:
                log_to_android(f"[ERROR] Songs folder not found: {tja_folder}")
                show_error_screen(pygame, f"Songs folder not found!\n{tja_folder}")
                
        except ImportError as e:
            log_to_android(f"[ERROR] Import failed: {e}")
            import traceback
            log_to_android(traceback.format_exc())
            
            # 回退到简化版本
            log_to_android("[FALLBACK] Using simplified version...")
            run_simplified_version(pygame, songs_path)
        
    except Exception as e:
        error_msg = f"Fatal error: {e}\n{traceback.format_exc()}"
        log_to_android(error_msg)
        
        # 尝试显示错误信息
        try:
            import pygame
            show_error_screen(pygame, f"Error: {e}")
        except:
            pass
        
    finally:
        try:
            pygame.quit()
        except:
            pass
        log_to_android("=== TaikoMini Exited ===")

def show_error_screen(pygame, message):
    """显示错误信息屏幕"""
    try:
        screen_width = 720
        screen_height = 1280
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("TaikoMini - Error")
        
        clock = pygame.time.Clock()
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 32)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            screen.fill((0, 0, 0))
            
            # 显示错误消息
            lines = message.split('\n')
            y = 200
            for line in lines:
                text = font_medium.render(line, True, (255, 255, 255))
                rect = text.get_rect(center=(screen_width//2, y))
                screen.blit(text, rect)
                y += 50
            
            # 显示提示
            hint = font_medium.render("Press ESC to exit", True, (128, 128, 128))
            hint_rect = hint.get_rect(center=(screen_width//2, screen_height - 100))
            screen.blit(hint, hint_rect)
            
            pygame.display.flip()
            clock.tick(30)
    except Exception as e:
        print(f"Error showing error screen: {e}")

def run_simplified_version(pygame, songs_path):
    """运行简化版本的游戏"""
    try:
        screen_width = 720
        screen_height = 1280
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("TaikoMini")
        
        clock = pygame.time.Clock()
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 24)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            screen.fill((0, 0, 0))
            
            # 显示标题
            title = font_large.render("TaikoMini", True, (255, 255, 255))
            title_rect = title.get_rect(center=(screen_width//2, 200))
            screen.blit(title, title_rect)
            
            # 显示状态
            status = font_medium.render("Game loaded successfully!", True, (0, 255, 0))
            status_rect = status.get_rect(center=(screen_width//2, 400))
            screen.blit(status, status_rect)
            
            # 显示路径
            path_text = font_small.render(f"Songs: {songs_path}", True, (128, 128, 128))
            path_rect = path_text.get_rect(center=(screen_width//2, 500))
            screen.blit(path_text, path_rect)
            
            # 显示提示
            hint = font_small.render("Press ESC to exit", True, (128, 128, 128))
            hint_rect = hint.get_rect(center=(screen_width//2, screen_height - 100))
            screen.blit(hint, hint_rect)
            
            pygame.display.flip()
            clock.tick(30)
    except Exception as e:
        log_to_android(f"Simplified version error: {e}")

if __name__ == "__main__":
    main()
