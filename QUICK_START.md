# Android APK 构建快速指南

## ⚠️ 重要提示

**Buildozer 不支持 Windows 系统！**

您需要在 Linux 或 macOS 环境中构建 APK。

---

## 🚀 最简单的方法：GitHub Actions（推荐）

无需安装任何软件，自动在云端构建！

### 步骤：

1. **将代码推送到 GitHub**
   ```bash
   cd "216 github"
   git add .
   git commit -m "准备构建 Android APK"
   git push
   ```

2. **触发构建**
   - 访问 GitHub 仓库
   - 点击 "Actions" 标签
   - 选择 "Build Android APK" 工作流
   - 点击 "Run workflow" → "Run workflow"
   - 等待 10-20 分钟

3. **下载 APK**
   - 构建完成后，在 "Artifacts" 部分下载 APK 文件

---

## 💻 本地构建：使用 WSL2

如果您想在本地构建，推荐使用 WSL2：

### 1. 安装 WSL2

```powershell
# 以管理员身份打开 PowerShell
wsl --install
# 重启电脑
```

### 2. 打开 Ubuntu (WSL2)

在开始菜单搜索 "Ubuntu" 并打开

### 3. 安装依赖

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip3 install buildozer cython
```

### 4. 构建 APK

```bash
# 进入项目目录（Windows 文件系统挂载在 /mnt/）
cd /mnt/d/temp/py太鼓/TaikoMini/216\ github

# 首次构建（需要下载很多东西，等待 1-2 小时）
buildozer android debug

# APK 会在 .buildozer/android/platform/build/dists/taikomini/bin/ 目录
```

---

## 📦 其他方案

详见 `BUILD_GUIDE.md` 了解更多方案：
- 虚拟机 (VMware/VirtualBox)
- Docker
- macOS 构建

---

## 🎯 常见问题

**Q: 能否直接导入 Android Studio？**  
A: 不能！这是 Python/pygame 项目，需要用 Buildozer 转换。

**Q: 构建需要多长时间？**  
A: 首次构建 1-2 小时，后续构建 5-10 分钟。

**Q: 能否在 Windows 上运行 Buildozer？**  
A: 不能，必须在 Linux 环境（WSL2、虚拟机或 GitHub Actions）。

---

## ✅ 推荐流程

1. **开发阶段**：在 Windows 上用 Python 运行和测试
2. **构建 APK**：使用 GitHub Actions（最简单）
3. **如果需要频繁构建**：使用 WSL2

---

## 📞 需要帮助？

查看详细指南：`BUILD_GUIDE.md`

