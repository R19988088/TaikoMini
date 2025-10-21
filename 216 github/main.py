#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaikoMini - Android 太鼓达人小游戏
支持 Android 13-16
"""

import os
import sys
import pygame
import json
from pathlib import Path

# Android 适配
def get_android_storage_path():
    """获取 Android 存储路径"""
    if hasattr(sys, 'getandroidapp'):
        # Android 环境
        android_app = sys.getandroidapp()
        return android_app.getExternalFilesDir(None)
    else:
        # 开发环境
        return Path.home() / "TaikoMini"

def check_android_permissions():
    """检查 Android 权限"""
    if hasattr(sys, 'getandroidapp'):
        android_app = sys.getandroidapp()
        # 请求存储权限
        android_app.requestPermissions(['android.permission.READ_EXTERNAL_STORAGE',
                                      'android.permission.WRITE_EXTERNAL_STORAGE',
                                      'android.permission.READ_MEDIA_AUDIO'])

class TaikoMini:
    def __init__(self):
        pygame.init()
        
        # 设置屏幕尺寸 (Android 竖屏)
        self.screen_width = 720
        self.screen_height = 1280
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("TaikoMini")
        
        # 设置时钟
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 游戏状态
        self.running = True
        self.game_state = "menu"  # menu, playing, paused
        
        # 颜色定义
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'green': (0, 255, 0),
            'yellow': (255, 255, 0),
            'gray': (128, 128, 128)
        }
        
        # 字体
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # 存储路径
        self.storage_path = get_android_storage_path()
        self.songs_path = self.storage_path / "songs"
        
        # 创建目录
        self.songs_path.mkdir(parents=True, exist_ok=True)
        
        # 检查权限
        check_android_permissions()
        
        # 加载歌曲列表
        self.songs = self.load_songs()
        
    def load_songs(self):
        """加载歌曲列表"""
        songs = []
        if self.songs_path.exists():
            for song_dir in self.songs_path.iterdir():
                if song_dir.is_dir():
                    tja_file = song_dir / f"{song_dir.name}.tja"
                    ogg_file = song_dir / f"{song_dir.name}.ogg"
                    if tja_file.exists() and ogg_file.exists():
                        songs.append({
                            'name': song_dir.name,
                            'path': song_dir,
                            'tja': tja_file,
                            'ogg': ogg_file
                        })
        return songs
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.game_state = "paused"
                    elif self.game_state == "paused":
                        self.game_state = "playing"
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.game_state == "menu":
                        self.start_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "menu":
                    self.start_game()
    
    def start_game(self):
        """开始游戏"""
        if self.songs:
            self.game_state = "playing"
            # 这里可以添加选择歌曲的逻辑
        else:
            self.show_no_songs_message()
    
    def show_no_songs_message(self):
        """显示没有歌曲的消息"""
        # 简单的消息显示，实际应该用UI界面
        pass
    
    def draw_menu(self):
        """绘制主菜单"""
        self.screen.fill(self.colors['black'])
        
        # 标题
        title_text = self.font_large.render("TaikoMini", True, self.colors['white'])
        title_rect = title_text.get_rect(center=(self.screen_width//2, 200))
        self.screen.blit(title_text, title_rect)
        
        # 说明文字
        if self.songs:
            info_text = self.font_medium.render(f"找到 {len(self.songs)} 首歌曲", True, self.colors['green'])
            info_rect = info_text.get_rect(center=(self.screen_width//2, 400))
            self.screen.blit(info_text, info_rect)
            
            start_text = self.font_medium.render("点击屏幕开始游戏", True, self.colors['yellow'])
            start_rect = start_text.get_rect(center=(self.screen_width//2, 500))
            self.screen.blit(start_text, start_rect)
        else:
            no_songs_text = self.font_medium.render("没有找到歌曲文件", True, self.colors['red'])
            no_songs_rect = no_songs_text.get_rect(center=(self.screen_width//2, 400))
            self.screen.blit(no_songs_text, no_songs_rect)
            
            help_text = self.font_small.render("请将歌曲文件放入:", True, self.colors['gray'])
            help_rect = help_text.get_rect(center=(self.screen_width//2, 450))
            self.screen.blit(help_text, help_rect)
            
            path_text = self.font_small.render(str(self.songs_path), True, self.colors['gray'])
            path_rect = path_text.get_rect(center=(self.screen_width//2, 480))
            self.screen.blit(path_text, path_rect)
        
        # 退出提示
        exit_text = self.font_small.render("按 ESC 键退出", True, self.colors['gray'])
        exit_rect = exit_text.get_rect(center=(self.screen_width//2, self.screen_height - 100))
        self.screen.blit(exit_text, exit_rect)
    
    def draw_game(self):
        """绘制游戏界面"""
        self.screen.fill(self.colors['black'])
        
        # 简单的游戏界面
        if self.game_state == "playing":
            game_text = self.font_large.render("游戏进行中...", True, self.colors['white'])
            game_rect = game_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(game_text, game_rect)
            
            pause_text = self.font_small.render("按 ESC 暂停", True, self.colors['gray'])
            pause_rect = pause_text.get_rect(center=(self.screen_width//2, self.screen_height//2 + 50))
            self.screen.blit(pause_text, pause_rect)
            
        elif self.game_state == "paused":
            pause_text = self.font_large.render("游戏暂停", True, self.colors['yellow'])
            pause_rect = pause_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(pause_text, pause_rect)
            
            resume_text = self.font_small.render("按 ESC 继续", True, self.colors['gray'])
            resume_rect = resume_text.get_rect(center=(self.screen_width//2, self.screen_height//2 + 50))
            self.screen.blit(resume_text, resume_rect)
    
    def draw(self):
        """绘制界面"""
        if self.game_state == "menu":
            self.draw_menu()
        else:
            self.draw_game()
        
        pygame.display.flip()
    
    def run(self):
        """主游戏循环"""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(self.fps)
        
        pygame.quit()

def main():
    """主函数"""
    try:
        game = TaikoMini()
        game.run()
    except Exception as e:
        print(f"游戏启动失败: {e}")
        # 在 Android 上记录错误日志
        if hasattr(sys, 'getandroidapp'):
            android_app = sys.getandroidapp()
            android_app.log(f"TaikoMini Error: {e}")

if __name__ == "__main__":
    main()
