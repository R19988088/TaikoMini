"""
配置管理模块 (Config Manager Module)
负责读取和保存游戏配置，包括分类颜色、上次选择的歌曲等
"""

import configparser
from pathlib import Path
from typing import Dict, Tuple, Optional


class ConfigManager:
    """
    配置管理器
    
    功能：
    - 读取和保存分类颜色配置
    - 记忆上次选择的歌曲
    - 管理其他游戏设置
    """
    
    def __init__(self, config_path: Path = None):
        """
        初始化配置管理器
        
        参数:
            config_path: 配置文件路径，默认为 config.ini
        """
        if config_path is None:
            config_path = Path("config.ini")
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # 确保配置文件存在
        self._ensure_config_exists()
        
        # 加载配置
        self.load_config()
    
    def _ensure_config_exists(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        if not self.config_path.exists():
            # 创建默认配置
            self.config['Paths'] = {
                'song_folder': ''
            }
            
            self.config['CategoryColors'] = {
                '流行音乐': '#42C0D2',
                'VOCALOID音乐': '#CDCFDF',
                '南梦宫原创音乐': '#FF7027',
                '动漫音乐': '#FF90D3',
                '游戏音乐': '#CC8AEA',
                '儿童音乐': '#FEC000',
                '古典音乐': '#C9C000',
                '综合音乐': '#1DC83B',
                '华语流行音乐': '#c81d21',
            }
            
            self.config['LastSelected'] = {
                'song_path': '',
                'difficulty': 'Oni',
                'category': ''
            }
            
            self.config['GameSettings'] = {
                'default_speed': '1.0',
                'auto_play': 'false'
            }
            
            self.config['DisplaySettings'] = {
                'title_font_size': '84',
                'category_font_size': '26',
                'title_outline': '3',
                'category_outline': '2',
                'use_category_image': 'true',
                'category_image_path': 'songs/Resource/genre_bg1.png'
            }
            
            # 保存默认配置
            self.save_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'utf-8-sig']
            for encoding in encodings:
                try:
                    self.config.read(self.config_path, encoding=encoding)
                    break
                except:
                    continue
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_song_folder(self) -> Optional[str]:
        """获取歌曲文件夹路径"""
        if 'Paths' in self.config:
            return self.config['Paths'].get('song_folder')
        return None

    def set_song_folder(self, path: str):
        """设置歌曲文件夹路径"""
        if 'Paths' not in self.config:
            self.config['Paths'] = {}
        self.config['Paths']['song_folder'] = path
        self.save_config()

    def get_category_info(self, category: str) -> Optional[Tuple[Optional[Tuple[int, int, int]], Optional[str], Optional[str]]]:
        """
        获取分类信息（颜色、b1图片文件名、genre_bg图片文件名）
        
        参数:
            category: 分类名称
        
        返回:
            ((R, G, B), b1_image_filename, genre_bg_image_filename) 元组，如果未找到则返回 None
            b1_image_filename 和 genre_bg_image_filename 可能为 None（表示没有图片）
            颜色现在总是返回 None，因为不再使用颜色染色
        """
        if 'CategoryColors' not in self.config:
            return None
        
        if category not in self.config['CategoryColors']:
            return None
        
        value_str = self.config['CategoryColors'][category].strip()
        
        try:
            # 新格式：(r,g,b), b1图片文件名, genre_bg图片文件名
            if ',' in value_str:
                parts = [p.strip() for p in value_str.split(',')]
                
                # 解析颜色（如果存在）
                color = None
                start_idx = 0
                if parts[0].startswith('('):
                    # 第一部分是颜色 (r, g, b)
                    # 可能需要合并前三个部分
                    if len(parts) >= 3:
                        color_str = f"{parts[0]},{parts[1]},{parts[2]}"
                        # 解析 (r, g, b)
                        color_str = color_str.strip('()')
                        color_parts = [int(x.strip()) for x in color_str.split(',')]
                        if len(color_parts) == 3:
                            color = tuple(color_parts)
                        start_idx = 3
                
                # 解析图片文件名
                b1_image_filename = parts[start_idx] if len(parts) > start_idx else None
                genre_bg_image_filename = parts[start_idx + 1] if len(parts) > start_idx + 1 else None
            else:
                # 如果只有一个值，假设是b1图片文件名
                color = None
                b1_image_filename = value_str
                genre_bg_image_filename = None
            
            return (color, b1_image_filename, genre_bg_image_filename)
        except Exception as e:
            print(f"Error parsing category info for '{category}': {e}")
            return None
        
        return None
    
    def get_category_color(self, category: str) -> Optional[Tuple[int, int, int]]:
        """
        获取分类颜色（向后兼容方法）
        
        参数:
            category: 分类名称
        
        返回:
            (R, G, B) 颜色元组，如果未找到则返回 None
        """
        info = self.get_category_info(category)
        if info:
            return info[0]  # 只返回颜色
        return None
    
    def set_category_color(self, category: str, color: Tuple[int, int, int]):
        """
        设置分类颜色
        
        参数:
            category: 分类名称
            color: (R, G, B) 颜色元组
        """
        if 'CategoryColors' not in self.config:
            self.config['CategoryColors'] = {}
        
        # 转换为十六进制格式
        color_hex = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        self.config['CategoryColors'][category] = color_hex
        self.save_config()
    
    def get_last_selected(self) -> Dict[str, str]:
        """
        获取上次选择的歌曲信息
        
        返回:
            包含 song_path, difficulty, category 的字典
        """
        if 'LastSelected' not in self.config:
            return {
                'song_path': '',
                'difficulty': 'Oni',
                'category': ''
            }
        
        return {
            'song_path': self.config['LastSelected'].get('song_path', ''),
            'difficulty': self.config['LastSelected'].get('difficulty', 'Oni'),
            'category': self.config['LastSelected'].get('category', '')
        }
    
    def set_last_selected(self, song_path: str, difficulty: str, category: str = ''):
        """
        保存上次选择的歌曲信息
        
        参数:
            song_path: 歌曲文件路径
            difficulty: 难度
            category: 分类
        """
        if 'LastSelected' not in self.config:
            self.config['LastSelected'] = {}
        
        self.config['LastSelected']['song_path'] = str(song_path)
        self.config['LastSelected']['difficulty'] = difficulty
        self.config['LastSelected']['category'] = category
        self.save_config()
    
    def get_game_setting(self, key: str, default: str = '') -> str:
        """
        获取游戏设置
        
        参数:
            key: 设置键名
            default: 默认值
        
        返回:
            设置值
        """
        if 'GameSettings' not in self.config:
            return default
        
        return self.config['GameSettings'].get(key, default)
    
    def set_game_setting(self, key: str, value: str):
        """
        设置游戏设置
        
        参数:
            key: 设置键名
            value: 设置值
        """
        if 'GameSettings' not in self.config:
            self.config['GameSettings'] = {}
        
        self.config['GameSettings'][key] = str(value)
        self.save_config()
    
    def get_display_setting(self, key: str, default: str = '') -> str:
        """
        获取显示设置
        
        参数:
            key: 设置键名
            default: 默认值
        
        返回:
            设置值
        """
        if 'DisplaySettings' not in self.config:
            return default
        
        return self.config['DisplaySettings'].get(key, default)
    
    def set_display_setting(self, key: str, value: str):
        """
        设置显示设置
        
        参数:
            key: 设置键名
            value: 设置值
        """
        if 'DisplaySettings' not in self.config:
            self.config['DisplaySettings'] = {}
        
        self.config['DisplaySettings'][key] = str(value)
        self.save_config()

