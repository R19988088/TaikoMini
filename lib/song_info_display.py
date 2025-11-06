"""
歌曲信息显示模块 (Song Info Display Module)
负责在游戏界面右上角显示歌名和分类
"""

import pygame
from pathlib import Path


class SongInfoDisplay:
    """
    歌曲信息显示类
    
    功能：
    - 在屏幕右上角显示歌名和分类
    - 支持自定义字体、大小、颜色、位置
    - 支持圆角背景
    """
    
    def __init__(self, screen, config_manager=None):
        """
        初始化歌曲信息显示器
        
        参数:
            screen: Pygame屏幕对象
            config_manager: 配置管理器实例（用于获取分类图片）
        """
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.config_manager = config_manager
        
        # 显示位置配置（距离右上角的偏移）
        self.right_margin = 20   # 右边距
        self.top_margin = 20     # 上边距（直接控制整个区域的Y位置）
        self.vertical_spacing = 10  # 歌名和分类之间的间距
        
        # 分类背景配置
        self.category_padding_x = 15  # 横向内边距
        self.category_padding_y = 0   # 纵向内边距
        self.category_border_radius_ratio = 0.5  # 圆角半径（相对于高度）
        self.genre_image_dir = Path("songs/Resource")  # 分类图片目录
        
        # 字体大小配置
        self.title_font_size = 30    # 歌名字体大小
        self.category_font_size = 25  # 分类字体大小
        
        # 描边配置
        self.title_outline_width = 0    # 歌名描边宽度
        self.category_outline_width = 0  # 分类描边宽度
        self.outline_color = (0, 0, 0)   # 描边颜色（黑色）
        
        # 颜色配置
        self.title_color = (255, 255, 255)      # 白色
        self.category_text_color = (255, 255, 255)  # 白色
        self.default_category_bg_color = (247, 152, 36)  # 默认橙色
        
        # 字体
        self.font_title = None
        self.font_category = None
        
        # 分类图片缓存 {分类名: pygame.Surface}
        self.category_image_cache = {}
        
        # 加载字体
        self._load_fonts()
    
    def _load_fonts(self):
        """加载中文字体"""
        # === 歌名字体：使用项目字体 ===
        try:
            font_path = Path("lib/res/FZPangWaUltra-Regular.ttf")
            if font_path.exists():
                self.font_title = pygame.font.Font(str(font_path), self.title_font_size)
                print(f"Loaded title font: FZPangWaUltra-Regular.ttf (size: {self.title_font_size})")
            else:
                # 后备：使用系统字体
                cjk_fonts = ['Microsoft YaHei', 'SimHei', 'MS Gothic', 'Meiryo', 'Arial']
                for font_name in cjk_fonts:
                    try:
                        if pygame.font.match_font(font_name):
                            self.font_title = pygame.font.SysFont(font_name, self.title_font_size)
                            print(f"Loaded title font: {font_name} (size: {self.title_font_size})")
                            break
                    except:
                        continue
                else:
                    self.font_title = pygame.font.Font(None, self.title_font_size)
        except Exception as e:
            print(f"Warning: Could not load title font: {e}")
            self.font_title = pygame.font.Font(None, self.title_font_size)
        
        # === 分类字体：优先使用支持™符号和中日文的字体（粗体）===
        # Arial 和 Microsoft YaHei 都支持™符号
        category_fonts = ['Microsoft YaHei', 'Arial Unicode MS', 'Arial', 'SimHei']
        for font_name in category_fonts:
            try:
                if pygame.font.match_font(font_name):
                    self.font_category = pygame.font.SysFont(font_name, self.category_font_size, bold=True)
                    print(f"Loaded category font: {font_name} Bold (size: {self.category_font_size})")
                    return
            except:
                continue
        
        # 最后后备：使用默认字体
        self.font_category = pygame.font.Font(None, self.category_font_size)
        print(f"Warning: Using default category font (size: {self.category_font_size})")
    
    def _load_category_image(self, category: str) -> pygame.Surface:
        """
        加载分类背景图片
        
        参数:
            category: 分类名称
        
        返回:
            加载的图片 Surface，如果失败则返回 None
        """
        # 检查缓存
        if category in self.category_image_cache:
            return self.category_image_cache[category]
        
        # 从配置获取图片文件名
        if self.config_manager:
            category_info = self.config_manager.get_category_info(category)
            if category_info and category_info[2]:  # category_info = (color, b1_image_filename, genre_bg_image_filename)
                image_filename = category_info[2]  # 使用genre_bg图片作为分类背景
                image_path = self.genre_image_dir / image_filename
                
                try:
                    if image_path.exists():
                        # 加载图片
                        image = pygame.image.load(str(image_path)).convert_alpha()
                        # 缓存图片
                        self.category_image_cache[category] = image
                        print(f"Loaded category image: {image_filename} for {category}")
                        return image
                    else:
                        print(f"Category image not found: {image_path}")
                except Exception as e:
                    print(f"Error loading category image '{image_filename}': {e}")
        
        return None
    
    def _render_text_with_outline(self, text, font, text_color, outline_color, outline_width):
        """
        渲染带描边的文字
        
        参数:
            text: 文字内容
            font: 字体对象
            text_color: 文字颜色 (R, G, B)
            outline_color: 描边颜色 (R, G, B)
            outline_width: 描边宽度（像素）
        
        返回:
            pygame.Surface: 渲染后的surface
        """
        # 创建文字surface
        text_surface = font.render(text, True, text_color)
        w, h = text_surface.get_size()
        
        # 创建更大的surface来容纳描边
        outline_surface = pygame.Surface((w + outline_width * 2, h + outline_width * 2), pygame.SRCALPHA)
        
        # 在8个方向绘制描边
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:  # 跳过中心
                    if dx*dx + dy*dy <= outline_width * outline_width:  # 圆形描边
                        outline_text = font.render(text, True, outline_color)
                        outline_surface.blit(outline_text, (outline_width + dx, outline_width + dy))
        
        # 在中心绘制主文字
        outline_surface.blit(text_surface, (outline_width, outline_width))
        
        return outline_surface
    
    def update_screen_size(self, width, height):
        """
        更新屏幕尺寸（窗口大小改变时调用）
        
        参数:
            width: 新的屏幕宽度
            height: 新的屏幕高度
        """
        self.screen_width = width
        self.screen_height = height
    
    def draw(self, song_title="", category="", category_color=None):
        """
        绘制歌曲信息
        
        参数:
            song_title: 歌曲标题（可以为空）
            category: 分类名称（可以为空）
            category_color: 分类背景颜色 (R, G, B)，如果为None则使用默认颜色
        """
        if not song_title and not category:
            return  # 如果都为空则不绘制
        
        # 右对齐基准点
        right_x = self.screen_width - self.right_margin
        # 起始Y坐标（直接使用top_margin，不做额外偏移）
        current_y = self.top_margin
        
        # 绘制歌名（右对齐，带描边）
        if song_title:
            if self.title_outline_width > 0:
                # 绘制描边
                title_outline = self._render_text_with_outline(
                    song_title, self.font_title, self.title_color, 
                    self.outline_color, self.title_outline_width
                )
                # 右对齐
                title_rect = title_outline.get_rect(topright=(right_x, current_y))
                self.screen.blit(title_outline, title_rect)
                current_y += title_outline.get_height() + (self.vertical_spacing if category else 0)
            else:
                # 无描边
                title_surface = self.font_title.render(song_title, True, self.title_color)
                # 右对齐
                title_rect = title_surface.get_rect(topright=(right_x, current_y))
                self.screen.blit(title_surface, title_rect)
                current_y += title_surface.get_height() + (self.vertical_spacing if category else 0)
        
        # 绘制分类（右对齐，带背景和描边）
        if category:
            # 使用指定颜色或默认颜色
            bg_color = category_color if category_color else self.default_category_bg_color
            
            # 渲染分类文字（带描边）
            if self.category_outline_width > 0:
                category_surface = self._render_text_with_outline(
                    category, self.font_category, self.category_text_color,
                    self.outline_color, self.category_outline_width
                )
            else:
                category_surface = self.font_category.render(category, True, self.category_text_color)
            
            # 计算背景矩形（右对齐）
            text_width = category_surface.get_width()
            text_height = category_surface.get_height()
            bg_width = text_width + self.category_padding_x * 2
            bg_height = text_height + self.category_padding_y * 2
            # 右对齐：从右边界向左计算
            bg_x = right_x - bg_width
            bg_y = current_y
            bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
            
            # 绘制背景（优先使用分类独立图片）
            category_image = self._load_category_image(category)
            
            if category_image:
                # 使用分类独立图片（保持原始宽高比，不变形）
                # 获取图片原始尺寸
                orig_width = category_image.get_width()
                orig_height = category_image.get_height()
                orig_ratio = orig_width / orig_height
                
                # 计算目标高度（以文字高度为基准，放大1.7倍）
                target_height = int(text_height * 1.7)
                # 根据原始比例计算目标宽度
                target_width = int(target_height * orig_ratio)
                
                # 按比例缩放图片（保持宽高比）
                scaled_bg = pygame.transform.smoothscale(category_image, (target_width, target_height))
                
                # 右对齐图片：从right_x向左绘制
                image_x = right_x - target_width
                # 垂直居中对齐：考虑文字的实际位置
                image_y = bg_y + (bg_height - target_height) // 2
                self.screen.blit(scaled_bg, (image_x, image_y))
                
                # 绘制分类文字（在图片上，水平和垂直都居中）
                # 使用图片的实际区域作为基准
                image_rect = pygame.Rect(image_x, image_y, target_width, target_height)
                text_rect = category_surface.get_rect(center=image_rect.center)
                self.screen.blit(category_surface, text_rect)
            else:
                # 使用圆角矩形背景
                border_radius = int(bg_height * self.category_border_radius_ratio)
                pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=border_radius)
                
                # 绘制分类文字（在矩形上居中）
                text_rect = category_surface.get_rect(center=bg_rect.center)
                self.screen.blit(category_surface, text_rect)
    
    # ===== 配置方法（方便用户调整） =====
    
    def set_position(self, right_margin=None, top_margin=None, vertical_spacing=None):
        """
        设置显示位置
        
        参数:
            right_margin: 右边距（像素）
            top_margin: 上边距（像素）
            vertical_spacing: 歌名和分类之间的间距（像素）
        """
        if right_margin is not None:
            self.right_margin = right_margin
        if top_margin is not None:
            self.top_margin = top_margin
        if vertical_spacing is not None:
            self.vertical_spacing = vertical_spacing
    
    def set_font_sizes(self, title_size=None, category_size=None):
        """
        设置字体大小（会立即重新加载字体）
        
        参数:
            title_size: 歌名字体大小
            category_size: 分类字体大小
        """
        reload_needed = False
        
        if title_size is not None and title_size != self.title_font_size:
            self.title_font_size = title_size
            reload_needed = True
            print(f"Set title font size to: {title_size}")
        
        if category_size is not None and category_size != self.category_font_size:
            self.category_font_size = category_size
            reload_needed = True
            print(f"Set category font size to: {category_size}")
        
        if reload_needed:
            print("Reloading fonts with new sizes...")
            self._load_fonts()
    
    def set_colors(self, title_color=None, category_text_color=None, default_category_bg=None):
        """
        设置颜色
        
        参数:
            title_color: 歌名颜色 (R, G, B)
            category_text_color: 分类文字颜色 (R, G, B)
            default_category_bg: 默认分类背景颜色 (R, G, B)
        """
        if title_color is not None:
            self.title_color = title_color
        if category_text_color is not None:
            self.category_text_color = category_text_color
        if default_category_bg is not None:
            self.default_category_bg_color = default_category_bg
    
    def set_outline(self, title_outline=None, category_outline=None, outline_color=None):
        """
        设置文字描边
        
        参数:
            title_outline: 歌名描边宽度（像素，0=无描边）
            category_outline: 分类描边宽度（像素，0=无描边）
            outline_color: 描边颜色 (R, G, B)，默认黑色
        """
        if title_outline is not None:
            self.title_outline_width = title_outline
        if category_outline is not None:
            self.category_outline_width = category_outline
        if outline_color is not None:
            self.outline_color = outline_color
    
    def set_category_padding(self, padding_x=None, padding_y=None):
        """
        设置分类背景内边距
        
        参数:
            padding_x: 横向内边距（像素）
            padding_y: 纵向内边距（像素）
        """
        if padding_x is not None:
            self.category_padding_x = padding_x
        if padding_y is not None:
            self.category_padding_y = padding_y
    
    def set_border_radius_ratio(self, ratio):
        """
        设置圆角半径比例
        
        参数:
            ratio: 圆角半径相对于背景高度的比例（0.0-1.0）
                  0.5 = 完全圆角（椭圆）
                  0.0 = 无圆角（矩形）
        """
        self.category_border_radius_ratio = max(0.0, min(1.0, ratio))
    
    def set_category_background_image(self, image_path: str):
        """
        设置分类背景图片
        
        参数:
            image_path: 图片文件路径
        """
        try:
            from pathlib import Path
            img_path = Path(image_path)
            if img_path.exists():
                self.category_bg_image = pygame.image.load(str(img_path)).convert_alpha()
                self.use_category_bg_image = True
                print(f"Loaded category background image: {image_path}")
            else:
                print(f"Category background image not found: {image_path}")
                self.use_category_bg_image = False
        except Exception as e:
            print(f"Error loading category background image: {e}")
            self.use_category_bg_image = False

