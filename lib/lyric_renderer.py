"""
歌词渲染模块
Lyric Renderer Module

负责在游戏界面显示 LRC 歌词
"""

import pygame
from typing import Optional
from pathlib import Path


class LyricRenderer:
    """
    歌词渲染器
    Lyric Renderer
    
    在游戏界面底部显示同步歌词
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        初始化歌词渲染器
        Initialize lyric renderer
        
        Args:
            screen: Pygame 屏幕对象
        """
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # 歌词显示位置（屏幕中心偏下100px）
        self.lyric_y = self.screen_height // 2 + 50
        
        # 字体设置 - 使用支持中日文和特殊符号的字体（粗体）
        self.font_size = 42
        # 优先使用微软雅黑，支持™等特殊符号和中日文
        lyric_fonts = ['Microsoft YaHei', 'Arial Unicode MS', 'SimHei', 'MS Gothic']
        self.font = None
        for font_name in lyric_fonts:
            try:
                if pygame.font.match_font(font_name):
                    self.font = pygame.font.SysFont(font_name, self.font_size, bold=True)
                    break
            except:
                continue
        
        # 如果都没找到，使用默认字体
        if self.font is None:
            self.font = pygame.font.Font(None, self.font_size)
        
        # 颜色设置
        self.text_color = (255, 255, 255)  # 白色文字
        self.outline_color = (76, 95, 132)  # #4c5f84 描边色
        self.outline_width = 3  # 描边宽度
        
        # 动画状态
        self.current_lyric = ""  # 当前显示的歌词
        self.old_lyric_surface = None  # 旧歌词的渲染表面
        self.new_lyric_surface = None  # 新歌词的渲染表面
        self.animation_start_time = 0  # 动画开始时间（毫秒）
        self.animation_duration = 120  # 动画持续时间（毫秒）- 快速版本
        self.is_animating = False  # 是否正在动画
    
    def _render_lyric_surface(self, lyric_text: str) -> pygame.Surface:
        """
        渲染歌词为带描边的Surface
        Render lyric text with outline to a surface
        
        Args:
            lyric_text: 歌词文本
            
        Returns:
            pygame.Surface: 渲染好的歌词表面
        """
        # 渲染文字表面
        text_surface = self.font.render(lyric_text, True, self.text_color)
        
        # 创建描边效果
        outline_surface = pygame.Surface(
            (text_surface.get_width() + self.outline_width * 2,
             text_surface.get_height() + self.outline_width * 2),
            pygame.SRCALPHA
        )
        
        # 8个方向绘制描边
        for dx in range(-self.outline_width, self.outline_width + 1):
            for dy in range(-self.outline_width, self.outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_text = self.font.render(lyric_text, True, self.outline_color)
                    outline_surface.blit(
                        outline_text,
                        (self.outline_width + dx, self.outline_width + dy)
                    )
        
        # 在描边上绘制主文字
        outline_surface.blit(text_surface, (self.outline_width, self.outline_width))
        
        return outline_surface
    
    def draw_lyric(self, lyric_text: Optional[str]):
        """
        绘制歌词（带滑动切换动画）
        Draw lyric with sliding transition animation
        
        动画效果：
        - 旧歌词：向上滑动并淡出（透明度 100% → 0%）
        - 新歌词：从下方快速滑入，先超过中心10px再回弹对齐（带过冲效果）
        - 移动范围：歌词高度的125%
        - 动画时长：120ms（快速）
        
        Args:
            lyric_text: 歌词文本，如果为 None 或空字符串则不绘制
        """
        current_time = pygame.time.get_ticks()
        
        # 检测歌词是否改变
        if lyric_text != self.current_lyric:
            # 如果有旧歌词，启动切换动画
            if self.current_lyric:
                self.old_lyric_surface = self._render_lyric_surface(self.current_lyric)
                self.is_animating = True
                self.animation_start_time = current_time
            
            # 准备新歌词
            self.current_lyric = lyric_text if lyric_text else ""
            if self.current_lyric:
                self.new_lyric_surface = self._render_lyric_surface(self.current_lyric)
            else:
                self.new_lyric_surface = None
        
        # 如果没有歌词，直接返回
        if not self.current_lyric and not self.is_animating:
            return
        
        # 如果正在动画中
        if self.is_animating:
            elapsed = current_time - self.animation_start_time
            progress = min(1.0, elapsed / self.animation_duration)  # 0.0 到 1.0
            
            # 绘制旧歌词（向上淡出）
            if self.old_lyric_surface:
                old_alpha = int(255 * (1.0 - progress))  # 255 → 0
                # 计算移动距离：歌词高度的125%（减少50%）
                lyric_height = self.old_lyric_surface.get_height()
                move_distance = int(lyric_height * 1.25)
                old_offset_y = -int(move_distance * progress)  # 向上移动
                old_y = self.lyric_y + old_offset_y
                old_x = (self.screen_width - self.old_lyric_surface.get_width()) // 2
                
                # 应用透明度
                old_surface_copy = self.old_lyric_surface.copy()
                old_surface_copy.set_alpha(old_alpha)
                self.screen.blit(old_surface_copy, (old_x, old_y))
            
            # 绘制新歌词（从下方快速滑入，带过冲回弹效果）
            if self.new_lyric_surface:
                # 透明度：50% → 100%
                new_alpha = int(255 * (0.5 + 0.5 * progress))  # 127 → 255
                
                # 计算移动距离：歌词高度的125%（减少50%）
                lyric_height = self.new_lyric_surface.get_height()
                move_distance = int(lyric_height * 1.25)
                
                # 位置计算：带过冲效果（先超过中心10px，再回弹）
                if progress < 0.7:
                    # 前70%时间：从下方快速滑到中心偏上10px
                    t = progress / 0.7
                    new_offset_y = int(move_distance * (1.0 - t) - 10 * t)  # 从下方 → 中心-10px
                else:
                    # 后30%时间：从偏上10px回弹到中心
                    t = (progress - 0.7) / 0.3
                    new_offset_y = int(-10 * (1.0 - t))  # -10 → 0
                
                new_y = self.lyric_y + new_offset_y
                new_x = (self.screen_width - self.new_lyric_surface.get_width()) // 2
                
                # 应用透明度
                new_surface_copy = self.new_lyric_surface.copy()
                new_surface_copy.set_alpha(new_alpha)
                self.screen.blit(new_surface_copy, (new_x, new_y))
            
            # 动画结束
            if progress >= 1.0:
                self.is_animating = False
                self.old_lyric_surface = None
        else:
            # 没有动画，直接绘制当前歌词
            if self.new_lyric_surface:
                x = (self.screen_width - self.new_lyric_surface.get_width()) // 2
                self.screen.blit(self.new_lyric_surface, (x, self.lyric_y))
    
    def get_animation_duration(self) -> int:
        """
        获取动画持续时间（毫秒）
        Get animation duration in milliseconds
        
        Returns:
            int: 动画持续时间
        """
        return self.animation_duration

