"""
歌曲选择界面模块
Song Selection Screen Module

这个模块负责处理歌曲选择界面的所有功能，包括：
- 歌曲分类管理（按文件夹自动分类）
- 倾斜圆角矩形UI设计
- 平滑滚动和循环显示
- 难度选择（Easy, Normal, Hard, Oni, Edit/Ura）
- 练习模式支持
- 收藏功能
- 鼠标和键盘交互

主要类：
- SongSelectScreen: 歌曲选择界面的主控制器

设计特点：
- 使用倾斜的圆角矩形按钮设计
- 支持无限循环滚动
- 选中歌曲会有发光呼吸效果
- 支持长按鬼难度切换到里模式
- 自动保存用户选择状态
"""

import pygame
import math
from pathlib import Path
from typing import List, Tuple, Dict
from lib.song_button import SongButton  # 导入歌曲按钮类
from lib.resource_loader import ResourceLoader  # 导入资源加载器
from lib.data_organizer import DataOrganizer  # 导入数据组织器
from lib.event_handler import EventHandler  # 导入事件处理器
from lib.ui_renderer import UIRenderer  # 导入UI渲染器
from lib.scroll_manager import ScrollManager  # 导入滚动管理器
from lib.selection_manager import SelectionManager  # 导入选择管理器
from lib.sound_manager import SoundManager  # 导入音效管理器

# ==================== 颜色常量 ====================
# Color constants for UI elements
BLACK = (0, 0, 0)           # 黑色 - 文字描边、背景
WHITE = (255, 255, 255)     # 白色 - 文字、边框
ORANGE = (247, 152, 36)     # 橙色 - 背景色
RED = (230, 74, 25)         # 红色 - 警告、错误
GREEN = (0, 200, 100)       # 绿色 - 成功、激活状态
BLUE = (0, 162, 232)        # 蓝色 - 普通按钮
YELLOW = (255, 242, 0)      # 黄色 - 选中、高亮
GRAY = (100, 100, 100)      # 灰色 - 禁用状态

# ==================== 难度映射 ====================
# Difficulty mapping to image level (1-5)
# 难度等级到图片编号的映射关系
DIFF_MAPPING = {
    'Easy': 1,      # 简单难度 - 对应 lv_1.png
    'Normal': 2,    # 普通难度 - 对应 lv_2.png
    'Hard': 3,      # 困难难度 - 对应 lv_3.png
    'Oni': 4,       # 鬼难度 - 对应 lv_4.png
    'Edit': 5       # 里/编辑难度 - 对应 lv_5.png
}

# ==================== 说明 ====================
# SongButton 类已移至 lib/song_button.py（见上方 import）
# 该类负责单个歌曲按钮的显示和状态管理

