# 🏆 粗趣计分 (Live Scoreboard)

一个基于 PySide6 的实时比赛记分板桌面应用，专为线下体育活动设计。支持 OBS 推流叠加、手机扫码远程控制、模板热重载——适合飞盘比赛、羽毛球局、匹克球等场景投屏使用。

## ✨ 功能

### 🎯 多运动预设

内置三种运动规则，开箱即用：

| 运动 | 计时模式 | 节次 | 得分规则 | 特殊机制 |
|------|----------|------|----------|----------|
| 🥏 极限飞盘 | 倒计时 | 上半场 / 中场休息 / 下半场 | 15分制·领先2分 | 犯规追踪 · 加时赛 |
| 🏸 羽毛球 | 正计时（秒表） | 第一局 / 第二局 / 第三局 | 21分制·领先2分 | - |
| 🏓 匹克球 | 正计时（秒表） | 第一局 / 第二局 / 第三局 | 11分制·领先2分 | - |

### 🎨 记分板窗口

- **无边框透明窗口** — 可叠加在 OBS / 推流画面之上
- **自由拖动 / 边缘缩放** — 右键菜单切换"改变大小"模式，拖动边缘调整尺寸
- **右键菜单** — 置顶 / 改变大小 / 隐藏 / 关闭
- **ESC 隐藏 / Ctrl+Q 退出**
- **透明背景** — 极简透明模板，适合直播叠加
- **悬浮置顶** — 始终显示在其他窗口之上
- **居中显示** — 一键居中对齐屏幕顶部

### 🎛️ 控制面板

- **比分控制** — +/-1 按钮，支持负分
- **计时器** — 开始 / 暂停 / 重置，支持自定义时分秒
- **倒计时 / 秒表切换** — 一键切换计时模式
- **节次切换** — 下拉选择当前节次（含加时赛）
- **队伍名称编辑** — 实时同步到记分板
- **交换比分** — 换边时一键交换两队比分和名称
- **全部重置** — 重置比分、计时器、节次
- **样式编辑器入口** — 打开内置样式编辑器
- **手机控制入口** — 显示二维码供手机扫描

### 📱 手机远程控制

内建轻量 HTTP 服务器（端口 5000），手机连接同一 WiFi 即可控制：

- 📱 **移动端网页界面** — 响应式设计，适配手机屏幕
- 🔲 **二维码扫码** — 控制面板自动生成二维码，扫码即用
- 📊 **实时状态同步** — 每秒轮询，比分 / 计时器实时更新
- 🎮 **完整控制** — 加减分、计时器、节次切换、比分交换、加时赛

### 🖌️ 样式编辑器

无需编辑 JSON，可视化调整记分板外观：

- **背景** — 颜色 / 渐变 / 透明度
- **两队设置** — 队名和比分的颜色、字体大小
- **独立元素** — 计时器、节次标签、VS 分隔符的颜色和字体
- **统一布局** — 所有元素的 X/Y 坐标，双精度微调
- **实时预览** — 修改即时反映在记分板上
- **显示/隐藏** — 每个元素可独立控制可见性
- **设为默认** — 一键将当前样式保存为默认模板
- **重置为默认** — 一键恢复原始样式

### 📐 模板系统

JSON 驱动，支持自定义记分板布局：

```json
{
  "template_id": "banner",
  "name": "粗趣简约横条",
  "resolution": { "width": 2450, "height": 500 },
  "background": {
    "color": "#0a0a1a",
    "gradient": true,
    "gradient_from": "#0d0d2b",
    "gradient_to": "#1a1a3e",
    "opacity": 1.0,
    "image": ""
  },
  "elements": {
    "team_a_name": { "type": "label", "geometry": {"x": 0.1, "y": 0.15, "w": 0.18, "h": 0.18}, ... },
    "team_a_score": { "type": "digits", "geometry": ..., "min_digits": 2 },
    "timer": { "type": "timer", "geometry": ..., "format": "mm:ss" },
    "period": { "type": "label", ... },
    "vs_divider": { "type": "label", ... },
    "team_b_score": { "type": "digits", ... },
    "team_b_name": { "type": "label", ... }
  }
}
```

- **热重载** — 修改 `template.json` 后自动刷新记分板
- **多模板切换** — 控制面板下拉切换，启动向导预览选择
- **内置两个模板** — `default`（粗趣简约横条）和 `minimal`（极简透明）

## 📦 安装

### 方式一：直接运行 exe（Windows）

