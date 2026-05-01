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
        self.start_y = 0              # 起始Y坐标（列表顶部的虚拟Y坐标）
        
        # ==================== 动画控制 ====================
        self.scroll_speed = 0.48      # 滚动速度系数 (平衡速度与流畅度)
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
        
        极简算法：直接计算目标位置，考虑start_y偏移
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
        """
        if not buttons:
            return
        
        # ==================== 常量定义 ====================
        START_Y = 250  # 必须与 draw_song_buttons 中的 start_y 一致！
        SPACING = -15  # 统一间距
        
        def get_button_height(button, is_selected):
            """获取按钮高度（统一的计算方式）"""
            if is_selected and button.expanded:
                glow_width, glow_height = self.ui_renderer._get_glow_frame_size()
                if glow_height > 0:
                    return int(glow_height * 1.25)
                else:
                    return int((self.button_height + 100) * 1.25)
            elif is_selected:
                return int(self.button_height * 1.25)
            else:
                return int((self.button_height * 0.85) * 1.25)
        
        # ==================== 计算选中项在列表中的相对位置 ====================
        relative_y = 0.0  # 相对于列表顶部的Y坐标
        
        for i in range(selected_index):
            relative_y += get_button_height(buttons[i], False) + SPACING
        
        # 选中项的高度和中心（相对位置）
        selected_height = get_button_height(buttons[selected_index], True)
        selected_center_relative = relative_y + selected_height / 2
        
        # ==================== 计算总高度（用于判断是否整体居中）====================
        # 使用未展开状态计算，确保稳定
        total_height_unexpanded = 0.0
        for btn in buttons:
            total_height_unexpanded += get_button_height(btn, False) + SPACING
        total_height_unexpanded -= SPACING  # 最后一个不需要间距
        
        # ==================== 决定滚动位置 ====================
        screen_center = self.screen_height / 2
        
        # 只有列表非常短（少于3首歌或高度小于屏幕40%）时才整体居中
        # 否则始终让选中项居中，这样用户滚动时会有反馈
        use_list_centering = (len(buttons) <= 2) or (total_height_unexpanded < self.screen_height * 0.4)
        
        if use_list_centering:
            # 列表非常短：整体居中
            # 计算实际总高度（包含展开状态）
            total_height_actual = 0.0
            for i in range(len(buttons)):
                total_height_actual += get_button_height(buttons[i], i == selected_index) + SPACING
            total_height_actual -= SPACING
            
            # 整体居中公式：
            # 列表中心实际Y = START_Y + total_height_actual / 2
            # 目标：列表中心实际Y = screen_center
            # START_Y + total_height_actual / 2 - scroll_offset = screen_center
            # scroll_offset = START_Y + total_height_actual / 2 - screen_center
            new_target = START_Y + total_height_actual / 2 - screen_center
        else:
            # 默认模式：选中项居中（3首歌及以上）
            # 选中项中心实际Y = START_Y + selected_center_relative - scroll_offset
            # 目标：选中项中心实际Y = screen_center
            # START_Y + selected_center_relative - scroll_offset = screen_center
            # scroll_offset = START_Y + selected_center_relative - screen_center
            new_target = START_Y + selected_center_relative - screen_center
            
            # ==================== 循环滚动优化 ====================
            # 为了解决循环边界跳跃问题，找到距离当前目标位置最近的等效目标
            # 注意：使用 target_scroll 而不是 scroll_offset，避免动画中的值导致错误判断
            total_height = self.ui_renderer._calculate_total_height(buttons, selected_index)
            if total_height > 0:
                # 使用上一次的目标位置作为参考，而不是当前动画中的位置
                current = self.target_scroll
                
                # 生成多个等效位置（由于循环渲染）
                candidates = []
                for offset in [-2, -1, 0, 1, 2]:
                    candidate = new_target + offset * total_height
                    distance = abs(candidate - current)
                    candidates.append((distance, candidate))
                
                # 选择距离最近的
                candidates.sort()
                new_target = candidates[0][1]
        
        # ==================== 设置目标 ====================
        self.target_scroll = new_target
        
        # 初始化时立即跳转
        if not self._initialized_scroll:
            self.scroll_offset = new_target
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
        
        # 重置初始化标志，确保立即滚动到位置
        self._initialized_scroll = False
        
        # 滚动到第一个按钮（会立即设置 scroll_offset）
        self.scroll_to_selection(buttons, 0)
    
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
