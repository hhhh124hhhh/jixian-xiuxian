# 极简修仙项目 GitHub 部署指南

## 部署前准备

1. 确保已安装 Git（已验证）
2. 拥有 GitHub 账户
3. 项目已初始化为 Git 仓库（已完成）

## 部署步骤

### 第一步：在 GitHub 上创建新仓库

1. 登录 GitHub 账户
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `jixian-xiuxian`
   - **Description**: `极简修仙 - 一款基于Python和Pygame开发的修仙题材文字RPG游戏`
   - **Public**: 选择公开仓库 (✓)
   - **重要**：不要勾选任何初始化选项（不要初始化 README、.gitignore 或许可证文件）
4. 点击 "Create repository"

### 第二步：获取仓库 URL

创建完成后，您会看到类似这样的页面，记录下您的仓库 URL：
```
https://github.com/您的用户名/jixian-xiuxian.git
```

例如：
```
https://github.com/1772305619/jixian-xiuxian.git
```

### 第三步：配置本地仓库并推送代码

打开 Windows 命令提示符 (cmd)，依次执行以下命令：

```cmd
# 进入项目目录
cd /d "D:\极简修仙"

# 配置远程仓库（请将 YOUR_USERNAME 替换为您的实际 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/jixian-xiuxian.git

# 设置主分支
git branch -M main

# 推送代码到 GitHub
git push -u origin main
```

### 第四步：处理身份验证

当执行 `git push` 命令时，系统会提示您输入用户名和密码。

**重要**：GitHub 现在要求使用个人访问令牌而不是密码进行身份验证。

#### 创建个人访问令牌：

1. 在 GitHub 上：
   - 点击右上角头像，选择 "Settings"
   - 左侧菜单选择 "Developer settings"
   - 选择 "Personal access tokens" -> "Tokens (classic)"
   - 点击 "Generate new token" -> "Generate new token (classic)"
   - 设置令牌名称（如：jixian-xiuxian-deploy）
   - 选择过期时间
   - 在 "Select scopes" 中勾选 `repo` 权限
   - 点击 "Generate token"
   - 复制生成的令牌（请妥善保存）

2. 在身份验证时：
   - Username: 您的 GitHub 用户名
   - Password: 使用刚才生成的个人访问令牌

### 第五步：验证部署

推送成功后，刷新您的 GitHub 仓库页面，应该能看到所有项目文件。

## 后续维护

### 推送新的更改

```cmd
cd /d "D:\极简修仙"
git add .
git commit -m "更新说明"
git push
```

### 添加许可证文件（推荐）

建议为开源项目添加许可证文件：

1. 在项目根目录创建 `LICENSE` 文件
2. 添加 MIT 许可证内容：

```
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 常见问题及解决方案

### 1. 推送时出现权限错误

**问题**：
```
remote: Support for password authentication was removed on August 13, 2021.
remote: Please see https://docs.github.com/en/get-started/getting-started-with-git/about-remote-repositories#cloning-with-https-urls for information on currently recommended modes of authentication.
fatal: Authentication failed for 'https://github.com/username/repository.git/'
```

**解决方案**：使用个人访问令牌代替密码

### 2. 远程仓库已包含文件

**问题**：
```
error: failed to push some refs to 'https://github.com/username/repository.git'
hint: Updates were rejected because the remote contains work that you do not have locally.
```

**解决方案**：
```cmd
# 先拉取远程内容
git pull origin main

# 然后推送
git push -u origin main
```

### 3. 忘记设置 Git 用户信息

已配置：
- 用户名: YourName
- 邮箱: 1772305619@qq.com

如需修改，请使用以下命令：
```cmd
git config --global user.name "您的名字"
git config --global user.email "您的邮箱"
```

## 项目结构说明

```
极简修仙/
├── main.py                           # 主入口文件（运行v2.0版本）
├── README.md                         # 项目总体说明
├── CLAUDE.md                         # Claude开发指南
├── versions/                         # 版本分层目录
│   ├── v1.0-mvp/                     # 简单MVP版本
│   │   ├── jixian_mvp_pygame.py      # 单文件实现（148行）
│   │   ├── README_v1.md              # v1.0版本说明
│   │   └── requirements.txt          # v1.0依赖
│   │
│   └── v2.0-enterprise/              # 企业级架构版本
│       ├── main.py                   # v2.0主入口
│       ├── application.py            # 主应用程序
│       ├── models.py                 # 模型层
│       ├── actions.py                # 动作系统
│       ├── rules.py                  # 规则引擎
│       ├── run_tests.py              # 测试运行脚本
│       ├── 模型层.md                  # 设计文档
│       ├── requirements.txt          # v2.0依赖
│       ├── ui/                       # UI模块
│       ├── core/                     # 核心逻辑模块
│       └── tests/                    # 测试模块
└── 配置文件...
```

## 联系方式

如有部署问题，请通过以下方式联系：
- 创建 Issue
- 发起 Discussion