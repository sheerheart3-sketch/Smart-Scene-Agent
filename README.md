# Smart-Scene-Agent
A lightweight desktop AI agent based on LLM, supporting intent recognition and one-click launching of apps, websites, and daily work scenes.基于大模型的轻量级桌面 AI 助手，支持意图识别，一键启动软件、网站与日常工作场景。

🧠 智能语义理解：基于 LLM 理解自然语言指令，无需记忆复杂命令

📋 场景管理：创建 / 删除 / 编辑 / 查看自定义工作场景

🚀 一键启动：双击场景即可自动依次打开所有关联的软件 / 网页 / 文件

🎨 可视化界面：简洁美观的 TKinter GUI 界面，操作直观

🌐 多类型支持：支持打开网页、本地软件、文件路径等多种目标

## 环境要求
Python 3.7+
Windows
网络连接（用于调用 LLM API）

### 一、下载项目
```bash
git clone https://github.com/sheerheart3-sketch/Smart-Scene-Agent
```
### 二、安装依赖
```bash
pip install -r requirements.txt
```
### 三、配置 API 密钥及接口
1、在项目根目录创建.env文件
2、添加以下内容：
```
API_KEY=你的API密钥
URL=API接口
```
### 四、可选功能：自动在user文件夹下搜索软件，需要在.env文件中加入
USERNAME=你的用户名
添加后，可以在C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Programs\\文件夹下搜索所需软件

### 五、启动GUI界面
```bash
python agent_gui.py
```
### 六、操作说明
- 创建场景时，需要告知agent，场景的名字和需要打开的软件、网址。
- 网址不需要以http开头。
- 软件可以是文件绝对路径，如果软件的快捷方式存放在桌面上，或者软件的.exe文件存放在以下三种文件夹下时，可以直接输入软件名，自动查找
- C:\Program Files\<软件名>\<软件名>.exe
- C:\Program Files (x86)\<软件名>\<软件名>.exe
- C:\Users\<用户名>\AppData\Local\Programs\<软件名>\<软件名>.exe
- 告诉agent想要做某件事时，agent会联想场景库中合适的场景，打开对应的场景
- 如：我想玩游戏------联想到steam场景------自动打开steam游戏启动器

### 七、常见问题
#### Q1: API 调用失败 / 返回 HTML 页面
- 检查.env文件中的 API 密钥是否正确
- 确认网络连接正常，可访问 DMXAPI 服务
- 检查 API 额度是否充足

#### Q2: 无法打开指定软件
- 确认软件已安装，且路径正确
- 软件名需与安装目录中的可执行文件或桌面上的快捷方式匹配

#### Q3: 场景列表为空
- 首次使用需先创建场景
- 检查work_scenes.json文件是否存在且格式正确
- 权限问题：确保程序有读写文件的权限