class SongSelectScreen:
    """
    歌曲选择界面主控制器
    Song Selection Screen Controller
    
    负责管理整个歌曲选择界面的状态和交互逻辑
    """
    
    def __init__(self, screen, songs: List[Tuple[str, Path]]):
        """
        初始化歌曲选择界面
        
        Args:
            screen: pygame显示表面
            songs: 歌曲列表，格式为[(标题, 路径), ...]
        """
        # ==================== 基础属性 ====================
        self.screen = screen                    # pygame显示表面
        self.width = screen.get_width()         # 屏幕宽度
        self.height = screen.get_height()       # 屏幕高度
        
        # ==================== 歌曲数据管理 ====================
        self.data_organizer = DataOrganizer()   # 数据组织器
        self.categories, self.folder_songs = self.data_organizer.organize_songs(songs)  # 组织歌曲数据
        
        # ==================== 分类选择状态 ====================
        self.selected_category_index = 0        # 当前选中的分类索引
        self.current_category = self.categories[0] if self.categories else "All"  # 当前分类名称
        
        # ==================== 按钮管理 ====================
        self._update_buttons()                  # 创建当前分类的歌曲按钮
        
        
        # ==================== UI视觉设置 ====================
        self.button_height = 140                # 按钮高度（像素）
        self.button_spacing = 2                 # 按钮间距（像素）
        self.slant_angle = 5                    # 按钮倾斜角度（度）
        
        # ==================== 资源加载 ====================
        self.resource_loader = ResourceLoader()        # 资源加载器
        self.diff_images = self.resource_loader.load_difficulty_images()    # 难度图标图片
        self.bg_images = self.resource_loader.load_background_images()      # 按钮背景图片
        
        # ==================== 动画状态 ====================
        self.blink_time = 0                     # 闪烁动画时间计数器
        
        # ==================== 练习模式设置 ====================
        self.practice_mode = False               # 练习模式开关
        self.practice_audio_paths = {}          # 练习音频文件路径字典
        self.practice_generating = False        # 是否正在生成练习音频
        self.practice_speeds = [0.5, 0.8, 1.0, 1.3]  # 练习速度选项
        
        # ==================== 配置管理 ====================
        # 加载配置管理器
        from lib.config_manager import ConfigManager
        self.config = ConfigManager()
        
        # ==================== UI渲染 ====================
        self.ui_renderer = UIRenderer(screen, self.resource_loader)  # UI渲染器
        
        # ==================== 滚动管理 ====================
        self.scroll_manager = ScrollManager(screen.get_height(), self.button_height, self.button_spacing, self.ui_renderer)  # 滚动管理器
        
        # ==================== 选择管理 ====================
        self.selection_manager = SelectionManager(self.config, self.scroll_manager)  # 选择管理器
        
        # ==================== 音效管理 ====================
        self.sound_manager = SoundManager()     # 音效管理器
        
        # ==================== 事件处理 ====================
        self.event_handler = EventHandler()     # 事件处理器
        self._setup_event_callbacks()           # 设置事件回调
        
        # ==================== 字体加载 ====================
        # 使用资源加载器加载所有字体
        ui_fonts = self.resource_loader.load_ui_fonts()
        self.font_title = ui_fonts['title']          # 主标题字体
        self.font_title_cn = ui_fonts['title_cn']    # 中文标题字体
        self.font_subtitle = ui_fonts['subtitle']    # 副标题字体
        self.font_small = ui_fonts['small']          # 小字体
        self.font_category = ui_fonts['category']    # 分类字体
        self.font_star = ui_fonts['star']            # 星级显示字体
        self.font_header = ui_fonts['header']        # 页面标题字体
        
        # ==================== 时钟 ====================
        self.clock = pygame.time.Clock()                                # 游戏时钟
        
        # ==================== 状态恢复 ====================
        # 设置按钮列表到选择管理器
        self.selection_manager.set_buttons(self.buttons)
        # 恢复上次选择的歌曲
        self.selection_manager.set_selected_index(self.selection_manager.restore_last_selection())
    
    def _setup_event_callbacks(self):
        """
        设置事件回调函数
        Setup event callback functions
        """
        # 设置移动选择回调（带音效）
        self.event_handler.set_callback('move_selection', self._move_selection_with_sound)
        
        # 设置分类切换回调（带音效）
        self.event_handler.set_callback('change_category', self._change_category_with_sound)
        
        # 设置返回回调（带音效）
        self.event_handler.set_callback('cancel', self._cancel_with_sound)
        
        # 设置选中索引回调
        self.event_handler.set_callback('set_selected_index', self.selection_manager.set_selected_index)
        
        # 设置收藏切换回调
        self.event_handler.set_callback('toggle_favorite', self._toggle_favorite_callback)
        
        # 设置练习模式切换回调
        self.event_handler.set_callback('toggle_practice', self._toggle_practice_callback)
        
        # 设置退出回调
        self.event_handler.set_callback('quit', self._quit_callback)
        
        # 设置确认回调（带音效）
        self.event_handler.set_callback('confirm', self._confirm_with_sound)
    
    def _move_selection_with_sound(self, delta: int):
        """
        移动选择（带音效）
        Move selection with sound
        
        Args:
            delta: 移动步数
        """
        # 播放选择音效
        self.sound_manager.play_select_sound()
        # 执行选择移动
        self.selection_manager.move_selection(delta)
    
    def _change_category_with_sound(self, delta: int):
        """
        切换分类（带音效）
        Change category with sound
        
        Args:
            delta: 切换步数
        """
        # 播放切换分类音效
        self.sound_manager.play_fast_sound()
        # 执行分类切换
        self.change_category(delta)
    
    def _cancel_with_sound(self):
        """
        返回操作（带音效）
        Cancel operation with sound
        """
        # 播放返回音效
        self.sound_manager.play_cancel_sound()
    
    def _confirm_with_sound(self):
        """
        确认选择（带音效）
        Confirm selection with sound
        """
        # 播放确认音效
        self.sound_manager.play_confirm_sound()
    
    def _toggle_favorite_callback(self):
        """
        收藏切换回调
        Toggle favorite callback
        """
        if self.buttons and self.selected_index < len(self.buttons):
            self._toggle_favorite(self.buttons[self.selected_index])
    
    def _toggle_practice_callback(self):
        """
        练习模式切换回调
        Toggle practice mode callback
        """
        if self.buttons and self.selected_index < len(self.buttons):
            self._toggle_practice_mode(self.buttons[self.selected_index])
    
    def _quit_callback(self):
        """
        退出回调
        Quit callback
        """
        pygame.quit()
        exit()
    
    
    def _update_buttons(self):
        """
        根据选中的分类更新按钮列表
        Update buttons based on selected category
        
        处理逻辑：
        1. 根据当前分类获取歌曲列表
        2. 对歌曲进行排序（支持数字前缀）
        3. 为每首歌曲创建SongButton对象
        4. 传递分类信息给按钮
        """
        # ==================== 获取歌曲列表 ====================
        songs = self.data_organizer.get_songs_for_category(self.current_category)
        
        # ==================== 排序歌曲 ====================
        # 使用数据组织器的排序功能
        sorted_songs = self.data_organizer.sort_songs(songs)
        
        # ==================== 创建按钮 ====================
        self.buttons = []
        for i, (title, path) in enumerate(sorted_songs):
            # 确定分类：如果是All分类，则从路径中提取实际分类
            if self.current_category == "All":
                category = self.data_organizer.get_category_for_song(path)
            else:
                category = self.current_category
            
            # 创建歌曲按钮对象
            self.buttons.append(SongButton(title, path, i, category))
    
    
    
        
    def run(self) -> Tuple[Path, str]:
        """
        运行歌曲选择界面
        Run song selection interface
        
        主循环处理：
        1. 事件处理（键盘、鼠标）
        2. 平滑滚动更新
        3. 动画状态更新
        4. 界面绘制
        
        返回:
            Tuple[Path, str]: (歌曲路径, 难度, 分类) 或 None（退出）
        """
        running = True
        
        # ==================== 主循环 ====================
        while running:
            # 获取所有事件
            events = pygame.event.get()
            
            # 使用事件处理器处理事件
            result = self.event_handler.process_events(
                events, self.buttons, self.selection_manager.get_selected_index(),
                self.current_category, self.categories, self.selected_category_index,
                self.scroll_manager.get_scroll_offset(), self.width, self.height
            )
            
            # 如果事件处理器返回了结果，处理它
            if result is not None:
                if result == "quit":
                    return None
                elif isinstance(result, tuple) and len(result) == 3:
                    # 保存上次选择
                    song_path, difficulty, category = result
                    self.config.set_last_selected(str(song_path), difficulty, category)
                    return result
            
            # ==================== 更新滚动 ====================
            self.scroll_manager.update_scroll(self.buttons, self.selection_manager.get_selected_index())
            
            # 更新闪烁动画
            self.blink_time += self.clock.get_time()
            
            self._draw()
            self.clock.tick(60)
    
    
    
    
    def change_category(self, delta: int):
        """Change category left/right"""
        self.selected_category_index = (self.selected_category_index + delta) % len(self.categories)
        self.current_category = self.categories[self.selected_category_index]
        self._update_buttons()
        self.selection_manager.set_buttons(self.buttons)  # 更新按钮列表
        self.selection_manager.reset_selection()  # 重置选择到第一个
    
    
    def _toggle_favorite(self, button: SongButton):
        """Toggle favorite status for a song"""
        # TODO: Implement favorite functionality
        print(f"Toggled favorite for: {button.title}")
    
    def _toggle_practice_mode(self, button: SongButton):
        """Toggle practice mode for a song"""
        if self.practice_generating:
            return  # Don't allow multiple generations
            
        self.practice_mode = not self.practice_mode
        if self.practice_mode:
            print(f"Starting practice mode for: {button.title}")
            self._generate_practice_audio(button)
        else:
            print(f"Stopped practice mode for: {button.title}")
            self.practice_audio_paths = {}
    
    def _generate_practice_audio(self, button: SongButton):
        """Generate practice audio files for different speeds"""
        import threading
        import subprocess
        import tempfile
        
        self.practice_generating = True
        
        def generate_audio():
            # Find audio file
            audio_file = None
            for ext in ['.ogg', '.wav', '.mp3']:
                test_path = button.tja_path.with_suffix(ext)
                if test_path.exists():
                    audio_file = test_path
                    break
            
            if not audio_file:
                print(f"No audio file found for {button.title}")
                self.practice_generating = False
                return
            
            # Create cache directory
            cache_dir = Path("cache") / "practice_audio"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            for speed in self.practice_speeds:
                if speed == 1.0:
                    self.practice_audio_paths[speed] = audio_file
                    continue
                
                output_path = cache_dir / f"{audio_file.stem}_{speed}x.ogg"
                self.practice_audio_paths[speed] = output_path
                
                if output_path.exists():
                    print(f"Using cached practice audio for {speed}x: {output_path}")
                    continue
                
                print(f"Generating practice audio for {speed}x...")
                try:
                    result = subprocess.run([
                        "ffmpeg",
                        "-i", str(audio_file),
                        "-filter:a", f"atempo={speed}",
                        "-vn",
                        "-acodec", "libvorbis",
                        "-q:a", "5",
                        str(output_path),
                        "-y"
                    ], check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    print(f"Finished generating {speed}x audio.")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"Error generating practice audio for {speed}x: {e}")
                    if isinstance(e, subprocess.CalledProcessError):
                        print("FFmpeg stderr:", e.stderr)
                    self.practice_audio_paths[speed] = None
            
            self.practice_generating = False
            print("All practice audio generated.")
        
        threading.Thread(target=generate_audio).start()
    
    def _draw(self):
        """
        绘制选择界面
        Draw selection screen
        """
        # ==================== 绘制主界面 ====================
        # 绘制提示文字
        selected_index = self.selection_manager.get_selected_index()
        if self.buttons and selected_index < len(self.buttons) and self.buttons[selected_index].expanded:
            hint = "Click: Choose Difficulty | F/J/Enter: Confirm | ESC: Back"
        else:
            hint = "↑↓/D/K: Song | ←→: Category | F/J/Enter: Select | Click: Difficulty"
        
        self.ui_renderer.draw_main_screen("SELECT SONG", hint)
        
        # ==================== 绘制分类选择器 ====================
        self.ui_renderer.draw_categories(self.categories, self.selected_category_index)
        
        # ==================== 绘制歌曲按钮 ====================
        if self.buttons:
            self.ui_renderer.draw_song_buttons(
                self.buttons, self.selection_manager.get_selected_index(), 
                self.scroll_manager.get_scroll_offset(), self.blink_time
            )
        
        # ==================== 刷新显示 ====================
        self.ui_renderer.flip_display()
    
    
    

