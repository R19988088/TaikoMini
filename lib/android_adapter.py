"""
Android平台适配模块
Android Platform Adapter Module

处理Android平台特定的功能和兼容性
"""

import sys
import os
from pathlib import Path
import pygame


# 检测是否在Android平台运行
IS_ANDROID = hasattr(sys, 'getandroidapilevel')


class AndroidAdapter:
    """
    Android平台适配器
    
    功能：
    - 平台检测
    - 文件路径选择
    - 全屏模式设置
    - 字体适配
    - 权限请求
    """
    
    def __init__(self):
        """初始化Android适配器"""
        self.is_android = IS_ANDROID
        self.songs_path = None
        
        if self.is_android:
            print("[Android] Running on Android platform")
            self._init_android()
        else:
            print("[Android] Running on Desktop platform")
    
    def _init_android(self):
        """初始化Android特定设置"""
        try:
            # 请求存储权限
            self._request_permissions()
            
            # 设置默认路径 - 使用SD卡根目录的taikomini文件夹
            self.base_path = Path("/sdcard/taikomini")
            self.songs_path = self.base_path / "songs"
            
            # 首次启动时创建必要的目录结构
            self._create_directory_structure()
            
        except Exception as e:
            print(f"[Android] Initialization error: {e}")
    
    def _create_directory_structure(self):
        """创建必要的目录结构"""
        if not self.is_android:
            return
        
        try:
            # 创建基础目录
            if not self.base_path.exists():
                self.base_path.mkdir(parents=True, exist_ok=True)
                print(f"[Android] Created base directory: {self.base_path}")
            
            # 创建songs目录
            if not self.songs_path.exists():
                self.songs_path.mkdir(parents=True, exist_ok=True)
                print(f"[Android] Created songs directory: {self.songs_path}")
            
            # 创建Resource目录
            resource_path = self.songs_path / "Resource"
            if not resource_path.exists():
                resource_path.mkdir(parents=True, exist_ok=True)
                print(f"[Android] Created resource directory: {resource_path}")
            
            # 创建默认配置文件（如果不存在）
            config_path = self.songs_path / "config.ini"
            if not config_path.exists():
                print(f"[Android] Config file will be created at: {config_path}")
            
            print(f"[Android] Directory structure ready at: {self.base_path}")
            
        except Exception as e:
            print(f"[Android] Failed to create directory structure: {e}")
    
    def _request_permissions(self):
        """请求Android权限"""
        if not self.is_android:
            return
        
        try:
            from android.permissions import request_permissions, Permission
            
            # 请求存储权限
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
            print("[Android] Storage permissions requested")
        except ImportError:
            print("[Android] Warning: android module not available")
        except Exception as e:
            print(f"[Android] Permission request error: {e}")
    
    def get_screen_mode(self, base_width=720, base_height=1280):
        """
        获取屏幕模式设置
        
        Args:
            base_width: 基础宽度
            base_height: 基础高度
        
        Returns:
            tuple: (size, flags) - 屏幕尺寸和标志
        """
        if self.is_android:
            # Android: 使用全屏模式，自动检测分辨率
            return (0, 0), pygame.FULLSCREEN
        else:
            # Desktop: 使用可调整大小的窗口
            return (base_width, base_height), (
                pygame.RESIZABLE | 
                pygame.SCALED | 
                pygame.DOUBLEBUF | 
                pygame.HWSURFACE
            )
    
    def get_songs_folder(self):
        """
        获取歌曲文件夹路径
        
        Returns:
            Path: 歌曲文件夹路径
        """
        if self.is_android:
            # Android: 使用文件选择器或默认路径
            if self.songs_path is None:
                self.songs_path = self._select_songs_folder()
            return self.songs_path
        else:
            # Desktop: 使用当前目录下的songs文件夹
            return Path("songs")
    
    def _select_songs_folder(self):
        """
        在Android上选择歌曲文件夹
        
        Returns:
            Path: 选择的文件夹路径
        """
        # 直接返回已经初始化的songs_path
        return self.songs_path
    
    def get_base_path(self):
        """
        获取应用数据根目录
        
        Returns:
            Path: Android上返回 /sdcard/taikomini, Desktop上返回当前目录
        """
        if self.is_android:
            return self.base_path
        else:
            return Path(".")
    
    def get_system_font(self, size, bold=False):
        """
        获取系统字体（优先黑体）
        
        Args:
            size: 字体大小
            bold: 是否粗体
        
        Returns:
            pygame.font.Font: 字体对象
        """
        if self.is_android:
            # Android系统字体
            # Android默认有Droid Sans Fallback，支持中文
            font_names = [
                'notosanscjk',      # Noto Sans CJK (新版Android)
                'droidsansfallback', # Droid Sans Fallback (老版Android)
                'simhei',            # 黑体
                'microsoftyahei',    # 微软雅黑
            ]
        else:
            # Desktop系统字体
            font_names = [
                'simhei',            # 黑体
                'microsoftyahei',    # 微软雅黑
                'songti',            # 宋体
                'arial',             # Arial
            ]
        
        # 尝试加载字体
        for font_name in font_names:
            try:
                if pygame.font.match_font(font_name):
                    return pygame.font.SysFont(font_name, size, bold=bold)
            except:
                continue
        
        # 都失败了，使用pygame默认字体
        return pygame.font.Font(None, size)
    
    def apply_platform_settings(self):
        """应用平台特定设置"""
        if not self.is_android:
            return
        
        try:
            # 保持屏幕常亮
            from android import activity
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            View = autoclass('android.view.View')
            WindowManager = autoclass('android.view.WindowManager')
            
            activity_inst = PythonActivity.mActivity
            window = activity_inst.getWindow()
            
            # 保持屏幕常亮
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            print("[Android] Screen will stay on during gameplay")
            
            # 隐藏状态栏和导航栏（沉浸式模式）
            decorView = window.getDecorView()
            decorView.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            )
            print("[Android] Immersive mode enabled")
            
        except Exception as e:
            print(f"[Android] Failed to apply settings: {e}")
    
    def get_audio_buffer_size(self):
        """
        获取推荐的音频缓冲区大小
        
        Returns:
            int: 缓冲区大小
        """
        if self.is_android:
            # Android需要更大的buffer避免卡顿
            return 2048
        else:
            # Desktop使用小buffer获得低延迟
            return 512
    
    def should_disable_windows_features(self):
        """
        是否应该禁用Windows特定功能
        
        Returns:
            bool: True表示应该禁用
        """
        return self.is_android


# 全局适配器实例
_adapter = None


def get_adapter():
    """
    获取全局Android适配器实例
    
    Returns:
        AndroidAdapter: 适配器实例
    """
    global _adapter
    if _adapter is None:
        _adapter = AndroidAdapter()
    return _adapter


def is_android():
    """
    快捷函数：检测是否在Android平台
    
    Returns:
        bool: 是否在Android平台
    """
    return IS_ANDROID



