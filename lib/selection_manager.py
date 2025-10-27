"""
选择管理模块
Selection Manager Module

负责处理歌曲选择界面的选择逻辑，包括：
- 歌曲选择状态管理
- 选择索引的循环导航
- 上次选择状态的恢复
- 选择状态的回调处理
- 分类切换时的选择重置

主要类：
- SelectionManager: 选择管理器，提供统一的选择控制接口
"""

from typing import List, Dict, Optional, Callable
from lib.song_button import SongButton


class SelectionManager:
    """
    选择管理器
    Selection Manager
    
    负责处理歌曲选择界面的所有选择相关功能
    """
    
    def __init__(self, config_manager, scroll_manager):
        """
        初始化选择管理器
        Initialize selection manager
        
        Args:
            config_manager: 配置管理器
            scroll_manager: 滚动管理器
        """
        # ==================== 依赖注入 ====================
        self.config = config_manager
        self.scroll_manager = scroll_manager
        
        # ==================== 选择状态 ====================
        self.selected_index = 0
        self.buttons = []
        
        # ==================== 回调函数 ====================
        self.on_selection_changed: Optional[Callable] = None
    
    def set_buttons(self, buttons: List[SongButton]):
        """
        设置按钮列表
        Set buttons list
        
        Args:
            buttons: 歌曲按钮列表
        """
        self.buttons = buttons
    
    def get_selected_index(self) -> int:
        """
        获取当前选中索引
        Get current selected index
        
        Returns:
            int: 当前选中索引
        """
        return self.selected_index
    
    def set_selected_index(self, index: int):
        """
        设置选中索引
        Set selected index
        
        Args:
            index: 新的选中索引
        """
        if 0 <= index < len(self.buttons):
            self.selected_index = index
            self.scroll_manager.scroll_to_selection(self.buttons, self.selected_index)
            
            # 触发选择变化回调
            if self.on_selection_changed:
                self.on_selection_changed(index)
    
    def move_selection(self, delta: int):
        """
        移动选择（循环）
        Move selection (circular)
        
        Args:
            delta: 移动步数（正数向下，负数向上）
        """
        if not self.buttons:
            return
        
        # 简单地更新选中索引（循环）
        new_index = (self.selected_index + delta) % len(self.buttons)
        self.set_selected_index(new_index)
    
    def restore_last_selection(self) -> int:
        """
        恢复上次选择的歌曲
        Restore last selected song from configuration
        
        处理逻辑：
        1. 从配置中读取上次选择的歌曲路径和难度
        2. 在当前按钮列表中查找匹配的歌曲
        3. 如果找到，恢复难度选择并返回索引
        4. 如果未找到，返回默认索引0
        
        Returns:
            int: 选中按钮的索引，如果未找到则返回0
        """
        try:
            # 从配置中获取上次选择
            last_selected = self.config.get_last_selected()
            last_path = last_selected.get('song_path', '')
            
            if not last_path:
                return 0
            
            # ==================== 查找匹配歌曲 ====================
            # 在按钮列表中查找匹配的歌曲
            for i, button in enumerate(self.buttons):
                if str(button.tja_path) == last_path:
                    # 找到了，恢复难度选择
                    last_diff = last_selected.get('difficulty', 'Oni')
                    if last_diff in button.difficulties:
                        button.selected_diff_index = button.difficulties.index(last_diff)
                    return i
            
        except Exception as e:
            print(f"Error restoring last selection: {e}")
        
        # 默认返回第一个按钮的索引
        return 0
    
    def reset_selection(self):
        """
        重置选择到第一个
        Reset selection to first item
        """
        self.set_selected_index(0)
    
    def get_selected_button(self) -> Optional[SongButton]:
        """
        获取当前选中的按钮
        Get currently selected button
        
        Returns:
            Optional[SongButton]: 选中的按钮，如果没有则返回None
        """
        if 0 <= self.selected_index < len(self.buttons):
            return self.buttons[self.selected_index]
        return None
    
    def has_selection(self) -> bool:
        """
        检查是否有有效的选择
        Check if there is a valid selection
        
        Returns:
            bool: 是否有有效选择
        """
        return 0 <= self.selected_index < len(self.buttons)
    
    def set_selection_changed_callback(self, callback: Callable[[int], None]):
        """
        设置选择变化回调
        Set selection changed callback
        
        Args:
            callback: 回调函数，参数为新的选中索引
        """
        self.on_selection_changed = callback
    
    def get_selection_info(self) -> Dict:
        """
        获取选择信息
        Get selection information
        
        Returns:
            Dict: 包含选择信息的字典
        """
        button = self.get_selected_button()
        if button:
            return {
                'index': self.selected_index,
                'title': button.title,
                'title_cn': button.title_cn,
                'difficulties': button.difficulties,
                'selected_difficulty': button.difficulties[button.selected_diff_index] if button.difficulties else None,
                'expanded': button.expanded
            }
        return {
            'index': self.selected_index,
            'title': None,
            'title_cn': None,
            'difficulties': [],
            'selected_difficulty': None,
            'expanded': False
        }
