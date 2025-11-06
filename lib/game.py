"""
TaikoMini Game Logic
Simplified Taiko game with basic gameplay

重构版本 - 使用模块化架构
"""

import pygame
import gc
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

# Import from original tja.py
from lib.tja import Note, Drumroll, Balloon
from lib.audio import AudioEngine

# Import new modular components
from lib.combo_display import ComboDisplay
from lib.game_input import InputHandler
from lib.note_judgment import NoteJudgment
from lib.sound_manager import SoundManager
from lib.game_renderer import GameRenderer
from lib.game_controls import GameControls
from lib.practice_controls import PracticeControls
from lib.timing_manager import TimingManager
from lib.song_info_display import SongInfoDisplay
from lib.score_manager import ScoreManager
from lib.lrc_parser import LRCParser, find_lrc_file
from lib.srt_parser import SRTParser, find_srt_file
from lib.lyric_renderer import LyricRenderer
from lib.resource_loader import ResourceLoader
from lib.result_screen import ResultScreen
# from lib.memory_monitor import get_monitor  # 已禁用 - 影响性能

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (230, 74, 25)
BLUE = (0, 162, 232)
ORANGE = (247, 152, 36)
YELLOW = (255, 242, 0)
GREEN = (0, 200, 100)
GRAY = (127, 127, 127)
DARK_GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 150, 255)

# Judgment windows (milliseconds)
PERFECT_WINDOW = 25   # ±25ms = Perfect
GOOD_WINDOW = 75      # ±75ms = Good
OK_WINDOW = 108       # ±108ms = OK

# Layout ratios (based on window size percentage)
GAME_AREA_RATIO = 0.20   # Game area occupies 20% of screen height (orange strip)
JUDGE_X_RATIO = 0.15     # Judge line position (15% from left)

# === 可调整的大鼓布局 ===
# 鼓的大小 (相对于窗口宽度). 默认: 0.40, 增加了20% -> 0.48
DRUM_RATIO = 0.48
# 鼓的垂直偏移量 (相对于鼓自身的高度). 0.0 为贴紧底部, 0.2 为向下移动20%, 使其部分在屏幕外.
DRUM_Y_OFFSET_RATIO = 0.20
# =======================

# Game timing constants
NOTE_LEAD_TIME = 1500    # Note lead time (milliseconds) - time from screen right to judge line