从 [Releases](../../releases) 下载 `粗趣计分.exe`，双击运行即可。无需安装 Python 或任何依赖。

### 方式二：源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/Azeen999/live-scoreboard.git
cd live-scoreboard

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

**环境要求：** Python 3.8+

### 方式三：自行打包 exe

```bash
python build.py
```

生成的 exe 位于 `dist/粗趣计分.exe`。

## 🚀 使用指南

### 启动流程

1. 运行 `python main.py`（或双击 `粗趣计分.exe`）
2. **步骤 1/3** — 选择比赛类型（极限飞盘 / 羽毛球 / 匹克球）
3. **步骤 2/3** — 选择记分板模板（粗趣简约横条 / 极简透明）
4. **步骤 3/3** — 确认设置，点击「开始比赛」
5. 出现两个窗口：**控制面板** 和 **记分板**

### 典型工作流

```
控制面板（操作端）          记分板（展示端）
┌──────────────┐         ┌──────────────────┐
│ 队伍A  +1 -1 │         │  队伍A  15 : 12  队伍B  │
│ 计时器 开始/暂停│   ──▶  │       30:00        │
│ 节次切换      │         │      上半场        │
│ 模板切换      │         └──────────────────┘
│ 手机控制      │              ▲ 投屏 / OBS 叠加
└──────────────┘              │
                              ▼
                         📱 手机扫码远程控制
```

### 投屏 / OBS 使用

1. 记分板窗口默认无边框，右键菜单可选择「置顶」或「改变大小」
2. 在 OBS 中添加「窗口捕获」，选择「粗趣计分 - 记分板」
3. 推荐使用 `minimal` 模板（透明背景），叠加在直播画面上方
4. 用「居中显示」一键将记分板放在屏幕顶部中央

### 手机控制

1. 手机与电脑连接**同一 WiFi**
2. 点击控制面板的「手机控制」按钮
3. 扫描二维码，或在手机浏览器输入显示的地址
4. 手机即可控制比分、计时器、节次等

## 🏗️ 项目结构

```
scoreboard/
├── main.py                  # 入口：启动向导 + 主窗口
├── build.py                 # PyInstaller 打包脚本
├── requirements.txt         # PySide6, PyInstaller
├── start.bat / start.ps1    # Windows 启动脚本
├── 粗趣计分.spec            # PyInstaller spec 文件
├── src/
│   ├── app/
│   │   └── application.py   # ScoreboardApp：组装控制面板 + 记分板 + Web
│   ├── models/
│   │   ├── game_state.py    # GameState：核心状态管理（信号驱动）
│   │   └── sport_config.py  # SportConfig：运动规则数据类
│   ├── config/
│   │   └── sports.py        # 运动预设配置（飞盘/羽毛球/匹克球）
│   ├── views/
│   │   ├── control_panel.py      # 控制面板窗口
│   │   ├── scoreboard_window.py  # 记分板窗口（无边框+Canvas渲染）
│   │   ├── setup_wizard.py       # 启动向导（3步）
│   │   └── style_editor.py       # 样式编辑器
│   ├── templates/
│   │   └── template_config.py    # 模板加载 & 数据模型
│   ├── utils/
│   │   └── resource_path.py      # 资源路径解析（开发/打包兼容）
│   └── web_controller.py         # HTTP 服务器 + 移动端网页
└── templates/
    ├── default/
    │   ├── template.json         # 粗趣简约横条
    │   └── bg.png               # 背景图
    └── minimal/
        └── template.json         # 极简透明
```

## 🛠️ 技术栈

- **UI 框架**: [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt 6 for Python)
- **打包工具**: [PyInstaller](https://pyinstaller.org/)
- **架构模式**: 信号驱动（Qt Signals & Slots）
- **模板系统**: JSON 配置文件 + Canvas 自绘
- **移动端**: 内建 HTTP Server + 原生 HTML/JS 页面
- **样式**: Catppuccin Mocha 暗色主题

## 🔧 扩展自定义运动

在 `src/config/sports.py` 中添加新的 `SportConfig`：

```python
"basketball": SportConfig(
    sport_id="basketball",
    name_zh="篮球",
    name_en="Basketball",
    periods_count=4,
    period_labels=["第一节", "第二节", "第三节", "第四节"],
    period_duration_seconds=600,  # 10分钟
    max_score=None,               # 无上限
    timer_mode="countdown",
    score_increment_buttons=[1, 2, 3],  # 支持1/2/3分
    preset_durations=[300, 600, 720],
    ...
),
```

## 📄 License

MIT
