"""
事件处理模块
Event Handler Module

负责处理歌曲选择界面的所有用户交互事件，包括：
- 键盘事件处理（方向键、确认键、ESC等）
- 鼠标事件处理（点击、滚动）
- 长按检测（用于里模式切换）
- 事件分发和状态管理

主要类：
- EventHandler: 事件处理器，提供统一的事件处理接口
"""

import pygame
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict, Any
from lib.song_button import SongButton


class EventHandler:
    """
    事件处理器
    Event Handler
    
    负责处理歌曲选择界面的所有用户交互事件
    """
    
    def __init__(self):
        """
        初始化事件处理器
        Initialize event handler
        """
        # ==================== 事件回调函数 ====================
        self.callbacks = {}  # 事件回调函数字典
        
        # ==================== 长按检测 ====================
        self.oni_press_start_time = None        # 长按鬼难度开始时间
        self.ura_mode_threshold = 2000          # 长按阈值（2秒，毫秒）
        
        # ==================== 事件状态 ====================
        self.last_event_time = 0                # 上次事件时间
        self.event_count = 0                    # 事件计数
    
    def set_callback(self, event_type: str, callback: Callable):
        """
        设置事件回调函数
        Set event callback function
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.callbacks[event_type] = callback
    
    def handle_keyboard_event(self, event: pygame.event.Event, 
                            buttons: List[SongButton], 
                            selected_index: int,
                            current_category: str,
                            categories: List[str],
                            selected_category_index: int) -> Optional[Tuple[Path, str, str]]:
        """
        处理键盘事件
        Handle keyboard events
        
        支持的按键：
        - 上下键/K/D键：切换歌曲或难度
        - 左右键：切换分类或返回
        - F/J/回车/空格：激活/确认歌曲
        - ESC键：取消展开或退出
        
        Args:
            event: pygame键盘事件
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            current_category: 当前分类
            categories: 分类列表
            selected_category_index: 当前分类索引
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        if not buttons:
            return None
        
        current_button = buttons[selected_index] if buttons else None
        
        # ==================== 上下键/K/D键处理 ====================
        if event.key in [pygame.K_UP, pygame.K_k]:
            if current_button and current_button.expanded:
                # K键：在展开状态下向右切换选项（返回->Easy->Normal->Hard->Oni->[Edit]）
                if not hasattr(current_button, 'selected_option_index'):
                    current_button.selected_option_index = 1  # 默认从Easy开始
                
                # 根据是否有Edit决定选项数量
                has_edit = 'Edit' in current_button.difficulties
                num_diffs = 5 if has_edit else 4  # 难度数量
                total_options = num_diffs + 1  # 返回按钮 + 难度
                
                current_button.selected_option_index = (current_button.selected_option_index + 1) % total_options
                
                # 更新对应的难度索引
                if current_button.selected_option_index > 0:
                    diff_list = ['Easy', 'Normal', 'Hard', 'Oni', 'Edit'] if has_edit else ['Easy', 'Normal', 'Hard', 'Oni']
                    target_diff = diff_list[current_button.selected_option_index - 1]
                    if target_diff in current_button.difficulties:
                        current_button.selected_diff_index = current_button.difficulties.index(target_diff)
            else:
                # 上/K键：未展开时切换歌曲（向上）
                if 'move_selection' in self.callbacks:
                    self.callbacks['move_selection'](1)
                    
        elif event.key in [pygame.K_DOWN, pygame.K_d]:
            if current_button and current_button.expanded:
                # D键：在展开状态下向左切换选项
                if not hasattr(current_button, 'selected_option_index'):
                    current_button.selected_option_index = 1
                
                # 根据是否有Edit决定选项数量
                has_edit = 'Edit' in current_button.difficulties
                num_diffs = 5 if has_edit else 4
                total_options = num_diffs + 1
                
                current_button.selected_option_index = (current_button.selected_option_index - 1) % total_options
                
                # 更新对应的难度索引
                if current_button.selected_option_index > 0:
                    diff_list = ['Easy', 'Normal', 'Hard', 'Oni', 'Edit'] if has_edit else ['Easy', 'Normal', 'Hard', 'Oni']
                    target_diff = diff_list[current_button.selected_option_index - 1]
                    if target_diff in current_button.difficulties:
                        current_button.selected_diff_index = current_button.difficulties.index(target_diff)
            else:
                # 下/D键：未展开时切换歌曲（向下）
                if 'move_selection' in self.callbacks:
                    self.callbacks['move_selection'](-1)
        
        # ==================== 左右键处理 ====================
        elif event.key == pygame.K_LEFT:
            if current_button and current_button.expanded:
                # 展开状态下，左键返回（关闭展开）
                current_button.expanded = False
                # 收起后重新计算滚动位置
                if 'update_scroll' in self.callbacks:
                    self.callbacks['update_scroll']()
            else:
                # 未展开时，左键切换分类
                if 'change_category' in self.callbacks:
                    self.callbacks['change_category'](-1)
                    
        elif event.key == pygame.K_RIGHT:
            if 'change_category' in self.callbacks:
                self.callbacks['change_category'](1)
        
        # ==================== 确认键处理 ====================
        elif event.key in [pygame.K_f, pygame.K_j, pygame.K_RETURN, pygame.K_SPACE]:
            if not current_button.expanded:
                # 展开难度选择
                current_button.expanded = True
                # 初始化选项索引，默认选中第一个难度（Oni）
                if not hasattr(current_button, 'selected_option_index'):
                    # 找到Oni的位置（索引4）
                    current_button.selected_option_index = 4
                # 展开后重新计算滚动位置
                if 'update_scroll' in self.callbacks:
                    self.callbacks['update_scroll']()
            else:
                # 检查是否选中了返回按钮
                if hasattr(current_button, 'selected_option_index') and current_button.selected_option_index == 0:
                    # 选中返回，关闭展开
                    current_button.expanded = False
                    # 收起后重新计算滚动位置
                    if 'update_scroll' in self.callbacks:
                        self.callbacks['update_scroll']()
                else:
                    # 直接确认选择（不再使用长按）
                    selected_diff = current_button.difficulties[current_button.selected_diff_index]
                    
                    # 触发确认音效回调
                    if 'confirm' in self.callbacks:
                        self.callbacks['confirm']()
                    
                    category = getattr(current_button, 'category', '')
                    return (current_button.tja_path, selected_diff, category)
        
        # ==================== ESC键和X键处理 ====================
        elif event.key in [pygame.K_ESCAPE, pygame.K_x]:
            if current_button and current_button.expanded:
                # 播放返回音效
                if 'cancel' in self.callbacks:
                    self.callbacks['cancel']()
                current_button.expanded = False
            else:
                # 播放返回音效
                if 'cancel' in self.callbacks:
                    self.callbacks['cancel']()
                return None  # ESC/X退出
        
        # ==================== Tab键处理（查看结算画面） ====================
        elif event.key == pygame.K_TAB:
            if current_button and not current_button.expanded:
                # Tab键：查看选中歌曲的结算画面（仅未展开时）
                if 'show_result_screen' in self.callbacks:
                    self.callbacks['show_result_screen'](current_button)
        
        return None
    
    def handle_keyup_event(self, event: pygame.event.Event, 
                          buttons: List[SongButton], 
                          selected_index: int) -> Optional[Tuple[Path, str, str]]:
        """
        处理按键释放事件
        Handle key release events
        
        主要用于检测长按操作（里模式切换）
        
        Args:
            event: pygame按键释放事件
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        # 不再处理长按逻辑（已移到keydown直接确认）
        return None
    
    def handle_mouse_event(self, event: pygame.event.Event, 
                          buttons: List[SongButton], 
                          selected_index: int,
                          scroll_offset: float,
                          width: int, height: int,
                          categories: List[str],
                          selected_category_index: int) -> Optional[Tuple[Path, str, str]]:
        """
        处理鼠标事件
        Handle mouse events
        
        支持的鼠标操作：
        - 点击分类切换
        - 点击歌曲按钮
        - 点击难度选择
        - 点击功能按钮（收藏、练习）
        
        Args:
            event: pygame鼠标事件
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            scroll_offset: 滚动偏移量
            width: 屏幕宽度
            height: 屏幕高度
            categories: 分类列表
            selected_category_index: 当前分类索引
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_click(event.pos, buttons, selected_index, scroll_offset, 
                                   width, height, categories, selected_category_index)
        return None
    
    def _handle_click(self, pos: Tuple[int, int], 
                     buttons: List[SongButton], 
                     selected_index: int,
                     scroll_offset: float,
                     width: int, height: int,
                     categories: List[str],
                     selected_category_index: int) -> Optional[Tuple[Path, str, str]]:
        """
        处理鼠标点击
        Handle mouse click
        
        Args:
            pos: 点击位置
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            scroll_offset: 滚动偏移量
            width: 屏幕宽度
            height: 屏幕高度
            categories: 分类列表
            selected_category_index: 当前分类索引
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        mx, my = pos
        
        # ==================== 分类点击检测 ====================
        category_result = self._check_category_click(mx, my, width, categories, selected_category_index)
        if category_result is not None:
            return category_result
        
        # ==================== 歌曲按钮点击检测 ====================
        if not buttons:
            return None
        
        start_y = 250
        
        for i, button in enumerate(buttons):
            # Calculate button position (same as drawing logic) - 整体扩大25%，减小垂直间距
            is_selected = (i == selected_index)
            
            if is_selected:
                button_height = int((140 + (100 if button.expanded else 0)) * 1.25)
            else:
                button_height = int((140 * 0.85) * 1.25)
            
            # Calculate cumulative Y position - 整体扩大25%，减小垂直间距
            button_y = start_y
            for j in range(i):
                if j == selected_index and buttons[j].expanded:
                    button_y += int((140 + 100) * 1.25) + 1  # 减小间距到1
                elif j == selected_index:
                    button_y += int(140 * 1.25) + 1  # 减小间距到1
                else:
                    button_y += int((140 * 0.85) * 1.25) + 1  # 减小间距到1
            
            button_y -= scroll_offset
            
            # Check if click is on this button
            if button_y < my < button_y + button_height:
                if not button.expanded:
                    # Expand this song, close others
                    for b in buttons:
                        b.expanded = False
                    button.expanded = True
                    if 'set_selected_index' in self.callbacks:
                        self.callbacks['set_selected_index'](i)
                    return None
                else:
                    # Check back button first
                    if hasattr(button, 'back_button_rect') and button.back_button_rect.collidepoint(mx, my):
                        # 播放返回音效
                        if 'cancel' in self.callbacks:
                            self.callbacks['cancel']()
                        # Close expanded state
                        button.expanded = False
                        return None
                    
                    # Check action buttons (favorite/practice)
                    if self._check_action_button_click(mx, my, button_y, button_height, width):
                        return None
                    
                    # Click on difficulty (固定4个难度)
                    diff_result = self._check_difficulty_click(mx, my, button_y, button_height, width, button)
                    if diff_result:
                        return diff_result
        
        return None
    
    def _check_category_click(self, mx: int, my: int, width: int, 
                            categories: List[str], selected_category_index: int) -> Optional[Tuple[Path, str, str]]:
        """
        检查分类点击
        Check category click
        
        Args:
            mx: 鼠标X坐标
            my: 鼠标Y坐标
            width: 屏幕宽度
            categories: 分类列表
            selected_category_index: 当前分类索引
            
        Returns:
            Optional[Tuple[Path, str, str]]: 分类切换结果或None
        """
        category_top = 120
        category_height = 60
        category_width = width // 5  # Each category box width
        
        # Left arrow (switch category left)
        arrow_size = 40
        left_arrow_x = 20
        if left_arrow_x < mx < left_arrow_x + arrow_size and category_top < my < category_top + category_height:
            if 'change_category' in self.callbacks:
                self.callbacks['change_category'](-1)
            return None
        
        # Right arrow (switch category right)
        right_arrow_x = width - 60
        if right_arrow_x < mx < right_arrow_x + arrow_size and category_top < my < category_top + category_height:
            if 'change_category' in self.callbacks:
                self.callbacks['change_category'](1)
            return None
        
        # Category boxes (show 3 at a time)
        start_idx = max(0, selected_category_index - 1)
        for i in range(3):
            cat_idx = start_idx + i
            if cat_idx >= len(categories):
                break
            
            box_x = 80 + i * category_width
            box_width = category_width - 20
            
            if box_x < mx < box_x + box_width and category_top < my < category_top + category_height:
                # 计算相对于当前分类的delta
                delta = cat_idx - selected_category_index
                if delta != 0:
                    if 'change_category' in self.callbacks:
                        self.callbacks['change_category'](delta)
                return None
        
        return None
    
    def _check_action_button_click(self, mx: int, my: int, button_y: int, 
                                 button_height: int, width: int) -> bool:
        """
        检查功能按钮点击
        Check action button click (favorite/practice)
        
        Args:
            mx: 鼠标X坐标
            my: 鼠标Y坐标
            button_y: 按钮Y坐标
            button_height: 按钮高度
            width: 屏幕宽度
            
        Returns:
            bool: 是否点击了功能按钮
        """
        # Button dimensions
        button_width = 80
        button_height_btn = 35
        button_spacing = 10
        
        # Position buttons in the top right of the expanded song area
        right_x = width - 20
        top_y = button_y + 10
        
        # Favorite button
        favorite_x = right_x - button_width
        favorite_y = top_y
        
        if favorite_x < mx < favorite_x + button_width and favorite_y < my < favorite_y + button_height_btn:
            if 'toggle_favorite' in self.callbacks:
                self.callbacks['toggle_favorite']()
            return True
        
        # Practice button
        practice_x = right_x - button_width * 2 - button_spacing
        practice_y = top_y
        
        if practice_x < mx < practice_x + button_width and practice_y < my < practice_y + button_height_btn:
            if 'toggle_practice' in self.callbacks:
                self.callbacks['toggle_practice']()
            return True
        
        return False
    
    def _check_difficulty_click(self, mx: int, my: int, button_y: int, 
                              button_height: int, width: int, button: SongButton) -> Optional[Tuple[Path, str, str]]:
        """
        检查难度点击
        Check difficulty click
        
        Args:
            mx: 鼠标X坐标
            my: 鼠标Y坐标
            button_y: 按钮Y坐标
            button_height: 按钮高度
            width: 屏幕宽度
            button: 歌曲按钮
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        # 使用UI渲染器存储的按钮位置信息
        if hasattr(button, 'diff_button_rects'):
            for diff, rect in button.diff_button_rects.items():
                if rect.collidepoint(mx, my) and diff in button.difficulties:
                    # 触发确认音效回调
                    if 'confirm' in self.callbacks:
                        self.callbacks['confirm']()
                    
                    category = getattr(button, 'category', '')
                    return (button.tja_path, diff, category)
        
        return None
    
    def process_events(self, events: List[pygame.event.Event], 
                      buttons: List[SongButton], 
                      selected_index: int,
                      current_category: str,
                      categories: List[str],
                      selected_category_index: int,
                      scroll_offset: float,
                      width: int, height: int) -> Optional[Tuple[Path, str, str]]:
        """
        处理事件列表
        Process list of events
        
        Args:
            events: pygame事件列表
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            current_category: 当前分类
            categories: 分类列表
            selected_category_index: 当前分类索引
            scroll_offset: 滚动偏移量
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            Optional[Tuple[Path, str, str]]: (歌曲路径, 难度, 分类) 或 None
        """
        for event in events:
            if event.type == pygame.QUIT:
                if 'quit' in self.callbacks:
                    self.callbacks['quit']()
                return None
            elif event.type == pygame.KEYDOWN:
                result = self.handle_keyboard_event(event, buttons, selected_index, 
                                                  current_category, categories, selected_category_index)
                if result is not None:
                    return result
            elif event.type == pygame.KEYUP:
                result = self.handle_keyup_event(event, buttons, selected_index)
                if result is not None:
                    return result
            elif event.type == pygame.MOUSEBUTTONDOWN:
                result = self.handle_mouse_event(event, buttons, selected_index, 
                                               scroll_offset, width, height, 
                                               categories, selected_category_index)
                if result is not None:
                    return result
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取事件统计信息
        Get event statistics
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        stats = {
            'event_count': self.event_count,
            'last_event_time': self.last_event_time,
            'oni_press_start_time': self.oni_press_start_time,
            'ura_mode_threshold': self.ura_mode_threshold,
            'callbacks_count': len(self.callbacks),
        }
        return stats
