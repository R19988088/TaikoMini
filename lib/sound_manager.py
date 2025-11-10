"""
音效管理模块
Sound Manager Module

负责处理歌曲选择界面的音效，包括：
- 选择音效（咔）
- 确认音效（咚）
- 音效加载和播放
- 音效配置管理

主要类：
- SoundManager: 音效管理器，提供统一的音效控制接口
"""

import pygame
import os
from pathlib import Path
from typing import Optional, Dict


class SoundManager:
    """
    音效管理器
    Sound Manager
    
    负责处理歌曲选择界面的所有音效功能
    """
    
    def __init__(self):
        """
        初始化音效管理器
        Initialize sound manager
        """
        # ==================== 音效文件路径 ====================
        self.sounds_dir = Path("lib/res/wav")
        
        # ==================== 音效文件 ====================
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {
            'select': None,      # 选择音效（咔）- 使用 taiko_ka
            'confirm': None,     # 确认音效（咚）- 使用 taiko_don
            'pause': None,       # 暂停音效 - 使用 pause.wav
            'fast': None,        # 切换分类音效 - 使用 fast.wav
            'cancel': None       # 返回音效 - 使用 cancel.wav
        }
        
        # ==================== 音效配置 ====================
        self.enabled = True  # 音效开关
        self.volume = 0.5    # 音效音量 (0.0 - 1.0)
        
        # ==================== 加载音效 ====================
        self._load_sounds()
    
    def _load_sounds(self):
        """
        加载音效文件
        Load sound files
        """
        try:
            # ==================== 加载选择音效（咔） ====================
            # 使用游戏中的 taiko_ka 音效作为选择音效
            select_path = self.sounds_dir / "taiko_ka.wav"
            if select_path.exists():
                self.sounds['select'] = pygame.mixer.Sound(str(select_path))
                print(f"Loaded select sound (ka): {select_path}")
            else:
                print(f"Select sound (ka) not found: {select_path}")
            
            # ==================== 加载确认音效（咚） ====================
            # 使用游戏中的 taiko_don 音效作为确认音效
            confirm_path = self.sounds_dir / "taiko_don.wav"
            if confirm_path.exists():
                self.sounds['confirm'] = pygame.mixer.Sound(str(confirm_path))
                print(f"Loaded confirm sound (don): {confirm_path}")
            else:
                print(f"Confirm sound (don) not found: {confirm_path}")
            
            # ==================== 加载暂停音效 ====================
            pause_path = self.sounds_dir / "pause.wav"
            if pause_path.exists():
                self.sounds['pause'] = pygame.mixer.Sound(str(pause_path))
                print(f"Loaded pause sound: {pause_path}")
            else:
                print(f"Pause sound not found: {pause_path}")
            
            # ==================== 加载切换分类音效 ====================
            fast_path = self.sounds_dir / "fast.wav"
            if fast_path.exists():
                self.sounds['fast'] = pygame.mixer.Sound(str(fast_path))
                print(f"Loaded fast sound: {fast_path}")
            else:
                print(f"Fast sound not found: {fast_path}")
            
            # ==================== 加载返回音效 ====================
            cancel_path = self.sounds_dir / "cancel.wav"
            if cancel_path.exists():
                self.sounds['cancel'] = pygame.mixer.Sound(str(cancel_path))
                print(f"Loaded cancel sound: {cancel_path}")
            else:
                print(f"Cancel sound not found: {cancel_path}")
                
        except Exception as e:
            print(f"Error loading sounds: {e}")
    
    def play_select_sound(self):
        """
        播放选择音效（咔）
        Play select sound (click)
        """
        if not self.enabled:
            return
        
        sound = self.sounds.get('select')
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                print(f"Error playing select sound: {e}")
        else:
            # 如果没有加载到音效文件，使用系统默认音效
            self._play_fallback_sound()
    
    def play_confirm_sound(self):
        """
        播放确认音效（咚）
        Play confirm sound (don)
        """
        if not self.enabled:
            return
        
        sound = self.sounds.get('confirm')
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                print(f"Error playing confirm sound: {e}")
        else:
            # 如果没有加载到音效文件，使用系统默认音效
            self._play_fallback_sound()
    
    def play_pause_sound(self):
        """
        播放暂停音效
        Play pause sound
        """
        if not self.enabled:
            return
        
        sound = self.sounds.get('pause')
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                print(f"Error playing pause sound: {e}")
    
    def play_fast_sound(self):
        """
        播放切换分类音效
        Play fast sound
        """
        if not self.enabled:
            return
        
        sound = self.sounds.get('fast')
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                print(f"Error playing fast sound: {e}")
    
    def play_cancel_sound(self):
        """
        播放返回音效
        Play cancel sound
        """
        if not self.enabled:
            return
        
        sound = self.sounds.get('cancel')
        if sound:
            try:
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                print(f"Error playing cancel sound: {e}")
    
    def _play_fallback_sound(self):
        """
        播放备用音效（使用系统默认音效）
        Play fallback sound (using system default)
        """
        try:
            # 使用pygame的默认音效
            # 这里可以创建一个简单的音效
            pass
        except Exception as e:
            print(f"Error playing fallback sound: {e}")
    
    def set_enabled(self, enabled: bool):
        """
        设置音效开关
        Set sound enabled state
        
        Args:
            enabled: 是否启用音效
        """
        self.enabled = enabled
    
    def set_volume(self, volume: float):
        """
        设置音效音量
        Set sound volume
        
        Args:
            volume: 音量 (0.0 - 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        
        # 更新已加载音效的音量
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
    
    def is_enabled(self) -> bool:
        """
        检查音效是否启用
        Check if sound is enabled
        
        Returns:
            bool: 音效是否启用
        """
        return self.enabled
    
    def get_volume(self) -> float:
        """
        获取音效音量
        Get sound volume
        
        Returns:
            float: 当前音量
        """
        return self.volume
    
    def reload_sounds(self):
        """
        重新加载音效文件
        Reload sound files
        """
        self._load_sounds()
    
    def get_sound_info(self) -> Dict[str, bool]:
        """
        获取音效加载状态
        Get sound loading status
        
        Returns:
            Dict[str, bool]: 音效加载状态字典
        """
        return {
            'select_loaded': self.sounds['select'] is not None,
            'confirm_loaded': self.sounds['confirm'] is not None,
            'pause_loaded': self.sounds['pause'] is not None,
            'fast_loaded': self.sounds['fast'] is not None,
            'cancel_loaded': self.sounds['cancel'] is not None,
            'enabled': self.enabled,
            'volume': self.volume
        }
