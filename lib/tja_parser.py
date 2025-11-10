"""
TJA 文件解析器
TJA File Parser

负责解析 TJA 文件的元数据信息
包括：标题、副标题、难度、星级等
"""

from pathlib import Path
from typing import Tuple, List, Dict


# ==================== TJA 文件解析函数 ====================

def parse_title_info(tja_path: Path) -> Tuple[str, str, str, str]:
    """
    从 TJA 文件解析标题信息
    
    参数:
        tja_path: TJA 文件路径
    
    返回:
        (title, title_cn, subtitle, subtitle_cn) 元组
        - title: 英文标题
        - title_cn: 中文标题
        - subtitle: 英文副标题
        - subtitle_cn: 中文副标题
    
    说明:
        1. 支持多种编码：utf-8, shift-jis, gbk, cp932
        2. 优先使用 TITLECN 和 SUBTITLECN（中文版本）
        3. 自动清理副标题的前导 "--" 符号
    """
    title = tja_path.stem  # 默认使用文件名
    title_cn = None
    subtitle = ""
    subtitle_cn = None
    
    # 尝试多种编码读取
    encodings = ['utf-8', 'shift-jis', 'gbk', 'cp932', 'utf-8-sig']
    for encoding in encodings:
        try:
            with open(tja_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    # 解析标题字段
                    if line.startswith('TITLE:'):
                        title = line[6:].strip()
                    elif line.startswith('TITLECN:') or line.startswith('TITLEcn:'):
                        title_cn = line[8:].strip()
                    elif line.startswith('SUBTITLE:'):
                        subtitle = line[9:].strip()
                    elif line.startswith('SUBTITLECN:') or line.startswith('SUBTITLEcn:'):
                        subtitle_cn = line[11:].strip()
                    # 遇到谱面数据就停止（元数据都在文件开头）
                    if line.startswith('#START'):
                        break
            break  # 成功读取就退出
        except:
            continue  # 尝试下一个编码
    
    # 清理副标题
    subtitle = _clean_subtitle(subtitle)
    subtitle_cn = _clean_subtitle(subtitle_cn)
    
    return title, title_cn, subtitle, subtitle_cn


def detect_difficulties(tja_path: Path) -> List[str]:
    """
    检测 TJA 文件中的可用难度
    
    参数:
        tja_path: TJA 文件路径
    
    返回:
        难度列表，例如 ['Easy', 'Normal', 'Hard', 'Oni']
    
    难度编号映射:
        0 或 EASY   = Easy（简单）
        1 或 NORMAL = Normal（普通）
        2 或 HARD   = Hard（困难）
        3 或 ONI    = Oni（鬼）
        4 或 EDIT/URA = Edit（裏/编辑）
    """
    found_difficulties = set()
    encodings = ['utf-8', 'shift-jis', 'gbk', 'cp932', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(tja_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip().upper()
                    if line.startswith('COURSE:'):
                        course_val = line.split(':', 1)[1].strip()
                        # 检测各种难度
                        if course_val in ['EASY', '0']:
                            found_difficulties.add('Easy')
                        elif course_val in ['NORMAL', '1']:
                            found_difficulties.add('Normal')
                        elif course_val in ['HARD', '2']:
                            found_difficulties.add('Hard')
                        elif course_val in ['ONI', '3']:
                            found_difficulties.add('Oni')
                        elif course_val in ['EDIT', 'URA', '4']:
                            found_difficulties.add('Edit')
            break  # 成功读取就退出
        except:
            continue
    
    # 按固定顺序返回
    ordered = []
    for diff in ['Easy', 'Normal', 'Hard', 'Oni']:
        if diff in found_difficulties:
            ordered.append(diff)
    # Edit/Ura 放在最后
    if 'Edit' in found_difficulties:
        ordered.append('Edit')
    
    # 如果没有检测到任何难度，返回默认值
    return ordered if ordered else ['Normal']


def get_difficulty_stars(tja_path: Path, difficulties: List[str]) -> Dict[str, int]:
    """
    获取每个难度的星级评定
    
    参数:
        tja_path: TJA 文件路径
        difficulties: 已检测到的难度列表
    
    返回:
        难度星级字典，例如 {'Easy': 3, 'Normal': 5, 'Hard': 7, 'Oni': 9}
    
    说明:
        星级范围通常为 1-10
        从 TJA 文件的 LEVEL: 字段读取
    """
    stars = {}
    encodings = ['utf-8', 'shift-jis', 'gbk', 'cp932', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(tja_path, 'r', encoding=encoding) as f:
                current_course = None
                for line in f:
                    line = line.strip()
                    # 检测当前课程（难度）
                    if line.startswith('COURSE:'):
                        course_val = line.split(':')[1].strip().upper()
                        if course_val in ['EASY', '0']:
                            current_course = 'Easy'
                        elif course_val in ['NORMAL', '1']:
                            current_course = 'Normal'
                        elif course_val in ['HARD', '2']:
                            current_course = 'Hard'
                        elif course_val in ['ONI', '3']:
                            current_course = 'Oni'
                        elif course_val in ['EDIT', 'URA', '4']:
                            current_course = 'Edit'
                    # 检测星级
                    elif line.startswith('LEVEL:') and current_course:
                        try:
                            level = int(line.split(':')[1].strip())
                            stars[current_course] = level
                        except:
                            stars[current_course] = 5  # 解析失败时的默认星级
            break
        except:
            continue
    
    # 为所有难度设置默认星级（如果没有读取到）
    for diff in difficulties:
        if diff not in stars:
            stars[diff] = 5
    
    return stars


# ==================== 辅助函数 Helper Functions ====================

def get_audio_info(tja_path: Path) -> Tuple[str, float]:
    """
    获取音频文件信息
    
    参数:
        tja_path: TJA 文件路径
    
    返回:
        (audio_filename, demo_start) 元组
        - audio_filename: 音频文件名（从WAVE字段读取）
        - demo_start: 预览开始时间（秒），从DEMOSTART字段读取
    
    说明:
        如果没有DEMOSTART字段，默认从60秒开始预览
    """
    audio_filename = ""
    demo_start = 60.0  # 默认从60秒开始
    
    encodings = ['utf-8', 'shift-jis', 'gbk', 'cp932', 'utf-8-sig']
    for encoding in encodings:
        try:
            with open(tja_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    # 读取WAVE字段
                    if line.startswith('WAVE:'):
                        audio_filename = line[5:].strip()
                    # 读取DEMOSTART字段
                    elif line.startswith('DEMOSTART:'):
                        try:
                            demo_start = float(line[10:].strip())
                        except ValueError:
                            demo_start = 60.0
                    # 遇到谱面数据就停止
                    if line.startswith('#START'):
                        break
            break
        except:
            continue
    
    return audio_filename, demo_start


def _clean_subtitle(subtitle: str) -> str:
    """
    清理副标题字符串
    
    参数:
        subtitle: 原始副标题
    
    返回:
        清理后的副标题
    
    规则:
        1. 移除前导的 "--" 符号
        2. 如果只剩下 "--" 或空字符串，返回空
    """
    if not subtitle:
        return ""
    
    subtitle = subtitle.strip()
    
    # 移除所有前导的 "--"
    while subtitle.startswith('--'):
        subtitle = subtitle[2:].strip()
    
    # 如果只剩下 "--" 或空，返回空字符串
    if subtitle == '--' or not subtitle:
        return ""
    
    return subtitle

