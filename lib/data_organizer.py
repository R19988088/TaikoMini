"""
数据组织模块
Data Organizer Module

负责处理歌曲数据的组织、分类和排序，包括：
- 按文件夹自动分类歌曲
- 清理文件夹名称
- 生成排序键
- 管理分类和歌曲列表

主要类：
- DataOrganizer: 数据组织器，提供歌曲数据管理功能
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class DataOrganizer:
    """
    数据组织器
    Data Organizer
    
    负责管理歌曲数据的组织、分类和排序
    """
    
    def __init__(self):
        """
        初始化数据组织器
        Initialize data organizer
        """
        # ==================== 数据结构 ====================
        self.all_songs = []                    # 所有歌曲列表
        self.categories = []                    # 分类列表
        self.folder_songs = {}                  # 分类 -> 歌曲列表的映射
        self.folder_sort_keys = {}             # 存储排序用的原始文件夹名
    
    def organize_songs(self, songs: List[Tuple[str, Path]]) -> Tuple[List[str], Dict[str, List[Tuple[str, Path]]]]:
        """
        按文件夹组织歌曲分类
        Organize songs by folder structure
        
        分类规则：
        - 只使用songs文件夹下的第一层子文件夹作为分类
        - 例如：songs/5 南梦宫原创音乐/1 画龙/song.tja
        - 分类为：南梦宫原创音乐（去掉前面的数字）
        - 排序时使用原始文件夹名（保留数字）
        
        处理逻辑：
        1. 遍历所有歌曲路径
        2. 向上查找songs文件夹
        3. 提取songs的直接子文件夹作为分类
        4. 清理显示名称（去掉数字前缀）
        5. 按原始文件夹名排序
        
        Args:
            songs: 歌曲列表，格式为[(标题, 路径), ...]
            
        Returns:
            Tuple[List[str], Dict[str, List[Tuple[str, Path]]]]: (分类列表, 分类歌曲映射)
        """
        # ==================== 初始化数据结构 ====================
        self.all_songs = songs
        self.folder_songs = {}
        self.folder_sort_keys = {}
        
        # ==================== 遍历所有歌曲 ====================
        for title, path in songs:
            # 向上查找songs文件夹
            current = path.parent
            category_folder = None
            
            # 递归向上查找，直到找到songs文件夹
            while current:
                if current.name.lower() == 'songs':
                    # 找到songs文件夹，提取其直接子文件夹作为分类
                    # 处理路径：songs/category/subcategory/.../song.tja
                    parts = path.parts
                    songs_idx = -1
                    
                    # 查找songs在路径中的位置
                    for i, part in enumerate(parts):
                        if part.lower() == 'songs':
                            songs_idx = i
                            break
                    
                    # 提取songs的直接子文件夹
                    if songs_idx >= 0 and songs_idx + 1 < len(parts):
                        category_folder = parts[songs_idx + 1]
                        break
                
                current = current.parent
            
            # 如果没找到songs文件夹，使用直接父文件夹作为分类
            if not category_folder:
                category_folder = path.parent.name
            
            # ==================== 清理和存储 ====================
            # 清理显示名称（去掉前面的数字和空格）
            display_name = self.clean_folder_name(category_folder)
            
            # 记录原始文件夹名用于排序
            if display_name not in self.folder_sort_keys:
                self.folder_sort_keys[display_name] = category_folder
            
            # 将歌曲添加到对应分类
            if display_name not in self.folder_songs:
                self.folder_songs[display_name] = []
            self.folder_songs[display_name].append((title, path))
        
        # ==================== 排序和最终处理 ====================
        # 按原始文件夹名排序（保留数字用于排序）
        sorted_categories = sorted(self.folder_songs.keys(), 
                                  key=lambda x: self.folder_sort_keys.get(x, x))
        
        # 创建分类列表（All + 文件夹分类）
        self.categories = ["All"] + sorted_categories
        
        return self.categories, self.folder_songs
    
    def clean_folder_name(self, folder_name: str) -> str:
        """
        清理文件夹名称
        Clean folder name by removing leading numbers and spaces
        
        Args:
            folder_name: 原始文件夹名称
            
        Returns:
            清理后的文件夹名称
            
        示例：
        - "5 南梦宫原创音乐" -> "南梦宫原创音乐"
        - "1 画龙" -> "画龙"
        - "VOCALOID™音乐" -> "VOCALOID™音乐"
        """
        # 移除开头的数字、空格、下划线和连字符
        cleaned = re.sub(r'^[\d\s_-]+', '', folder_name)
        return cleaned if cleaned else folder_name
    
    def get_sort_key(self, path: Path) -> tuple:
        """
        获取排序键
        Get sort key for song ordering
        
        支持文件夹和文件名的数字前缀排序
        例如：1 画龙 -> (1, "画龙")
        
        排序规则：
        1. 先按文件夹名排序（支持数字前缀）
        2. 再按文件名排序（支持数字前缀）
        3. 没有数字前缀的排在最后
        
        Args:
            path: 歌曲文件路径
            
        Returns:
            tuple: 排序键，格式为 ((文件夹数字, 文件夹名), (文件数字, 文件名))
        """
        # ==================== 提取名称 ====================
        folder_name = path.parent.name  # 文件夹名称（父文件夹）
        file_name = path.stem           # 文件名（不含扩展名）
        
        # ==================== 数字前缀提取函数 ====================
        def extract_number_prefix(name):
            """
            提取名称中的数字前缀
            
            Args:
                name: 要处理的名称
                
            Returns:
                tuple: (数字, 名称) 或 (无穷大, 名称)
            """
            match = re.match(r'^(\d+)', name)
            if match:
                return (int(match.group(1)), name)
            return (float('inf'), name)  # 没有数字的放在后面
        
        # ==================== 生成排序键 ====================
        folder_key = extract_number_prefix(folder_name)  # 文件夹排序键
        file_key = extract_number_prefix(file_name)      # 文件排序键
        
        # 先按文件夹排序，再按文件名排序
        return (folder_key, file_key)
    
    def sort_songs(self, songs: List[Tuple[str, Path]]) -> List[Tuple[str, Path]]:
        """
        对歌曲列表进行排序
        Sort songs list using sort key
        
        Args:
            songs: 歌曲列表
            
        Returns:
            排序后的歌曲列表
        """
        return sorted(songs, key=lambda x: self.get_sort_key(x[1]))
    
    def get_songs_for_category(self, category: str) -> List[Tuple[str, Path]]:
        """
        获取指定分类的歌曲列表
        Get songs for specific category
        
        Args:
            category: 分类名称
            
        Returns:
            该分类的歌曲列表
        """
        if category == "All":
            return self.all_songs
        else:
            return self.folder_songs.get(category, [])
    
    def get_category_for_song(self, song_path: Path) -> str:
        """
        获取歌曲所属的分类
        Get category for specific song
        
        Args:
            song_path: 歌曲文件路径
            
        Returns:
            歌曲所属的分类名称
        """
        # 查找songs文件夹下的第一层文件夹作为分类
        parts = song_path.parts
        songs_idx = -1
        for j, part in enumerate(parts):
            if part.lower() == 'songs':
                songs_idx = j
                break
        
        if songs_idx >= 0 and songs_idx + 1 < len(parts):
            category_folder = parts[songs_idx + 1]
            return self.clean_folder_name(category_folder)
        else:
            return ""
    
    def get_categories(self) -> List[str]:
        """
        获取所有分类列表
        Get all categories list
        
        Returns:
            分类列表
        """
        return self.categories
    
    def get_folder_songs(self) -> Dict[str, List[Tuple[str, Path]]]:
        """
        获取分类歌曲映射
        Get folder songs mapping
        
        Returns:
            分类 -> 歌曲列表的映射
        """
        return self.folder_songs
    
    def get_all_songs(self) -> List[Tuple[str, Path]]:
        """
        获取所有歌曲列表
        Get all songs list
        
        Returns:
            所有歌曲列表
        """
        return self.all_songs
    
    def get_folder_sort_keys(self) -> Dict[str, str]:
        """
        获取文件夹排序键
        Get folder sort keys
        
        Returns:
            文件夹排序键映射
        """
        return self.folder_sort_keys
    
    def add_song(self, title: str, path: Path):
        """
        添加歌曲到数据组织器
        Add song to data organizer
        
        Args:
            title: 歌曲标题
            path: 歌曲路径
        """
        self.all_songs.append((title, path))
        # 重新组织数据
        self.organize_songs(self.all_songs)
    
    def remove_song(self, path: Path):
        """
        从数据组织器中移除歌曲
        Remove song from data organizer
        
        Args:
            path: 歌曲路径
        """
        self.all_songs = [(title, p) for title, p in self.all_songs if p != path]
        # 重新组织数据
        self.organize_songs(self.all_songs)
    
    def get_stats(self) -> Dict[str, any]:
        """
        获取数据统计信息
        Get data statistics
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_songs': len(self.all_songs),
            'total_categories': len(self.categories),
            'category_counts': {cat: len(songs) for cat, songs in self.folder_songs.items()},
            'categories': self.categories,
        }
        return stats
