"""
滚动管理模块
Scroll Manager Module

负责处理歌曲选择界面的滚动逻辑，包括：
- 平滑滚动动画
- 循环滚动支持
- 滚动位置计算和归一化
- 选中项居中逻辑
- 滚动性能优化

主要类：
- ScrollManager: 滚动管理器，提供统一的滚动控制接口
"""

import pygame
from typing import List, Tuple, Optional
from lib.song_button import SongButton


class ScrollManager:
    """
    滚动管理器
    Scroll Manager
    
    负责处理歌曲选择界面的所有滚动相关功能
    """
    
    def __init__(self, screen_height: int, button_height: int, button_spacing: int, ui_renderer):
        """
        初始化滚动管理器
        Initialize scroll manager
        
        Args:
            screen_height: 屏幕高度
            button_height: 按钮高度
            button_spacing: 按钮间距
            ui_renderer: UI渲染器引用
        """
        # ==================== 基础属性 ====================
        self.screen_height = screen_height
        self.button_height = button_height
        self.button_spacing = button_spacing
        self.ui_renderer = ui_renderer
        
        # ==================== 滚动状态 ====================
        self.scroll_offset = 0.0      # 当前滚动偏移量
        self.target_scroll = 0.0      # 目标滚动位置
        self.start_y = 250            # 起始Y坐标
        
        # ==================== 动画控制 ====================
        self.scroll_speed = 0.2       # 滚动速度系数
        self.normalization_threshold = 5.0  # 归一化阈值
        
        # ==================== 初始化标志 ====================
        self._initialized_scroll = False
    
    def update_scroll(self, buttons: List[SongButton], selected_index: int) -> float:
        """
        更新滚动位置
        Update scroll position
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            
        Returns:
            float: 更新后的滚动偏移量
        """
        # ==================== 平滑滚动 ====================
        self.scroll_offset += (self.target_scroll - self.scroll_offset) * self.scroll_speed
        
        # ==================== 归一化滚动值 ====================
        # 当滚动接近目标时，将两者都归一化到合理范围
        if abs(self.scroll_offset - self.target_scroll) < self.normalization_threshold:
            total_height = self.ui_renderer._calculate_total_height(buttons, selected_index)
            if total_height > 0:
                # 将滚动值归一化到 [0, total_height) 范围
                offset_diff = self.scroll_offset - self.target_scroll
                self.target_scroll = self.target_scroll % total_height
                self.scroll_offset = self.target_scroll + offset_diff
        
        return self.scroll_offset
    
    def scroll_to_selection(self, buttons: List[SongButton], selected_index: int):
        """
        滚动到选中项，使其垂直居中
        Scroll to selected item to center it vertically
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
        """
        if not buttons:
            return
        
        # ==================== 计算选中歌曲位置 ====================
        selected_y = self.start_y
        
        # 累加选中歌曲之前所有歌曲的高度 - 整体扩大25%，减小垂直间距
        for j in range(selected_index):
            # 之前的歌曲都使用缩小高度（因为它们不是选中的）- 整体扩大25%
            selected_y += int((self.button_height * 0.85) * 1.25) + 1  # 减小间距到1
        
        # ==================== 计算选中歌曲中心点 ====================
        # 选中歌曲的高度（可能包括展开的难度选择）- 整体扩大25%
        selected_button = buttons[selected_index]
        selected_height = int((self.button_height + (100 if selected_button.expanded else 0)) * 1.25)
        selected_center_y = selected_y + selected_height / 2
        
        # ==================== 计算目标滚动位置 ====================
        # 屏幕垂直中心点
        screen_center_y = self.screen_height / 2
        
        # 计算新的目标滚动位置
        new_target = selected_center_y - screen_center_y
        
        # ==================== 智能选择等效滚动位置 ====================
        # 智能选择最近的等效滚动位置（考虑循环）
        total_height = self.ui_renderer._calculate_total_height(buttons, selected_index)
        if total_height > 0:
            # 找到所有等效的滚动位置（由于循环）
            # 选择最接近当前 target_scroll 的那个
            current = self.target_scroll
            
            # 计算几个可能的等效位置
            options = []
            for offset in [-2, -1, 0, 1, 2]:
                option = new_target + offset * total_height
                options.append((abs(option - current), option))
            
            # 选择最接近的
            options.sort()
            new_target = options[0][1]
        
        self.target_scroll = new_target
        
        # ==================== 初始化处理 ====================
        # 初始化时立即设置scroll_offset，避免滚动动画
        if not self._initialized_scroll:
            self.scroll_offset = self.target_scroll
            self._initialized_scroll = True
    
    def scroll_to_category(self, buttons: List[SongButton]):
        """
        滚动到分类开始位置
        Scroll to category start position
        
        Args:
            buttons: 歌曲按钮列表
        """
        if not buttons:
            return
        
        # 滚动到第一个按钮
        self.scroll_to_selection(buttons, 0)
        
        # 重置初始化标志以立即居中
        self._initialized_scroll = False
    
    def reset_scroll(self):
        """
        重置滚动状态
        Reset scroll state
        """
        self.scroll_offset = 0.0
        self.target_scroll = 0.0
        self._initialized_scroll = False
    
    def get_scroll_offset(self) -> float:
        """
        获取当前滚动偏移量
        Get current scroll offset
        
        Returns:
            float: 当前滚动偏移量
        """
        return self.scroll_offset
    
    def set_scroll_offset(self, offset: float):
        """
        设置滚动偏移量
        Set scroll offset
        
        Args:
            offset: 滚动偏移量
        """
        self.scroll_offset = offset
        self.target_scroll = offset
    
    def is_scroll_initialized(self) -> bool:
        """
        检查滚动是否已初始化
        Check if scroll is initialized
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized_scroll
