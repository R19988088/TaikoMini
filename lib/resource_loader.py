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
        self.result_texture_path = self.res_path / 'Texture' / 'result'  # 结算画面资源路径
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
        
        # ==================== 加载彩色星星图标 ====================
        # Load colored star images for each difficulty (lv_s_1.png - lv_s_5.png)
        for i in range(1, 6):
            star_path = self.texture_path / f'lv_s_{i}.png'
            if star_path.exists():
                try:
                    star_img = pygame.image.load(str(star_path)).convert_alpha()
                    # Scale to match difficulty icon height (增大30%再减少10%: 0.5 * 1.3 * 0.9 = 0.585)
                    orig_w, orig_h = star_img.get_size()
                    scale = (self.target_height * 0.585) / orig_h
                    new_w = int(orig_w * scale)
                    star_img = pygame.transform.smoothscale(star_img, (new_w, int(self.target_height * 0.585)))
                    images[f'star_{i}'] = star_img
                    print(f"Loaded star image: lv_s_{i}.png")
                except Exception as e:
                    print(f"Failed to load {star_path}: {e}")
        
        # ==================== 加载数字图片 ====================
        # Load number images (SN_01.png - SN_10.png)
        for n in range(1, 11):
            num_filename = f'SN_{n:02d}.png'
            num_path = self.texture_path / num_filename
            if num_path.exists():
                try:
                    num_img = pygame.image.load(str(num_path)).convert_alpha()
                    # Scale numbers to match star height (增大30%再减少10%: 0.4 * 1.3 * 0.9 = 0.468)
                    orig_w, orig_h = num_img.get_size()
                    scale = (self.target_height * 0.468) / orig_h
                    new_w = int(orig_w * scale)
                    num_img = pygame.transform.smoothscale(num_img, (new_w, int(self.target_height * 0.468)))
                    images[f'num_{n}'] = num_img
                    print(f"Loaded number image: {num_filename}")
                except Exception as e:
                    print(f"Failed to load {num_path}: {e}")
        
        # ==================== 加载星星背景矩形 ====================
        # Load star background rectangles (lv_SB_1.png, lv_SB_2.png)
        for sb_i in [1, 2]:
            sb_path = self.texture_path / f'lv_SB_{sb_i}.png'
            if sb_path.exists():
                try:
                    sb_img = pygame.image.load(str(sb_path)).convert_alpha()
                    # Don't scale SB images, use original size
                    images[f'sb_{sb_i}'] = sb_img
                    print(f"Loaded SB image: lv_SB_{sb_i}.png (size: {sb_img.get_width()}x{sb_img.get_height()})")
                except Exception as e:
                    print(f"Failed to load {sb_path}: {e}")
        
        # ==================== 加载皇冠图标 ====================
        # Load crown images (Crown.png - 3 crowns in one image)
        crown_path = self.texture_path / 'Crown.png'
        if crown_path.exists():
            try:
                crown_sheet = pygame.image.load(str(crown_path)).convert_alpha()
                sheet_width, sheet_height = crown_sheet.get_size()
                
                # 皇冠是横向并排的三张，拆分成单独的三个图标
                # 0: 过关(分数>6000), 1: 全连(Full Combo), 2: 全P的全连(All Perfect)
                crown_width = sheet_width // 3
                
                for crown_type in range(3):
                    # 提取单个皇冠
                    crown_rect = pygame.Rect(crown_type * crown_width, 0, crown_width, sheet_height)
                    crown_img = crown_sheet.subsurface(crown_rect).copy()
                    
                    # 缩放皇冠到合适大小（高度为难度图标的140%，放大100%）
                    target_crown_height = int(self.target_height * 1.4)
                    scale = target_crown_height / sheet_height
                    new_crown_width = int(crown_width * scale)
                    crown_img = pygame.transform.smoothscale(crown_img, (new_crown_width, target_crown_height))
                    
                    images[f'crown_{crown_type}'] = crown_img
                
                print(f"Loaded crown images from Crown.png (3 types, size: {new_crown_width}x{target_crown_height})")
            except Exception as e:
                print(f"Failed to load {crown_path}: {e}")
        
        # 缓存结果
        self._diff_images_cache = images
        return images
    
    def load_background_images(self) -> Dict[str, pygame.Surface]:
        """
        加载歌曲按钮背景图片
        Load song button background images
        
        加载内容：
        1. big_1.png - 主背景图片
        2. big_2_1.png ~ big_2_2.png - 发光动画帧
        3. big_3.png - 信息背景图片
        
        用途：
        - big_1: 按钮主体背景
        - big_2_1~2: 选中时的发光动画效果（交替循环）
        - big_3: 歌曲信息显示区域背景
        
        Returns:
            Dict[str, pygame.Surface]: 背景图片字典
        """
        # 使用缓存避免重复加载
        if self._bg_images_cache is not None:
            return self._bg_images_cache
        
        images = {}
        
        # ==================== 加载背景图片 ====================
        # 加载 big_1.png 和 big_3.png
        for i in [1, 3]:
            img_path = self.texture_path / f'big_{i}.png'
            if img_path.exists():
                try:
                    # 加载背景图片，保持透明度
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    images[i] = img
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
        
        # 加载发光动画帧 big_2_1.png ~ big_2_2.png
        glow_frames = []
        for i in range(1, 3):
            img_path = self.texture_path / f'big_2_{i}.png'
            if img_path.exists():
                try:
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    glow_frames.append(img)
                    print(f"Loaded glow frame: big_2_{i}.png")
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
        
        # 将发光动画帧存储在 images[2] 中（作为列表）
        if glow_frames:
            images[2] = glow_frames  # 存储为列表
        else:
            print("Warning: No glow animation frames loaded")
        
        # ==================== 加载投影图片 ====================
        # b1_0.png 在 songs/Resource 目录下
        shadow_path = self.custom_resource_path / 'b1_0.png'
        if shadow_path.exists():
            try:
                # 加载投影图片，保持透明度
                shadow_img = pygame.image.load(str(shadow_path)).convert_alpha()
                images[0] = shadow_img
                print(f"Loaded shadow image: b1_0.png (from {shadow_path})")
            except Exception as e:
                print(f"Failed to load shadow image: {e}")
        else:
            print(f"Shadow image not found at: {shadow_path}")
        
        # ==================== 加载成绩显示图片 ====================
        # scores.png 在 lib/res/Texture/selectsongs 目录下
        scores_path = self.texture_path / 'scores.png'
        if scores_path.exists():
            try:
                # 加载成绩显示图片，保持透明度
                scores_img = pygame.image.load(str(scores_path)).convert_alpha()
                images['scores'] = scores_img
                print(f"Loaded scores image: scores.png")
            except Exception as e:
                print(f"Failed to load scores image: {e}")
        else:
            print(f"Warning: scores.png not found at {scores_path}")
        
        # ==================== 加载分数数字图片 ====================
        # n 4 00.png (数字0) 到 n 4 09.png (数字9) 在 lib/res/Texture/nu 目录下
        score_numbers = {}
        nu_path = self.res_path / 'Texture' / 'nu'
        
        # 加载数字0-9 (n 4 00.png 到 n 4 09.png，正序)
        for i in range(10):
            num_path = nu_path / f'n 4 {i:02d}.png'
            if num_path.exists():
                try:
                    num_img = pygame.image.load(str(num_path)).convert_alpha()
                    score_numbers[i] = num_img
                except Exception as e:
                    print(f"Failed to load n 4 {i:02d}.png: {e}")
        
        if score_numbers:
            images['score_numbers'] = score_numbers
            print(f"Loaded {len(score_numbers)} score number images")
        
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
    
    def load_result_screen_resources(self) -> Dict[str, pygame.Surface]:
        """
        加载结算画面资源
        Load result screen resources
        
        加载内容：
        1. 背景图片 (result_0.png)
        2. 皇冠图标 (crown_01.png, crown_02.png, crown_03.png)
        3. 难度图标 (lv_1.png 到 lv_5.png)
        4. 数字图片 (n 2 00.png 到 n 2 09.png)
        
        Returns:
            Dict[str, pygame.Surface]: 图片字典，键为图片名称，值为pygame表面
        """
        resources = {}
        
        # 加载背景图片
        bg_path = self.result_texture_path / 'result_0.png'
        if bg_path.exists():
            try:
                resources['background'] = pygame.image.load(str(bg_path)).convert_alpha()
                print(f"Loaded result background: {bg_path}")
            except Exception as e:
                print(f"Failed to load {bg_path}: {e}")
        
        # 加载皇冠图标（放大50%）
        for i in range(1, 4):
            crown_path = self.result_texture_path / f'crown_{i:02d}.png'
            if crown_path.exists():
                try:
                    crown_img = pygame.image.load(str(crown_path)).convert_alpha()
                    # 缩放皇冠图标到合适大小（80像素高 * 1.5 = 120像素高）
                    orig_w, orig_h = crown_img.get_size()
                    target_h = 120  # 放大50%
                    scale = target_h / orig_h
                    new_w = int(orig_w * scale)
                    crown_img = pygame.transform.smoothscale(crown_img, (new_w, target_h))
                    resources[f'crown_{i:02d}'] = crown_img
                    print(f"Loaded crown icon: crown_{i:02d}.png")
                except Exception as e:
                    print(f"Failed to load {crown_path}: {e}")
        
        # 加载难度图标
        for i in range(1, 6):
            lv_path = self.result_texture_path / f'lv_{i}.png'
            if lv_path.exists():
                try:
                    lv_img = pygame.image.load(str(lv_path)).convert_alpha()
                    # 缩放难度图标到合适大小（约80像素高）
                    orig_w, orig_h = lv_img.get_size()
                    target_h = 80
                    scale = target_h / orig_h
                    new_w = int(orig_w * scale)
                    lv_img = pygame.transform.smoothscale(lv_img, (new_w, target_h))
                    resources[f'lv_{i}'] = lv_img
                    print(f"Loaded difficulty icon: lv_{i}.png")
                except Exception as e:
                    print(f"Failed to load {lv_path}: {e}")
        
        # 加载数字图片（n 2 00.png - n 2 09.png）
        nu_path = self.res_path / 'Texture' / 'nu'
        for i in range(10):
            num_filename = f'n 2 {i:02d}.png'
            num_path = nu_path / num_filename
            if num_path.exists():
                try:
                    num_img = pygame.image.load(str(num_path)).convert_alpha()
                    # 保持原始大小
                    resources[f'num_{i}'] = num_img
                    print(f"Loaded number image: {num_filename}")
                except Exception as e:
                    print(f"Failed to load {num_path}: {e}")
        
        return resources
    
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
