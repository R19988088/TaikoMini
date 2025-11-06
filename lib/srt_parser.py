"""
SRT 字幕解析模块
SRT Subtitle Parser Module

负责解析 SRT 格式的字幕文件（带时间范围）
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


class SRTParser:
    """
    SRT 字幕解析器
    SRT Subtitle Parser
    
    解析 SRT 格式的字幕文件并提供时间同步功能
    SRT格式支持开始和结束时间，比LRC更适合歌词显示
    """
    
    def __init__(self, srt_path: Path):
        """
        初始化 SRT 解析器
        Initialize SRT parser
        
        Args:
            srt_path: SRT 文件路径
        """
        self.srt_path = srt_path
        self.subtitles: List[Tuple[float, float, str]] = []  # (开始时间(ms), 结束时间(ms), 文本)
        
        if srt_path.exists():
            self._parse_srt()
    
    def _parse_time(self, time_str: str) -> float:
        """
        解析 SRT 时间格式为毫秒
        Parse SRT time format to milliseconds
        
        Args:
            time_str: 时间字符串，格式如 "00:00:12,000"
        
        Returns:
            float: 时间戳（毫秒）
        """
        # SRT 格式: HH:MM:SS,mmm
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str.strip())
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4))
            
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
            return total_ms
        return 0.0
    
    def _parse_srt(self):
        """
        解析 SRT 文件
        Parse SRT file
        
        SRT 格式示例：
        1
        00:00:12,000 --> 00:00:15,123
        第一句歌词
        
        2
        00:00:15,500 --> 00:00:18,000
        第二句歌词
        """
        try:
            with open(self.srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割字幕块（用空行分隔）
            subtitle_blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # 第一行：序号（跳过）
                # 第二行：时间范围
                time_line = lines[1]
                time_match = re.match(r'(.+?)\s*-->\s*(.+)', time_line)
                
                if time_match:
                    start_time_str = time_match.group(1)
                    end_time_str = time_match.group(2)
                    
                    start_time = self._parse_time(start_time_str)
                    end_time = self._parse_time(end_time_str)
                    
                    # 第三行及以后：字幕文本（可能多行）
                    subtitle_text = '\n'.join(lines[2:]).strip()
                    
                    if subtitle_text:
                        self.subtitles.append((start_time, end_time, subtitle_text))
            
            # 按开始时间排序
            self.subtitles.sort(key=lambda x: x[0])
            
            if self.subtitles:
                print(f"[SRT] Successfully parsed {len(self.subtitles)} subtitle entries")
            
        except Exception as e:
            print(f"[SRT] Failed to parse file {self.srt_path}: {e}")
    
    def get_lyric_at_time(self, current_time_ms: float) -> Optional[str]:
        """
        获取指定时间的字幕
        Get subtitle at specified time
        
        Args:
            current_time_ms: 当前时间（毫秒）
        
        Returns:
            Optional[str]: 当前应该显示的字幕文本，如果没有则返回 None
        """
        if not self.subtitles:
            return None
        
        # 找到当前时间范围内的字幕
        for start_time, end_time, text in self.subtitles:
            if start_time <= current_time_ms <= end_time:
                return text
        
        return None
    
    def get_next_lyric_time(self, current_time_ms: float) -> Optional[float]:
        """
        获取下一句字幕的开始时间
        Get next subtitle start time
        
        Args:
            current_time_ms: 当前时间（毫秒）
        
        Returns:
            Optional[float]: 下一句字幕的开始时间（毫秒），如果没有则返回 None
        """
        for start_time, end_time, text in self.subtitles:
            if start_time > current_time_ms:
                return start_time
        return None
    
    def get_current_lyric_end_time(self, current_time_ms: float) -> Optional[float]:
        """
        获取当前字幕的结束时间
        Get current subtitle end time
        
        Args:
            current_time_ms: 当前时间（毫秒）
        
        Returns:
            Optional[float]: 当前字幕的结束时间（毫秒），如果没有则返回 None
        """
        for start_time, end_time, text in self.subtitles:
            if start_time <= current_time_ms <= end_time:
                return end_time
        return None
    
    def has_lyrics(self) -> bool:
        """
        检查是否有字幕
        Check if subtitles exist
        
        Returns:
            bool: 是否有字幕
        """
        return len(self.subtitles) > 0


def find_srt_file(tja_path: Path) -> Optional[Path]:
    """
    查找与 TJA 文件对应的 SRT 文件
    Find SRT file corresponding to TJA file
    
    Args:
        tja_path: TJA 文件路径
    
    Returns:
        Optional[Path]: SRT 文件路径，如果不存在则返回 None
    """
    # 将 .tja 后缀替换为 .srt
    srt_path = tja_path.with_suffix('.srt')
    
    if srt_path.exists():
        return srt_path
    
    return None

