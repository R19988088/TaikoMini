"""
Android路径配置验证脚本
用于验证所有路径在Android平台上是否正确配置
"""

import sys
from pathlib import Path

# 添加lib到路径
sys.path.insert(0, str(Path(__file__).parent))

from lib.android_adapter import get_adapter, is_android
from lib.resource_loader import ResourceLoader
from lib.config_manager import ConfigManager

def test_paths():
    """测试所有路径配置"""
    print("=" * 70)
    print("Android路径配置验证 / Android Path Configuration Test")
    print("=" * 70)
    print()
    
    # 1. 测试平台检测
    print("1. 平台检测 / Platform Detection")
    print("-" * 70)
    adapter = get_adapter()
    print(f"   是否为Android平台 / Is Android: {adapter.is_android}")
    print()
    
    # 2. 测试Android适配器路径
    print("2. Android适配器路径 / Android Adapter Paths")
    print("-" * 70)
    songs_folder = adapter.get_songs_folder()
    print(f"   歌曲文件夹 / Songs Folder: {songs_folder}")
    
    if adapter.is_android:
        base_path = adapter.get_base_path()
        print(f"   基础路径 / Base Path: {base_path}")
        print(f"   预期路径 / Expected: /sdcard/taikomini")
        
        # 验证路径是否正确
        expected_songs = Path("/sdcard/taikomini/songs")
        if songs_folder == expected_songs:
            print(f"   ✓ 歌曲文件夹路径正确！")
        else:
            print(f"   ✗ 歌曲文件夹路径错误！")
            print(f"     实际: {songs_folder}")
            print(f"     预期: {expected_songs}")
    else:
        print(f"   桌面平台，使用相对路径 / Desktop platform, using relative path")
        print(f"   预期路径 / Expected: songs")
    print()
    
    # 3. 测试资源加载器路径
    print("3. 资源加载器路径 / Resource Loader Paths")
    print("-" * 70)
    loader = ResourceLoader()
    print(f"   自定义资源路径 / Custom Resource Path: {loader.custom_resource_path}")
    
    if adapter.is_android:
        expected_resource = Path("/sdcard/taikomini/songs/Resource")
        if loader.custom_resource_path == expected_resource:
            print(f"   ✓ 资源路径正确！")
        else:
            print(f"   ✗ 资源路径错误！")
            print(f"     实际: {loader.custom_resource_path}")
            print(f"     预期: {expected_resource}")
    else:
        print(f"   桌面平台，使用相对路径 / Desktop platform, using relative path")
        print(f"   预期路径 / Expected: songs/Resource")
    print()
    
    # 4. 测试配置管理器路径
    print("4. 配置管理器路径 / Config Manager Paths")
    print("-" * 70)
    config = ConfigManager()
    print(f"   配置文件路径 / Config File Path: {config.config_path}")
    
    if adapter.is_android:
        expected_config = Path("/sdcard/taikomini/songs/config.ini")
        if config.config_path == expected_config:
            print(f"   ✓ 配置文件路径正确！")
        else:
            print(f"   ✗ 配置文件路径错误！")
            print(f"     实际: {config.config_path}")
            print(f"     预期: {expected_config}")
    else:
        print(f"   桌面平台，使用相对路径 / Desktop platform, using relative path")
        print(f"   预期路径 / Expected: songs/config.ini")
    print()
    
    # 5. 测试目录是否存在
    print("5. 目录存在性检查 / Directory Existence Check")
    print("-" * 70)
    print(f"   歌曲目录存在 / Songs folder exists: {songs_folder.exists()}")
    if adapter.is_android:
        resource_path = songs_folder / "Resource"
        print(f"   资源目录存在 / Resource folder exists: {resource_path.exists()}")
    print()
    
    # 6. 总结
    print("=" * 70)
    if adapter.is_android:
        print("Android平台路径配置摘要 / Android Path Configuration Summary:")
        print("-" * 70)
        print(f"  基础目录 / Base:     /sdcard/taikomini")
        print(f"  歌曲目录 / Songs:    /sdcard/taikomini/songs")
        print(f"  资源目录 / Resource: /sdcard/taikomini/songs/Resource")
        print(f"  配置文件 / Config:   /sdcard/taikomini/songs/config.ini")
    else:
        print("桌面平台路径配置摘要 / Desktop Path Configuration Summary:")
        print("-" * 70)
        print(f"  基础目录 / Base:     . (当前目录)")
        print(f"  歌曲目录 / Songs:    songs")
        print(f"  资源目录 / Resource: songs/Resource")
        print(f"  配置文件 / Config:   songs/config.ini")
    print("=" * 70)
    print()
    
    # 7. 使用说明
    if adapter.is_android:
        print("Android使用说明 / Android Usage Instructions:")
        print("-" * 70)
        print("1. 首次启动时，应用会自动创建以下目录结构：")
        print("   /sdcard/taikomini/")
        print("   └── songs/")
        print("       └── Resource/")
        print()
        print("2. 将您的歌曲文件放入 /sdcard/taikomini/songs/ 目录")
        print("   每首歌需要：")
        print("   - .tja 文件（谱面）")
        print("   - .ogg/.wav/.mp3 文件（音乐）")
        print()
        print("3. 可选：将分类背景图片放入 /sdcard/taikomini/songs/Resource/")
        print()
        print("4. 重新启动应用即可看到歌曲")
        print("=" * 70)

if __name__ == "__main__":
    try:
        test_paths()
        print("\n✓ 测试完成 / Test completed successfully")
    except Exception as e:
        print(f"\n✗ 测试失败 / Test failed: {e}")
        import traceback
        traceback.print_exc()

