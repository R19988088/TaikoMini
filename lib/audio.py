"""
TaikoMini Audio Engine
Handles audio loading, playback, and real-time speed changes.
Uses FFmpeg for audio processing with intelligent caching.
Uses pygame.mixer.music for proper pause/resume support.
"""
import pygame
import numpy as np
import threading
import time
import subprocess
import tempfile
import os
import hashlib
import json

class AudioEngine:
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.master_volume = 1.0
        self.playback_speed = 1.0
        self._is_playing = False
        self._paused = False
        self._use_music = True  # 使用pygame.mixer.music而不是Sound
        self._current_audio_file = None  # 当前加载的音频文件路径
        self._play_pos_ms = 0
        self._last_update_time = 0
        self._audio_length_ms = 0
        self._speed_start_time = 0
        self._speed_start_pos = 0
        self._audio_path = None
        
        # 独立游戏计时器系统
        self._game_time_ms = 0.0  # 游戏内部时间（独立于系统时钟）
        self._last_update_ticks = 0  # 上次更新时的系统时间
        self._ffmpeg_available = False
        self._processed_audio_cache = {}
        self._cache_dir = None
        self._processing_thread = None
        self._stop_processing = False

    def load_sound(self, audio_path: str):
        """Loads a sound from a file path."""
        try:
            # Store the audio path for later use
            self._audio_path = audio_path
            
            # Create cache directory
            self._cache_dir = os.path.join(tempfile.gettempdir(), "taiko_audio_cache")
            os.makedirs(self._cache_dir, exist_ok=True)
            
            # Check if FFmpeg is available
            self._check_ffmpeg()
            
            # Load original audio to get length
            temp_sound = pygame.mixer.Sound(audio_path)
            self._audio_length_ms = int(temp_sound.get_length() * 1000)
            
            try:
                print(f"Audio loaded: {audio_path} ({self._audio_length_ms}ms)")
            except UnicodeEncodeError:
                print(f"Audio loaded (path contains special characters): {self._audio_length_ms}ms")
            if self._ffmpeg_available:
                print("FFmpeg available - intelligent audio speed change enabled")
            else:
                print("FFmpeg not available - using time-based speed simulation")
            return True
        except Exception as e:
            try:
                print(f"Error loading audio: {e}")
            except UnicodeEncodeError:
                print(f"Error loading audio (contains special characters)")
            self._audio_path = None
            return False

    def play(self):
        """Starts playback from the beginning."""
        if self._audio_path is None:
            return
        
        self.stop() # Stop any currently playing sound
        self._play_pos_ms = 0
        self._is_playing = True
        self._paused = False
        current_ticks = pygame.time.get_ticks()
        self._last_update_time = current_ticks
        self._speed_start_time = current_ticks
        self._speed_start_pos = 0
        
        # 初始化独立游戏计时器
        self._game_time_ms = 0.0
        self._last_update_ticks = current_ticks
        
        # Load audio for current speed
        audio_file = self._load_speed_variant()
        
        # Start playback using pygame.mixer.music
        if audio_file and os.path.exists(audio_file):
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.set_volume(self.master_volume)
                pygame.mixer.music.play()
                print(f"Audio started playing at speed: {self.playback_speed}x")
            except Exception as e:
                # 使用 repr 避免 gbk 编码错误
                print(f"Error playing audio: {repr(e)}")
                self._is_playing = False

    def stop(self):
        """Stops playback completely."""
        self._stop_processing = True
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)
        
        pygame.mixer.music.stop()
        self._is_playing = False
        self._paused = False
        self._play_pos_ms = 0
        self._speed_start_pos = 0

    def set_speed(self, speed: float):
        """Sets the playback speed."""
        old_speed = self.playback_speed
        self.playback_speed = max(0.1, min(3.0, speed))  # Limit to reasonable range
        
        # Note: This method is now only called before playback starts
        # Speed changes during playback will trigger a restart in game.py
        print(f"Speed set to: {self.playback_speed}x")
    
    def change_speed_seamless(self, new_speed):
        """
        无缝切换播放速度（尽可能保持当前播放位置）
        
        参数:
            new_speed: 新的播放速度
        
        返回:
            bool: 是否成功切换
        """
        if not self._is_playing:
            self.playback_speed = new_speed
            return True
        
        # 保存当前状态
        was_paused = self._paused
        current_pos = self._play_pos_ms
        
        print(f"[SPEED] Switching: {self.playback_speed}x -> {new_speed}x (pos: {current_pos:.0f}ms)")
        
        # 更新速度
        old_speed = self.playback_speed
        self.playback_speed = new_speed
        
        # 停止当前播放
        pygame.mixer.music.stop()
        
        # 加载新速度的音频文件
        audio_file = self._load_speed_variant()
        
        if not audio_file or not os.path.exists(audio_file):
            print(f"[ERROR] Unable to load audio at {new_speed}x speed")
            self.playback_speed = old_speed
            return False
        
        try:
            # 加载新音频文件
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.set_volume(self.master_volume)
            
            # 从当前位置继续播放
            self._play_pos_ms = current_pos
            current_ticks = pygame.time.get_ticks()
            self._speed_start_time = current_ticks
            self._speed_start_pos = current_pos
            
            # 重置独立游戏计时器
            self._game_time_ms = float(current_pos)
            self._last_update_ticks = current_ticks
            
            # 开始播放
            pygame.mixer.music.play()
            
            # 如果之前是暂停状态，立即暂停
            if was_paused:
                pygame.mixer.music.pause()
            
            print(f"[OK] Speed changed: {new_speed}x")
            return True
            
        except Exception as e:
            print(f"[ERROR] Speed change failed: {e}")
            self.playback_speed = old_speed
            return False

    def set_volume(self, volume: float):
        """Sets the master volume (0.0 to 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.master_volume)

    def pause(self):
        """Pauses playback - 使用pygame.mixer.music的真正暂停功能."""
        if self._is_playing and not self._paused:
            self._paused = True
            # 更新到暂停时的准确位置
            self._update_play_position()
            # 保存暂停时间
            self._pause_system_time = pygame.time.get_ticks()
            
            # 使用pygame.mixer.music的暂停功能
            pygame.mixer.music.pause()
            
            print(f"Paused at: {self._play_pos_ms:.0f}ms")

    def unpause(self):
        """Resumes playback - 使用pygame.mixer.music的恢复功能."""
        if self._is_playing and self._paused:
            self._paused = False
            
            # 计算暂停持续时间
            pause_duration = pygame.time.get_ticks() - self._pause_system_time
            
            # 调整时间基准，补偿暂停时间
            self._speed_start_time += pause_duration
            
            # 使用pygame.mixer.music的恢复功能
            pygame.mixer.music.unpause()
            
            print(f"Resumed playback (paused for {pause_duration}ms)")

    def seek(self, position_ms: float):
        """Seeks to a specific position in milliseconds."""
        if self._audio_path is None:
            return
        
        # Stop current playback
        self.stop()
        
        # Set new position
        self._play_pos_ms = max(0, min(position_ms, self._audio_length_ms))
        
        # Restart playback from new position
        self._is_playing = True
        self._paused = False
        current_ticks = pygame.time.get_ticks()
        self._last_update_time = current_ticks
        self._speed_start_time = current_ticks
        self._speed_start_pos = self._play_pos_ms
        
        # 重置独立游戏计时器
        self._game_time_ms = float(self._play_pos_ms)
        self._last_update_ticks = current_ticks
        
        # Load audio for current speed
        self._load_speed_variant()
        
        # Start playback
        if self._sound_object:
            self._sound_object.play()
            print(f"Audio seeked to {position_ms:.2f}ms at speed: {self.playback_speed}x")

    def get_time_ms(self) -> float:
        """Gets the current playback position in milliseconds."""
        if self._is_playing and not self._paused:
            self._update_play_position()
        return self._play_pos_ms

    def is_busy(self) -> bool:
        """Checks if audio is currently playing."""
        # Check if pygame.mixer.music is still playing
        if self._is_playing and not self._paused:
            if not pygame.mixer.music.get_busy():
                # Audio finished playing
                self._is_playing = False
        
        # Also check if we have reached the end by time
        if self._is_playing and self._play_pos_ms >= self._audio_length_ms:
            self._is_playing = False
        
        return self._is_playing

    def _check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            self._ffmpeg_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._ffmpeg_available = False

    def _get_cache_path(self, speed_key):
        """Get cache file path for a specific speed."""
        # Create hash of audio file path for unique cache key
        audio_hash = hashlib.md5(self._audio_path.encode()).hexdigest()[:8]
        cache_filename = f"audio_{audio_hash}_speed_{speed_key}.wav"
        return os.path.join(self._cache_dir, cache_filename)

    def _load_speed_variant(self):
        """Loads or creates a speed variant of the audio. Returns the file path."""
        if self._audio_path is None:
            return None
        
        # Round speed to nearest 0.1 for caching
        speed_key = round(self.playback_speed, 1)
        
        if speed_key == 1.0:
            # Use original audio
            self._current_audio_file = self._audio_path
            return self._audio_path
        
        # Check cache first
        cache_path = self._get_cache_path(speed_key)
        if os.path.exists(cache_path):
            print(f"[OK] Loaded cached speed variant: {speed_key}x")
            self._current_audio_file = cache_path
            return cache_path
        
        if self._ffmpeg_available:
            # Create speed variant using FFmpeg
            success = self._create_ffmpeg_speed_variant(speed_key, cache_path)
            if success:
                self._current_audio_file = cache_path
                return cache_path
        
        # Fallback: use original audio
        print(f"[WARN] Using original audio for speed {speed_key}x (FFmpeg not available)")
        self._current_audio_file = self._audio_path
        return self._audio_path

    def _create_ffmpeg_speed_variant(self, speed_key, cache_path):
        """Creates a speed variant using FFmpeg. Returns True on success."""
        try:
            # Use FFmpeg to change speed with pitch preservation
            # For speeds > 2.0 or < 0.5, chain multiple atempo filters
            if speed_key > 2.0:
                # Split into multiple atempo filters (max 2.0 each)
                filters = []
                remaining = speed_key
                while remaining > 2.0:
                    filters.append("atempo=2.0")
                    remaining /= 2.0
                filters.append(f"atempo={remaining}")
                filter_str = ",".join(filters)
            elif speed_key < 0.5:
                # Split into multiple atempo filters (min 0.5 each)
                filters = []
                remaining = speed_key
                while remaining < 0.5:
                    filters.append("atempo=0.5")
                    remaining /= 0.5
                filters.append(f"atempo={remaining}")
                filter_str = ",".join(filters)
            else:
                filter_str = f"atempo={speed_key}"
            
            cmd = [
                "ffmpeg", "-i", self._audio_path,
                "-filter:a", filter_str,
                "-codec:a", "pcm_s16le",  # Uncompressed PCM (no encoding delay)
                "-ar", "44100",  # Sample rate
                "-ac", "2",  # Stereo
                "-y", cache_path
            ]
            
            print(f"[INFO] Generating speed variant: {speed_key}x...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and os.path.exists(cache_path):
                print(f"[OK] Created speed variant: {speed_key}x")
                return True
            else:
                print(f"[ERROR] FFmpeg failed for speed {speed_key}x")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"[ERROR] Error creating speed variant: {repr(e)}")
            return False
    
    def pregenerate_speed_variants(self, speeds, callback=None):
        """Pre-generate speed variants in background thread."""
        if not self._ffmpeg_available or not self._audio_path:
            return
        
        def generate_worker():
            for speed in speeds:
                if self._stop_processing:
                    break
                    
                speed_key = round(speed, 1)
                if speed_key == 1.0:
                    continue  # Skip original
                
                cache_path = self._get_cache_path(speed_key)
                if os.path.exists(cache_path):
                    print(f"Speed variant {speed_key}x already cached")
                    if callback:
                        callback(speed_key, True)
                    continue
                
                # Generate the variant
                try:
                    if speed_key > 2.0:
                        filters = []
                        remaining = speed_key
                        while remaining > 2.0:
                            filters.append("atempo=2.0")
                            remaining /= 2.0
                        filters.append(f"atempo={remaining}")
                        filter_str = ",".join(filters)
                    elif speed_key < 0.5:
                        filters = []
                        remaining = speed_key
                        while remaining < 0.5:
                            filters.append("atempo=0.5")
                            remaining /= 0.5
                        filters.append(f"atempo={remaining}")
                        filter_str = ",".join(filters)
                    else:
                        filter_str = f"atempo={speed_key}"
                    
                    cmd = [
                        "ffmpeg", "-i", self._audio_path,
                        "-filter:a", filter_str,
                        "-codec:a", "pcm_s16le",  # Uncompressed PCM (no encoding delay)
                        "-ar", "44100",  # Sample rate
                        "-ac", "2",  # Stereo
                        "-y", cache_path
                    ]
                    
                    print(f"Pre-generating {speed_key}x speed variant...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
                    
                    if result.returncode == 0 and os.path.exists(cache_path):
                        print(f"Pre-generated {speed_key}x")
                        if callback:
                            callback(speed_key, True)
                    else:
                        print(f"Failed to generate {speed_key}x")
                        if callback:
                            callback(speed_key, False)
                except Exception as e:
                    print(f"Error generating {speed_key}x: {e}")
                    if callback:
                        callback(speed_key, False)
        
        self._stop_processing = False
        self._processing_thread = threading.Thread(target=generate_worker, daemon=True)
        self._processing_thread.start()

    def _update_play_position(self):
        """Internal method to update the playback position using independent game timer."""
        if not self._is_playing or self._paused:
            return
        
        # 获取当前系统时间
        current_ticks = pygame.time.get_ticks()
        
        # 计算自上次更新以来的实际时间增量（毫秒）
        if self._last_update_ticks == 0:
            self._last_update_ticks = current_ticks
            self._game_time_ms = self._speed_start_pos
            return
        
        # 计算实际经过的时间
        delta_ticks = current_ticks - self._last_update_ticks
        
        # 防止delta_ticks为0导致的问题
        if delta_ticks <= 0:
            return
        
        self._last_update_ticks = current_ticks
        
        # 使用实际增量更新游戏时间（保证速度正确）
        time_increment = delta_ticks * self.playback_speed
        self._game_time_ms += time_increment
        
        # 更新播放位置
        self._play_pos_ms = self._game_time_ms
        
        # Check if we've reached the end
        if self._play_pos_ms >= self._audio_length_ms:
            self._play_pos_ms = self._audio_length_ms
            self._is_playing = False

    def clear_cache(self):
        """Clears the audio cache."""
        if self._cache_dir and os.path.exists(self._cache_dir):
            try:
                import shutil
                shutil.rmtree(self._cache_dir)
                os.makedirs(self._cache_dir, exist_ok=True)
                print("Audio cache cleared")
            except Exception as e:
                print(f"Error clearing cache: {e}")

    def __del__(self):
        """Cleanup when object is destroyed."""
        self._stop_processing = True
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)