class TaikoGame:
    def __init__(self, screen, chart_data: Dict, audio_path: Path, song_category: str = "", tja_path: Path = None):
        self.screen = screen
        self.chart_data = chart_data
        self.audio_path = audio_path
        self.song_category = song_category  # 歌曲分类
        self.tja_path = tja_path if tja_path else audio_path  # TJA文件路径（用于保存成绩ID）

        # === 音频引擎 ===
        self.audio_engine = AudioEngine()
        
        # === 时间管理器 ===
        offset_seconds = chart_data.get('offset', 0)
        self.timing_manager = TimingManager(self.audio_engine, offset_seconds * 1000)
        
        # 配置管理器（用于读取配置）
        from lib.config_manager import ConfigManager
        from lib.game_settings import GameSettings
        self.config = ConfigManager()
        self.game_settings = GameSettings()
        
        # 设置目标帧率
        self.target_fps = self.game_settings.get_target_fps()
        
        # 初始化歌曲信息显示（传递配置管理器）
        self.song_info_display = SongInfoDisplay(screen, self.config)
        
        # 设置歌曲信息显示位置（直接控制整个区域的位置）
        self.song_info_display.set_position(
            right_margin=30,
            top_margin=100,  # 直接设置Y位置（如需调整，直接修改此值）
            vertical_spacing=15
        )
        
        # 从配置文件读取字体大小和描边设置
        try:
            # 读取配置值并去除行内注释（支持 # 注释）
            title_size_str = self.config.get_display_setting('title_font_size', '84').split('#')[0].strip()
            category_size_str = self.config.get_display_setting('category_font_size', '26').split('#')[0].strip()
            title_outline_str = self.config.get_display_setting('title_outline', '3').split('#')[0].strip()
            category_outline_str = self.config.get_display_setting('category_outline', '2').split('#')[0].strip()
            
            title_size = int(title_size_str)
            category_size = int(category_size_str)
            title_outline = int(title_outline_str)
            category_outline = int(category_outline_str)
        except Exception as e:
            # 如果配置读取失败，使用默认值
            print(f"Warning: Failed to read display settings ({e}), using defaults")
            title_size = 84
            category_size = 26
            title_outline = 3
            category_outline = 2
        
        self.song_info_display.set_font_sizes(
            title_size=title_size,
            category_size=category_size
        )
        self.song_info_display.set_outline(
            title_outline=title_outline,
            category_outline=category_outline
        )
        
        # 歌名和分类
        self.song_title = chart_data.get('title', '')
        self.category_color = self._load_category_color()
        # ====================
        
        # 鼓动画时间变量
        self.drum_don_left_time = -10000
        self.drum_don_right_time = -10000
        self.drum_kat_left_time = -10000
        self.drum_kat_right_time = -10000
        self.drum_press_time = -10000
        
        # Note list (with branching support)
        master_notes = chart_data['notes']
        self.notes: List[Note] = master_notes.play_notes
        self.bars: List[Note] = master_notes.bars
        self.branch_m = chart_data.get('branch_m', [])
        self.branch_n = chart_data.get('branch_n', [])
        self.branch_e = chart_data.get('branch_e', [])
        
        # 应用谱面偏移（正数提前 负数延后）
        chart_offset = self.game_settings.get_chart_offset()
        if chart_offset != 0:
            for note in self.notes:
                note.hit_ms -= chart_offset  # 正数减 = 提前
                note.load_ms -= chart_offset
            for bar in self.bars:
                bar.hit_ms -= chart_offset
                bar.load_ms -= chart_offset
            # 同样应用到分支谱面
            for branch_notes in [self.branch_m, self.branch_n, self.branch_e]:
                if branch_notes and hasattr(branch_notes, 'play_notes'):
                    for note in branch_notes.play_notes:
                        note.hit_ms -= chart_offset
                        note.load_ms -= chart_offset
                if branch_notes and hasattr(branch_notes, 'bars'):
                    for bar in branch_notes.bars:
                        bar.hit_ms -= chart_offset
                        bar.load_ms -= chart_offset
            print(f"Applied chart offset: {chart_offset:+.0f}ms")
        
        # === 计算真打分数系统（需要在notes被赋值后） ===
        self.base_note_score = self._calculate_shinuchi_score()
        
        # === 模块初始化（需要在真打分数计算后） ===
        self.renderer = GameRenderer(screen)
        
        # === 歌词系统（优先使用SRT，支持时间范围）===
        # 优先查找SRT字幕文件（带开始/结束时间）
        srt_path = find_srt_file(self.tja_path)
        lrc_path = find_lrc_file(self.tja_path)
        
        self.lyric_parser = None  # 统一的歌词解析器接口
        
        if srt_path:
            print(f"[Lyric] Found SRT file: {srt_path}")
            self.lyric_parser = SRTParser(srt_path)
            if self.lyric_parser.has_lyrics():
                print(f"[SRT] Loaded {len(self.lyric_parser.subtitles)} subtitle entries")
            else:
                print(f"[SRT] File found but no subtitles parsed")
                self.lyric_parser = None
        
        # 如果没有SRT，尝试使用LRC
        if not self.lyric_parser and lrc_path:
            print(f"[Lyric] Found LRC file: {lrc_path}")
            self.lyric_parser = LRCParser(lrc_path)
            if self.lyric_parser.has_lyrics():
                print(f"[LRC] Loaded {len(self.lyric_parser.lyrics)} lyric lines")
            else:
                print(f"[LRC] File found but no lyrics parsed")
                self.lyric_parser = None
        
        if not self.lyric_parser:
            print(f"[Lyric] No lyric file found (searched for .srt and .lrc)")
        
        self.lyric_renderer = LyricRenderer(screen)
        
        # 初始化结算画面渲染器
        self.resource_loader = ResourceLoader()
        self.result_screen = ResultScreen(screen, self.resource_loader)
        
        self.input_handler = InputHandler()
        self.note_judgment = NoteJudgment(base_note_score=self.base_note_score)
        self.combo_display = ComboDisplay()
        self.game_controls = GameControls(screen)
        self.practice_controls = PracticeControls(screen)
        self.sound_manager = SoundManager()
        
        # Save original note types and lists for restart
        self.original_note_types = {id(note): note.type for note in self.notes}
        self.original_notes = list(self.notes)  # 保存初始音符列表（分支前）
        self.original_bars = list(self.bars)    # 保存初始小节线列表（分支前）
        
        # 同时保存分支音符的原始类型（用于复位）
        self.original_branch_note_types = {}
        for branch_notes in [self.branch_m, self.branch_n, self.branch_e]:
            if branch_notes:
                for branch_section in branch_notes:
                    if hasattr(branch_section, 'play_notes'):
                        for note in branch_section.play_notes:
                            self.original_branch_note_types[id(note)] = note.type
        
        self.branch_index = 0
        
        # Find all bars that trigger a branch choice
        self.branch_bars = sorted(
            [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
            key=lambda b: b.hit_ms
        )
        self.next_branch_idx = 0
        
        # 延迟分支判断：记录分支小节开始时的状态
        self.pending_branch_bar = None  # 待判断的分支小节线
        self.branch_section_start_perfect = 0  # 分支小节开始时的Perfect数
        self.branch_section_start_drumroll_hits = 0  # 分支小节开始时的连打数
        self.current_note_index = 0
        
        # Timing
        self.clock = pygame.time.Clock()
        
        # Performance monitoring
        # 移除性能监控以提升性能
        self.frames_elapsed = -1
        
        # Statistics
        self.score = 0
        self.combo = 0
        self.max_combo = 0  # 最大连段数
        self.perfect_count = 0
        self.good_count = 0
        self.ok_count = 0
        self.miss_count = 0
        self.drumroll_hits = 0  # 连打总数
        
        # Score manager
        self.score_manager = ScoreManager()
        
        # Control state
        self.is_paused = False
        self.playback_speed = 1.0
        self.is_dragging_slider = False
        self._speed_changed = False
        
        # 从配置文件读取自动演奏设置
        try:
            auto_play_config = self.config.get_game_setting('auto_play', 'false').lower()
            self.auto_play = auto_play_config == 'true'
            self.practice_controls.set_auto_play_state(self.auto_play)
            if self.auto_play:
                print("Auto Play: ON (from config)")
        except:
            self.auto_play = False
        
        # Practice mode
        self.is_practice_mode = False
        self.practice_audio_paths = {}
        self.current_practice_speed = 1.0
        self.practice_music_streams = {}
        
        # Drumroll/Balloon state
        self.active_drumroll = None
        self.last_drumroll_hit_time = 0
        
        # Metronome (节拍器) state
        self.metronome_events = []  # 节拍器事件列表 [(time_ms, sound_type), ...]
        self.metronome_event_index = 0  # 当前待播放的节拍器事件索引

        # Load sound effects
        self._load_sounds()
        
        # Generate metronome events for slow speed mode
        self._generate_metronome_events()
        
        # Update layout and UI elements
        self._update_ui_layout()
    
    def _load_category_color(self):
        """从配置文件加载分类颜色"""
        try:
            return self.config.get_category_color(self.song_category)
        except Exception as e:
            print(f"Error loading category color: {e}")
            return None
    
    def _calculate_shinuchi_score(self):
        """
        计算真打分数系统的每音符基础分数
        完全按照parse_tja.py中的规则计算
        目标总分: 1,000,000分
        
        对于有分支的谱面，始终按照达人分支（M）的音符数量计算
        这样无论实际进入哪个分支，满分都是1,000,000
        """
        import math
        
        # 统计主路径音符数量
        note_count = 0
        balloon_count = 0
        
        for note in self.notes:
            if note.type in [1, 2, 3, 4]:  # don, ka, big don, big ka
                note_count += 1
            elif note.type in [7, 9]:  # balloon, 草
                balloon_count += 1
        
        # 统计分支音符数量（始终使用达人分支M，确保分数一致性）
        # 分支谱面的音符总数 = 主路径音符 + 达人分支音符
        branch_note_count = 0
        branch_balloon_count = 0
        branch_type = "None"
        
        # 始终优先使用达人分支 (Master) 来计算分数
        if self.branch_m:
            branch_type = "Master (M)"
            for branch_notelist in self.branch_m:
                for note in branch_notelist.play_notes:
                    if note.type in [1, 2, 3, 4]:
                        branch_note_count += 1
                    elif note.type in [7, 9]:
                        branch_balloon_count += 1
        # 如果没有达人分支，尝试玄人分支 (Expert)
        elif self.branch_e:
            branch_type = "Expert (E)"
            for branch_notelist in self.branch_e:
                for note in branch_notelist.play_notes:
                    if note.type in [1, 2, 3, 4]:
                        branch_note_count += 1
                    elif note.type in [7, 9]:
                        branch_balloon_count += 1
        # 如果没有玄人分支，尝试普通分支 (Normal)
        elif self.branch_n:
            branch_type = "Normal (N)"
            for branch_notelist in self.branch_n:
                for note in branch_notelist.play_notes:
                    if note.type in [1, 2, 3, 4]:
                        branch_note_count += 1
                    elif note.type in [7, 9]:
                        branch_balloon_count += 1
        
        # 总音符数 = 主路径 + 分支音符
        total_note_count = note_count + branch_note_count
        total_balloon_count = balloon_count + branch_balloon_count
        
        # 固定的连打速度（每秒次数）假设为5次/秒
        # 这里暂时假设没有连打，或者连打分数很少
        drumroll_score = 0
        
        # 气球分数：每个气球100分
        balloon_score = total_balloon_count * 100
        
        # 音符分数计算
        remaining_score = 1000000 - balloon_score - drumroll_score
        
        if total_note_count > 0:
            # 计算每个音符的基础分数
            per_note_score = remaining_score / total_note_count
            # 除以10后向上取整，再乘以10
            per_note_score = math.ceil(per_note_score / 10) * 10
        else:
            per_note_score = 100  # 默认值
        
        # 调试输出
        if branch_note_count > 0:
            print(f"[Shinuchi Score] Score Calculation Branch: {branch_type}")
            print(f"[Shinuchi Score] Master Notes: {note_count}, Branch Notes: {branch_note_count}, Total: {total_note_count}")
            print(f"[Shinuchi Score] Balloons: {total_balloon_count}")
        else:
            print(f"[Shinuchi Score] Notes: {total_note_count}, Balloons: {total_balloon_count}")
        print(f"[Shinuchi Score] Per Note: {per_note_score}, Total Target: ~1,000,000")
        
        return per_note_score
    
    def restart(self):
        """Resets the game to its initial state for a restart."""
        # 保存自动演奏状态（重启时保持）
        current_auto_play = self.auto_play
        
        # Reset timing
        self.timing_manager.reset()
        
        # Reset statistics
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.ok_count = 0
        self.miss_count = 0
        self.drumroll_hits = 0
        
        # Reset note state
        self.current_note_index = 0
        
        # 恢复初始的音符和小节线列表（分歧谱面会动态添加音符）
        self.notes = list(self.original_notes)
        self.bars = list(self.original_bars)
        
        # 恢复音符类型
        for note in self.notes:
            if id(note) in self.original_note_types:
                note.type = self.original_note_types[id(note)]
        
        # 恢复分支音符的类型（关键修复：确保分支音符在复位后状态正确）
        for branch_notes in [self.branch_m, self.branch_n, self.branch_e]:
            if branch_notes:
                for branch_section in branch_notes:
                    if hasattr(branch_section, 'play_notes'):
                        for note in branch_section.play_notes:
                            if id(note) in self.original_branch_note_types:
                                note.type = self.original_branch_note_types[id(note)]
        
        # 重新计算分支小节线列表
        self.branch_bars = sorted(
            [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
            key=lambda b: b.hit_ms
        )
        
        # Reset branch logic
        self.branch_index = 0
        self.next_branch_idx = 0
        self.pending_branch_bar = None
        self.branch_section_start_perfect = 0
        self.branch_section_start_drumroll_hits = 0
        
        # Reset drumroll state
        self.active_drumroll = None
        self.note_judgment.active_drumroll = None
        self.note_judgment.last_drumroll_hit_time = 0  # 重置连打时间
        
        # Reset judgment display state
        self.note_judgment.current_judgment = ""
        self.note_judgment.judgment_time = 0
        self.note_judgment.is_super_large_note = False
        
        # 清除输入处理器状态，避免积累音符
        self.input_handler.last_auto_hit_index = -1
        self.input_handler.last_drumroll_hit_time = 0
        self.input_handler._last_auto_drumroll_time = 0
        
        # 重置鼓动画时间
        self.drum_don_left_time = -10000
        self.drum_don_right_time = -10000
        self.drum_kat_left_time = -10000
        self.drum_kat_right_time = -10000
        self.drum_press_time = -10000

        # Stop current audio and reload it with the new speed
        self.audio_engine.stop()
        if not self.audio_engine.load_sound(str(self.audio_path)):
             print("Failed to reload audio on restart.")
             return # Or handle error appropriately
        
        self.timing_manager.playback_speed = self.playback_speed
        
        # 变速模式下静音播放音乐，使用节拍器
        self.audio_engine.play()
        
        if self.playback_speed != 1.0:
            # 变速模式（慢速/快速）：静音背景音乐，使用节拍器
            pygame.mixer.music.set_volume(0.0)
            self.metronome_event_index = 0
            print(f"[Metronome] Variable speed mode ({self.playback_speed}x): Music muted, metronome ready with {len(self.metronome_events)} events")
        else:
            # 正常速度：恢复音乐音量
            pygame.mixer.music.set_volume(1.0)
        
        self.timing_manager.start()

        # Reset controls state if needed
        self.is_paused = False

        # Reset renderer state
        self.renderer.reset()
        self.frames_elapsed = -1
        
        # 恢复自动演奏状态（确保 practice_controls 与 self.auto_play 同步）
        self.auto_play = current_auto_play
        self.practice_controls.set_auto_play_state(self.auto_play)

    def _load_sounds(self):
        """Load sound effects from the 'wav' resource folder."""
        try:
            sound_dir = Path("lib/res/wav")
            if not sound_dir.exists():
                print("Warning: Sound directory not found")
                self.sound_don = None
                self.sound_kat = None
                self.metronome_se01 = None
                self.metronome_se02 = None
                return
                
            don_file = sound_dir / "taiko_don.wav"
            kat_file = sound_dir / "taiko_ka.wav"
            se01_file = sound_dir / "se_01.wav"
            se02_file = sound_dir / "se_02.wav"
            
            if don_file.exists():
                self.sound_don = pygame.mixer.Sound(str(don_file))
                print(f"Loaded: {don_file.name}")
            else:
                self.sound_don = None
                print(f"Warning: {don_file.name} not found")
                
            if kat_file.exists():
                self.sound_kat = pygame.mixer.Sound(str(kat_file))
                print(f"Loaded: {kat_file.name}")
            else:
                self.sound_kat = None
                print(f"Warning: {kat_file.name} not found")
                
            # 加载节拍器音效
            if se01_file.exists():
                self.metronome_se01 = pygame.mixer.Sound(str(se01_file))
                print(f"Loaded metronome: {se01_file.name}")
            else:
                self.metronome_se01 = None
                print(f"Warning: {se01_file.name} not found")
                
            if se02_file.exists():
                self.metronome_se02 = pygame.mixer.Sound(str(se02_file))
                print(f"Loaded metronome: {se02_file.name}")
            else:
                self.metronome_se02 = None
                print(f"Warning: {se02_file.name} not found")
                
        except Exception as e:
            print(f"Error loading sounds: {e}")
            self.sound_don = None
            self.sound_kat = None
            self.metronome_se01 = None
            self.metronome_se02 = None

    def _generate_metronome_events(self):
        """
        生成节拍器事件列表
        根据小节线的拍号，在慢速模式下播放节拍器音效
        
        注意：如果在游戏中途调用（如分歧后），会保持当前播放位置
        """
        # 保存当前游戏时间（如果已经开始播放）
        current_time = self.timing_manager.get_game_time() if hasattr(self, 'timing_manager') else 0
        
        self.metronome_events = []
        
        try:
            for bar in self.bars:
                # 获取拍号（如4/4拍=1.0, 3/4拍=0.75, 8/4拍=2.0）
                time_sig = getattr(bar, 'time_signature', 1.0)
                
                # 计算拍数（例如：1.0 -> 4拍, 0.75 -> 3拍, 2.0 -> 8拍）
                beat_count = int(time_sig * 4)
                
                if beat_count < 1:
                    beat_count = 1
                
                # 计算这个小节的持续时间
                bpm = getattr(bar, 'bpm', 120.0)
                if bpm <= 0:
                    bpm = 120.0
                
                ms_per_measure = 60000 * (time_sig * 4) / bpm
                ms_per_beat = ms_per_measure / beat_count
                
                # 第一拍使用 se_01
                self.metronome_events.append((bar.hit_ms, 'se01'))
                
                # 剩余拍使用 se_02
                for beat_num in range(1, beat_count):
                    beat_time = bar.hit_ms + (beat_num * ms_per_beat)
                    self.metronome_events.append((beat_time, 'se02'))
            
            # 按时间排序
            self.metronome_events.sort(key=lambda x: x[0])
            
            # 如果在游戏中途重新生成（如分歧后），更新播放索引到当前时间
            self.metronome_event_index = 0
            for i, (event_time, _) in enumerate(self.metronome_events):
                if event_time > current_time:
                    self.metronome_event_index = i
                    break
            else:
                # 所有事件都已过期
                self.metronome_event_index = len(self.metronome_events)
            
            print(f"[Metronome] Generated {len(self.metronome_events)} metronome events (index: {self.metronome_event_index})")
        except Exception as e:
            print(f"[Metronome] Error generating metronome events: {e}")
            self.metronome_events = []
    
    def _play_metronome(self, game_time):
        """
        播放节拍器音效（仅在慢速模式下）
        
        Args:
            game_time: 当前游戏时间（毫秒）
        """
        # 检查是否有待播放的节拍器事件
        played_count = 0
        while (self.metronome_event_index < len(self.metronome_events) and 
               self.metronome_events[self.metronome_event_index][0] <= game_time):
            
            event_time, sound_type = self.metronome_events[self.metronome_event_index]
            
            # 播放对应的音效
            if sound_type == 'se01' and self.metronome_se01:
                self.metronome_se01.play()
                played_count += 1
            elif sound_type == 'se02' and self.metronome_se02:
                self.metronome_se02.play()
                played_count += 1
            
            self.metronome_event_index += 1
        
        # 节拍器播放完成（不打印避免影响性能）
    
    def _update_ui_layout(self):
        """
        Dynamically updates UI element positions based on the current window size.
        """
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # Calculate layout areas
        self.game_area_height = int(self.screen_height * GAME_AREA_RATIO)
        self.game_area_top = int((self.screen_height - self.game_area_height) * 0.35)  # Mid-upper position
        self.game_area_bottom = self.game_area_top + self.game_area_height
        
        # Judge position
        self.judge_x = int(self.screen_width * JUDGE_X_RATIO)
        self.judge_y = self.game_area_top + self.game_area_height // 2
        self.judge_radius = int(min(self.screen_width, self.screen_height) * 0.05)
        
        # Update controls layout
        self.game_controls.update_layout()
        self.practice_controls.update_layout()
        
        # Drum position (lower part)
        self.drum_center_x = self.screen_width // 2
        self.drum_radius = int(self.screen_width * DRUM_RATIO)
        
        # Scale drum image to fit screen width
        if self.renderer.drum_img:
            drum_width = self.drum_radius * 2
            drum_height = int(self.renderer.drum_img.get_height() * drum_width / self.renderer.drum_img.get_width())
            drum_size = (drum_width, drum_height) # This size is used for the entire group

            # Scale all three images to the exact same size to act as a container group
            self.renderer.scaled_drum_img = pygame.transform.smoothscale(self.renderer.drum_img, drum_size)
            if self.renderer.drum_don_hit_img:
                self.renderer.scaled_don_hit_img = pygame.transform.smoothscale(self.renderer.drum_don_hit_img, drum_size)
            if self.renderer.drum_kat_hit_img:
                self.renderer.scaled_kat_hit_img = pygame.transform.smoothscale(self.renderer.drum_kat_hit_img, drum_size)
            
            # Align drum to the bottom of the screen, with a vertical offset
            y_offset = int(self.renderer.scaled_drum_img.get_height() * DRUM_Y_OFFSET_RATIO)
            self.drum_center_y = self.screen_height - self.renderer.scaled_drum_img.get_height() // 2 + y_offset
        else:
            # Fallback if image isn't loaded
            self.drum_center_y = int(self.screen_height * 0.75)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

    def run(self):
        """Main game loop."""
        # 内存监控已禁用
        # memory_monitor = get_monitor()
        # memory_monitor.full_report("Game Start")
        
        # Load audio using the new engine
        if not self.audio_engine.load_sound(str(self.audio_path)):
            return False  # Return False if audio loading fails
        
        # Apply initial speed setting
        self.timing_manager.playback_speed = self.playback_speed
        
        # Start playback (变速模式下静音播放音乐，使用节拍器)
        self.audio_engine.play()
        
        if self.playback_speed != 1.0:
            # 变速模式（慢速/快速）：静音背景音乐，使用节拍器
            pygame.mixer.music.set_volume(0.0)
            self.metronome_event_index = 0
            print(f"Variable speed mode ({self.playback_speed}x): Music muted, using metronome")
        else:
            # 正常速度：恢复音乐音量
            pygame.mixer.music.set_volume(1.0)
            print(f"Normal speed mode ({self.playback_speed}x): Playing music")
        
        self.timing_manager.start()
        
        running = True
        while running:
            # --- Event Handling (delegated to InputHandler) ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    # 播放返回音效
                    self.sound_manager.play_cancel_sound()
                    running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    self._update_ui_layout()
                
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # ESC键返回选曲界面
                    self.sound_manager.play_cancel_sound()
                    running = False
                
                else:
                    # Handle game controls (always use practice controls)
                    action = self.practice_controls.handle_event(event, self.playback_speed, self.is_paused)
                    
                    if action:
                        if action['action'] == 'toggle_pause':
                            self.is_paused = not self.is_paused
                            # 播放暂停音效
                            self.sound_manager.play_pause_sound()
                            if self.is_paused:
                                self.timing_manager.pause()
                            else:
                                self.timing_manager.unpause()
                        elif action['action'] == 'restart':
                            # 播放返回音效
                            self.sound_manager.play_cancel_sound()
                            # 直接重启游戏，不退出循环
                            self.restart()
                        elif action['action'] == 'toggle_auto':
                            self.auto_play = not self.auto_play
                            self.practice_controls.set_auto_play_state(self.auto_play)
                            print(f"Auto Play: {'ON' if self.auto_play else 'OFF'}")
                        elif action['action'] == 'change_speed':
                            new_speed = action['value']
                            # 切换速度会重新开始（因为技术限制无法完美保持位置）
                            self.playback_speed = new_speed
                            print(f"Changing speed to {new_speed}x, game will restart")
                            
                            # 变速模式切换
                            if new_speed != 1.0:
                                print(f"Switching to variable speed mode: Metronome enabled")
                            else:
                                print(f"Switching to normal speed mode: Music enabled")
                            
                            self.restart()

                    # Handle gameplay input
                    self.input_handler.handle_event(
                        event,
                        self.timing_manager.get_game_time(),
                        self._try_hit_manual,
                        self.screen.get_width()
                    )

            # --- Game Logic ---
            if not self.is_paused:
                game_time = self.timing_manager.get_game_time()
                
                # 节拍器播放（变速模式下）
                if self.playback_speed != 1.0:
                    self._play_metronome(game_time)
                
                # 同步自动演奏状态（从控制按钮）
                self.auto_play = self.practice_controls.get_auto_play_state()
                
                # 检查连打结束
                self._check_drumroll_end(game_time)
                
                if self.frames_elapsed >= 0:
                    self.input_handler.auto_play_notes(
                        self.auto_play,
                        self.current_note_index,
                        self.notes,
                        game_time,
                        self._try_hit,
                        self.active_drumroll,  # 传递连打状态
                        self,  # 传递game对象用于更新鼓动画时间
                        self.sound_don,  # 传递音效
                        self.sound_kat   # 传递音效
                    )
                
                self._check_miss()
                self._check_branching()  # 标记待判断的分支小节
                self._check_pending_branch()  # 执行待判断的分支
                
                # Check for game end
                if not self.audio_engine.is_busy():
                    running = False

            # --- Drawing ---
            self._draw()
            
            if self.frames_elapsed < 0:
                self.frames_elapsed = 0
            else:
                self.frames_elapsed += 1
            # 使用配置的目标帧率，无论播放速度如何都保持固定帧率
            self.clock.tick(self.target_fps)
            
        self.audio_engine.stop()
        
        # 保存分数记录
        self._save_score_record()
        
        # 显示结算画面
        self._show_result()
        
        # 内存监控已禁用
        # memory_monitor = get_monitor()
        # memory_monitor.full_report("Game End - Before GC")
        
        # 游戏结束后手动触发垃圾回收
        gc.collect()
        
        # 内存监控已禁用
        # memory_monitor.full_report("Game End - After GC")
        
        return False
    
    def _save_score_record(self):
        """保存游戏成绩到文件"""
        try:
            # 获取歌曲ID（TJA文件名，不含扩展名）
            song_id = self.tja_path.stem
            
            # 获取难度
            difficulty = self.chart_data.get('difficulty', 'Oni')
            
            # 计算总音符数（不包括连打和气球的子音符）
            total_notes = len([n for n in self.notes if n.type in ['don', 'ka', 'big_don', 'big_ka']])
            
            # 保存分数
            self.score_manager.save_score(
                song_id=song_id,
                difficulty=difficulty,
                score=self.score,
                perfect_count=self.perfect_count,
                good_count=self.good_count,
                ok_count=self.ok_count,
                miss_count=self.miss_count,
                drumroll_hits=self.drumroll_hits,
                max_combo=self.max_combo,
                total_notes=total_notes
            )
            
            # 打印成绩统计
            print("\n=== Game Results ===")
            print(f"Song: {song_id}")
            print(f"Difficulty: {difficulty}")
            print(f"Score: {self.score}")
            print(f"Perfect: {self.perfect_count}")
            print(f"Good: {self.good_count}")
            print(f"OK: {self.ok_count}")
            print(f"Miss: {self.miss_count}")
            print(f"Max Combo: {self.max_combo}")
            print(f"Drumroll Hits: {self.drumroll_hits}")
            print("===================\n")
            
        except Exception as e:
            print(f"Error saving score: {e}")
    
    def _handle_keydown(self, key):
        """Handle key press"""
        # Set drum press time for animation
        if key in [pygame.K_f, pygame.K_j, pygame.K_d, pygame.K_k]:
            self.drum_press_time = self.game_time
            
        # Don keys (F/J)
        if key == pygame.K_f:
            self.key_don_left = True
            self.drum_don_left_time = self.game_time
            self._try_hit(is_don=True)
        elif key == pygame.K_j:
            self.key_don_right = True
            self.drum_don_right_time = self.game_time
            self._try_hit(is_don=True)
        # Kat keys (D/K)
        elif key == pygame.K_d:
            self.key_kat_left = True
            self.drum_kat_left_time = self.game_time
            self._try_hit(is_don=False)
        elif key == pygame.K_k:
            self.key_kat_right = True
            self.drum_kat_right_time = self.game_time
            self._try_hit(is_don=False)
    
    def _handle_keyup(self, key):
        """Handle key release"""
        if key == pygame.K_f:
            self.key_don_left = False
        elif key == pygame.K_j:
            self.key_don_right = False
        elif key == pygame.K_d:
            self.key_kat_left = False
        elif key == pygame.K_k:
            self.key_kat_right = False
    
    def _try_hit_manual(self, is_don: bool):
        """手动输入的击打尝试（会检查自动演奏状态）"""
        # 获取实时时间用于鼓动画
        real_time = self.timing_manager.get_real_time()
        
        # 更新鼓按下时间（用于下沉动画）
        self.drum_press_time = real_time
        
        # 更新鼓击打时间（用于闪光效果）
        if is_don:
            # 咚 - 交替左右
            if real_time - self.drum_don_right_time > 100:
                self.drum_don_left_time = real_time
            else:
                self.drum_don_right_time = real_time
        else:
            # 咔 - 交替左右
            if real_time - self.drum_kat_right_time > 100:
                self.drum_kat_left_time = real_time
            else:
                self.drum_kat_right_time = real_time
        
        # 立即播放音效（手动敲击总是有音效）
        if is_don:
            self.sound_don.play()
        else:
            self.sound_kat.play()
        
        # Auto模式下的手动输入也参与判定（可以破坏良率）
        # 只有在有音符时才进行判定
        if self.current_note_index < len(self.notes):
            self._try_hit(is_don)
    
    def _try_hit(self, is_don: bool):
        """Attempts a hit and updates game state based on the judgment."""
        # 获取两种时间
        game_time = self.timing_manager.get_game_time()  # 用于判定
        real_time = self.timing_manager.get_real_time()  # 用于动画
        
        # 在判定之前先检查连打是否该结束了
        self._check_drumroll_end(game_time)
        
        # 如果在连打中，即使索引超出范围也允许击打连打
        if self.active_drumroll:
            # 直接调用note_judgment的连打击打逻辑
            result = self.note_judgment._handle_drumroll_hit(
                is_don, 
                game_time, 
                self.sound_don, 
                self.sound_kat
            )
            
            # 处理连打更新
            if result.get('drumroll_update') is not None:
                self.active_drumroll = result['drumroll_update']
                self.note_judgment.active_drumroll = self.active_drumroll
            
            # 真打系统：连打/气球每次击打实时加100分
            if result['score'] > 0:
                self.score += result['score']
                # 如果是连打击打，计数
                if result.get('drumroll_hit'):
                    self.drumroll_hits += 1
            return
        
        # 不在连打中，检查索引
        if self.current_note_index >= len(self.notes):
            return

        note = self.notes[self.current_note_index]
        
        # Delegate judgment to the NoteJudgment module
        result = self.note_judgment.try_hit(
            is_don,
            note,
            game_time,
            self.sound_don,
            self.sound_kat,
            self.renderer.trigger_hit_animation,
            self.current_note_index,
            real_time,  # 传递实时时间给动画
            self.notes  # 传递音符列表用于获取气球最大敲打数
        )
        
        # 处理连打开始
        if result.get('drumroll_start'):
            # 激活连打状态
            self.active_drumroll = (self.current_note_index, -1, note.type, 0)
            self.note_judgment.active_drumroll = self.active_drumroll
            print(f"Drumroll started: type={note.type}, game_time={game_time:.1f}ms, auto={self.auto_play}")
        
        # 处理连打更新
        if result.get('drumroll_update') is not None:
            self.active_drumroll = result['drumroll_update']
            self.note_judgment.active_drumroll = self.active_drumroll
        
        # 真打系统：连打/气球每次击打实时加100分
        if result['score'] > 0:
            self.score += result['score']
            # 如果是连打击打，计数
            if self.active_drumroll and result.get('drumroll_hit'):
                self.drumroll_hits += 1
        
        # 连打击打：只加分，不计入判定数量
        # Drumroll hits only add score, do not count towards judgment statistics
        
        if result['note_hit']:
            note.type = -1  # Mark note as hit
            self.combo += result['combo_add']
            
            # 更新最大连段数
            if self.combo > self.max_combo:
                self.max_combo = self.combo
            
            if result['judgment'] == "Perfect":
                self.perfect_count += 1
            elif result['judgment'] == "Good":
                self.good_count += 1
            elif result['judgment'] == "OK":
                self.ok_count += 1
        
        if result['advance_index']:
            self.current_note_index += 1
            # print(f"[DEBUG] advance_index: {old_idx} -> {self.current_note_index}")

    def _check_drumroll_end(self, game_time):
        """检查连打/气球是否结束"""
        if not self.active_drumroll:
            return
        
        start_idx, end_idx, dr_type, hits = self.active_drumroll
        
        # 找到结束音符（type=8）
        if end_idx == -1:
            # 还没找到结束音符，搜索它
            for i in range(start_idx + 1, len(self.notes)):
                if self.notes[i].type == 8:
                    end_idx = i
                    self.active_drumroll = (start_idx, end_idx, dr_type, hits)
                    self.note_judgment.active_drumroll = self.active_drumroll
                    break
        
        if end_idx == -1:
            # 没找到结束音符，这是个错误
            return
        
        # 检查是否到达结束时间
        end_note = self.notes[end_idx]
        end_time = end_note.hit_ms if hasattr(end_note, 'hit_ms') else end_note.time_ms
        
        if game_time >= end_time:
            # 连打结束 - 不额外加分（每次击打已经加了100分）
            score = 0
            self.score += score
            
            # 标记结束音符为已处理
            end_note.type = -1
            
            # 清除连打状态
            self.active_drumroll = None
            self.note_judgment.active_drumroll = None
            self.note_judgment.last_drumroll_hit_time = 0  # 清除连打计时
            
            print(f"Drumroll ended: hits={hits}, score={score}")
            
            # 正确更新索引：移动到结束音符之后
            # 注意：连打开始时 current_note_index 已经 +1，所以现在应该在 start_idx+1
            # 我们需要跳过结束音符，移动到 end_idx+1
            self.current_note_index = end_idx + 1
            # print(f"[DEBUG] drumroll_end: idx {old_idx} -> {self.current_note_index}, start={start_idx}, end={end_idx}")

    def _check_miss(self):
        """Checks for missed notes."""
        if self.current_note_index >= len(self.notes):
            return
        
        game_time = self.timing_manager.get_game_time()
        note = self.notes[self.current_note_index]
        
        # 跳过连打结束标记（移动到下一个音符）
        if note.type == 8:
            self.current_note_index += 1
            return
        
        if self.note_judgment.check_miss(note, game_time):
            self.miss_count += 1
            self.combo = 0
            
            # 如果miss的是连打开始音符（5=连打咚, 6=连打咔, 7=气球, 9=草）
            # 需要跳过整个连打区间，包括结束标记
            if note.type in [5, 6, 7, 9]:
                print(f"[Miss] Drumroll start missed at index {self.current_note_index}, searching for end marker...")
                # 找到对应的连打结束标记（type=8）
                for i in range(self.current_note_index + 1, len(self.notes)):
                    if self.notes[i].type == 8:
                        # 跳过整个连打区间，移动到结束标记之后
                        self.current_note_index = i + 1
                        print(f"[Miss] Skipped drumroll, now at index {self.current_note_index}")
                        return
                # 如果没找到结束标记，只跳过开始音符
                print(f"[Miss] Warning: No end marker found for drumroll")
                self.current_note_index += 1
            else:
                # 普通音符miss，只跳过当前音符
                self.current_note_index += 1

    def _execute_branch(self):
        """
        Execute a branch choice based on player performance.
        分支判断基于玩家表现：良率（Perfect数）或连段数
        """
        game_time = self.timing_manager.get_game_time()
        branch_notelist = None
        branch_name = "None"
        
        # 获取当前分支点的判断条件
        # 分支参数格式：如 "p,80,95" 表示基于良率，E分支80%，M分支95%
        # 或 "r,50,80" 表示基于连段数，E分支50段，M分支80段
        branch_threshold_e = 0  # Expert分支阈值
        branch_threshold_m = 0  # Master分支阈值
        branch_type = 'p'  # 默认基于良率
        
        # 从已保存的待判断分支小节线获取判断条件
        # Use the saved pending branch bar instead of next_branch_idx (which has already been incremented)
        if self.pending_branch_bar is not None:
            branch_bar = self.pending_branch_bar
            # Branch调试输出已禁用
            if hasattr(branch_bar, 'branch_params') and branch_bar.branch_params:
                params_str = branch_bar.branch_params
                # 移除开头的 'r' 或 'p' 标记
                if params_str and len(params_str) > 0:
                    if params_str[0] in ['r', 'p']:
                        branch_type = params_str[0]
                        # 'r,1,2' -> '1,2'，移除 'r' 和紧跟的逗号
                        params_str = params_str[2:] if len(params_str) > 1 and params_str[1] == ',' else params_str[1:]
                    # 解析阈值: "1,2" -> E=1, M=2
                    if ',' in params_str:
                        parts = params_str.split(',')
                        if len(parts) >= 2:
                            try:
                                branch_threshold_e = float(parts[0])
                                branch_threshold_m = float(parts[1])
                                # Branch调试输出已禁用
                            except ValueError as e:
                                pass  # 忽略解析错误
        
        # 如果没有明确的分支条件，使用默认值
        if branch_threshold_e == 0 and branch_threshold_m == 0:
            # 默认值：良率80%进E，95%进M
            branch_type = 'p'
            branch_threshold_e = 80
            branch_threshold_m = 95
        
        # 计算玩家在该分支小节内的表现（增量，而不是全局累计）
        # Calculate player performance within this branch section (delta, not cumulative)
        player_value = 0
        if branch_type == 'p':
            # 基于良率（Perfect比例）- 使用该小节内的Perfect增量
            # Based on Perfect ratio - use Perfect delta within this section
            section_perfect = self.perfect_count - self.branch_section_start_perfect
            section_total = (self.perfect_count + self.good_count + self.ok_count + self.miss_count) - \
                           (self.branch_section_start_perfect + 0 + 0 + 0)  # 简化：假设只有Perfect会增加
            if section_total > 0:
                player_value = (section_perfect / section_total) * 100
            print(f"[Branch Calc] Section Perfect: {section_perfect}/{section_total} = {player_value:.1f}%")
        else:  # branch_type == 'r'
            # 基于连打数（Drumroll Hits）- 使用该小节内的连打增量
            # Based on Drumroll Hits - use drumroll delta within this section
            player_value = self.drumroll_hits - self.branch_section_start_drumroll_hits
            print(f"[Branch Calc] Section Drumroll: {player_value} (current:{self.drumroll_hits}, start:{self.branch_section_start_drumroll_hits})")
        
        # 打印分支判断详情（调试用）
        # Branch调试输出已禁用
        
        # 根据表现选择分支（优先M，然后E，最后N）
        if player_value >= branch_threshold_m and self.branch_m and len(self.branch_m) > self.branch_index:
            branch_notelist = self.branch_m[self.branch_index]
            branch_name = "Master (M)"
        elif player_value >= branch_threshold_e and self.branch_e and len(self.branch_e) > self.branch_index:
            branch_notelist = self.branch_e[self.branch_index]
            branch_name = "Expert (E)"
        elif self.branch_n and len(self.branch_n) > self.branch_index:
            branch_notelist = self.branch_n[self.branch_index]
            branch_name = "Normal (N)"
        # 如果没有对应分支，按优先级回退
        elif self.branch_e and len(self.branch_e) > self.branch_index:
            branch_notelist = self.branch_e[self.branch_index]
            branch_name = "Expert (E)"
        elif self.branch_m and len(self.branch_m) > self.branch_index:
            branch_notelist = self.branch_m[self.branch_index]
            branch_name = "Master (M)"
            
        if branch_notelist:
            # 统计分支音符数量
            branch_note_count = sum(1 for note in branch_notelist.play_notes if note.type in [1, 2, 3, 4])
            print(f"[{game_time / 1000:.2f}s] Branching to: {branch_name} (Notes: {branch_note_count})")

            # Add notes and bars from the selected branch
            self.notes.extend(branch_notelist.play_notes)
            self.bars.extend(branch_notelist.bars)
            
            # Re-sort to maintain chronological order
            self.notes.sort(key=lambda n: n.hit_ms)
            self.bars.sort(key=lambda b: b.hit_ms)

            # Update the list of branch bars since new ones might have been added
            self.branch_bars = sorted(
                [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
                key=lambda b: b.hit_ms
            )
            
            # Regenerate metronome events with the new bars (for variable speed mode)
            self._generate_metronome_events()
            
            # 重新定位 current_note_index 到当前时间之后的第一个未处理的音符
            # 因为 notes 列表被重新排序，旧的索引已经无效
            # 注意：跳过已经处理的音符（type == -1）
            old_index = self.current_note_index
            for i, note in enumerate(self.notes):
                # 跳过已处理的音符，找到第一个未处理且在当前时间之后的音符
                if note.type != -1 and note.hit_ms > game_time - OK_WINDOW:
                    self.current_note_index = i
                    print(f"[Branch] Repositioned index: {old_index} -> {i} (game_time={game_time:.1f}ms, note_time={note.hit_ms:.1f}ms, type={note.type})")
                    break
            else:
                # 所有音符都已经过去
                self.current_note_index = len(self.notes)
                print(f"[Branch] All notes passed, index set to end: {old_index} -> {self.current_note_index}")
        
        # Move to the next set of branches for the next branch point
        # (Always increment, even if no branch was found, to stay in sync with next_branch_idx)
        self.branch_index += 1

    def _check_branching(self):
        """
        Check if it's time to mark a branch section for delayed judgment.
        分支判断改为延迟模式：分支小节线到达时，只记录开始状态，不立即判断
        """
        if self.next_branch_idx >= len(self.branch_bars):
            return

        game_time = self.timing_manager.get_game_time()
        bar = self.branch_bars[self.next_branch_idx]
        
        # 当分支小节线到达判定线时，标记为"待判断"，记录当前状态
        # When the branch bar reaches the judgment line, mark it as "pending" and record current state
        if game_time >= bar.hit_ms and self.pending_branch_bar is None:
            self.pending_branch_bar = bar
            self.branch_section_start_perfect = self.perfect_count
            self.branch_section_start_drumroll_hits = self.drumroll_hits
            self.next_branch_idx += 1
            print(f"[Branch Pending] Marked branch at {bar.hit_ms:.1f}ms, StartPerfect={self.perfect_count}, StartDrumroll={self.drumroll_hits}")
    
    def _check_pending_branch(self):
        """
        Check and execute pending branch judgment after the branch section ends.
        检查并执行待判断的分支（在分支小节结束后）
        """
        if self.pending_branch_bar is None:
            return
        
        game_time = self.timing_manager.get_game_time()
        
        # 找到待判断分支小节线后的下一个小节线
        # Find the next bar after the pending branch bar
        next_bar_time = None
        for bar in self.bars:
            if bar.hit_ms > self.pending_branch_bar.hit_ms:
                next_bar_time = bar.hit_ms
                break
        
        # 如果没有找到下一个小节线，使用一个固定的延迟（比如4拍）
        # If no next bar found, use a fixed delay (e.g., 4 beats)
        if next_bar_time is None:
            # 假设BPM=120，4拍=2000ms（保守估计）
            next_bar_time = self.pending_branch_bar.hit_ms + 2000
        
        # 当游戏时间超过下一个小节线时，执行分支判断
        # Execute branch judgment when game time passes the next bar
        if game_time >= next_bar_time:
            print(f"[Branch Execute] Section ended at {game_time:.1f}ms, executing branch judgment...")
            self._execute_branch()
            self.pending_branch_bar = None  # 清除待判断状态
            
    def _check_gogo_time(self, game_time: float) -> bool:
        """
        检测当前是否在 GOGOTIME
        Check if currently in GOGOTIME
        
        Args:
            game_time: 当前游戏时间（毫秒）
            
        Returns:
            bool: 是否在 GOGOTIME
        """
        # 检查当前附近的音符或小节线的 gogo_time 状态
        # 优先检查小节线（bars），因为它们记录了准确的 gogotime 状态
        for bar in self.bars:
            # 检查判定线前后的小节线
            if abs(bar.hit_ms - game_time) < 2000:  # 2秒范围内
                if hasattr(bar, 'gogo_time'):
                    return bar.gogo_time
        
        # 如果没有小节线，检查音符
        for i in range(self.current_note_index, min(self.current_note_index + 10, len(self.notes))):
            note = self.notes[i]
            if abs(note.hit_ms - game_time) < 2000:  # 2秒范围内
                if hasattr(note, 'gogo_time'):
                    return note.gogo_time
        
        return False
    
    def _draw(self):
        """Draws all game elements to the screen."""
        self.screen.fill(BLACK)

        # 获取两种时间
        game_time = self.timing_manager.get_game_time()  # 用于游戏逻辑（音符移动）
        real_time = self.timing_manager.get_real_time()  # 用于动画和特效

        # 检测当前是否在 GOGOTIME
        is_gogo = self._check_gogo_time(game_time)

        # === 渲染器模块 ===
        self.renderer.draw_game_area(is_gogo)
        self.renderer.draw_bars(self.bars, game_time)
        self.renderer.draw_drumrolls(self.notes, game_time, self.combo, self.playback_speed)
        self.renderer.draw_notes(self.notes, self.current_note_index, game_time, self.combo, self.playback_speed)
        self.renderer.draw_stats(self.score)
        
        # 歌名和分类显示（独立模块）
        self.song_info_display.draw(self.song_title, self.song_category, self.category_color)
        
        # 判定文字 - 使用游戏时间
        judgment_text, judgment_time, is_super_large = self.note_judgment.get_judgment_display(game_time)
        if judgment_text:
            self.renderer.draw_judgment(judgment_text, game_time, judgment_time, is_super_large)
            
        # 击打动画 - 使用实时时间（不受变速影响）
        self.renderer.draw_hit_animations(real_time)
        
        # Draw controls (always use practice controls)
        self.practice_controls.draw(self.playback_speed, self.is_paused)

        # 准备鼓动画时间数据
        drum_times = {
            'don_left': self.drum_don_left_time,
            'don_right': self.drum_don_right_time,
            'kat_left': self.drum_kat_left_time,
            'kat_right': self.drum_kat_right_time,
            'press': self.drum_press_time
        }
        # 鼓动画也使用实时时间
        self.renderer.draw_drum(drum_times, real_time)
        
        # === 连段显示模块 ===
        if self.renderer.scaled_drum_img:
            self.combo_display.draw(
                self.screen,
                self.combo,
                self.renderer.screen_width,
                self.renderer.screen_height,
                self.renderer.drum_center_x,
                self.renderer.drum_center_y,
                self.renderer.scaled_drum_img.get_height()
            )
        
        # === 歌词显示 ===
        if self.lyric_parser and self.lyric_parser.has_lyrics():
            # 使用音频原始时间（不应用TJA的OFFSET）
            audio_time = self.timing_manager.get_audio_time()
            # 歌词需要提前显示，动画完成时正好对应时间戳
            animation_duration = self.lyric_renderer.get_animation_duration()
            adjusted_time = audio_time + animation_duration
            current_lyric = self.lyric_parser.get_lyric_at_time(adjusted_time)
            self.lyric_renderer.draw_lyric(current_lyric)

        pygame.display.flip()

    def _show_result(self):
        """Show result screen using the new result screen renderer"""
        # 播放返回音效
        self.sound_manager.play_cancel_sound()
        
        # 获取难度名称
        difficulty = self.chart_data.get('difficulty', 'Oni')
        
        # 获取歌曲标题和副标题（优先使用中文版本）
        titlecn = self.chart_data.get('titlecn', '')
        subtitlecn = self.chart_data.get('subtitlecn', '')
        subtitle = self.chart_data.get('subtitle', '')
        
        # 计算总音符数（不包括连打和气球的子音符）
        total_notes = len([n for n in self.notes if n.type in ['don', 'ka', 'big_don', 'big_ka']])
        
        # 绘制结算画面
        self.result_screen.draw(
            song_title=self.song_title,
            difficulty=difficulty,
            score=self.score,
            perfect_count=self.perfect_count,
            good_count=self.good_count,
            ok_count=self.ok_count,
            miss_count=self.miss_count,
            drumroll_count=self.drumroll_hits,
            max_combo=self.max_combo,
            total_notes=total_notes,
            subtitle=subtitle,
            titlecn=titlecn,
            subtitlecn=subtitlecn,
            bg_color=self.category_color  # 使用歌曲分类颜色作为背景
        )
        
        # 等待用户输入
        self.result_screen.wait_for_input(self.clock)

