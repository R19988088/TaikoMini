# Buildozer Android 构建指南

## 重要说明

**⚠️ Buildozer 不支持 Windows 系统**

Buildozer 只能在 Linux 和 macOS 上运行。如果您使用 Windows，需要使用以下方案之一：

---

## 方案1：使用 WSL2 (Windows Subsystem for Linux) - 推荐 ⭐

这是 Windows 用户的最佳选择。

### 步骤 1：安装 WSL2

1. 以管理员身份打开 PowerShell
2. 运行以下命令：
```powershell
wsl --install
```
3. 重启电脑
4. 安装完成后，WSL2 会自动启动 Ubuntu

### 步骤 2：在 WSL2 中安装依赖

打开 Ubuntu (WSL2)，运行：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要的工具
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 安装 buildozer
pip3 install buildozer

# 安装 cython (推荐)
pip3 install cython
```

### 步骤 3：克隆项目并构建

```bash
# 如果项目在 Windows 文件系统，需要先复制到 WSL
# 假设项目在 D:\temp\py太鼓\TaikoMini\216 github
cd ~
mkdir taikomini
cp -r /mnt/d/temp/py太鼓/TaikoMini/216\ github/* ~/taikomini/
cd ~/taikomini

# 初始化 buildozer
buildozer init

# 构建 APK (首次构建会下载很多东西，需要等待)
buildozer android debug

# 成功后，APK 文件会在 .buildozer/android/platform/build/dists/taikomini/bin/ 目录
```

### 访问 Windows 文件

在 WSL2 中，Windows 文件系统挂载在 `/mnt/` 下：
- D盘 → `/mnt/d/`
- C盘 → `/mnt/c/`

---

## 方案2：使用虚拟机 (VMware/VirtualBox)

### 步骤 1：安装虚拟机软件

1. 下载 VMware Workstation Pro 或 VirtualBox
2. 下载 Ubuntu 22.04 LTS ISO 镜像

### 步骤 2：创建虚拟机

1. 创建新的 Ubuntu 虚拟机
2. 分配至少 4GB RAM 和 50GB 硬盘空间
3. 安装 Ubuntu

### 步骤 3：在虚拟机中构建

参考方案1的 WSL2 步骤（但不需要使用 `/mnt/` 路径）

---

## 方案3：使用 GitHub Actions 云构建 ⭐⭐⭐

**这是最简单的方法！** 无需本地安装任何东西。

### 步骤 1：准备 GitHub Actions 配置

我已经为您创建了 GitHub Actions 工作流文件 `.github/workflows/build-apk.yml`

### 步骤 2：提交到 GitHub

```bash
cd "216 github"
git add .
git commit -m "Add Android build configuration"
git push
```

### 步骤 3：触发构建

1. 访问 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择 "Build Android APK" 工作流
4. 点击 "Run workflow"
5. 等待构建完成（约 10-20 分钟）
6. 下载生成的 APK

---

## 方案4：使用 Docker (适用于高级用户)

### 步骤 1：安装 Docker Desktop

从 https://www.docker.com/products/docker-desktop 下载并安装

### 步骤 2：使用 Buildozer Docker 镜像

```bash
# 在项目目录运行
docker run --rm -v %cd%:/app kivy/buildozer android debug
```

---

## 详细构建说明

### Buildozer 配置

项目已包含完整的 `buildozer.spec` 配置文件：

```ini
# 关键配置
android.api = 34           # Android 14
android.minapi = 33        # Android 13
requirements = python3,pygame==2.6.1,setuptools,six
p4a.bootstrap = sdl2       # SDL2 后端（pygame 需要）
```

### 构建命令

```bash
# 清理之前的构建
buildozer android clean

# 构建调试版 APK
buildozer android debug

# 构建发布版 APK（需要签名）
buildozer android release

# 查看完整日志
buildozer android debug -v
```

### 首次构建

首次构建会：
1. 下载 Android SDK（约 500MB）
2. 下载 Android NDK（约 1GB）
3. 编译 Python（约 10-20 分钟）
4. 编译 pygame 和其他依赖（约 5-10 分钟）
5. 打包 APK（约 2-5 分钟）

**总计需要约 1-2 小时**（取决于网络速度）

### 后续构建

如果没有修改依赖，后续构建只需 5-10 分钟。

---

## 常见问题

### Q: 构建失败怎么办？

```bash
# 查看详细日志
buildozer android debug -v > build.log 2>&1

# 清理并重新构建
buildozer android clean
buildozer android debug
```

### Q: 网络很慢怎么办？

使用镜像源或在夜间运行构建。

### Q: APK 文件太大？

```bash
# 在 buildozer.spec 中添加
android.archs = arm64-v8a  # 只构建 64 位版本
```

### Q: 如何签名 APK？

```bash
# 生成密钥
keytool -genkey -v -keystore my-release-key.keystore -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000

# 在 buildozer.spec 中配置
android.keystore = my-release-key.keystore
android.keystore_password = 你的密码
android.keyalias = my-key-alias
android.key_password = 你的密码
```

---

## 推荐方案对比

| 方案 | 难度 | 速度 | 推荐度 |
|------|------|------|--------|
| WSL2 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 虚拟机 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| GitHub Actions | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Docker | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |

---

## 总结

**最推荐：使用 GitHub Actions**（无需本地安装，全自动）
**其次推荐：使用 WSL2**（性能好，设置简单）

**不推荐：在 Windows 上直接运行**（Buildozer 不支持）

祝您构建顺利！🎮

