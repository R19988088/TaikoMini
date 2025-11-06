"""
音符判定模块 (Note Judgment Module)
负责音符击打判定、连打/气球处理、Miss检测
"""

# 判定窗口常量（毫秒）- 根据难度动态设置
# 魔王/困难难度 (Oni/Hard)
PERFECT_WINDOW_HARD = 25.025  # 良
GOOD_WINDOW_HARD = 75.075      # 可
OK_WINDOW_HARD = 108.442       # 不可

# 一般/简单难度 (Normal/Easy)
PERFECT_WINDOW_EASY = 41.708  # 良
GOOD_WINDOW_EASY = 108.442     # 可
OK_WINDOW_EASY = 125.125       # 不可

# 默认使用困难难度
PERFECT_WINDOW = 25   # ±25ms = Perfect
GOOD_WINDOW = 75      # ±75ms = Good
OK_WINDOW = 108       # ±108ms = OK


class NoteJudgment:
    """
    音符判定类
    
    功能：
    - 击打判定（Perfect/Good/OK）
    - 连打/气球状态管理
    - Miss检测
    - 分数和连段计算
    """
    
    def __init__(self, base_note_score=100):
        """
        初始化判定系统
        
        参数:
            base_note_score: 每音符基础分数（真打系统计算得出）
        """
        # 连打/气球状态 (start_index, end_index, type, hits)
        self.active_drumroll = None
        self.last_drumroll_hit_time = 0
        
        # 当前判定结果
        self.current_judgment = ""
        self.judgment_time = 0
        self.is_super_large_note = False  # 记录当前判定的音符是否是超大音符
        
        # 真打分数系统：每音符固定分数
        self.base_note_score = base_note_score
    
    def try_hit(self, is_don, note, game_time, sound_don, sound_kat, 
                trigger_animation_callback, current_note_index, animation_time, notes_list=None):
        """
        尝试击打音符
        
        参数:
            is_don: 是否击打咚（False=咔）
            note: 当前音符对象
            game_time: 当前游戏时间（用于判定）
            sound_don: 咚音效
            sound_kat: 咔音效
            trigger_animation_callback: 触发动画的回调
            current_note_index: 当前音符索引
            animation_time: 动画时间（实时时间，不受变速影响）
            notes_list: 音符列表（用于获取气球最大敲打数）
        
        返回:
            dict: 判定结果 {'judgment': str, 'score': int, 'combo_add': int, 
                          'note_hit': bool, 'advance_index': bool}
        """
        # 如果在连打中，获取气球的最大敲打数
        balloon_count = None
        if self.active_drumroll and notes_list:
            start_idx, _, dr_type, _ = self.active_drumroll
            if dr_type in [7, 9]:  # 气球
                balloon_note = notes_list[start_idx]
                balloon_count = getattr(balloon_note, 'count', None)
        
        result = {
            'judgment': '',
            'score': 0,
            'combo_add': 0,
            'note_hit': False,
            'advance_index': False
        }
        
        # 检查是否在连打/气球中
        if self.active_drumroll:
            return self._handle_drumroll_hit(is_don, game_time, sound_don, sound_kat, balloon_count)
        
        # 计算时间差
        note_time = note.hit_ms if hasattr(note, 'hit_ms') else note.time_ms
        timing_diff = abs(game_time - note_time)
        
        # 超出判定窗口
        if timing_diff > OK_WINDOW:
            return result
        
        # 处理连打/气球开始
        if note.type in [5, 6, 7, 9]:
            return self._start_drumroll(note, is_don, game_time, sound_don, sound_kat, current_note_index)
        
        # 普通音符判定
        note_is_don = note.type in [1, 3]  # 1=咚, 3=大咚
        
        # 类型不匹配
        if is_don != note_is_don:
            return result
        
        # 判定不播放音效，音效由外部（_try_hit_manual）播放
        
        # 触发击打动画（使用实时时间，不受变速影响）
        is_big = note.type in [3, 4]
        trigger_animation_callback(is_big, is_don, animation_time)
        
        # 判定等级
        if timing_diff <= PERFECT_WINDOW:
            result['judgment'] = "Perfect"
        elif timing_diff <= GOOD_WINDOW:
            result['judgment'] = "Good"
        else:
            result['judgment'] = "OK"
        
        # 真打分数系统：每音符固定分数（不区分Perfect/Good/OK）
        result['score'] = self.base_note_score
        
        result['combo_add'] = 1
        result['note_hit'] = True
        result['advance_index'] = True
        self.current_judgment = result['judgment']
        self.judgment_time = game_time
        self.is_super_large_note = getattr(note, 'is_super_large', False)  # 记录是否是超大音符
        
        return result
    
    def _handle_drumroll_hit(self, is_don, game_time, sound_don, sound_kat, balloon_count=None):
        """
        处理连打/气球中的击打
        
        参数:
            balloon_count: 气球的最大敲打数（仅气球有效）
        """
        start_idx, end_idx, dr_type, hits = self.active_drumroll
        
        # 真打系统：每次 +100分
        score = 100
        
        # 气球有最大敲打数限制
        if dr_type in [7, 9] and balloon_count is not None:
            if hits >= balloon_count:
                score = 0  # 超过最大次数，不再加分
        
        result = {
            'judgment': '',  # 连打击打不计入判定统计
            'score': score,
            'combo_add': 0,  # 连打不增加连击，也不计入Perfect数
            'note_hit': False,
            'advance_index': False,
            'drumroll_update': (start_idx, end_idx, dr_type, hits + 1),
            'drumroll_hit': True  # 标记为连打击打（仅用于识别）
        }
        
        # 连打不限制咚咔类型，都可以击打
        # 5=连打咚, 6=连打咔, 7=气球, 9=草
        # 手动输入时，音效已经在 _try_hit_manual 中播放了，这里不再重复播放
        # 自动演奏时，由 game_input.py 中的 auto_play_notes 播放音效
        
        # 更新连打状态
        self.last_drumroll_hit_time = game_time
        result['drumroll_update'] = (start_idx, end_idx, dr_type, hits + 1)
        
        return result
    
    def _start_drumroll(self, note, is_don, game_time, sound_don, sound_kat, current_note_index):
        """开始连打/气球"""
        result = {
            'judgment': '',
            'score': 0,
            'combo_add': 1,
            'note_hit': True,
            'advance_index': True,
            'drumroll_start': True
        }
        
        # 连打开始不限制咚咔类型
        # 5=连打咚, 6=连打咔, 7=气球, 9=草
        # 手动输入时，音效已经在外部播放，这里不再重复播放
        
        return result
    
    def check_miss(self, note, game_time):
        """
        检查音符是否Miss
        
        参数:
            note: 当前音符
            game_time: 当前游戏时间
        
        返回:
            bool: 是否Miss
        """
        # 跳过结束标记
        if note.type == 8:
            return False
        
        # 音符已过判定区且未击打
        note_time = note.hit_ms if hasattr(note, 'hit_ms') else note.time_ms
        
        if game_time > note_time + OK_WINDOW and note.type != -1:
            self.current_judgment = "Miss"
            self.judgment_time = game_time
            self.is_super_large_note = getattr(note, 'is_super_large', False)  # Miss时也记录是否超大音符
            return True
        
        return False
    
    def check_drumroll_end(self, end_note, game_time):
        """
        检查连打/气球是否结束
        
        返回:
            dict: {'ended': bool, 'score': int} 或 None
        """
        if not self.active_drumroll:
            return None
        
        start_idx, end_idx, dr_type, hits = self.active_drumroll
        end_note_time = end_note.hit_ms if hasattr(end_note, 'hit_ms') else end_note.time_ms
        
        if game_time >= end_note_time:
            # 连打/气球结束 - 真打分数规则
            import math
            score = 0
            if dr_type in [7, 9]:  # 气球/草：每个100分
                score = hits * 100
            else:  # 连打：每10次1000分
                score = math.ceil(hits / 10) * 1000
            
            self.active_drumroll = None
            
            return {
                'ended': True,
                'score': score,
                'end_index': end_idx
            }
        
        return None
    
    def get_judgment_display(self, game_time):
        """
        获取判定显示的文本、时间和是否超大音符
        
        返回:
            tuple: (judgment_text, judgment_time, is_super_large)
        """
        if game_time - self.judgment_time < 500:
            return self.current_judgment, self.judgment_time, self.is_super_large_note
        return None, 0, False

