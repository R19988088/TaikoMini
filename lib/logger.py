"""
日志模块
Logger Module

在Android平台上将日志输出到文件，方便调试
"""

import sys
import os
from datetime import datetime
from pathlib import Path


class Logger:
    """日志记录器"""
    
    def __init__(self, log_file=None, enable_console=True, fallback_paths=None):
        """
        初始化日志记录器
        
        Args:
            log_file: 日志文件路径，如果为None则只输出到控制台
            enable_console: 是否同时输出到控制台
            fallback_paths: 备用日志路径列表
        """
        self.log_file = log_file
        self.enable_console = enable_console
        self.file_handle = None
        self.fallback_paths = fallback_paths or []
        
        # 如果指定了日志文件，打开它
        if self.log_file:
            # 尝试主路径
            if not self._try_open_log(self.log_file):
                # 主路径失败，尝试备用路径
                for fallback_path in self.fallback_paths:
                    print(f"[Logger] 尝试备用路径: {fallback_path}")
                    if self._try_open_log(fallback_path):
                        self.log_file = fallback_path
                        break
                
            # 如果都失败了
            if not self.file_handle:
                print(f"[Logger] 警告：所有日志路径都失败，仅输出到控制台")
    
    def _try_open_log(self, log_path):
        """
        尝试打开日志文件
        
        Args:
            log_path: 日志文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            log_path_obj = Path(log_path)
            log_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 打开文件（追加模式）
            self.file_handle = open(log_path, 'a', encoding='utf-8', buffering=1)
            
            # 写入分隔线和启动时间
            self.file_handle.write("\n" + "=" * 70 + "\n")
            self.file_handle.write(f"应用启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.file_handle.write(f"日志文件: {log_path}\n")
            self.file_handle.write("=" * 70 + "\n")
            self.file_handle.flush()
            
            print(f"[Logger] ✓ 日志文件已创建: {log_path}")
            return True
        except Exception as e:
            print(f"[Logger] ✗ 无法打开日志文件 {log_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def log(self, message, level="INFO"):
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_line = f"[{timestamp}] [{level}] {message}"
        
        # 输出到控制台
        if self.enable_console:
            print(log_line)
        
        # 输出到文件
        if self.file_handle:
            try:
                self.file_handle.write(log_line + "\n")
                self.file_handle.flush()  # 立即刷新到磁盘
            except Exception as e:
                print(f"[Logger] 写入日志文件失败: {e}")
    
    def info(self, message):
        """记录INFO级别日志"""
        self.log(message, "INFO")
    
    def warning(self, message):
        """记录WARNING级别日志"""
        self.log(message, "WARNING")
    
    def error(self, message):
        """记录ERROR级别日志"""
        self.log(message, "ERROR")
    
    def debug(self, message):
        """记录DEBUG级别日志"""
        self.log(message, "DEBUG")
    
    def exception(self, message):
        """记录异常信息（包含堆栈跟踪）"""
        import traceback
        error_msg = f"{message}\n{traceback.format_exc()}"
        self.log(error_msg, "ERROR")
    
    def close(self):
        """关闭日志文件"""
        if self.file_handle:
            try:
                self.file_handle.write("\n" + "=" * 70 + "\n")
                self.file_handle.write(f"应用关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.file_handle.write("=" * 70 + "\n\n")
                self.file_handle.close()
            except:
                pass
            self.file_handle = None
    
    def __del__(self):
        """析构函数，确保文件被关闭"""
        self.close()


# 全局日志实例
_global_logger = None


def init_logger(is_android=False, base_path=None):
    """
    初始化全局日志记录器
    
    Args:
        is_android: 是否为Android平台
        base_path: 基础路径（Android上为 /sdcard/taikomini）
    
    Returns:
        Logger: 日志记录器实例
    """
    global _global_logger
    
    print("[Logger] 开始初始化日志系统...")
    
    if is_android and base_path:
        # Android: 输出到SD卡，提供多个备用路径
        log_file = Path(base_path) / "taikomini.log"
        
        # 备用路径列表
        fallback_paths = [
            "/sdcard/taikomini.log",  # SD卡根目录
            "/storage/emulated/0/taikomini.log",  # 备用SD卡路径
            str(Path.home() / "taikomini.log"),  # 用户主目录
        ]
        
        print(f"[Logger] 主日志路径: {log_file}")
        print(f"[Logger] 备用路径: {fallback_paths}")
        
        _global_logger = Logger(
            log_file=str(log_file), 
            enable_console=True,
            fallback_paths=fallback_paths
        )
        _global_logger.info(f"日志文件位置: {_global_logger.log_file}")
    else:
        # Desktop: 输出到当前目录和控制台
        log_file = "taikomini.log"
        _global_logger = Logger(log_file=log_file, enable_console=True)
    
    print("[Logger] ✓ 日志系统初始化完成")
    return _global_logger


def get_logger():
    """
    获取全局日志记录器
    
    Returns:
        Logger: 日志记录器实例
    """
    global _global_logger
    if _global_logger is None:
        # 如果没有初始化，创建一个只输出到控制台的logger
        _global_logger = Logger(log_file=None, enable_console=True)
    return _global_logger


def close_logger():
    """关闭全局日志记录器"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None

