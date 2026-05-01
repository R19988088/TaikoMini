"""
LRC 歌词解析模块
LRC Lyrics Parser Module

负责解析 LRC 格式的歌词文件
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


class LRCParser:
    """
    LRC 歌词解析器
    LRC Lyrics Parser
    
    解析 LRC 格式的歌词文件并提供时间同步功能
    """
    
    def __init__(self, lrc_path: Path):
        """
        初始化 LRC 解析器
        Initialize LRC parser
        
        Args:
            lrc_path: LRC 文件路径
        """
        self.lrc_path = lrc_path
        self.lyrics: List[Tuple[float, str]] = []  # (时间戳(毫秒), 歌词文本)
        self.metadata = {}  # 元数据（标题、艺术家等）
        
        if lrc_path.exists():
            self._parse_lrc()
    
    def _parse_lrc(self):
        """
        解析 LRC 文件
        Parse LRC file
        
        LRC 格式示例：
        [ti:标题]
        [ar:艺术家]
        [00:12.00]第一句歌词
        [00:17.20]第二句歌词
        """
        try:
            with open(self.lrc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析元数据标签 [ti:标题] [ar:艺术家] 等（不匹配时间戳）
                    # 元数据标签的key必须是字母开头，不能是数字
                    metadata_match = re.match(r'\[([a-zA-Z]+):(.+)\]', line)
                    if metadata_match:
                        key, value = metadata_match.groups()
                        self.metadata[key.lower()] = value.strip()
                        continue
                    
                    # 解析时间戳和歌词 [00:12.00]歌词文本
                    # 支持多种格式：[00:12.00] [00:12.000] [00:12]
                    time_matches = re.findall(r'\[(\d+):(\d+)(?:\.(\d+))?\]', line)
                    if time_matches:
                        # 提取歌词文本（去掉所有时间戳）
                        lyric_text = re.sub(r'\[\d+:\d+(?:\.\d+)?\]', '', line).strip()
                        
                        if lyric_text:  # 只添加非空歌词
                            # 一行可能有多个时间戳（同一歌词在不同时间显示）
                            for match in time_matches:
                                minutes = int(match[0])
                                seconds = int(match[1])
                                # 毫秒部分可能不存在，默认为0
                                centiseconds = int(match[2]) if match[2] else 0
                                
                                # 转换为毫秒
                                timestamp_ms = (minutes * 60 + seconds) * 1000 + centiseconds * 10
                                self.lyrics.append((timestamp_ms, lyric_text))
            
            # 按时间戳排序
            self.lyrics.sort(key=lambda x: x[0])
            
            if self.lyrics:
                print(f"[LRC] Successfully parsed {len(self.lyrics)} lyric lines")
            
        except Exception as e:
            print(f"[LRC] Failed to parse file {self.lrc_path}: {e}")
    
    def get_lyric_at_time(self, current_time_ms: float) -> Optional[str]:
        """
        获取指定时间的歌词
        Get lyric at specified time
        
        Args:
            current_time_ms: 当前时间（毫秒）
        
        Returns:
            Optional[str]: 当前应该显示的歌词文本，如果没有则返回 None
        """
        if not self.lyrics:
            return None
        
        # 找到当前时间之前最近的一句歌词
        current_lyric = None
        for timestamp, text in self.lyrics:
            if timestamp <= current_time_ms:
                current_lyric = text
            else:
                break
        
        return current_lyric
    
    def get_next_lyric_time(self, current_time_ms: float) -> Optional[float]:
        """
        获取下一句歌词的时间戳
        Get next lyric timestamp
        
        Args:
            current_time_ms: 当前时间（毫秒）
        
        Returns:
            Optional[float]: 下一句歌词的时间戳（毫秒），如果没有则返回 None
        """
        for timestamp, text in self.lyrics:
            if timestamp > current_time_ms:
                return timestamp
        return None
    
    def has_lyrics(self) -> bool:
        """
        检查是否有歌词
        Check if lyrics exist
        
        Returns:
            bool: 是否有歌词
        """
        return len(self.lyrics) > 0


def find_lrc_file(tja_path: Path) -> Optional[Path]:
    """
    查找与 TJA 文件对应的 LRC 文件
    Find LRC file corresponding to TJA file
    
    Args:
        tja_path: TJA 文件路径
    
    Returns:
        Optional[Path]: LRC 文件路径，如果不存在则返回 None
    """
    # 将 .tja 后缀替换为 .lrc
    lrc_path = tja_path.with_suffix('.lrc')
    
    if lrc_path.exists():
        return lrc_path
    
    return None

