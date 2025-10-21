"""
资源加载模块
Resource Loader Module

负责加载游戏中的各种资源文件，包括：
- 难度图标图片
- 按钮背景图片
- 字体文件
- 其他UI资源

主要类：
- ResourceLoader: 资源加载器，提供统一的资源加载接口
"""

import pygame
from pathlib import Path
from typing import Dict, Optional, Tuple


class ResourceLoader:
    """
    资源加载器
    Resource Loader
    
    负责加载和管理游戏中的所有资源文件
    """
    
    def __init__(self):
        """
        初始化资源加载器
        Initialize resource loader
        """
        # ==================== 资源路径 ====================
        self.res_path = Path(__file__).parent / 'res'
        self.texture_path = self.res_path / 'Texture' / 'selectsongs'
        self.font_path = self.res_path / 'FZPangWaUltra-Regular.ttf'
        self.custom_resource_path = Path("songs/Resource")  # 自定义资源文件夹
        
        # ==================== 缓存 ====================
        self._diff_images_cache = None      # 难度图标缓存
        self._bg_images_cache = None       # 背景图片缓存
        self._fonts_cache = {}             # 字体缓存
        
        # ==================== 图标尺寸设置 ====================
        self.target_height = 45  # 统一图标高度，保持宽高比
    
    def load_difficulty_images(self) -> Dict[str, pygame.Surface]:
        """
        加载难度图标和返回按钮图片
        Load difficulty images and back buttons
        
        加载内容：
        1. 难度图标 (lv_1.png 到 lv_5.png)
        2. 难度图标的灰度版本（用于不存在的难度）
        3. 返回按钮 (back_1.png, back_2.png)
        
        处理逻辑：
        1. 统一图标高度为45像素
        2. 保持宽高比缩放
        3. 为每个难度图标创建灰度版本
        4. 处理加载失败的情况
        
        Returns:
            Dict[str, pygame.Surface]: 图片字典，键为图片名称，值为pygame表面
        """
        # 使用缓存避免重复加载
        if self._diff_images_cache is not None:
            return self._diff_images_cache
        
        images = {}
        
        # ==================== 加载难度图标 ====================
        # Load images for difficulty levels 1-5
        for i in range(1, 6):
            img_path = self.texture_path / f'lv_{i}.png'
            if img_path.exists():
                try:
                    # 加载原始图片
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    
                    # 保持宽高比缩放
                    orig_w, orig_h = img.get_size()
                    scale = self.target_height / orig_h
                    new_w = int(orig_w * scale)
                    img = pygame.transform.smoothscale(img, (new_w, self.target_height))
                    images[i] = img
                    
                    # ==================== 创建灰度版本 ====================
                    # 创建黑白版本（用于缺失的难度）
                    gray_img = img.copy()
                    arr = pygame.surfarray.pixels3d(gray_img)
                    # 使用标准灰度转换公式
                    gray = (arr[:,:,0] * 0.299 + arr[:,:,1] * 0.587 + arr[:,:,2] * 0.114).astype('uint8')
                    arr[:,:,0] = gray
                    arr[:,:,1] = gray
                    arr[:,:,2] = gray
                    del arr
                    images[f'{i}_gray'] = gray_img
                    
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
        
        # ==================== 加载返回按钮 ====================
        # Load back button images
        for name in ['back_1', 'back_2']:
            img_path = self.texture_path / f'{name}.png'
            if img_path.exists():
                try:
                    # 加载返回按钮图片
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    
                    # 保持宽高比缩放
                    orig_w, orig_h = img.get_size()
                    scale = self.target_height / orig_h
                    new_w = int(orig_w * scale)
                    img = pygame.transform.smoothscale(img, (new_w, self.target_height))
                    images[name] = img
                    
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
        
        # 缓存结果
        self._diff_images_cache = images
        return images
    
    def load_background_images(self) -> Dict[str, pygame.Surface]:
        """
        加载歌曲按钮背景图片
        Load song button background images
        
        加载内容：
        1. big_1.png - 主背景图片
        2. big_2.png - 发光背景图片
        3. big_3.png - 信息背景图片
        
        用途：
        - big_1: 按钮主体背景
        - big_2: 选中时的发光效果
        - big_3: 歌曲信息显示区域背景
        
        Returns:
            Dict[str, pygame.Surface]: 背景图片字典
        """
        # 使用缓存避免重复加载
        if self._bg_images_cache is not None:
            return self._bg_images_cache
        
        images = {}
        
        # ==================== 加载背景图片 ====================
        for i in [1, 2, 3]:
            img_path = self.texture_path / f'big_{i}.png'
            if img_path.exists():
                try:
                    # 加载背景图片，保持透明度
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    images[i] = img
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
        
        # 缓存结果
        self._bg_images_cache = images
        return images
    
    def load_custom_b1_image(self, filename: str) -> Optional[pygame.Surface]:
        """
        加载自定义b1图片
        
        参数:
            filename: 图片文件名（如 "b1_1.png"）
        
        返回:
            pygame.Surface: 图片表面，如果加载失败则返回 None
        """
        if not filename:
            return None
            
        # 确保文件名有.png扩展名
        if not filename.endswith('.png'):
            filename += '.png'
        
        img_path = self.custom_resource_path / filename
        if img_path.exists():
            try:
                img = pygame.image.load(str(img_path)).convert_alpha()
                return img
            except Exception as e:
                print(f"Failed to load custom b1 image {filename}: {e}")
                return None
        else:
            print(f"Custom b1 image not found: {img_path}")
            return None
    
    def load_custom_genre_bg_image(self, filename: str) -> Optional[pygame.Surface]:
        """
        加载自定义genre_bg图片
        
        参数:
            filename: 图片文件名（如 "genre_bg1.png"）
        
        返回:
            pygame.Surface: 图片表面，如果加载失败则返回 None
        """
        if not filename:
            return None
            
        # 确保文件名有.png扩展名
        if not filename.endswith('.png'):
            filename += '.png'
        
        img_path = self.custom_resource_path / filename
        if img_path.exists():
            try:
                img = pygame.image.load(str(img_path)).convert_alpha()
                return img
            except Exception as e:
                print(f"Failed to load custom genre_bg image {filename}: {e}")
                return None
        else:
            print(f"Custom genre_bg image not found: {img_path}")
            return None
    
    def load_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        """
        加载字体
        Load font with specified size and style
        
        Args:
            size: 字体大小
            bold: 是否加粗
            
        Returns:
            pygame.font.Font: 字体对象
        """
        # 创建缓存键
        cache_key = f"{size}_{bold}"
        
        # 使用缓存避免重复加载
        if cache_key in self._fonts_cache:
            return self._fonts_cache[cache_key]
        
        font = None
        
        # ==================== 优先使用自定义字体 ====================
        if self.font_path.exists():
            try:
                font = pygame.font.Font(str(self.font_path), size)
                if bold:
                    # 注意：pygame.font.Font 不支持 bold 参数
                    # 这里只是记录，实际渲染时可能需要其他处理
                    pass
            except Exception as e:
                print(f"Failed to load custom font: {e}")
                font = None
        
        # ==================== 回退到系统字体 ====================
        if font is None:
            # 回退到系统字体
            cjk_fonts = [
                'Microsoft YaHei',  # Windows 中文字体
                'SimHei',           # Windows 中文字体
                'MS Gothic',        # Windows 日文字体
                'Meiryo',           # Windows 日文字体
                'Arial Unicode MS', # 通用回退字体
            ]
            
            font_name = None
            for font_candidate in cjk_fonts:
                if pygame.font.match_font(font_candidate):
                    font_name = font_candidate
                    break
            
            if not font_name:
                font_name = pygame.font.get_default_font()
            
            font = pygame.font.SysFont(font_name, size, bold=bold)
        
        # 缓存字体
        self._fonts_cache[cache_key] = font
        return font
    
    def load_ui_fonts(self) -> Dict[str, pygame.font.Font]:
        """
        加载UI字体集合
        Load UI font collection
        
        返回常用的UI字体：
        - title: 主标题字体
        - title_cn: 中文标题字体
        - subtitle: 副标题字体
        - small: 小字体
        - category: 分类字体
        - star: 星级显示字体
        - header: 页面标题字体
        
        Returns:
            Dict[str, pygame.font.Font]: 字体字典
        """
        fonts = {}
        
        # ==================== 歌曲标题字体 ====================
        fonts['title'] = self.load_font(40)        # 主标题字体（英文）
        fonts['title_cn'] = self.load_font(40)     # 中文标题字体（统一高度）
        fonts['subtitle'] = self.load_font(18)     # 副标题字体
        
        # ==================== UI字体 ====================
        fonts['small'] = self.load_font(28)        # 小字体
        fonts['category'] = self.load_font(30, bold=True)  # 分类字体（稍微减小）
        
        # ==================== 系统字体 ====================
        fonts['star'] = pygame.font.SysFont('Arial', 48, bold=True)     # 星级显示字体
        fonts['header'] = pygame.font.SysFont('Arial', 56, bold=True)   # 页面标题字体
        
        return fonts
    
    def clear_cache(self):
        """
        清空缓存
        Clear all cached resources
        
        用于内存管理或重新加载资源
        """
        self._diff_images_cache = None
        self._bg_images_cache = None
        self._fonts_cache.clear()
    
    def get_resource_info(self) -> Dict[str, any]:
        """
        获取资源信息
        Get resource information
        
        Returns:
            Dict[str, any]: 资源信息字典
        """
        info = {
            'texture_path': str(self.texture_path),
            'font_path': str(self.font_path),
            'custom_resource_path': str(self.custom_resource_path),
            'target_height': self.target_height,
            'cached_images': {
                'difficulty': self._diff_images_cache is not None,
                'background': self._bg_images_cache is not None,
            },
            'cached_fonts': len(self._fonts_cache),
        }
        return info
