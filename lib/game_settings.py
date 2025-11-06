"""
游戏设置管理器
Game Settings Manager

管理游戏的各种参数设置
Manages various game parameter settings
"""

from pathlib import Path
from typing import Dict, Any
import configparser


class GameSettings:
    """游戏设置管理器"""
    
    def __init__(self, config_file: str = "songs/config.ini"):
        """
        初始化游戏设置
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        
        # 默认设置
        self.default_settings = {
            'Gameplay': {
                'note_distance': '1600',      # 音符距离
                'note_scale': '0.8',          # 音符缩放比例
                'note_speed': '1.0',          # 音符速度倍数
                'judge_line_position': '0.15', # 判定线位置比例
                'note_area_scale': '1.0',     # 音符区整体比例
                'hit_effect_scale': '0.6',    # 击中特效缩放比例
                'judge_x_scale': '1.0',       # 判定线位置缩放比例
                'chart_offset': '10',         # 谱面偏移(ms) 正数提前 负数延后
                'target_fps': '60'            # 目标帧率 可选: 60 或 120
            },
            'State': {
                'last_selected_song': '',
                'last_selected_difficulty': 'Oni',
                'auto_play': 'False'
            },
            'Audio': {
                'master_volume': '1.0',       # 主音量
                'sfx_volume': '1.0',          # 音效音量
                'music_volume': '1.0'         # 音乐音量
            },
            'Display': {
                'screen_width': '720',        # 屏幕宽度
                'screen_height': '1280',      # 屏幕高度
                'fullscreen': 'False'         # 全屏模式
            },
            'Graphics': {
                'game_area_ratio': '0.20',
                'judge_x_ratio': '0.15',
                'drum_ratio': '0.48',
                'drum_y_offset_ratio': '0.20',
                'don_color': '230, 74, 25, 255',
                'kat_color': '0, 162, 232, 255'
            }
        }
        
        self._load_settings()
    
    def _load_settings(self):
        """加载设置"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file, encoding='utf-8')
                print(f"Loaded game settings from {self.config_file}")
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入默认设置
            for section, options in self.default_settings.items():
                self.config[section] = options
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            print(f"Created default config file: {self.config_file}")
        except Exception as e:
            print(f"Error creating config file: {e}")
    
    def _ensure_gameplay_section(self):
        """确保Gameplay段存在"""
        if 'Gameplay' not in self.config:
            self.config['Gameplay'] = self.default_settings['Gameplay']
            self._save_settings()
            print("Created Gameplay section in config")
    
    def get_note_distance(self) -> int:
        """获取音符距离"""
        try:
            # 首先尝试从Gameplay段获取
            if 'Gameplay' in self.config:
                return int(self.config.get('Gameplay', 'note_distance', fallback='1200'))
            # 如果Gameplay段不存在，创建并返回默认值
            else:
                self._ensure_gameplay_section()
                return 1200
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1200
    
    def set_note_distance(self, distance: int):
        """设置音符距离"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['note_distance'] = str(distance)
            self._save_settings()
        except Exception as e:
            print(f"Error setting note distance: {e}")
    
    def get_note_scale(self) -> float:
        """获取音符缩放比例"""
        try:
            if 'Gameplay' in self.config:
                return float(self.config.get('Gameplay', 'note_scale', fallback='0.8'))
            else:
                self._ensure_gameplay_section()
                return 0.8
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 0.8
    
    def set_note_scale(self, scale: float):
        """设置音符缩放比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['note_scale'] = str(scale)
            self._save_settings()
        except Exception as e:
            print(f"Error setting note scale: {e}")
    
    def get_note_speed(self) -> float:
        """获取音符速度倍数"""
        try:
            return float(self.config.get('Gameplay', 'note_speed', fallback='1.0'))
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_note_speed(self, speed: float):
        """设置音符速度倍数"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['note_speed'] = str(speed)
            self._save_settings()
        except Exception as e:
            print(f"Error setting note speed: {e}")
    
    def get_judge_line_position(self) -> float:
        """获取判定线位置比例"""
        try:
            return float(self.config.get('Gameplay', 'judge_line_position', fallback='0.15'))
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 0.15
    
    def set_judge_line_position(self, position: float):
        """设置判定线位置比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['judge_line_position'] = str(position)
            self._save_settings()
        except Exception as e:
            print(f"Error setting judge line position: {e}")
    
    def get_note_area_scale(self) -> float:
        """获取音符区整体比例"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'note_area_scale', fallback='1.0')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                return float(clean_value)
            else:
                self._ensure_gameplay_section()
                return 1.0
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_note_area_scale(self, scale: float):
        """设置音符区整体比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['note_area_scale'] = str(scale)
            self._save_settings()
        except Exception as e:
            print(f"Error setting note area scale: {e}")
    
    def get_scaled_note_distance(self) -> int:
        """获取缩放后的音符距离"""
        base_distance = self.get_note_distance()
        area_scale = self.get_note_area_scale()
        return int(base_distance * area_scale)
    
    def get_scaled_note_scale(self) -> float:
        """获取缩放后的音符比例"""
        base_scale = self.get_note_scale()
        area_scale = self.get_note_area_scale()
        return base_scale * area_scale
    
    def get_judge_circle_scale(self) -> float:
        """获取判定圈缩放比例"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'judge_circle_scale', fallback='1.0')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                return float(clean_value)
            else:
                self._ensure_gameplay_section()
                return 1.0
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_judge_circle_scale(self, scale: float):
        """设置判定圈缩放比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['judge_circle_scale'] = str(scale)
            self._save_settings()
        except Exception as e:
            print(f"Error setting judge circle scale: {e}")
    
    def get_scaled_judge_circle_scale(self) -> float:
        """获取缩放后的判定圈比例（结合note_area_scale）"""
        base_scale = self.get_judge_circle_scale()
        area_scale = self.get_note_area_scale()
        return base_scale * area_scale
    
    def get_hit_effect_scale(self) -> float:
        """获取击中特效缩放比例"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'hit_effect_scale', fallback='0.6')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                return float(clean_value)
            else:
                self._ensure_gameplay_section()
                return 0.6
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 0.6
    
    def set_hit_effect_scale(self, scale: float):
        """设置击中特效缩放比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['hit_effect_scale'] = str(scale)
            self._save_settings()
        except Exception as e:
            print(f"Error setting hit effect scale: {e}")
    
    def get_scaled_hit_effect_scale(self) -> float:
        """获取缩放后的击中特效比例（结合note_area_scale）"""
        base_scale = self.get_hit_effect_scale()
        area_scale = self.get_note_area_scale()
        return base_scale * area_scale
    
    def get_judge_x_scale(self) -> float:
        """获取判定线位置缩放比例"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'judge_x_scale', fallback='1.0')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                return float(clean_value)
            else:
                self._ensure_gameplay_section()
                return 1.0
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_judge_x_scale(self, scale: float):
        """设置判定线位置缩放比例"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['judge_x_scale'] = str(scale)
            self._save_settings()
        except Exception as e:
            print(f"Error setting judge x scale: {e}")
    
    def get_scaled_judge_x_ratio(self) -> float:
        """获取缩放后的判定线位置比例（结合note_area_scale）"""
        base_ratio = 0.15  # JUDGE_X_RATIO
        scale = self.get_judge_x_scale()
        area_scale = self.get_note_area_scale()
        # 当note_area_scale缩小时，判定线位置应该向左移动（减小比例）
        return base_ratio * scale * area_scale
    
    def get_master_volume(self) -> float:
        """获取主音量"""
        try:
            return float(self.config.get('Audio', 'master_volume', fallback='1.0'))
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_master_volume(self, volume: float):
        """设置主音量"""
        try:
            if 'Audio' not in self.config:
                self.config['Audio'] = {}
            self.config['Audio']['master_volume'] = str(volume)
            self._save_settings()
        except Exception as e:
            print(f"Error setting master volume: {e}")
    
    def get_screen_size(self) -> tuple:
        """获取屏幕尺寸"""
        try:
            width = int(self.config.get('Display', 'screen_width', fallback='720'))
            height = int(self.config.get('Display', 'screen_height', fallback='1280'))
            return (width, height)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return (720, 1280)
    
    def set_screen_size(self, width: int, height: int):
        """设置屏幕尺寸"""
        try:
            if 'Display' not in self.config:
                self.config['Display'] = {}
            self.config['Display']['screen_width'] = str(width)
            self.config['Display']['screen_height'] = str(height)
            self._save_settings()
        except Exception as e:
            print(f"Error setting screen size: {e}")
    
    def get_fullscreen(self) -> bool:
        """获取全屏模式"""
        try:
            return self.config.getboolean('Display', 'fullscreen', fallback=False)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return False
    
    def set_fullscreen(self, fullscreen: bool):
        """设置全屏模式"""
        try:
            if 'Display' not in self.config:
                self.config['Display'] = {}
            self.config['Display']['fullscreen'] = str(fullscreen)
            self._save_settings()
        except Exception as e:
            print(f"Error setting fullscreen: {e}")
    
    # --- Graphics Settings ---

    def _get_color(self, key: str, fallback: str) -> tuple:
        """Helper to get a color from config."""
        color_str = self.config.get('Graphics', key, fallback=fallback)
        try:
            r, g, b, a = [int(c.strip()) for c in color_str.split(',')]
            return r / 255.0, g / 255.0, b / 255.0, a / 255.0
        except ValueError:
            r, g, b = [int(c.strip()) for c in fallback.split(',')[:3]]
            return r / 255.0, g / 255.0, b / 255.0, 1.0

    def get_don_color(self) -> tuple:
        """获取'咚'音符的颜色"""
        return self._get_color('don_color', '230, 74, 25, 255')

    def get_kat_color(self) -> tuple:
        """获取'咔'音符的颜色"""
        return self._get_color('kat_color', '0, 162, 232, 255')

    def get_game_area_ratio(self) -> float:
        """获取游戏区域高度比例"""
        return self.config.getfloat('Graphics', 'game_area_ratio', fallback=0.20)

    def get_judge_x_ratio(self) -> float:
        """获取判定线位置比例"""
        return self.config.getfloat('Graphics', 'judge_x_ratio', fallback=0.15)
        
    # --- State Settings ---

    def get_last_selected_song(self) -> str:
        """获取上次选择的歌曲路径"""
        return self.config.get('State', 'last_selected_song', fallback='')

    def set_last_selected_song(self, song_path: str):
        """设置上次选择的歌曲路径"""
        if 'State' not in self.config:
            self.config['State'] = {}
        self.config.set('State', 'last_selected_song', song_path)
        self._save_settings()

    def get_last_selected_difficulty(self) -> str:
        """获取上次选择的难度"""
        return self.config.get('State', 'last_selected_difficulty', fallback='Oni')

    def set_last_selected_difficulty(self, difficulty: str):
        """设置上次选择的难度"""
        if 'State' not in self.config:
            self.config['State'] = {}
        self.config.set('State', 'last_selected_difficulty', difficulty)
        self._save_settings()

    def get_auto_play(self) -> bool:
        """获取自动演奏设置"""
        return self.config.getboolean('State', 'auto_play', fallback=False)

    def set_auto_play(self, auto_play: bool):
        """设置自动演奏"""
        if 'State' not in self.config:
            self.config['State'] = {}
        self.config.set('State', 'auto_play', str(auto_play))
        self._save_settings()
    
    def _save_settings(self):
        """保存设置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        self.config.clear()
        for section, options in self.default_settings.items():
            self.config[section] = options
        self._save_settings()
        print("Settings reset to defaults")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        settings = {}
        for section in self.config.sections():
            settings[section] = dict(self.config[section])
        return settings
    
    def print_current_settings(self):
        """打印当前设置"""
        print("\n=== Current Game Settings ===")
        for section in self.config.sections():
            print(f"\n[{section}]")
            for key, value in self.config[section].items():
                try:
                    print(f"  {key} = {value}")
                except UnicodeEncodeError:
                    # 处理编码问题
                    safe_value = str(value).encode('ascii', errors='replace').decode('ascii')
                    print(f"  {key} = {safe_value}")
        print("=" * 30)
    
    # ========== GameSettings Section ==========
    def get_default_speed(self) -> float:
        """获取默认速度"""
        try:
            if 'GameSettings' in self.config:
                return float(self.config.get('GameSettings', 'default_speed', fallback='1.0'))
            return 1.0
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 1.0
    
    def set_default_speed(self, speed: float):
        """设置默认速度"""
        try:
            if 'GameSettings' not in self.config:
                self.config['GameSettings'] = {}
            self.config['GameSettings']['default_speed'] = str(speed)
            self._save_settings()
        except Exception as e:
            print(f"Error setting default speed: {e}")
    
    def get_default_difficulty(self) -> str:
        """获取默认难度"""
        try:
            if 'GameSettings' in self.config:
                return self.config.get('GameSettings', 'default_difficulty', fallback='Oni')
            return 'Oni'
        except (configparser.NoSectionError, configparser.NoOptionError):
            return 'Oni'
    
    def set_default_difficulty(self, difficulty: str):
        """设置默认难度"""
        try:
            if 'GameSettings' not in self.config:
                self.config['GameSettings'] = {}
            self.config['GameSettings']['default_difficulty'] = difficulty
            self._save_settings()
        except Exception as e:
            print(f"Error setting default difficulty: {e}")
    
    # ========== DisplaySettings Section ==========
    def get_title_font_size(self) -> int:
        """获取标题字体大小"""
        try:
            if 'DisplaySettings' in self.config:
                return int(self.config.get('DisplaySettings', 'title_font_size', fallback='46'))
            return 46
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 46
    
    def set_title_font_size(self, size: int):
        """设置标题字体大小"""
        try:
            if 'DisplaySettings' not in self.config:
                self.config['DisplaySettings'] = {}
            self.config['DisplaySettings']['title_font_size'] = str(size)
            self._save_settings()
        except Exception as e:
            print(f"Error setting title font size: {e}")
    
    def get_category_font_size(self) -> int:
        """获取分类字体大小"""
        try:
            if 'DisplaySettings' in self.config:
                return int(self.config.get('DisplaySettings', 'category_font_size', fallback='20'))
            return 20
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 20
    
    def set_category_font_size(self, size: int):
        """设置分类字体大小"""
        try:
            if 'DisplaySettings' not in self.config:
                self.config['DisplaySettings'] = {}
            self.config['DisplaySettings']['category_font_size'] = str(size)
            self._save_settings()
        except Exception as e:
            print(f"Error setting category font size: {e}")
    
    def get_title_outline(self) -> int:
        """获取标题描边大小"""
        try:
            if 'DisplaySettings' in self.config:
                return int(self.config.get('DisplaySettings', 'title_outline', fallback='3'))
            return 3
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 3
    
    def set_title_outline(self, size: int):
        """设置标题描边大小"""
        try:
            if 'DisplaySettings' not in self.config:
                self.config['DisplaySettings'] = {}
            self.config['DisplaySettings']['title_outline'] = str(size)
            self._save_settings()
        except Exception as e:
            print(f"Error setting title outline: {e}")
    
    def get_category_outline(self) -> int:
        """获取分类描边大小"""
        try:
            if 'DisplaySettings' in self.config:
                return int(self.config.get('DisplaySettings', 'category_outline', fallback='2'))
            return 2
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 2
    
    def set_category_outline(self, size: int):
        """设置分类描边大小"""
        try:
            if 'DisplaySettings' not in self.config:
                self.config['DisplaySettings'] = {}
            self.config['DisplaySettings']['category_outline'] = str(size)
            self._save_settings()
        except Exception as e:
            print(f"Error setting category outline: {e}")
    
    def get_chart_offset(self) -> float:
        """获取谱面偏移(ms) 正数提前 负数延后"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'chart_offset', fallback='10')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                return float(clean_value)
            else:
                self._ensure_gameplay_section()
                return 10.0
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 10.0
    
    def set_chart_offset(self, offset: float):
        """设置谱面偏移(ms) 正数提前 负数延后"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            self.config['Gameplay']['chart_offset'] = str(offset)
            self._save_settings()
        except Exception as e:
            print(f"Error setting chart offset: {e}")
    
    def get_target_fps(self) -> int:
        """获取目标帧率 (60 或 120)"""
        try:
            if 'Gameplay' in self.config:
                raw_value = self.config.get('Gameplay', 'target_fps', fallback='60')
                # 移除注释部分（#后面的内容）
                clean_value = raw_value.split('#')[0].strip()
                fps = int(clean_value)
                # 只允许60或120
                if fps in [60, 120]:
                    return fps
                return 60
            else:
                self._ensure_gameplay_section()
                return 60
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return 60
    
    def set_target_fps(self, fps: int):
        """设置目标帧率 (60 或 120)"""
        try:
            if 'Gameplay' not in self.config:
                self.config['Gameplay'] = {}
            # 确保只能设置60或120
            if fps in [60, 120]:
                self.config['Gameplay']['target_fps'] = str(fps)
                self._save_settings()
            else:
                print(f"Invalid FPS value: {fps}. Only 60 or 120 are allowed.")
        except Exception as e:
            print(f"Error setting target FPS: {e}")
    
    # ========== LastSelected Section ==========
    def get_last_selected_category(self) -> str:
        """获取上次选择的分类"""
        try:
            if 'LastSelected' in self.config:
                return self.config.get('LastSelected', 'category', fallback='')
            return ''
        except (configparser.NoSectionError, configparser.NoOptionError):
            return ''
    
    def set_last_selected_category(self, category: str):
        """设置上次选择的分类"""
        try:
            if 'LastSelected' not in self.config:
                self.config['LastSelected'] = {}
            self.config['LastSelected']['category'] = category
            self._save_settings()
        except Exception as e:
            print(f"Error setting last selected category: {e}")