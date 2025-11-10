"""
歌曲按钮类 - Song Button Class
负责单个歌曲的数据管理和UI状态

TJA 文件解析逻辑已移至 tja_parser.py
"""

from pathlib import Path
from typing import List, Dict, Tuple
from lib.tja_parser import parse_title_info, detect_difficulties, get_difficulty_stars, get_audio_info


class SongButton:
    """
    歌曲按钮类 - 封装单个歌曲的所有信息
    
    属性说明：
        tja_path: TJA文件路径
        index: 按钮索引（在列表中的位置）
        category: 歌曲分类名称
        title: 英文标题
        title_cn: 中文标题（优先显示）
        subtitle: 英文副标题
        subtitle_cn: 中文副标题（优先显示）
        difficulties: 可用难度列表 ['Easy', 'Normal', 'Hard', 'Oni', 'Edit']
        diff_stars: 难度星级字典 {难度名: 星级数}
        expanded: 是否展开显示难度选择
        selected_diff_index: 当前选中的难度索引
        y_offset: Y轴偏移量（用于动画）
    """
    
    def __init__(self, title: str, tja_path: Path, index: int, category: str = ""):
        """
        初始化歌曲按钮
        
        参数:
            title: 歌曲标题
            tja_path: TJA文件路径
            index: 按钮索引
            category: 歌曲分类名称
        """
        self.tja_path = tja_path
        self.index = index
        self.category = category  # 歌曲分类
        
        # 使用 tja_parser 模块解析 TJA 文件信息
        self.title, self.title_cn, self.subtitle, self.subtitle_cn = parse_title_info(tja_path)
        self.difficulties = detect_difficulties(tja_path)
        self.diff_stars = get_difficulty_stars(tja_path, self.difficulties)
        
        # 音频信息
        self.audio_filename, self.demo_start = get_audio_info(tja_path)
        # 获取音频文件的完整路径
        self.audio_path = tja_path.parent / self.audio_filename if self.audio_filename else None
        
        # UI状态
        self.expanded = False  # 是否展开难度选择
        
        # 缩放动画状态
        self.scale_factor = 0.85  # 当前缩放因子（0.85=小卡片，1.0=大卡片）
        self.target_scale = 0.85  # 目标缩放因子
        self.scale_animation_speed = 0.15  # 缩放动画速度（每帧变化量）
        
        # 默认选择鬼难度（Oni），如果没有则选第一个
        if 'Oni' in self.difficulties:
            self.selected_diff_index = self.difficulties.index('Oni')
        else:
            self.selected_diff_index = 0
            
        self.y_offset = 0  # 用于滚动动画的Y轴偏移
