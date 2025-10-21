#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 适配器
处理 Android 特定的功能和权限
"""

import os
import sys
from pathlib import Path

class AndroidAdapter:
    """Android 平台适配器"""
    
    def __init__(self):
        self.is_android = self._check_android()
        self.android_app = None
        
        if self.is_android:
            self._init_android()
    
    def _check_android(self):
        """检查是否在 Android 环境"""
        return hasattr(sys, 'getandroidapp')
    
    def _init_android(self):
        """初始化 Android 环境"""
        try:
            self.android_app = sys.getandroidapp()
        except Exception as e:
            print(f"Android 初始化失败: {e}")
            self.is_android = False
    
    def get_external_storage_path(self):
        """获取外部存储路径"""
        if self.is_android and self.android_app:
            try:
                return self.android_app.getExternalFilesDir(None)
            except Exception as e:
                print(f"获取外部存储路径失败: {e}")
                return None
        else:
            # 开发环境
            return Path.home() / "TaikoMini"
    
    def request_permissions(self, permissions):
        """请求权限"""
        if self.is_android and self.android_app:
            try:
                self.android_app.requestPermissions(permissions)
                return True
            except Exception as e:
                print(f"权限请求失败: {e}")
                return False
        return False
    
    def check_permission(self, permission):
        """检查权限状态"""
        if self.is_android and self.android_app:
            try:
                return self.android_app.checkSelfPermission(permission)
            except Exception as e:
                print(f"权限检查失败: {e}")
                return False
        return True  # 非 Android 环境默认有权限
    
    def log(self, message):
        """记录日志"""
        if self.is_android and self.android_app:
            try:
                self.android_app.log(message)
            except Exception as e:
                print(f"日志记录失败: {e}")
        else:
            print(message)
    
    def show_toast(self, message):
        """显示 Toast 消息"""
        if self.is_android and self.android_app:
            try:
                self.android_app.makeToast(message)
            except Exception as e:
                print(f"Toast 显示失败: {e}")
        else:
            print(f"Toast: {message}")
    
    def get_screen_size(self):
        """获取屏幕尺寸"""
        if self.is_android and self.android_app:
            try:
                # 获取屏幕尺寸
                return self.android_app.getScreenSize()
            except Exception as e:
                print(f"获取屏幕尺寸失败: {e}")
                return (720, 1280)  # 默认尺寸
        else:
            return (720, 1280)  # 默认尺寸
    
    def set_fullscreen(self, fullscreen=True):
        """设置全屏模式"""
        if self.is_android and self.android_app:
            try:
                if fullscreen:
                    self.android_app.setFullscreen()
                else:
                    self.android_app.setNormalScreen()
            except Exception as e:
                print(f"全屏设置失败: {e}")
    
    def get_system_info(self):
        """获取系统信息"""
        if self.is_android and self.android_app:
            try:
                return {
                    'version': self.android_app.getSystemVersion(),
                    'model': self.android_app.getSystemModel(),
                    'manufacturer': self.android_app.getSystemManufacturer(),
                }
            except Exception as e:
                print(f"获取系统信息失败: {e}")
                return {}
        return {}
    
    def create_directory(self, path):
        """创建目录"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.log(f"创建目录失败: {e}")
            return False
    
    def list_files(self, path, pattern="*"):
        """列出文件"""
        try:
            path_obj = Path(path)
            if path_obj.exists():
                return list(path_obj.glob(pattern))
            return []
        except Exception as e:
            self.log(f"列出文件失败: {e}")
            return []
    
    def copy_file(self, src, dst):
        """复制文件"""
        try:
            import shutil
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            self.log(f"复制文件失败: {e}")
            return False
    
    def get_available_storage(self):
        """获取可用存储空间"""
        if self.is_android and self.android_app:
            try:
                return self.android_app.getAvailableStorage()
            except Exception as e:
                self.log(f"获取存储空间失败: {e}")
                return 0
        else:
            # 开发环境
            try:
                import shutil
                return shutil.disk_usage(Path.home()).free
            except Exception as e:
                self.log(f"获取存储空间失败: {e}")
                return 0

# 全局实例
android_adapter = AndroidAdapter()
