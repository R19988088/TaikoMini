"""
时间管理模块 (Timing Manager Module)
管理游戏时间、速度、音频偏移等核心时间相关功能

时间类型说明：
1. real_time: 实际经过的时间，不受变速影响（用于UI动画、特效）
2. game_time: 游戏逻辑时间，受变速影响（用于音符判定）
3. audio_time: 音频播放时间
"""

import pygame

# ========================================
# 🎯 偏移配置 - 在这里调整每个速度的偏移数值
# ========================================

# 为每个播放速度单独设置偏移（毫秒）
# 正值 = 音符提前出现，负值 = 音符延后出现
SPEED_OFFSETS = {
    0.5: -0,   # 0.5x速度的偏移
    0.8: -0,   # 0.8x速度的偏移
    1.0: -0,   # 1.0x速度的偏移（正常速度）
    1.3: -0,   # 1.3x速度的偏移
    2.0: -0,   # 2.0x速度的偏移
}

# 默认偏移值（当速度不在上面列表中时使用）
DEFAULT_OFFSET = -0

# ========================================


class TimingManager:
    """
    时间管理器
    
    功能：
    - 管理游戏速度
    - 区分实时时间和游戏时间
    - 处理音频偏移（1x原始偏移和变速后的偏移）
    - 提供时间查询接口
    """
    
    def __init__(self, audio_engine, tja_offset_ms=0):
        """
        初始化时间管理器
        
        参数:
            audio_engine: 音频引擎实例
            tja_offset_ms: TJA文件中的OFFSET值（秒转毫秒）
        """
        self.audio_engine = audio_engine
        
        # 时间相关
        self.start_time = None  # 游戏开始时的系统时间
        self.pause_start_time = None  # 暂停开始时间
        self.total_paused_time = 0  # 总暂停时长
        
        # 速度设置
        self._playback_speed = 1.0
        
        # 音频偏移配置
        self.tja_offset_ms = tja_offset_ms  # TJA文件中的OFFSET（不变）
        self.speed_offsets = SPEED_OFFSETS.copy()  # 每个速度的偏移设置
        self.default_offset = DEFAULT_OFFSET  # 默认偏移
        
        # 计算得出的当前偏移
        self._current_total_offset = 0
        self._update_offset()
        
        # 暂停状态
        self._is_paused = False
    
    @property
    def playback_speed(self):
        """获取播放速度"""
        return self._playback_speed
    
    @playback_speed.setter
    def playback_speed(self, value):
        """
        设置播放速度并更新音频偏移
        """
        self._playback_speed = value
        
        # 更新音频引擎速度
        if self.audio_engine:
            self.audio_engine.playback_speed = value
        
        # 重新计算偏移
        self._update_offset()
    
    def _update_offset(self):
        """
        更新当前总偏移
        
        计算逻辑：
        - TJA的OFFSET保持不变
        - 根据当前速度查找对应的偏移值
        """
        # TJA偏移（不受变速影响）
        tja_part = self.tja_offset_ms
        
        # 查找当前速度的偏移值
        # 四舍五入到0.1精度以匹配配置
        speed_key = round(self._playback_speed, 1)
        
        if speed_key in self.speed_offsets:
            # 使用配置的偏移值
            speed_offset = self.speed_offsets[speed_key]
        else:
            # 使用默认偏移值
            speed_offset = self.default_offset
            print(f"⚠️ 速度 {speed_key}x 未配置偏移，使用默认值: {self.default_offset}ms")
        
        self._current_total_offset = tja_part + speed_offset
    
    def start(self):
        """启动计时"""
        self.start_time = pygame.time.get_ticks()
        self.total_paused_time = 0
        self._is_paused = False
    
    def pause(self):
        """暂停"""
        if not self._is_paused:
            self._is_paused = True
            self.pause_start_time = pygame.time.get_ticks()
            
            if self.audio_engine:
                self.audio_engine.pause()
    
    def unpause(self):
        """恢复"""
        if self._is_paused:
            self._is_paused = False
            
            # 累计暂停时长
            if self.pause_start_time:
                self.total_paused_time += pygame.time.get_ticks() - self.pause_start_time
                self.pause_start_time = None
            
            if self.audio_engine:
                self.audio_engine.unpause()
    
    def get_real_time(self):
        """
        获取实时时间（不受变速影响）
        
        用途：UI动画、击打特效等视觉效果
        
        返回:
            int: 从游戏开始到现在的实际毫秒数（扣除暂停时间）
        """
        if not self.start_time:
            return 0
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # 扣除暂停时间
        if self._is_paused and self.pause_start_time:
            paused = self.total_paused_time + (current_time - self.pause_start_time)
        else:
            paused = self.total_paused_time
        
        return elapsed - paused
    
    def get_game_time(self):
        """
        获取游戏时间（用于音符判定）
        
        这个时间是从音频引擎获取的，已经考虑了变速。
        同时会应用音频偏移。
        
        返回:
            float: 游戏逻辑时间（毫秒）
        """
        if not self.audio_engine or self._is_paused:
            # 暂停时返回暂停时的时间
            if hasattr(self, '_paused_game_time'):
                return self._paused_game_time
            return 0
        
        # 获取音频时间并应用总偏移
        audio_time = self.audio_engine.get_time_ms()
        game_time = audio_time + self._current_total_offset
        
        # 保存当前时间，用于暂停时返回
        self._paused_game_time = game_time
        
        return game_time
    
    def get_audio_time(self):
        """
        获取音频播放时间
        
        返回:
            float: 音频播放位置（毫秒）
        """
        if self.audio_engine:
            return self.audio_engine.get_time_ms()
        return 0
    
    def is_paused(self):
        """是否暂停"""
        return self._is_paused
    
    def reset(self):
        """重置时间管理器"""
        self.start_time = None
        self.pause_start_time = None
        self.total_paused_time = 0
        self._is_paused = False
        self._paused_game_time = 0
    
    def set_speed_offset(self, speed, offset_ms):
        """
        设置特定速度的偏移值
        
        参数:
            speed: 播放速度（如 1.0, 0.5, 2.0）
            offset_ms: 偏移量（毫秒）
                      正值 = 音符提前出现
                      负值 = 音符延后出现
        """
        speed_key = round(speed, 1)
        self.speed_offsets[speed_key] = offset_ms
        print(f"✅ 已设置 {speed_key}x 速度偏移: {offset_ms}ms")
        
        # 如果是当前速度，立即更新
        if abs(self._playback_speed - speed) < 0.01:
            self._update_offset()
    
    def get_current_speed_offset(self):
        """
        获取当前速度的偏移值
        
        返回:
            int: 当前速度对应的偏移值（毫秒）
        """
        speed_key = round(self._playback_speed, 1)
        return self.speed_offsets.get(speed_key, self.default_offset)
    
    def get_offset_info(self):
        """
        获取偏移信息（调试用）
        
        返回:
            dict: 包含各种偏移信息
        """
        speed_key = round(self._playback_speed, 1)
        current_speed_offset = self.get_current_speed_offset()
        
        return {
            'tja_offset': self.tja_offset_ms,
            'playback_speed': self._playback_speed,
            'current_speed_offset': current_speed_offset,
            'current_total_offset': self._current_total_offset,
            'all_speed_offsets': self.speed_offsets,
            'formula': f'{self.tja_offset_ms} (TJA) + {current_speed_offset} ({speed_key}x速度) = {self._current_total_offset}ms'
        }

