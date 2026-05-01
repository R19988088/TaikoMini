"""
输入处理模块 (Input Handler Module)
负责键盘、鼠标、触摸输入处理和自动演奏功能
"""

import pygame


# 判定窗口常量
PERFECT_WINDOW = 25  # ±25ms = Perfect


class InputHandler:
    """
    输入处理类
    
    功能：
    - 处理键盘输入（F/J键=咚，D/K键=咔）
    - 处理触摸/鼠标输入（为安卓准备）
    - 自动演奏模式
    - 鼓动画状态管理
    """
    
    def __init__(self):
        """初始化输入处理器"""
        # 按键状态
        self.key_don_left = False   # F键
        self.key_don_right = False  # J键
        self.key_kat_left = False   # D键
        self.key_kat_right = False  # K键
        
        # 鼓动画时间戳
        self.drum_don_left_time = -10000
        self.drum_don_right_time = -10000
        self.drum_kat_left_time = -10000
        self.drum_kat_right_time = -10000
        self.drum_press_time = -10000
        
        # 自动演奏状态
        self.last_auto_hit_index = -1
        self.last_drumroll_hit_time = 0
        self._last_auto_drumroll_time = 0
        
    
    def handle_event(self, event, game_time, hit_callback, screen_width):
        """
        统一处理所有输入事件
        """
        # 键盘按下
        if event.type == pygame.KEYDOWN:
            self.handle_keydown(event.key, game_time, hit_callback)
        
        # 键盘抬起
        elif event.type == pygame.KEYUP:
            self.handle_keyup(event.key)
            
        # 鼠标/触摸按下
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_touch(event, screen_width, game_time, hit_callback)
    
    def check_ui_click(self, event, rect):
        """
        检查UI元素的点击
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if rect.collidepoint(event.pos):
                return True
        return False

    def handle_keydown(self, key, game_time, hit_callback):
        """
        处理按键按下事件
        
        参数:
            key: Pygame按键码
            game_time: 当前游戏时间（毫秒）
            try_hit_callback: 尝试击打的回调函数 (is_don: bool) -> None
        
        返回:
            bool: 是否处理了该按键
        """
        # 设置鼓按压时间（用于动画）
        if key in [pygame.K_f, pygame.K_j, pygame.K_d, pygame.K_k]:
            self.drum_press_time = game_time
        
        # 咚键处理（F/J）
        if key == pygame.K_f:
            self.key_don_left = True
            self.drum_don_left_time = game_time
            hit_callback(is_don=True)
            return True
        elif key == pygame.K_j:
            self.key_don_right = True
            self.drum_don_right_time = game_time
            hit_callback(is_don=True)
            return True
        
        # 咔键处理（D/K）
        elif key == pygame.K_d:
            self.key_kat_left = True
            self.drum_kat_left_time = game_time
            hit_callback(is_don=False)
            return True
        elif key == pygame.K_k:
            self.key_kat_right = True
            self.drum_kat_right_time = game_time
            hit_callback(is_don=False)
        
        return False
    
    def handle_keyup(self, key):
        """
        处理按键释放事件
        
        参数:
            key: Pygame按键码
        
        返回:
            bool: 是否处理了该按键
        """
        if key == pygame.K_f:
            self.key_don_left = False
            return True
        elif key == pygame.K_j:
            self.key_don_right = False
            return True
        elif key == pygame.K_d:
            self.key_kat_left = False
            return True
        elif key == pygame.K_k:
            self.key_kat_right = False
            return True
        
        return False
    
    def handle_touch(self, event, screen_width, game_time, hit_callback):
        """
        处理触摸/鼠标点击事件（安卓兼容）
        
        参数:
            event: Pygame事件对象
            screen_width: 屏幕宽度
            game_time: 当前游戏时间
            try_hit_callback: 尝试击打的回调函数
        
        返回:
            bool: 是否处理了该事件
        
        触摸规则:
            - 左半屏 = 咚 (Don)
            - 右半屏 = 咔 (Kat)
        """
        # 获取触摸/点击位置
        if hasattr(event, 'pos'):
            # 鼠标事件
            x, y = event.pos
        elif hasattr(event, 'x'):
            # 触摸事件（安卓）
            x = int(event.x * screen_width)
            y = int(event.y * screen_width)  # 假设屏幕高度
        else:
            return False
        
        # 设置鼓按压时间
        self.drum_press_time = game_time
        
        # 根据位置判断咚/咔
        if x < screen_width // 2:
            # 左半屏：咚
            self.drum_don_left_time = game_time
            hit_callback(is_don=True)
        else:
            # 右半屏：咔
            self.drum_kat_left_time = game_time
            hit_callback(is_don=False)
        
        return True
    
    def auto_play_notes(self, auto_play, current_note_index, notes, game_time, try_hit_callback, active_drumroll=None, game=None, sound_don=None, sound_kat=None):
        """
        自动演奏模式 - 在完美时机自动击打音符
        
        参数:
            auto_play: 是否开启自动演奏
            current_note_index: 当前音符索引
            notes: 音符列表
            game_time: 当前游戏时间
            try_hit_callback: 尝试击打的回调函数
            active_drumroll: 当前连打状态 (start_idx, end_idx, type, hits)
            game: Game对象，用于更新鼓动画时间
            sound_don: 咚音效
            sound_kat: 咔音效
        """
        if not auto_play:
            return
        
        # 如果在连打中，持续击打
        if active_drumroll:
            start_idx, end_idx, dr_type, hits = active_drumroll
            
            # 所有连打类型都使用咚击打
            # 5=连打咚, 6=连打咔, 7=气球, 9=草
            hit_is_don = True
            
            # 每60.6ms自动击打一次（每秒16.5次）
            if not hasattr(self, '_last_auto_drumroll_time'):
                self._last_auto_drumroll_time = 0
            
            # 如果是连打刚开始，且上次击打时间为0，重置为当前时间-61ms，使得可以立即击打
            # This allows immediate hitting even when game_time is negative
            if self._last_auto_drumroll_time == 0 and hits == 0:
                self._last_auto_drumroll_time = game_time - 61.0
            
            if game_time - self._last_auto_drumroll_time >= 60.6:
                # 播放音效
                if hit_is_don and sound_don:
                    sound_don.play()
                elif not hit_is_don and sound_kat:
                    sound_kat.play()
                try_hit_callback(is_don=hit_is_don)
                # 触发鼓动画
                self._trigger_drum_animation(hit_is_don, game_time, game)
                self._last_auto_drumroll_time = game_time
            
            return
        else:
            # 重置连打计时器
            self._last_auto_drumroll_time = 0
        
        if current_note_index >= len(notes):
            return
        
        note = notes[current_note_index]
        
        # 如果音符尚未进入显示区域（load_ms > 当前时间），则不自动击打
        note_load_ms = getattr(note, 'load_ms', None)
        if note_load_ms is not None and game_time + PERFECT_WINDOW < note_load_ms:
            return
        
        # 计算时间差
        note_time = note.hit_ms if hasattr(note, 'hit_ms') else note.time_ms
        timing_diff = abs(game_time - note_time)
        
        # 在完美窗口内自动击打
        if timing_diff <= PERFECT_WINDOW:
            # 判断音符类型（咚/咔）
            # 1=咚, 2=咔, 3=大咚, 4=大咔, 5=连打咚, 6=连打咔, 7=气球, 9=草
            note_is_don = note.type in [1, 3, 5, 7, 9]
            
            # 跳过已击打和结束标记
            if note.type == 8 or note.type == -1:
                return
            
            # 播放音效
            if note_is_don and sound_don:
                sound_don.play()
            elif not note_is_don and sound_kat:
                sound_kat.play()
            # 自动击打
            try_hit_callback(is_don=note_is_don)
            # 触发鼓动画
            self._trigger_drum_animation(note_is_don, game_time, game)
    
    def _trigger_drum_animation(self, is_don, game_time, game=None):
        """触发鼓动画（用于自动演奏）"""
        if not game:
            return
        
        # 更新鼓按下时间（用于下沉动画）
        game.drum_press_time = game_time
        
        # 更新鼓击打时间（用于闪光效果）
        if is_don:
            # 咚 - 交替左右
            if game_time - game.drum_don_right_time > 100:
                game.drum_don_left_time = game_time
            else:
                game.drum_don_right_time = game_time
        else:
            # 咔 - 交替左右
            if game_time - game.drum_kat_right_time > 100:
                game.drum_kat_left_time = game_time
            else:
                game.drum_kat_right_time = game_time
    
    def get_drum_animation_times(self):
        """
        获取鼓动画时间戳
        
        返回:
            dict: 包含所有鼓动画时间的字典
        """
        return {
            'don_left': self.drum_don_left_time,
            'don_right': self.drum_don_right_time,
            'kat_left': self.drum_kat_left_time,
            'kat_right': self.drum_kat_right_time,
            'press': self.drum_press_time
        }

