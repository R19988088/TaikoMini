# APK 闪退问题修复总结

## 🔍 问题诊断

**症状**：GitHub Actions 编译的 APK 安装后闪退，连日志都无法生成

**可能原因**：
1. 资源文件路径在 Android 上不正确
2. Python 模块导入失败导致崩溃
3. 缺少异常处理，崩溃后无法记录日志
4. pygame 初始化在某些设备上失败

---

## ✅ 已实施的修复

### 1. 重写 main.py - 添加完整的错误处理

**文件**：`216 github/main.py`

**改进内容**：
- ✅ 添加完整的 try-except 异常捕获
- ✅ 实现 Android 日志记录函数 `log_to_android()`
- ✅ 添加多层回退机制（完整游戏 → 简化版本 → 错误显示）
- ✅ 改进资源路径检测（多个可能的路径）
- ✅ 添加详细的启动日志
- ✅ 确保即使崩溃也能显示错误信息

**关键代码**：
```python
def log_to_android(message):
    """在 Android 上记录日志"""
    try:
        if hasattr(sys, 'getandroidapp'):
            android_app = sys.getandroidapp()
            android_app.log(message)
        print(message)
    except Exception as e:
        print(f"[LOG ERROR] {e}")
```

### 2. 修复资源加载器路径问题

**文件**：`lib/resource_loader.py`

**改进内容**：
- ✅ 添加多个可能的资源路径检测
- ✅ 自动查找可用的资源目录
- ✅ 处理 Android 路径差异

**关键代码**：
```python
possible_res_paths = [
    Path(__file__).parent / 'res',  # 开发环境
    Path('.') / 'res',  # 当前目录
    Path('.') / 'lib' / 'res',  # lib 子目录
]
```

### 3. 添加 GitHub Actions 构建日志

**文件**：`.github/workflows/build-android.yml`

**改进内容**：
- ✅ 添加详细构建日志输出
- ✅ 保存构建日志为 artifact
- ✅ 即使构建失败也能下载日志

### 4. 创建调试指南

**文件**：`216 github/DEBUG_GUIDE.md`

**内容**：
- 📖 如何获取崩溃日志（ADB、Logcat）
- 🛠️ 常见问题修复方法
- 🧪 测试步骤和日志分析
- 💡 调试技巧和最佳实践

### 5. 创建兼容性测试脚本

**文件**：`216 github/test_android_compatibility.py`

**功能**：
- ✅ 测试 Python 模块导入
- ✅ 测试游戏模块加载
- ✅ 测试资源文件存在性
- ✅ 测试 pygame 初始化
- ✅ 测试字体加载
- ✅ 测试文件编码

**使用方法**：
```bash
python test_android_compatibility.py
```

### 6. 更新文档

**更新的文件**：
- `README.md` - 添加调试信息和快速修复步骤
- `QUICK_START.md` - 现有的快速开始指南
- `BUILD_GUIDE.md` - 现有的构建指南

---

## 🚀 如何测试修复

### 步骤 1：运行兼容性测试

```bash
cd "216 github"
python test_android_compatibility.py
```

### 步骤 2：推送代码到 GitHub

```bash
git add .
git commit -m "Fix Android crash issues"
git push
```

### 步骤 3：在 GitHub Actions 中构建

1. 访问 GitHub 仓库
2. 点击 "Actions" 标签
3. 运行 "Build Android APK" 工作流
4. 等待构建完成

### 步骤 4：下载并安装 APK

1. 下载构建好的 APK
2. 安装到 Android 设备
3. 使用 ADB 查看日志：

```bash
adb logcat | grep TaikoMini
```

### 步骤 5：分析日志

查看日志中的关键信息：
- `=== TaikoMini Starting ===` - 应用已启动
- `[ERROR]` - 错误信息
- `[FALLBACK]` - 降级到简化版本
- `Traceback` - Python 异常堆栈

---

## 📊 预期结果

### 最佳情况
应用正常启动，显示完整的游戏界面

### 次优情况
应用启动但使用简化版本（说明有部分模块加载失败）

### 最差情况
应用显示错误信息屏幕（说明主要逻辑有问题，但至少不闪退）

---

## 🔧 如果仍然闪退

### 步骤 1：获取完整日志

```bash
# 清除旧日志
adb logcat -c

# 启动应用
adb shell am start -n org.taikomini/org.kivy.android.PythonActivity

# 实时查看日志
adb logcat | grep -E "(python|TaikoMini|ERROR|FATAL)"
```

### 步骤 2：检查日志中的错误

常见错误：
- `ImportError` - 模块导入失败
- `FileNotFoundError` - 文件未找到
- `pygame.error` - pygame 初始化失败
- `Permission denied` - 权限问题

### 步骤 3：根据错误类型修复

**如果是 ImportError**：
- 检查 `buildozer.spec` 中的 `source.include_patterns`
- 确保所有 Python 文件都被包含

**如果是 FileNotFoundError**：
- 检查资源文件路径
- 确保 `lib/res/` 目录中的所有文件都被包含

**如果是 pygame.error**：
- 尝试降低图形要求
- 检查设备是否支持硬件加速

---

## 📝 日志示例

### 正常启动日志

```
=== TaikoMini Starting ===
[ANDROID] Environment configured
[PATH] Added lib path: /data/user/0/org.taikomini/files/app/lib
[INIT] Initializing pygame...
[AUDIO] Mixer initialized
[STORAGE] Songs path: /storage/emulated/0/Android/data/org.taikomini/files/songs
[IMPORT] Importing game modules...
[SONGS] Looking for songs in: /data/user/0/org.taikomini/files/app/songs
[SONGS] Found 5 songs
[GAME] Starting game loop...
```

### 错误但可用日志

```
=== TaikoMini Starting ===
[ERROR] Import failed: No module named 'lib.game'
[FALLBACK] Using simplified version...
```

---

## 💡 最佳实践

1. **始终查看日志** - 使用 ADB 或 Logcat
2. **渐进式测试** - 先确保基础功能正常
3. **记录所有错误** - 帮助诊断问题
4. **测试不同设备** - 某些问题只在特定设备上出现

---

## 📞 需要更多帮助？

如果问题仍然存在，请提供：
1. 完整的 logcat 日志
2. Android 版本和设备型号
3. 运行 `test_android_compatibility.py` 的结果
4. buildozer.spec 配置

查看详细调试指南：[DEBUG_GUIDE.md](DEBUG_GUIDE.md)

