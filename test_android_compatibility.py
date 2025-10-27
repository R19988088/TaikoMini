#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 兼容性测试脚本
在本地运行此脚本可以检查常见问题
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    modules = [
        'pygame',
        'numpy',
        'pathlib',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_game_modules():
    """测试游戏模块"""
    print("\n=== 测试游戏模块 ===")
    
    # 添加 lib 路径
    lib_path = Path(__file__).parent / 'lib'
    if lib_path.exists():
        sys.path.insert(0, str(lib_path))
    
    modules = [
        'lib.game',
        'lib.song_select',
        'lib.resource_loader',
        'lib.audio',
        'lib.tja_parser',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_resources():
    """测试资源文件"""
    print("\n=== 测试资源文件 ===")
    
    resources = [
        ('lib/res/FZPangWaUltra-Regular.ttf', 'Font'),
        ('lib/res/Texture/selectsongs', 'Texture directory'),
        ('lib/res/wav', 'Audio directory'),
    ]
    
    failed = []
    for path_str, name in resources:
        path = Path(__file__).parent / path_str
        if path.exists():
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: {path} (not found)")
            failed.append(name)
    
    return len(failed) == 0

def test_pygame_init():
    """测试 pygame 初始化"""
    print("\n=== 测试 pygame 初始化 ===")
    
    try:
        import pygame
        pygame.init()
        print("✓ pygame.init()")
        
        pygame.mixer.init()
        print("✓ pygame.mixer.init()")
        
        pygame.quit()
        print("✓ pygame.quit()")
        
        return True
    except Exception as e:
        print(f"✗ pygame 初始化失败: {e}")
        return False

def test_pygame_font():
    """测试字体加载"""
    print("\n=== 测试字体加载 ===")
    
    try:
        import pygame
        pygame.init()
        
        # 测试默认字体
        font = pygame.font.Font(None, 24)
        print("✓ 默认字体")
        
        # 测试自定义字体
        font_path = Path(__file__).parent / 'lib' / 'res' / 'FZPangWaUltra-Regular.ttf'
        if font_path.exists():
            font = pygame.font.Font(str(font_path), 24)
            print(f"✓ 自定义字体: {font_path}")
        else:
            print(f"! 自定义字体未找到: {font_path}")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"✗ 字体加载失败: {e}")
        return False

def test_file_encoding():
    """测试文件编码"""
    print("\n=== 测试文件编码 ===")
    
    try:
        # 测试读取包含中文的文件
        test_file = Path(__file__).parent / 'main.py'
        if test_file.exists():
            content = test_file.read_text(encoding='utf-8')
            print(f"✓ 读取 UTF-8 文件: {len(content)} 字符")
        
        return True
    except Exception as e:
        print(f"✗ 文件编码测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Android 兼容性测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("游戏模块", test_game_modules()))
    results.append(("资源文件", test_resources()))
    results.append(("pygame 初始化", test_pygame_init()))
    results.append(("字体加载", test_pygame_font()))
    results.append(("文件编码", test_file_encoding()))
    
    # 显示结果
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ 所有测试通过！可以尝试构建 APK。")
        return 0
    else:
        print("\n✗ 有测试失败，请修复问题后再构建 APK。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

