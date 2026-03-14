import os
import json
import webbrowser
import datetime
import subprocess
import requests
from dotenv import load_dotenv

# ========== 基础配置 ==========
load_dotenv()  # 加载.env文件中的API密钥
SCENE_FILE = "work_scenes.json"
DMXAPI_KEY = "sk-ifcCGAZTvicyJRyM5Bv4rXLJASUpw84rB1MAbuPFQyqKtePn"  # API密钥
DMXAPI_URL = "https://www.dmxapi.cn/v1/chat/completions"  # API端点

# ========== 工具函数 ==========
def load_scenes():
    """加载已保存的工作场景"""
    if not os.path.exists(SCENE_FILE):
        try:
            with open(SCENE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"⚠️  创建场景文件失败：{e}")
        return {}
    try:
        with open(SCENE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  加载场景文件失败：{e}")
        return {}

def save_scene(scene_name, targets):
    """保存工作场景到文件"""
    # 验证输入
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    if not targets or len(targets) == 0:
        return "❌ 打开项列表不能为空！"
    
    try:
        scenes = load_scenes()
        scenes[scene_name] = {
            "targets": targets,
            "create_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        return f"✅ 场景「{scene_name}」创建成功，包含{len(targets)}个打开项"
    except IOError as e:
        return f"❌ 保存场景失败：{e}"

def delete_scene(scene_name):
    """删除已保存的工作场景"""
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    
    try:
        scenes = load_scenes()
        if scene_name not in scenes:
            return f"❌ 场景「{scene_name}」不存在！已有场景：{list(scenes.keys())}"
        
        del scenes[scene_name]
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        return f"✅ 场景「{scene_name}」已删除"
    except IOError as e:
        return f"❌ 删除场景失败：{e}"

def update_scene(scene_name, targets):
    """修改已保存的工作场景"""
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    if not targets or len(targets) == 0:
        return "❌ 打开项列表不能为空！"
    
    try:
        scenes = load_scenes()
        if scene_name not in scenes:
            return f"❌ 场景「{scene_name}」不存在！已有场景：{list(scenes.keys())}"
        
        scenes[scene_name] = {
            "targets": targets,
            "create_time": scenes[scene_name].get("create_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        return f"✅ 场景「{scene_name}」已更新，包含{len(targets)}个打开项"
    except IOError as e:
        return f"❌ 更新场景失败：{e}"

def open_target(target):
    """打开单个目标（软件/网页）"""
    try:
        # 检查是否为URL格式（含有 . 且不以 \ 或 / 开头）
        is_url = ("." in target and not target.startswith(("\\", "/"))) and not os.path.exists(target)
        
        if target.startswith(("http://", "https://")):
            # 标准URL
            webbrowser.open(target)
            return f"✅ 已打开网页：{target}"
        elif is_url:
            # 自动添加 https:// 前缀（如 baidu.com）
            url = f"https://{target}"
            webbrowser.open(url)
            return f"✅ 已打开网页：{url}"
        else:
            # 先检查是否为完整路径
            if os.path.exists(target):
                if os.name == "nt":
                    # 检查是否为快捷方式
                    if target.lower().endswith('.lnk'):
                        # 用cmd启动快捷方式并隐藏输出
                        subprocess.Popen(f'cmd /c start "" "{target}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                else:
                    os.system(f"open '{target}' > /dev/null 2>&1 &")
                return f"✅ 已打开软件：{target}"
            
            # 尝试自动查找程序
            program_path = find_program(target)
            if program_path:
                if os.name == "nt":
                    # 检查是否为快捷方式
                    if program_path.lower().endswith('.lnk'):
                        # 用cmd启动快捷方式并隐藏输出
                        subprocess.Popen(f'cmd /c start "" "{program_path}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.Popen([program_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                else:
                    os.system(f"open '{program_path}' > /dev/null 2>&1 &")
                return f"✅ 已打开软件：{target} ({program_path})"
            
            # 最后尝试直接执行（可能在PATH中）
            if os.name == "nt":
                subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                os.system(f"open '{target}' > /dev/null 2>&1 &")
            return f"✅ 已打开软件：{target}"
    except Exception as e:
        return f"❌ 打开失败「{target}」：{str(e)}"

def start_scene(scene_name):
    """启动工作场景"""
    scenes = load_scenes()
    if scene_name not in scenes:
        return f"未找到场景「{scene_name}」！已保存场景：{list(scenes.keys())}"
    targets = scenes[scene_name]["targets"]
    results = []
    for target in targets:
        results.append(open_target(target))
        import time
        time.sleep(1)
    return f"场景「{scene_name}」启动完成！\n" + "\n".join(results)

def find_program(program_name):
    """自动查找程序的完整路径（Windows）"""
    if os.name != "nt":
        return None  # 仅在Windows下有效
    
    # 常见程序安装位置
    common_paths = [
        f"C:\\Program Files\\{program_name}\\{program_name}.exe",
        f"C:\\Program Files (x86)\\{program_name}\\{program_name}.exe",
        f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Programs\\{program_name}\\{program_name}.exe",
    ]
    
    # VSCode特殊处理
    if program_name.lower() == "vscode":
        common_paths.extend([
            f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "C:\\Program Files\\Microsoft VS Code\\Code.exe",
            "C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe",
        ])
    
    # Chrome特殊处理
    if program_name.lower() == "chrome":
        common_paths.extend([
            f"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            f"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ])
    
    # 检查路径是否存在
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # 在 Desktop 上搜索快捷方式
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    try:
        for filename in os.listdir(desktop_path):
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext.lower() == program_name.lower():
                return os.path.join(desktop_path, filename)
    except:
        pass
    
    # 最后尝试直接用name（可能在PATH中）
    try:
        result = subprocess.run(["where", program_name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None
# ========== LLM API 调用 ==========
def reason(model, messages):
    """调用 DMXAPI 接口（接收完整对话历史）"""
    headers = {
        "Accept": "application/json",
        "Authorization": DMXAPI_KEY,
        "User-Agent": "DMXAPI/1.0.0",
    }
    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        response = requests.post(DMXAPI_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        model_response = response_data['choices'][0]['message']['content']
        return model_response
    except Exception as e:
        print(f"⚠️  API调用失败：{e}")
        return ""
# ========== LLM 核心逻辑（Agent的灵魂） ==========
def llm_understand(user_input):
    """
    让大语言模型理解用户需求，从场景库中智能匹配场景
    核心能力：
    1. 创建新场景
    2. 从场景库中智能匹配用户需求
    3. 查看已保存的场景
    4. 删除场景
    5. 修改场景
    """
    # 检查简单指令
    if "查看" in user_input or "有哪些" in user_input or "所有场景" in user_input:
        return "LIST"
    
    # 加载已保存的场景库
    scenes = load_scenes()
    scene_list = list(scenes.keys())
    
    # 系统提示：定义Agent的核心能力
    system_prompt = f"""
    你是一个智能工作场景启动Agent。你的核心职责是理解用户需求，并从已有的场景库中匹配最合适的场景。

    【当前场景库】
    {', '.join(scene_list) if scene_list else '（暂无已保存的场景）'}

    【你能做的事】
    1. 创建新场景：用户想要保存一个新的工作流程
       格式：CREATE|场景名|打开项1,打开项2,打开项3
       例："创建工作环境，打开VSCode、Navicat、WeChat"
       返回："CREATE|工作环境|VSCode,Navicat,WeChat"

    2. 修改场景：用户想要更新已有场景的打开项
       用户说："修改编程场景，改成打开VSCode和Chrome"/"编辑看视频，添加微信"
       返回：UPDATE|场景名|打开项1,打开项2
       示例："UPDATE|编程|VSCode,Chrome"

    3. 智能匹配场景：用户说出他们的需求，你从场景库中找出最匹配的场景
       用户说："我想编程"/"给我编程环境"/"打开代码编辑器"
       你的任务：从场景库中找出最相关的场景，返回 START|场景名
       示例：如果场景库有"编程"场景，返回 "START|编程"

    4. 查看场景：用户要看所有已保存的场景
       返回：LIST

    5. 删除场景：用户想要删除一个已保存的场景
       用户说："删除看视频"/"删除看视频场景"/"干掉编程场景"
       返回：DELETE|场景名
       例：返回 "DELETE|看视频"

    【重要规则】
    - 如果用户要创建场景，严格按照 CREATE|name|items 格式
    - 如果用户要修改场景，返回 UPDATE|场景名|新的打开项 格式
    - 如果用户表达删除意图，返回 DELETE|场景名
    - 如果用户表达需求（不是明确说场景名），你要理解意图并从场景库中找最匹配的
    - 如果场景库为空且用户有需求，帮助用户创建新场景
    - 如果场景库中找不到匹配的场景，也建议创建新场景
    - 只返回命令，不返回其他内容

    【打开项类型】
    - 软件：VSCode、Chrome、Word、微信、钉钉、Navicat
    - 网址：https://www.bilibili.com、github.com、baidu.com
    - 路径：C:\\\\Program Files\\\\...
    """
    
    # 调用LLM进行智能匹配
    try:
        result_text = reason("Qwen/Qwen2.5-Coder-7B-Instruct", [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]).strip()
        
        # 检测是否返回了HTML（API被拦截）
        if result_text.startswith(("<!DOCTYPE", "<html", "Access")):
            print(f"⚠️  API返回异常响应")
            return "UNKNOWN|API服务连接失败"
        
        if not result_text:
            return "UNKNOWN|API未返回有效响应"
        
        return result_text
    except Exception as e:
        print(f"⚠️  LLM调用失败：{e}")
        return f"UNKNOWN|LLM服务异常：{str(e)}"

# ========== Agent 主入口 ==========
def work_agent():
    print("===== 智能工作场景Agent =====")
    print("Agent 会从场景库中智能匹配你的需求\n")
    print("📝 使用示例：")
    print("   1. 创建场景：\"创建看视频场景，打开Chrome和B站\"")
    print("   2. 启动场景：\"我想编程\" / \"给我工作环境\" / \"打开娱乐场景\"")
    print("   3. 查看场景：\"我的所有场景\" / \"查看已保存的场景\"")
    print("   4. 修改场景：\"修改编程，添加微信\" / \"编辑看视频，改成打开手机直播\"")
    print("   5. 删除场景：\"删除看视频\" / \"干掉编程场景\" / \"删除编程\"\n")
    print("输入「退出」结束对话\n")
    
    while True:
        user_input = input("你：").strip()
        if user_input == "退出":
            print("Agent：再见！")
            break
        
        # 让LLM理解用户指令
        llm_result = llm_understand(user_input)
        
        # 如果返回的是HTML或错误，直接显示错误信息
        if llm_result.startswith(("<!DOCTYPE", "<html", "UNKNOWN|")):
            if llm_result.startswith(("<!DOCTYPE", "<html")):
                print(f"Agent：❌ API服务异常，返回了HTML页面。请检查：")
                print(f"   1. API_KEY 是否正确")
                print(f"   2. 网络连接是否正常")
                print(f"   3. API服务是否可用\n")
                continue
            else:
                result = llm_result.replace("UNKNOWN|", "❌ ")
                print(f"Agent：{result}\n")
                continue
        
        print(f"【Agent思考】{llm_result}")
        
        # 执行对应操作（添加异常处理）
        try:
            if llm_result.startswith("CREATE|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 场景信息格式不完整，请重新表述"
                else:
                    scene_name = parts[1].strip()
                    targets_str = parts[2].strip()
                    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
                    result = save_scene(scene_name, targets)
            elif llm_result.startswith("START|"):
                parts = llm_result.split("|")
                if len(parts) < 2:
                    result = "❌ 场景名称信息不完整"
                else:
                    scene_name = parts[1].strip()
                    if not scene_name:
                        result = "❌ 场景名称不能为空"
                    else:
                        result = start_scene(scene_name)
            elif llm_result.startswith("DELETE|"):
                parts = llm_result.split("|")
                if len(parts) < 2:
                    result = "❌ 场景名称信息不完整"
                else:
                    scene_name = parts[1].strip()
                    if not scene_name:
                        result = "❌ 场景名称不能为空"
                    else:
                        result = delete_scene(scene_name)
            elif llm_result.startswith("UPDATE|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 场景信息格式不完整，请重新表述"
                else:
                    scene_name = parts[1].strip()
                    targets_str = parts[2].strip()
                    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
                    result = update_scene(scene_name, targets)
            elif llm_result == "LIST":
                scenes = load_scenes()
                if not scenes:
                    result = "📋 暂无已保存的场景！"
                else:
                    result = "📋 已保存的场景：\n"
                    for name, info in scenes.items():
                        count = len(info.get("targets", []))
                        result += f"- {name} ({count}个项)\n"
            else:
                result = llm_result.replace("UNKNOWN|", "❌ ") if "UNKNOWN" in llm_result else llm_result
        except Exception as e:
            result = f"❌ 执行指令失败：{str(e)}"
        
        print(f"Agent：{result}\n")

if __name__ == "__main__":
    work_agent()