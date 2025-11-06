"""
Sprite Atlas GUI工具
支持拖拽上传atlas图片，自动检测并切出子图
"""

import pygame
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from atlas_detector import AtlasDetector
from sprite_atlas import SpriteAtlas

# 设置编码
if sys.platform == "win32":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.utf8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass


class AtlasGUI:
    """Atlas GUI工具"""
    
    def __init__(self):
        # 设置高DPI支持
        self._setup_dpi()
        
        self.root = tk.Tk()
        self.root.title("Sprite Atlas 自动切图工具")
        self.root.geometry("1000x700")
        
        # 设置字体
        self._setup_fonts()
        
        # 变量
        self.atlas_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.min_size = tk.IntVar(value=8)
        self.min_density = tk.DoubleVar(value=0.05)
        self.detection_result = []
        
        # 自动设置输出目录为当前目录下的png文件夹
        current_dir = Path.cwd()
        png_dir = current_dir / "png"
        self.output_dir.set(str(png_dir))
        
        self.setup_ui()
        
    def _setup_dpi(self):
        """设置高DPI支持"""
        try:
            # Windows高DPI支持
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                
                # 设置DPI感知
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except:
                    try:
                        ctypes.windll.user32.SetProcessDPIAware()
                    except:
                        pass
                        
                # 获取DPI缩放比例
                try:
                    dpi = ctypes.windll.user32.GetDpiForSystem()
                    self.dpi_scale = dpi / 96.0
                except:
                    self.dpi_scale = 1.0
            else:
                self.dpi_scale = 1.0
                
        except Exception as e:
            print(f"DPI设置失败: {e}")
            self.dpi_scale = 1.0
            
    def _setup_fonts(self):
        """设置字体"""
        try:
            # 尝试使用系统字体
            if sys.platform == "win32":
                # Windows系统字体 - 使用更兼容的字体
                self.font_family = "Microsoft YaHei"
            elif sys.platform == "darwin":
                # macOS系统字体
                self.font_family = "PingFang SC"
            else:
                # Linux系统字体
                self.font_family = "DejaVu Sans"
                
            # 根据DPI缩放调整字体大小
            self.font_size_large = int(16 * self.dpi_scale)
            self.font_size_medium = int(12 * self.dpi_scale)
            self.font_size_small = int(10 * self.dpi_scale)
            
        except Exception as e:
            print(f"字体设置失败: {e}")
            # 使用默认字体，但确保中文显示
            self.font_family = "TkDefaultFont"
            self.font_size_large = 16
            self.font_size_medium = 12
            self.font_size_small = 10
        
    def setup_ui(self):
        """设置UI界面"""
        # 配置样式
        self._configure_styles()
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Atlas文件选择
        atlas_label = ttk.Label(file_frame, text="Atlas图片:")
        atlas_label.grid(row=0, column=0, sticky=tk.W)
        atlas_entry = ttk.Entry(file_frame, textvariable=self.atlas_path, width=50)
        atlas_entry.grid(row=0, column=1, padx=(5, 5))
        atlas_button = ttk.Button(file_frame, text="浏览", command=self.browse_atlas)
        atlas_button.grid(row=0, column=2)
        
        # 输出目录选择（只读显示）
        output_label = ttk.Label(file_frame, text="输出目录:")
        output_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        output_entry = ttk.Entry(file_frame, textvariable=self.output_dir, width=50, state='readonly')
        output_entry.grid(row=1, column=1, padx=(5, 5), pady=(5, 0))
        output_info_label = ttk.Label(file_frame, text="(自动设置为png文件夹)", foreground="gray")
        output_info_label.grid(row=1, column=2, pady=(5, 0))
        
        # 拖拽区域
        drop_frame = ttk.LabelFrame(main_frame, text="拖拽区域 (将atlas图片拖拽到这里)", padding="10")
        drop_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.drop_label = ttk.Label(drop_frame, text="拖拽atlas图片到此处", 
                                  background="lightgray", anchor="center")
        self.drop_label.pack(fill=tk.BOTH, expand=True, ipady=50)
        
        # 绑定拖拽事件
        self.drop_label.bind("<Button-1>", self.on_drop_click)
        
    def _configure_styles(self):
        """配置样式"""
        try:
            style = ttk.Style()
            
            # 设置字体 - 使用元组格式确保兼容性
            font_tuple = (self.font_family, self.font_size_medium)
            font_small_tuple = (self.font_family, self.font_size_small)
            
            style.configure("TLabel", font=font_tuple)
            style.configure("TButton", font=font_tuple)
            style.configure("TEntry", font=font_tuple)
            style.configure("TLabelFrame", font=font_tuple)
            style.configure("TLabelFrame.Label", font=font_tuple)
            style.configure("Treeview", font=font_small_tuple)
            style.configure("Treeview.Heading", font=font_small_tuple)
            
            # 设置主题
            try:
                style.theme_use('clam')  # 使用更现代的主题
            except:
                pass
                
        except Exception as e:
            print(f"样式配置失败: {e}")
        
        # 检测参数区域
        param_frame = ttk.LabelFrame(main_frame, text="检测参数", padding="10")
        param_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 最小尺寸
        size_label = ttk.Label(param_frame, text="最小尺寸:")
        size_label.grid(row=0, column=0, sticky=tk.W)
        size_spinbox = ttk.Spinbox(param_frame, from_=1, to=100, textvariable=self.min_size, width=10)
        size_spinbox.grid(row=0, column=1, padx=(5, 0))
        size_unit_label = ttk.Label(param_frame, text="像素")
        size_unit_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 最小密度
        density_label = ttk.Label(param_frame, text="最小密度:")
        density_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        density_spinbox = ttk.Spinbox(param_frame, from_=0.01, to=1.0, increment=0.01, textvariable=self.min_density, width=10)
        density_spinbox.grid(row=1, column=1, padx=(5, 0), pady=(5, 0))
        density_unit_label = ttk.Label(param_frame, text="(0.01-1.0)")
        density_unit_label.grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        detect_button = ttk.Button(button_frame, text="开始检测", command=self.start_detection)
        detect_button.pack(side=tk.LEFT, padx=(0, 10))
        
        export_button = ttk.Button(button_frame, text="导出数据", command=self.export_data)
        export_button.pack(side=tk.LEFT, padx=(0, 10))
        
        extract_button = ttk.Button(button_frame, text="提取所有", command=self.extract_all)
        extract_button.pack(side=tk.LEFT, padx=(0, 10))
        
        preview_button = ttk.Button(button_frame, text="预览结果", command=self.preview_result)
        preview_button.pack(side=tk.LEFT)
        
        # 移除浏览输出目录按钮，因为现在自动设置
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="检测结果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview显示结果
        columns = ('ID', '名称', 'X', 'Y', '宽度', '高度', '像素数', '密度')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 设置窗口图标（如果有的话）
        try:
            # 可以设置自定义图标
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
    def browse_atlas(self):
        """浏览atlas文件"""
        filename = filedialog.askopenfilename(
            title="选择Atlas图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.tga"), ("所有文件", "*.*")]
        )
        if filename:
            self.atlas_path.set(filename)
            self.status_var.set(f"已选择: {os.path.basename(filename)}")
            
    def browse_output(self):
        """浏览输出目录（已移除，现在自动设置）"""
        pass
            
    def on_drop_click(self, event):
        """点击拖拽区域"""
        filename = filedialog.askopenfilename(
            title="选择Atlas图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.tga"), ("所有文件", "*.*")]
        )
        if filename:
            self.atlas_path.set(filename)
            self.status_var.set(f"已选择: {os.path.basename(filename)}")
            
    def start_detection(self):
        """开始检测"""
        if not self.atlas_path.get():
            messagebox.showerror("错误", "请先选择atlas图片文件")
            return
            
        # 确保输出目录存在
        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)
            
        # 在新线程中运行检测
        self.progress.start()
        self.status_var.set("正在检测...")
        
        thread = threading.Thread(target=self._detect_sprites)
        thread.daemon = True
        thread.start()
        
    def _detect_sprites(self):
        """检测sprites（在后台线程中运行）"""
        try:
            # 创建检测器
            detector = AtlasDetector(self.atlas_path.get())
            
            # 检测sprites
            self.detection_result = detector.detect_sprites(
                min_size=(self.min_size.get(), self.min_size.get()),
                min_density=self.min_density.get()
            )
            
            # 更新UI（在主线程中）
            self.root.after(0, self._update_results)
            
        except Exception as e:
            self.root.after(0, lambda: self._detection_error(str(e)))
            
    def _update_results(self):
        """更新结果显示"""
        self.progress.stop()
        
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 添加新结果
        for sprite in self.detection_result:
            self.result_tree.insert('', 'end', values=(
                sprite['id'],
                sprite['name'],
                sprite['x'],
                sprite['y'],
                sprite['width'],
                sprite['height'],
                sprite['pixel_count'],
                f"{sprite['density']:.3f}"
            ))
            
        self.status_var.set(f"检测完成，找到 {len(self.detection_result)} 个sprites")
        
    def _detection_error(self, error_msg):
        """检测错误处理"""
        self.progress.stop()
        self.status_var.set("检测失败")
        messagebox.showerror("检测错误", f"检测过程中出现错误:\n{error_msg}")
        
    def export_data(self):
        """导出数据"""
        if not self.detection_result:
            messagebox.showwarning("警告", "请先进行检测")
            return
            
        filename = filedialog.asksaveasfilename(
            title="保存sprite数据",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                detector = AtlasDetector(self.atlas_path.get())
                detector.sprites = self.detection_result
                detector.export_sprite_data(filename)
                self.status_var.set(f"数据已导出到: {os.path.basename(filename)}")
                messagebox.showinfo("成功", "数据导出成功")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")
                
    def extract_all(self):
        """提取所有sprites"""
        if not self.detection_result:
            messagebox.showwarning("警告", "请先进行检测")
            return
            
        output_dir = self.output_dir.get()
        
        try:
            detector = AtlasDetector(self.atlas_path.get())
            detector.sprites = self.detection_result
            detector.extract_all_sprites(output_dir)
            self.status_var.set(f"已提取到: {output_dir}")
            messagebox.showinfo("成功", f"成功提取 {len(self.detection_result)} 个sprites")
        except Exception as e:
            messagebox.showerror("错误", f"提取失败:\n{str(e)}")
            
    def preview_result(self):
        """预览检测结果"""
        if not self.detection_result:
            messagebox.showwarning("警告", "请先进行检测")
            return
            
        try:
            detector = AtlasDetector(self.atlas_path.get())
            detector.sprites = self.detection_result
            
            # 生成预览图片
            preview_path = "detection_preview.png"
            detector.visualize_detection(preview_path)
            
            # 显示预览窗口
            self._show_preview(preview_path)
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败:\n{str(e)}")
            
    def _show_preview(self, image_path):
        """显示预览窗口"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("检测结果预览")
        
        # 加载图片
        try:
            from PIL import Image, ImageTk
            image = Image.open(image_path)
            
            # 缩放图片以适应窗口
            max_size = 800
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            label = ttk.Label(preview_window, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)
            
        except ImportError:
            messagebox.showwarning("警告", "需要安装PIL库来显示预览图片")
        except Exception as e:
            messagebox.showerror("错误", f"无法显示预览:\n{str(e)}")
            
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    app = AtlasGUI()
    app.run()


if __name__ == "__main__":
    main()
