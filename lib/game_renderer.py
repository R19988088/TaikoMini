"""
游戏渲染模块 (Game Renderer Module)
负责所有游戏元素的绘制：音符、鼓、UI、动画等
"""

import pygame
from pathlib import Path
from collections import OrderedDict
from .note_pattern_manager import NotePatternManager
from .game_settings import GameSettings


class NoteSprite(pygame.sprite.Sprite):
    """音符精灵类 - 用于GPU加速渲染（对象池复用）"""
    def __init__(self):
        super().__init__()
        self.image = None
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.active = False
    
    def setup(self, image, x, y):
        """设置精灵（复用对象）"""
        self.image = image
        self.rect = image.get_rect(center=(int(x), int(y)))
        self.active = True
    
    def deactivate(self):
        """停用精灵"""
        self.active = False


# 颜色常量
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (230, 74, 25)
BLUE = (0, 162, 232)
ORANGE = (247, 152, 36)
YELLOW = (255, 242, 0)
GREEN = (0, 200, 100)
GRAY = (127, 127, 127)
DARK_GRAY = (50, 50, 50)

# 布局常量
GAME_AREA_RATIO = 0.20
JUDGE_X_RATIO = 0.15
# NOTE_LEAD_TIME 已删除，统一使用 distance 参数


class GameRenderer:
    """
    游戏渲染器
    
    功能：
    - 绘制游戏区域（橙色轨道）
    - 绘制音符（咚/咔/大咚/大咔/连打/气球）
    - 绘制鼓和鼓动画
    - 绘制击打特效
    - 绘制UI（分数、控制按钮等）
    - 绘制判定文字
    """
    
    def __init__(self, screen):
        """
        初始化渲染器
        
        参数:
            screen: Pygame屏幕对象
        """
        self.screen = screen
        
        # 屏幕尺寸（动态更新）
        self.screen_width = screen.get_width()
        
        # 初始化音符图案管理器
        self.note_pattern_manager = NotePatternManager()
        
        # 初始化游戏设置
        self.game_settings = GameSettings()
        
        # 音符缩放比例（从设置中获取缩放后的比例）
        self.note_scale = self.game_settings.get_scaled_note_scale()
        # 判定圈缩放比例（从设置中获取缩放后的比例）
        self.judge_circle_scale = self.game_settings.get_scaled_judge_circle_scale()
        # 击中特效缩放比例（从设置中获取缩放后的比例）
        self.hit_effect_scale = self.game_settings.get_scaled_hit_effect_scale()
        self.screen_height = screen.get_height()
        
        # === 硬件加速优化 ===
        # 创建离屏渲染surface（GPU加速）
        self.render_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        # 批量绘制缓存
        self.batch_draw_cache = {
            'notes': [],      # 音符批量绘制缓存
            'bars': [],       # 小节线批量绘制缓存
            'drumrolls': [],  # 连打条批量绘制缓存
        }
        # 预计算缓存 (使用OrderedDict实现LRU)
        self.position_cache = OrderedDict()  # 位置计算结果缓存
        self.max_cache_size = 100  # 最多保留100个缓存条目,防止内存泄漏
        self.last_game_time = -1  # 用于检测时间变化
        
        # 布局参数
        self.game_area_height = 0
        self.game_area_top = 0
        self.game_area_bottom = 0
        self.judge_x = 0
        self.judge_y = 0
        self.judge_radius = 0
        self.drum_center_x = 0
        self.drum_center_y = 0
        
        # 字体
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_cjk_large = None  # 中文字体（大）
        self.font_cjk_medium = None  # 中文字体（中）
        self.font_cjk_small = None   # 中文字体（小）
        
        # 图片资源
        self.hit_effect_img = None  # 判定圈图片
        self.hit_anims = {}  # 击打动画
        self.drum_img = None  # 鼓底图
        self.scaled_drum_img = None
        self.drum_don_hit_img = None  # 咚击打效果
        self.scaled_don_hit_img = None
        self.drum_kat_hit_img = None  # 咔击打效果
        self.scaled_kat_hit_img = None
        
        # 判定文字图片
        self.judgment_images = {}  # 判定文字图片 {"Perfect": img, "Good": img, "OK": img}
        
        # 判定文字动画状态
        self.judgment_animation = {
            'active': False,
            'text': '',
            'start_time': 0,
            'is_super_large': False
        }
        
        # 击打动画列表 (image, start_time, duration, is_big, blend_mode)
        self.active_animations = []
        
        # === GPU加速渲染 ===
        # 音符精灵组
        self.note_sprite_group = pygame.sprite.Group()
        # 预渲染的音符纹理缓存 {(pattern_name, scale): surface}
        self.note_texture_cache = {}
        # 连打条渲染Surface缓存
        self.drumroll_surface_cache = {}
        # 精灵对象池（避免每帧创建/销毁对象）
        self.sprite_pool = []
        self.max_visible_notes = 100  # 最大同时显示音符数
        self._init_sprite_pool()
        
        # 连打图案缓存
        self.drumroll_textures = {}
        
        # 加载资源
        self.load_resources()
        self.update_layout()
    
    def _init_sprite_pool(self):
        """初始化精灵对象池"""
        for _ in range(self.max_visible_notes):
            sprite = NoteSprite()
            self.sprite_pool.append(sprite)
            self.note_sprite_group.add(sprite)
    
    def load_resources(self):
        """加载图片资源"""
        try:
            res_dir = Path("lib/res/Texture")
            
            # 加载鼓图片
            self.drum_img = pygame.image.load(str(res_dir / "touch-1.png")).convert_alpha()
            self.drum_don_hit_img = pygame.image.load(str(res_dir / "touch-2.png")).convert_alpha()
            self.drum_kat_hit_img = pygame.image.load(str(res_dir / "touch-3.png")).convert_alpha()
            
            # 加载击打特效（使用配置的缩放比例）
            scale = self.hit_effect_scale
            img = pygame.image.load(str(res_dir / "hit_1.png")).convert_alpha()
            new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            self.hit_effect_img = pygame.transform.smoothscale(img, new_size)
            
            # 加载动画帧
            self.hit_anims = {}
            anim_files = {
                'big_don': "hit_2.png",
                'big_kat': "hit_3.png",
                'flash_1': "hit_4.png",
                'flash_2': "hit_5.png",
            }
            for name, filename in anim_files.items():
                img = pygame.image.load(str(res_dir / filename)).convert_alpha()
                if name == 'flash_2':
                    img = self._clean_alpha_channel(img)
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                self.hit_anims[name] = pygame.transform.smoothscale(img, new_size)
            
            # 加载判定文字图片（缩小30%，即保留70%）
            hit_effect_dir = res_dir / "hit_effect"
            self.judgment_images = {}
            judgment_files = {
                'Perfect': "hit_effect_multi_1.png",  # 良
                'Good': "hit_effect_multi_2.png",      # 可
                'OK': "hit_effect_multi_3.png"         # 不可
            }
            for judgment, filename in judgment_files.items():
                try:
                    img = pygame.image.load(str(hit_effect_dir / filename)).convert_alpha()
                    # 缩小30%（保留70%）
                    original_size = img.get_size()
                    scaled_size = (int(original_size[0] * 0.7), int(original_size[1] * 0.7))
                    img = pygame.transform.smoothscale(img, scaled_size)
                    self.judgment_images[judgment] = img
                except Exception as e:
                    print(f"Warning: Could not load judgment image {filename}: {e}")
            
            print("OK - Renderer resources loaded")
            
        except Exception as e:
            print(f"Error loading renderer resources: {e}")
    
    def _clean_alpha_channel(self, surf):
        """清理alpha通道（防止additive blend伪影）"""
        cleaned_surf = surf.copy()
        width, height = cleaned_surf.get_size()
        
        for y in range(height):
            for x in range(width):
                if cleaned_surf.get_at((x, y))[3] == 0:
                    cleaned_surf.set_at((x, y), (0, 0, 0, 0))
        
        return cleaned_surf
    
    def update_layout(self):
        """更新布局参数（屏幕尺寸改变时调用）"""
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # 游戏区域（应用note_area_scale缩放）
        base_game_area_height = int(self.screen_height * GAME_AREA_RATIO)
        self.game_area_height = int(base_game_area_height * self.game_settings.get_note_area_scale())
        self.game_area_top = int((self.screen_height - self.game_area_height) * 0.35)
        self.game_area_bottom = self.game_area_top + self.game_area_height
        
        # 判定线位置（使用缩放配置）
        scaled_judge_x_ratio = self.game_settings.get_scaled_judge_x_ratio()
        self.judge_x = int(self.screen_width * scaled_judge_x_ratio)
        self.judge_y = self.game_area_top + self.game_area_height // 2
        self.judge_radius = int(min(self.screen_width, self.screen_height) * 0.05)
        
        # 鼓位置
        self.drum_center_x = self.screen_width // 2
        drum_ratio = 0.48
        drum_radius = int(self.screen_width * drum_ratio)
        
        # 缩放鼓图片
        if self.drum_img:
            drum_width = drum_radius * 2
            drum_height = int(self.drum_img.get_height() * drum_width / self.drum_img.get_width())
            drum_size = (drum_width, drum_height)
            
            self.scaled_drum_img = pygame.transform.smoothscale(self.drum_img, drum_size)
            if self.drum_don_hit_img:
                self.scaled_don_hit_img = pygame.transform.smoothscale(self.drum_don_hit_img, drum_size)
            if self.drum_kat_hit_img:
                self.scaled_kat_hit_img = pygame.transform.smoothscale(self.drum_kat_hit_img, drum_size)
            
            # 鼓的Y位置（部分在屏幕外）
            y_offset = int(self.scaled_drum_img.get_height() * 0.20)
            self.drum_center_y = self.screen_height - self.scaled_drum_img.get_height() // 2 + y_offset
        else:
            self.drum_center_y = int(self.screen_height * 0.75)
        
        # 字体（英文）
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        
        # 中文字体
        try:
            font_path = Path("lib/res/FZPangWaUltra-Regular.ttf")
            if font_path.exists():
                self.font_cjk_large = pygame.font.Font(str(font_path), 48)
                self.font_cjk_medium = pygame.font.Font(str(font_path), 36)
                self.font_cjk_small = pygame.font.Font(str(font_path), 28)
            else:
                # 使用系统中文字体作为后备
                cjk_fonts = ['Microsoft YaHei', 'SimHei', 'MS Gothic', 'Meiryo']
                font_name = None
                for font in cjk_fonts:
                    if pygame.font.match_font(font):
                        font_name = font
                        break
                if font_name:
                    self.font_cjk_large = pygame.font.SysFont(font_name, 48)
                    self.font_cjk_medium = pygame.font.SysFont(font_name, 36)
                    self.font_cjk_small = pygame.font.SysFont(font_name, 28)
                else:
                    self.font_cjk_large = self.font_large
                    self.font_cjk_medium = self.font_medium
                    self.font_cjk_small = self.font_small
        except Exception as e:
            print(f"Error loading CJK font: {e}")
            self.font_cjk_large = self.font_large
            self.font_cjk_medium = self.font_medium
            self.font_cjk_small = self.font_small
    
    def reset(self):
        """Resets the renderer's state, like clearing active animations."""
        self.active_animations.clear()
        self.note_sprite_group.empty()
        self.note_texture_cache.clear()
        self.drumroll_surface_cache.clear()
        # 清空位置缓存防止内存泄漏
        self.position_cache.clear()
        self.last_game_time = -1
        self.batch_draw_cache = {'notes': [], 'bars': [], 'drumrolls': []}  # 重置批量绘制缓存
        print("[Renderer] Cleared all caches")
    
    def optimize_for_android(self):
        """
        Android移植优化设置
        针对移动设备的性能优化
        """
        # 减少最大可见音符数量（移动设备性能限制）
        self.max_visible_notes = 50
        
        # 减少精灵对象池大小
        self.sprite_pool.clear()
        for _ in range(self.max_visible_notes):
            sprite = NoteSprite()
            self.sprite_pool.append(sprite)
            self.note_sprite_group.add(sprite)
        
        # 调整缓存策略（移动设备内存限制）
        max_cache_size = 20
        if len(self.position_cache) > max_cache_size:
            # 删除最旧的缓存项
            cache_keys = list(self.position_cache.keys())
            for key in cache_keys[:len(cache_keys) - max_cache_size]:
                del self.position_cache[key]
        
        # 减少纹理缓存大小
        if len(self.note_texture_cache) > 10:
            # 保留最常用的纹理
            texture_keys = list(self.note_texture_cache.keys())
            for key in texture_keys[10:]:
                del self.note_texture_cache[key]
        
        print("Android optimization applied: reduced sprite pool, limited caches")

    def draw_game_area(self, is_gogo: bool = False):
        """绘制游戏区域（轨道和判定圈，不显示判定线）
        
        Args:
            is_gogo: 是否在 GOGOTIME
        """
        # 游戏区域底色 #282828（深灰色）
        pygame.draw.rect(
            self.screen,
            (40, 40, 40),  # #282828
            (0, self.game_area_top, self.screen_width, self.game_area_height)
        )
        
        # GOGOTIME 特效：叠加半透明橘红色
        if is_gogo:
            gogo_overlay = pygame.Surface((self.screen_width, self.game_area_height), pygame.SRCALPHA)
            # 橘红色，透明度80（约30%不透明）
            gogo_overlay.fill((255, 100, 50, 80))
            self.screen.blit(gogo_overlay, (0, self.game_area_top))
        
        # 判定线已隐藏
        # pygame.draw.line(
        #     self.screen,
        #     WHITE,
        #     (self.judge_x, self.game_area_top),
        #     (self.judge_x, self.game_area_bottom),
        #     3
        # )
        
        # 判定圈图片（应用缩放）
        if self.hit_effect_img:
            # 计算缩放后的尺寸
            original_size = self.hit_effect_img.get_size()
            scaled_size = (
                int(original_size[0] * self.judge_circle_scale),
                int(original_size[1] * self.judge_circle_scale)
            )
            
            # 缩放图片
            if self.judge_circle_scale != 1.0:
                scaled_img = pygame.transform.scale(self.hit_effect_img, scaled_size)
            else:
                scaled_img = self.hit_effect_img
            
            # 绘制缩放后的判定圈
            rect = scaled_img.get_rect(center=(self.judge_x, self.judge_y))
            self.screen.blit(scaled_img, rect)
    
    def draw_bars(self, bars, game_time):
        """
        绘制小节线（优化：批量绘制 + 缓存）
        
        参数:
            bars: 小节线列表
            game_time: 当前游戏时间
        """
        # 检查缓存
        cache_key = f"bars_{int(game_time // 16)}"  # 每16ms缓存一次
        if cache_key in self.position_cache:
            bars_to_draw = self.position_cache[cache_key]
        else:
            # 批量收集需要绘制的小节线
            bars_to_draw = []
            
            for bar in bars:
                bar_time = bar.hit_ms if hasattr(bar, 'hit_ms') else (bar.time_ms if hasattr(bar, 'time_ms') else 0)
                time_until_bar = bar_time - game_time
                
                if time_until_bar < -200:
                    continue
                
                # 使用小节线自带的 pixels_per_frame_x 计算位置
                if not hasattr(bar, 'pixels_per_frame_x') or bar.pixels_per_frame_x == 0:
                    continue
                
                pixels_per_ms = bar.pixels_per_frame_x * 0.06  # 60fps -> 0.06 = 60/1000
                x = round(self.judge_x + (time_until_bar * pixels_per_ms))
                
                if x < self.judge_x - 100 or x > self.screen_width + 100:
                    continue
                
                display = bar.display if hasattr(bar, 'display') else True
                if not display:
                    continue
                
                # 检查是否是分歧点后的小节线
                is_branch = hasattr(bar, 'is_branch_start') and bar.is_branch_start
                bars_to_draw.append((int(x), is_branch))
            
            # 缓存结果
            self.position_cache[cache_key] = bars_to_draw
        
        # 批量绘制所有小节线（减少draw调用）
        for x, is_branch in bars_to_draw:
            # 分歧点小节线使用橙黄色 #F9B100，普通小节线使用白色
            color = (249, 177, 0) if is_branch else WHITE
            pygame.draw.line(
                self.screen,
                color,
                (x, self.game_area_top),
                (x, self.game_area_bottom),
                2
            )
    
    def _get_note_texture(self, note_type, combo=0, game_time=0, is_super_large=False):
        """
        获取预渲染的音符纹理（GPU优化）
        
        参数:
            note_type: 音符类型
            combo: 当前连击数
            game_time: 当前游戏时间
            is_super_large: 是否为超大音符（J/K/L/M）
            
        返回:
            pygame.Surface: 预渲染的音符表面
        """
        pattern_name = self._get_note_pattern(note_type, combo, game_time)
        # 缓存key包含is_super_large状态
        scale_multiplier = 2.0 if is_super_large else 1.0
        cache_key = (pattern_name, self.note_scale, scale_multiplier)
        
        # 检查缓存
        if cache_key in self.note_texture_cache:
            return self.note_texture_cache[cache_key]
        
        # 生成音符纹理
        texture = None
        if pattern_name:
            # 使用音符图案管理器预渲染
            img = self.note_pattern_manager.get_pattern(pattern_name)
            if img:
                # 应用缩放（超大音符额外放大2倍）
                final_scale = self.note_scale * scale_multiplier
                scaled_size = (int(img.get_width() * final_scale), 
                             int(img.get_height() * final_scale))
                texture = pygame.transform.smoothscale(img, scaled_size)
                # 转换为硬件加速格式
                texture = texture.convert_alpha()
        
        # 如果没有图案，创建回退纹理
        if texture is None:
            if note_type in [1, 3, 5]:  # 咚
                color = RED
            elif note_type in [2, 4, 6]:  # 咔
                color = BLUE
            elif note_type in [7, 9]:  # 气球
                color = YELLOW
            else:
                color = WHITE
            
            radius = 50 if note_type in [3, 4] else 35
            size = radius * 2 + 4
            texture = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(texture, color, (size//2, size//2), radius)
            pygame.draw.circle(texture, WHITE, (size//2, size//2), radius, 2)
            texture = texture.convert_alpha()
        
        # 缓存纹理
        self.note_texture_cache[cache_key] = texture
        return texture
    
    def draw_notes(self, notes, current_note_index, game_time, combo=0, playback_speed=1.0):
        """
        绘制音符（GPU加速批量渲染 + 对象池优化 + 位置缓存）
        
        参数:
            notes: 音符列表
            current_note_index: 当前音符索引
            game_time: 当前游戏时间
            combo: 当前连击数（用于动态动画）
            playback_speed: 播放速度（用于调整裁剪边界）
        """
        # 禁用缓存以防止内存泄漏 - 直接重新计算位置
        # 现代CPU足够快，每帧重算位置的性能损失可以忽略
        notes_to_draw = []
        
        for i, note in enumerate(notes[current_note_index:], start=current_note_index):
            if note.type == -1:  # 已击打
                continue
            
            note_time = note.hit_ms if hasattr(note, 'hit_ms') else note.time_ms
            time_until_hit = note_time - game_time
            
            if time_until_hit < -200 or note.type == -1:
                continue
            
            # 使用音符自带的 pixels_per_frame_x 计算位置
            if not hasattr(note, 'pixels_per_frame_x') or note.pixels_per_frame_x == 0:
                continue
            
            # 使用精确的像素每毫秒计算（基于BPM，与帧率无关）
            # pixels_per_frame_x 是60fps时每帧移动的像素
            # 转换为每毫秒移动的像素：pixels_per_frame_x / (1000/60)
            pixels_per_ms = note.pixels_per_frame_x / 16.666666666666668
            x = self.judge_x + (time_until_hit * pixels_per_ms)
            
            # 减速时需要更大的渲染边界（音符会在更远处出现）
            right_boundary = self.screen_width + (100 / max(playback_speed, 0.1))
            if x < self.judge_x - 100 or x > right_boundary:
                continue
            
            # 跳过连打相关音符（由draw_drumrolls绘制）
            if note.type in [5, 6, 7, 8, 9]:  # 5=连打 6=大连打 7=气球 8=结束标记 9=大气球
                continue
            
            # 收集音符信息
            # 使用round()四舍五入，避免截断导致的抖动
            notes_to_draw.append({
                'note': note,
                'x': round(x),
                'y': self.judge_y,
                'time_until_hit': time_until_hit,
                'index': i
            })
        
        # 缓存已禁用，直接使用计算结果
        
        # 按距离排序：距离越近（时间越短）的音符在后面绘制（覆盖前面的）
        notes_to_draw.sort(key=lambda n: n['time_until_hit'], reverse=True)
        
        # === 使用对象池：复用精灵而不是创建新的 ===
        # 先停用所有精灵
        for sprite in self.sprite_pool:
            sprite.deactivate()
        
        # 复用对象池中的精灵
        num_notes = min(len(notes_to_draw), self.max_visible_notes)
        for i in range(num_notes):
            note_info = notes_to_draw[i]
            note = note_info['note']
            x = note_info['x']
            y = note_info['y']
            
            # 获取预渲染的音符纹理（传入combo、game_time和is_super_large）
            is_super_large = getattr(note, 'is_super_large', False)
            texture = self._get_note_texture(note.type, combo, game_time, is_super_large)
            if texture:
                # 如果是超大音符，添加旋转效果
                if is_super_large:
                    # 计算旋转角度（逆时针）
                    # 使用距离判定线的时间和滚动速度来计算旋转
                    time_until_hit = note_info['time_until_hit']
                    pixels_per_ms = note.pixels_per_frame_x / 16.666666666666668  # 60fps
                    
                    # 旋转速度与滚动速度成正比（逆时针，使用负角度）
                    rotation_angle = -(time_until_hit * pixels_per_ms * 0.1)  # 负值=逆时针
                    rotation_angle = rotation_angle % 360  # 标准化角度
                    
                    # 旋转纹理（使用rotozoom更高效）
                    rotated_texture = pygame.transform.rotozoom(texture, rotation_angle, 1.0)
                    rotated_rect = rotated_texture.get_rect(center=(x, y))
                    
                    # 设置精灵
                    sprite = self.sprite_pool[i]
                    sprite.image = rotated_texture
                    sprite.rect = rotated_rect
                    sprite.active = True
                else:
                    # 普通音符不旋转
                    sprite = self.sprite_pool[i]
                    sprite.setup(texture, x, y)
        
        # 一次性批量绘制所有激活的音符（GPU加速）
        for sprite in self.sprite_pool:
            if sprite.active and sprite.image:
                self.screen.blit(sprite.image, sprite.rect)
    
    def _get_note_pattern(self, note_type: int, combo: int = 0, game_time: float = 0) -> str:
        """
        根据音符类型获取图案名称（支持动态动画）
        
        Args:
            note_type: 音符类型
            combo: 当前连击数
            game_time: 当前游戏时间（毫秒）
            
        Returns:
            str: 图案名称
        """
        # 连击>20时，使用动态动画（每200ms切换一次）
        if combo > 20:
            # 根据游戏时间计算当前帧（200ms一帧，2帧循环）
            frame = int(game_time / 200) % 2  # 0 or 1
            suffix = 2 + frame  # 2 or 3
            
            pattern_mapping = {
                1: f'don{suffix}',      # don2 或 don3
                2: f'ka{suffix}',       # ka2 或 ka3
                3: f'big_don{suffix}',  # big_don2 或 big_don3
                4: f'big_ka{suffix}',   # big_ka2 或 big_ka3
            }
        else:
            # 连击<=20时，使用静态图案
            pattern_mapping = {
                1: 'don',        # don1.png
                2: 'a',          # a1.png (ka1.png)
                3: 'big_don1',   # big_don1.png
                4: 'big_ka1',    # big_ka1.png
            }
        
        return pattern_mapping.get(note_type, '')
    
    def _load_drumroll_texture(self, texture_name):
        """
        加载连打图案纹理
        
        参数:
            texture_name: 纹理名称（如 'rapid', 'rapid_tail', 'front' 等）
            
        返回:
            pygame.Surface: 加载的纹理，如果加载失败返回None
        """
        if texture_name in self.drumroll_textures:
            return self.drumroll_textures[texture_name]
        
        try:
            texture_path = Path("lib/res/Texture/note") / f'{texture_name}.png'
            if texture_path.exists():
                texture = pygame.image.load(str(texture_path)).convert_alpha()
                # 按音符缩放比例缩放
                scaled_width = int(texture.get_width() * self.note_scale)
                scaled_height = int(texture.get_height() * self.note_scale)
                texture = pygame.transform.smoothscale(texture, (scaled_width, scaled_height))
                self.drumroll_textures[texture_name] = texture
                return texture
        except Exception as e:
            print(f"加载连打纹理失败 {texture_name}: {e}")
        
        return None
    
    def _draw_drumroll_with_texture(self, start_x, end_x, y, body_texture, front_texture, tail_texture, note_type, game_time):
        """
        使用纹理绘制连打条
        
        参数:
            start_x: 起始X坐标（连打开始音符的中心）
            end_x: 结束X坐标（连打结束音符的中心）
            y: Y坐标
            body_texture: 连打条主体纹理（平铺）或气球动画纹理1
            front_texture: 连打条前端纹理
            tail_texture: 连打条尾端纹理或气球动画纹理2
            note_type: 音符类型
            game_time: 当前游戏时间（用于气球抖动动画）
        """
        # 气球连打（type 7和9）特殊处理：移动到判定线后固定并抖动
        if note_type in [7, 9]:
            # 获取纹理尺寸
            front_width = front_texture.get_width() if front_texture else 0
            balloon_width = body_texture.get_width() if body_texture else 0
            
            # 如果start_x（移动中的位置）已经到达或经过判定线，则固定在判定线
            if start_x <= self.judge_x:
                # 固定在判定线，图片几何中心对齐
                display_x = self.judge_x
            else:
                # 移动中，图片几何中心对齐
                display_x = start_x
            
            # 绘制前端图案，几何中心对齐
            if front_texture:
                front_rect = front_texture.get_rect(center=(display_x, y))
                self.screen.blit(front_texture, front_rect)
            
            # 使用游戏时间来决定显示哪个抖动动画帧（每100ms切换一次）
            animation_frame = int(game_time / 100) % 2
            
            if animation_frame == 0:
                balloon_texture = body_texture  # ballon_tail.png
            else:
                balloon_texture = tail_texture  # ballon_tail2.png
            
            # 气球图案紧挨着前端图案右侧
            # 前端右边缘 = display_x + front_width // 2
            if balloon_texture:
                balloon_x = display_x + front_width // 2 + balloon_width // 2
                balloon_rect = balloon_texture.get_rect(center=(balloon_x, y))
                self.screen.blit(balloon_texture, balloon_rect)
            return
        
        # 普通连打和大连打（type 5和6）：显示完整的连打条
        # 获取纹理尺寸
        body_width = body_texture.get_width()
        body_height = body_texture.get_height()
        front_width = front_texture.get_width()
        front_height = front_texture.get_height()
        tail_width = tail_texture.get_width()
        tail_height = tail_texture.get_height()
        
        # 直接使用几何中心对齐（用户会手动切图调整）
        # 1. 先绘制尾端图案（最底层）- 几何中心对齐在 end_x
        tail_rect = tail_texture.get_rect(center=(end_x, y))
        self.screen.blit(tail_texture, tail_rect)
        
        # 前端位置：几何中心对齐在 start_x
        front_x = start_x
        
        # 2. 计算主体绘制区域（从前端图案右边缘到尾端图案左边缘）
        # 前端右边缘 = front_x + front_width // 2
        # 尾端左边缘 = end_x - tail_width // 2
        body_start_x = front_x + front_width // 2
        body_end_x = end_x - tail_width // 2
        body_length = body_end_x - body_start_x
        
        # 3. 平铺主体纹理（左对齐，中间层）
        if body_length > 0:
            num_tiles = int(body_length / body_width) + 1
            
            for i in range(num_tiles):
                tile_x = body_start_x + i * body_width
                
                # 如果超出范围，裁剪纹理
                if tile_x + body_width > body_end_x:
                    clip_width = body_end_x - tile_x
                    if clip_width > 0:
                        # 创建裁剪后的纹理（左对齐）
                        clipped_texture = body_texture.subsurface((0, 0, int(clip_width), body_height))
                        tile_rect = clipped_texture.get_rect(midleft=(tile_x, y))
                        self.screen.blit(clipped_texture, tile_rect)
                else:
                    # 完整的tile（左对齐）
                    tile_rect = body_texture.get_rect(midleft=(tile_x, y))
                    self.screen.blit(body_texture, tile_rect)
        
        # 4. 最后绘制前端图案（最顶层）- 逻辑中心对齐在 start_x
        front_rect = front_texture.get_rect(center=(front_x, y))
        self.screen.blit(front_texture, front_rect)
    
    def _get_drumroll_end_circle(self, note_type):
        """获取连打条结束圈纹理（使用tail图案）"""
        # 根据音符类型选择对应的tail图案
        texture_mapping = {
            5: 'rapid_tail',       # 5~8 普通连打
            6: 'big_rapid_tail',   # 6~8 大连打
            7: 'ballon_tail',      # 7~8 气球
            9: 'ballon_tail',      # 9~8 使用7~8一样的图案
        }
        
        texture_name = texture_mapping.get(note_type)
        if texture_name:
            texture = self._load_drumroll_texture(texture_name)
            if texture:
                return texture
        
        # 如果加载失败，使用原来的圆圈绘制
        cache_key = f"end_circle_{note_type}"
        if cache_key in self.drumroll_surface_cache:
            return self.drumroll_surface_cache[cache_key]
        
        color = YELLOW if note_type in [7, 9] else (RED if note_type == 5 else BLUE)
        radius = 35
        size = radius * 2 + 6
        
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (size//2, size//2), radius)
        pygame.draw.circle(surface, WHITE, (size//2, size//2), radius, 2)
        surface = surface.convert_alpha()
        
        self.drumroll_surface_cache[cache_key] = surface
        return surface
    
    def draw_drumrolls(self, notes, game_time, combo=0, playback_speed=1.0):
        """
        绘制连打条（优化：减少pygame.draw调用）
        
        参数:
            notes: 音符列表
            game_time: 当前游戏时间
            combo: 当前连击数（用于动态动画）
            playback_speed: 播放速度（用于调整裁剪边界）
        """
        # 缓存连打对（优化），保存原始类型以防被修改
        # 使用notes列表的id和长度作为缓存键，支持分歧谱面的动态音符列表切换
        if not hasattr(self, '_drumroll_pairs_cache'):
            self._drumroll_pairs_cache = {}
        
        # 对于分歧谱面，列表对象不变但内容会改变，所以需要同时检查长度
        cache_key = (id(notes), len(notes))
        if cache_key not in self._drumroll_pairs_cache:
            drumroll_pairs = []
            for i, note in enumerate(notes):
                if note.type in [5, 6, 7, 9]:
                    for j in range(i + 1, len(notes)):
                        if notes[j].type == 8:
                            # 保存原始类型，防止音符被标记为-1后丢失类型信息
                            original_type = note.type
                            drumroll_pairs.append((note, notes[j], original_type))
                            break
            self._drumroll_pairs_cache[cache_key] = drumroll_pairs
        
        drumroll_pairs = self._drumroll_pairs_cache[cache_key]
        
        # 批量收集需要绘制的连打条
        drumrolls_to_draw = []
        
        for start_note, end_note, original_type in drumroll_pairs:
            start_time = start_note.hit_ms if hasattr(start_note, 'hit_ms') else start_note.time_ms
            end_time = end_note.hit_ms if hasattr(end_note, 'hit_ms') else end_note.time_ms
            
            # 气球连打特殊处理：检查是否已打爆
            if original_type in [7, 9]:
                # 检查气球是否已被打爆
                if hasattr(start_note, 'popped') and start_note.popped:
                    continue
                # 气球过了结束时间后不再显示
                if game_time > end_time:
                    continue
            else:
                # 普通连打：超过结束时间200ms后不再显示
                if game_time > end_time + 200:
                    continue
            
            time_until_hit = start_time - game_time
            
            # 使用连打条自带的 pixels_per_frame_x 计算位置
            if not hasattr(start_note, 'pixels_per_frame_x') or start_note.pixels_per_frame_x == 0:
                continue
            
            pixels_per_ms = start_note.pixels_per_frame_x * 0.06  # 60fps -> 0.06 = 60/1000
            x = round(self.judge_x + (time_until_hit * pixels_per_ms))
            
            end_time_diff = end_time - game_time
            end_pixels_per_ms = (end_note.pixels_per_frame_x * 0.06) if hasattr(end_note, 'pixels_per_frame_x') else pixels_per_ms
            end_x = round(self.judge_x + (end_time_diff * end_pixels_per_ms))
            
            if end_x <= x:
                continue
            
            # 减速时需要更大的渲染边界（连打条会在更远处出现）
            right_boundary = self.screen_width + (100 / max(playback_speed, 0.1))
            # 只有当连打条的起始点在屏幕范围内，或者连打条横跨屏幕时才绘制
            if x > right_boundary and end_x > right_boundary:
                continue
            
            drumrolls_to_draw.append({
                'x': x,
                'end_x': end_x,
                'note_type': original_type  # 使用保存的原始类型
            })
        
        # 批量绘制连打条（使用图案）
        for dr in drumrolls_to_draw:
            x = dr['x']
            end_x = dr['end_x']
            note_type = dr['note_type']
            
            y = self.judge_y
            width = int(end_x - x)
            
            if width > 0:
                # 根据音符类型和combo选择图案 (body, front, tail)
                # 连击>20时，front部分使用动态动画
                if combo > 20:
                    # 根据游戏时间计算当前帧（200ms一帧，2帧循环）
                    frame = int(game_time / 200) % 2  # 0 or 1
                    suffix = 2 + frame  # 2 or 3
                    texture_mapping = {
                        5: ('rapid', f'front{suffix}', 'rapid_tail'),           # 5~8 普通连打 front动画
                        6: ('big_rapid', 'big_front2', 'big_rapid_tail'),        # 6~8 大连打（没有front3）
                        7: ('ballon_tail', f'ballon_front{suffix}', 'ballon_tail2'),  # 7~8 气球 front动画
                        9: ('ballon_tail', f'ballon_front{suffix}', 'ballon_tail2'),  # 9~8 气球 front动画
                    }
                else:
                    texture_mapping = {
                        5: ('rapid', 'front', 'rapid_tail'),           # 5~8 普通连打
                        6: ('big_rapid', 'big_front2', 'big_rapid_tail'),  # 6~8 大连打
                        7: ('ballon_tail', 'ballon_front', 'ballon_tail2'),  # 7~8 气球
                        9: ('ballon_tail', 'ballon_front', 'ballon_tail2'),  # 9~8 气球
                    }
                
                texture_names = texture_mapping.get(note_type, (None, None, None))
                body_texture_name, front_texture_name, tail_texture_name = texture_names
                
                # 加载图案纹理
                body_texture = self._load_drumroll_texture(body_texture_name) if body_texture_name else None
                front_texture = self._load_drumroll_texture(front_texture_name) if front_texture_name else None
                tail_texture = self._load_drumroll_texture(tail_texture_name) if tail_texture_name else None
                
                if body_texture and tail_texture and (front_texture or note_type in [7, 9]):
                    # 使用图案绘制连打条（气球只需要body和tail动画帧）
                    self._draw_drumroll_with_texture(
                        int(x), int(end_x), y, 
                        body_texture, front_texture, tail_texture, note_type, game_time
                    )
                else:
                    # 如果图案加载失败，使用原来的矩形绘制
                    color = YELLOW if note_type in [7, 9] else (RED if note_type == 5 else BLUE)
                    bar_height = 40 if note_type in [7, 9] else 30
                    pygame.draw.rect(self.screen, color, (int(x), y - bar_height//2, width, bar_height))
                    pygame.draw.rect(self.screen, WHITE, (int(x), y - bar_height//2, width, bar_height), 3)
                    
                    # 如果使用矩形，仍需绘制结束圈
                    end_circle = self._get_drumroll_end_circle(note_type)
                    circle_rect = end_circle.get_rect(center=(int(end_x), y))
                    self.screen.blit(end_circle, circle_rect)
    
    def draw_drum(self, drum_animation_times, game_time):
        """
        绘制鼓和击打动画
        
        参数:
            drum_animation_times: 鼓动画时间字典
            game_time: 当前游戏时间
        """
        # 下沉动画
        sink_amount = 10
        animation_duration = 100
        y_offset = 0
        
        if game_time - drum_animation_times['press'] < animation_duration:
            y_offset = sink_amount
        
        # 绘制鼓底图
        if self.scaled_drum_img:
            rect = self.scaled_drum_img.get_rect(center=(self.drum_center_x, self.drum_center_y + y_offset))
            self.screen.blit(self.scaled_drum_img, rect)
            
            hit_flash_duration = 150
            
            # 咚闪光
            last_don_hit = max(drum_animation_times['don_left'], drum_animation_times['don_right'])
            don_elapsed = game_time - last_don_hit
            
            if don_elapsed < hit_flash_duration and self.scaled_don_hit_img:
                fade = 1.0 - (don_elapsed / hit_flash_duration)
                alpha = int(255 * max(0.0, min(1.0, fade)))
                hit_img = self.scaled_don_hit_img.copy()
                hit_img.set_alpha(alpha)
                self.screen.blit(hit_img, rect)
            
            # 咔闪光
            last_kat_hit = max(drum_animation_times['kat_left'], drum_animation_times['kat_right'])
            kat_elapsed = game_time - last_kat_hit
            
            if kat_elapsed < hit_flash_duration and self.scaled_kat_hit_img:
                fade = 1.0 - (kat_elapsed / hit_flash_duration)
                alpha = int(255 * max(0.0, min(1.0, fade)))
                hit_img = self.scaled_kat_hit_img.copy()
                hit_img.set_alpha(alpha)
                self.screen.blit(hit_img, rect)
    
    def draw_hit_animations(self, game_time):
        """
        绘制击打动画
        
        参数:
            game_time: 当前游戏时间
        """
        for anim in self.active_animations[:]:
            img, start_time, duration, is_big, blend_mode = anim
            elapsed = game_time - start_time
            
            if elapsed >= duration:
                self.active_animations.remove(anim)
                continue
            
            progress = elapsed / duration
            fade = 1.0 - progress
            
            if is_big:
                scale = 1.0 + progress * 0.5
            else:
                scale = 1.0 + progress * 0.2
            
            pulse_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            if pulse_size[0] <= 0 or pulse_size[1] <= 0:
                continue
            
            final_img = pygame.transform.smoothscale(img, pulse_size)
            rect = final_img.get_rect(center=(self.judge_x, self.judge_y))
            
            if blend_mode == pygame.BLEND_RGB_ADD:
                # 金色特效强度减少60%
                glow_img = final_img.copy()
                fade_value = int(255 * fade * 0.5)  # 原本是 fade，现在是 fade * 0.4 (减少60%)
                fade_value = max(0, min(255, fade_value))  # Clamp value
                glow_img.fill((fade_value, fade_value, fade_value), special_flags=pygame.BLEND_RGB_MULT)
                self.screen.blit(glow_img, rect, special_flags=blend_mode)
            else:
                alpha = int(255 * fade)
                alpha = max(0, min(255, alpha))  # Clamp value
                final_img.set_alpha(alpha)
                self.screen.blit(final_img, rect)
    
    def trigger_hit_animation(self, is_big, is_don, game_time):
        """
        触发击打动画
        
        参数:
            is_big: 是否大音符
            is_don: 是否咚
            game_time: 当前游戏时间
        """
        anim_duration = 200
        
        if is_big:
            anim_img = self.hit_anims.get('big_don' if is_don else 'big_kat')
            if anim_img:
                self.active_animations.append((anim_img, game_time, anim_duration, True, 0))
        
        flash_1 = self.hit_anims.get('flash_1')
        flash_2 = self.hit_anims.get('flash_2')
        
        if flash_1:
            self.active_animations.append((flash_1, game_time, anim_duration, False, 0))
        if flash_2:
            self.active_animations.append((flash_2, game_time, anim_duration, False, pygame.BLEND_RGB_ADD))
    
    def draw_stats(self, score):
        """
        绘制统计信息（使用图片显示分数）
        
        参数:
            score: 当前分数
        """
        # 加载白色数字图片（如果还未加载）
        if not hasattr(self, 'score_numbers'):
            self.score_numbers = {}
            score_dir = Path("lib/res/Texture/combo")
            for digit in range(10):
                filename = f"combo_1_{digit:02d}.png"
                try:
                    img = pygame.image.load(str(score_dir / filename)).convert_alpha()
                    self.score_numbers[digit] = img
                except Exception as e:
                    print(f"Warning: Could not load score digit {filename}: {e}")
        
        # 转换分数为6位字符串（补0）
        score_str = f"{score:06d}"
        
        # 分数位置：音符区下方5px，距离左边15px
        score_x = 15
        score_y = self.game_area_bottom + 5
        
        # 数字缩放（缩小60%）
        score_scale = 0.6
        digit_spacing = -6  # 数字间距（负值=重叠，按比例缩小）
        
        # 收集所有数字图片
        digit_images = []
        for digit_char in score_str:
            digit = int(digit_char)
            if digit in self.score_numbers:
                digit_images.append(self.score_numbers[digit])
        
        # 逐个绘制数字（从左到右）
        current_x = score_x
        for img in digit_images:
            # 应用缩放
            if score_scale != 1.0:
                original_size = img.get_size()
                new_size = (
                    int(original_size[0] * score_scale),
                    int(original_size[1] * score_scale)
                )
                score_img = pygame.transform.smoothscale(img, new_size)
            else:
                score_img = img.copy()
            
            # 绘制数字（顶部对齐）
            num_rect = score_img.get_rect(topleft=(current_x, score_y))
            self.screen.blit(score_img, num_rect)
            
            # 移动到下一个数字位置
            current_x += score_img.get_width() + digit_spacing
    
    def draw_judgment(self, judgment_text, game_time, judgment_time, is_super_large=False):
        """
        绘制判定文字（0 → 上2px → 下4px，停留10帧，渐隐5帧）
        
        参数:
            judgment_text: 判定文字（Perfect/Good/OK/Miss）
            game_time: 当前游戏时间
            judgment_time: 判定发生时间
            is_super_large: 是否是超大音符（JK音符）
        """
        # 动画总时长：3帧移动 + 10帧停留 + 5帧渐隐 = 18帧 ≈ 300ms (at 60fps)
        ANIMATION_DURATION = 300  # ms
        FADE_START_FRAME = 13  # 从第13帧开始渐隐
        FADE_FRAMES = 5  # 渐隐5帧
        
        elapsed_time = game_time - judgment_time
        
        if elapsed_time < ANIMATION_DURATION:
            # 使用图片而不是文字
            if judgment_text in self.judgment_images:
                judge_img = self.judgment_images[judgment_text].copy()  # 复制以便修改alpha
                
                # 如果是超大音符，放大判定图片2倍
                if is_super_large:
                    original_size = judge_img.get_size()
                    scaled_size = (int(original_size[0] * 2.0), int(original_size[1] * 2.0))
                    judge_img = pygame.transform.smoothscale(judge_img, scaled_size)
                
                # 计算Y轴偏移（0 → 上2px → 下4px，然后停留）
                frame_time = 16.67  # 60fps下每帧时间
                current_frame = int(elapsed_time / frame_time)
                
                if current_frame == 0:
                    # 第0帧：初始位置
                    y_offset = 0
                elif current_frame == 1:
                    # 第1帧：上移2px
                    y_offset = -2
                elif current_frame == 2:
                    # 第2帧：下移4px（相对初始位置）
                    y_offset = 6
                else:
                    # 第3-12帧：停留在下移4px的位置
                    y_offset = 4
                
                # 计算渐隐alpha值
                alpha = 255
                if current_frame >= FADE_START_FRAME:
                    # 第13-17帧：渐隐
                    fade_progress = (current_frame - FADE_START_FRAME) / FADE_FRAMES
                    alpha = int(255 * (1.0 - fade_progress))
                    alpha = max(0, min(255, alpha))
                
                # 应用透明度
                judge_img.set_alpha(alpha)
                
                # 绘制判定图片在判定圈上方（整体上移25px）
                img_rect = judge_img.get_rect()
                img_x = self.judge_x - img_rect.width // 2
                img_y = self.judge_y - img_rect.height - 50 + y_offset  # 在判定圈上方35px（原10px + 上移10px + 再上移15px）
                
                self.screen.blit(judge_img, (img_x, img_y))
            elif judgment_text == "Miss":
                # Miss不显示判定文字（或可以使用文字渲染）
                pass
    

