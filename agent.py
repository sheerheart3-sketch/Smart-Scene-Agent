import os
import json
import webbrowser
import datetime
import subprocess
import requests
from dotenv import load_dotenv

# 导入记忆管理模块
from memory_manager import (
    add_memory, get_memory_summary, clear_memory, 
    get_memory_stats, load_memory, get_scene_recommendation, 
    get_detailed_recommendation, get_7day_raw_memory, get_recently_opened
)

# ========== 基础配置 ==========
load_dotenv()  # 加载.env文件中的API密钥
SCENE_FILE = "work_scenes.json"
DMXAPI_KEY = os.getenv('API_KEY')  # API密钥
DMXAPI_URL = os.getenv('URL')  # API端点
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
        
        # 【新增】记录到记忆系统
        add_memory(scene_name, "CREATE")
        
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
        
        # 【新增】记录到记忆系统
        add_memory(scene_name, "DELETE")
        
        return f"✅ 场景「{scene_name}」已删除"
    except IOError as e:
        return f"❌ 删除场景失败：{e}"

def update_scene(scene_name, targets):
    """修改已保存的工作场景 - 完全替换所有打开项"""
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
        
        # 【新增】记录到记忆系统
        add_memory(scene_name, "UPDATE")
        
        return f"✅ 场景「{scene_name}」已更新，包含{len(targets)}个打开项"
    except IOError as e:
        return f"❌ 更新场景失败：{e}"

def add_item_to_scene(scene_name, item):
    """为场景添加单个打开项（不删除原有）"""
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    if not item or not item.strip():
        return "❌ 打开项不能为空！"
    
    try:
        scenes = load_scenes()
        if scene_name not in scenes:
            return f"❌ 场景「{scene_name}」不存在！"
        
        current_targets = scenes[scene_name].get("targets", [])
        item = item.strip()
        
        # 检查是否已存在
        if item in current_targets:
            return f"⚠️  项目「{item}」已在场景中，未添加"
        
        # 添加新项目
        current_targets.append(item)
        scenes[scene_name]["targets"] = current_targets
        scenes[scene_name]["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        
        add_memory(scene_name, "ADD")
        return f"✅ 已向「{scene_name}」添加「{item}」，现共{len(current_targets)}个项"
    except IOError as e:
        return f"❌ 添加项目失败：{e}"

def remove_item_from_scene(scene_name, item):
    """从场景中移除单个打开项（保留其他）"""
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    if not item or not item.strip():
        return "❌ 打开项不能为空！"
    
    try:
        scenes = load_scenes()
        if scene_name not in scenes:
            return f"❌ 场景「{scene_name}」不存在！"
        
        current_targets = scenes[scene_name].get("targets", [])
        item = item.strip()
        
        # 检查是否存在
        if item not in current_targets:
            return f"❌ 项目「{item}」不在场景中，无法删除"
        
        # 如果只剩一个项目，不允许删除
        if len(current_targets) <= 1:
            return f"⚠️  场景至少要保留1个打开项，无法删除最后一项"
        
        # 删除项目
        current_targets.remove(item)
        scenes[scene_name]["targets"] = current_targets
        scenes[scene_name]["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        
        add_memory(scene_name, "REMOVE")
        return f"✅ 已从「{scene_name}」移除「{item}」，现共{len(current_targets)}个项"
    except IOError as e:
        return f"❌ 移除项目失败：{e}"

def replace_item_in_scene(scene_name, old_item, new_item):
    """将场景中的一个项目替换成另一个"""
    if not scene_name or not scene_name.strip():
        return "❌ 场景名称不能为空！"
    if not old_item or not old_item.strip():
        return "❌ 原项目不能为空！"
    if not new_item or not new_item.strip():
        return "❌ 新项目不能为空！"
    
    old_item = old_item.strip()
    new_item = new_item.strip()
    
    if old_item == new_item:
        return f"⚠️  新项目和原项目相同，无需替换"
    
    try:
        scenes = load_scenes()
        if scene_name not in scenes:
            return f"❌ 场景「{scene_name}」不存在！"
        
        current_targets = scenes[scene_name].get("targets", [])
        
        # 检查原项目是否存在
        if old_item not in current_targets:
            return f"❌ 项目「{old_item}」不在场景中，无法替换"
        
        # 检查新项目是否已存在
        if new_item in current_targets:
            return f"⚠️  项目「{new_item}」已在场景中，无法添加"
        
        # 替换项目
        index = current_targets.index(old_item)
        current_targets[index] = new_item
        scenes[scene_name]["targets"] = current_targets
        scenes[scene_name]["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        with open(SCENE_FILE, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        
        add_memory(scene_name, "REPLACE")
        return f"✅ 已将「{scene_name}」中的「{old_item}」替换成「{new_item}」"
    except IOError as e:
        return f"❌ 替换项目失败：{e}"

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


def _start_scene_recursive(scene_name, visited_scenes=None):
    """
    递归启动工作场景（支持复合场景）
    参数：
    - scene_name: 场景名称
    - visited_scenes: 已访问场景列表（用于循环引用检测）
    返回：(结果列表, 是否成功)
    """
    if visited_scenes is None:
        visited_scenes = set()
    
    # 检测循环引用
    if scene_name in visited_scenes:
        return [f"⚠️  检测到循环引用：场景「{scene_name}」"], False
    
    visited_scenes.add(scene_name)
    
    scenes = load_scenes()
    if scene_name not in scenes:
        return [f"❌ 场景「{scene_name}」不存在"], False
    
    results = []
    targets = scenes[scene_name].get("targets", [])
    
    for target in targets:
        # 检查是否是复合场景引用（@开头）
        if target.startswith("@"):
            # 递归调用其他场景
            referenced_scene = target[1:].strip()  # 去掉@符号
            sub_results, _ = _start_scene_recursive(referenced_scene, visited_scenes.copy())
            results.extend(sub_results)
        else:
            # 正常打开目标
            results.append(open_target(target))
            import time
            time.sleep(0.5)
    
    return results, True


def start_scene(scene_name):
    """启动工作场景（支持复合场景）"""
    scenes = load_scenes()
    if scene_name not in scenes:
        return f"未找到场景「{scene_name}」！已保存场景：{list(scenes.keys())}"
    
    # 【新增】记录到记忆系统
    add_memory(scene_name, "START")
    
    # 递归启动场景
    results, success = _start_scene_recursive(scene_name)
    
    if success:
        return f"场景「{scene_name}」启动完成！\n" + "\n".join(results)
    else:
        return f"场景「{scene_name}」启动失败！\n" + "\n".join(results)

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
    model=os.getenv('MODELNAME')
    scenes = load_scenes()
    scene_list = list(scenes.keys())
    
    # 【新增】加载记忆信息
    memory_items, memory_available = load_memory()
    memory_context = ""
    if memory_available and memory_items:
        # 记忆摘要（用于LLM参考）
        memory_summary = get_memory_summary()
        memory_context = f"\n【用户操作记忆】\n{memory_summary}"
    else:
        memory_context = "\n【用户操作记忆】暂无记忆数据（记忆功能可能未启用）"
    
    # 系统提示：定义Agent的核心能力
    system_prompt = f"""
    你是一个智能工作场景启动Agent。你的核心职责是理解用户需求，并从已有的场景库中匹配最合适的场景。

    【当前场景库】
    {', '.join(scene_list) if scene_list else '（暂无已保存的场景）'}
    
    {memory_context}

    【你能做的事】
    1. 创建新场景：用户想要保存一个新的工作流程 - 格式：CREATE|场景名|项目,项目
       例："创建看视频场景，打开Chrome咋B站"
       返回："CREATE|看视频|Chrome,B站"
    
    2. 启动场景：用户想要启动一个存存的场景
       用户说："我想编程"/"窗口 ┌ LIST ┌ 挛司"
       你的任务：从每个场景库中找出最相关的场景，返回 START|场景名
       示例：如果场景库有"编程"场景，返回 "START|编程"
    
    3. 查看场景：用户要看所有已保存的场景
       返回：LIST
    
    4. 删除场景：用户想要删除一个已保存的场景
       用户说："删除看视频"/"K掉编程场景"
       返回：DELETE|场景名
       例："DELETE|看视频"
    
    5. 修改场景（四种方式）：
       方式A - 单项替换：用户说"把 A 改成 B"（指定了具体项目替换）
          用户说："编程的VSCode改成Cursor" / "把编程中的Chrome换成Firefox"
          场景原有：VSCode,Navicat
          返回：REPLACE|编程|VSCode,Cursor
          → 结果：Cursor,Navicat（VSCode被替换成Cursor）
       
       方式B - 只添加：用户说"添加..."、"加上..."（只新増，不删o名）
          用户说："编程场景添加微信" / "给编程加微信"
          场景原有：VSCode,Navicat
          返回：ADD|编程|微信
          → 结果：VSCode,Navicat,微信
       
       方式C - 只删除：用户说"删除..."、"移除..."（只移除一个，保毆余的）
          用户说："编程场景删除Navicat" / "从编程移除Chrome"
          场景原有：VSCode,Navicat,Chrome
          返回：REMOVE|编程|Navicat
          → 结果：VSCode,Chrome
       
       方式D - 完全替换：用户未明确表示如何修改或表示全部替换时
          用户说："修改编程场景，改成打开VSCode和Chrome"
          返回：UPDATE|编程|VSCode,Chrome
    
    【重要规则】
    - 场景名必须准确匹配】当前场景库】中的场景
    - 用户可能識蝱（"编程场景"候库中命前是"编程"） → 你必须返回编库中的准确名字"编程"
    - 如果场景库为NULL且用户有需求，帮婊用户创建新场景
    - 如果场景库中找不到匹配的场景，也建议创建新场景
    - 只返回命令，不返回其他内容
    """
    # 调用LLM进行智能匹配
    try:
        result_text = reason(model, [
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
    print("   2. 复合场景：\"创建完整工作，包含编程和工作和Chrome\"")
    print("      （自动识别编程/工作是已有场景，无需手动加@）")
    print("   3. 启动场景：\"我想编程\" / \"给我工作环境\" / \"打开娱乐场景\"")
    print("   4. 查看场景：\"我的所有场景\" / \"查看已保存的场景\"")
    print("   5. 修改场景：\"修改编程，添加微信\" / \"编辑看视频，改成打开手机直播\"")
    print("   6. 删除场景：\"删除看视频\" / \"干掉编程场景\" / \"删除编程\"")
    print("   【新增】7. 查看记忆：\"查看记忆\" / \"展示我的操作记录\"")
    print("   【新增】8. 清空记忆：\"清空记忆\" / \"重置记忆\"")
    print("   【新增】9. 记忆统计：\"记忆统计\" / \"显示记忆数据\"")
    print("   【新增】10. 场景推荐：\"建议我做什么\" / \"有什么建议\" / \"推荐场景\"\n")
    print("输入「退出」结束对话\n")
    
    while True:
        user_input = input("你：").strip()
        if user_input == "退出":
            print("Agent：再见！")
            break
        
        # 【新增】处理特殊指令：清空记忆
        if "清空记忆" in user_input or "重置记忆" in user_input:
            confirm = input("确定要清空所有记忆吗？(y/n)：").strip().lower()
            if confirm == 'y':
                if clear_memory():
                    print("Agent：✅ 所有记忆已清空，Agent开始新的学习过程\n")
                else:
                    print("Agent：❌ 清空记忆失败\n")
            else:
                print("Agent：取消了清空操作\n")
            continue
        
        # 【新增】处理特殊指令：查看记忆
        if "查看记忆" in user_input or "显示记忆" in user_input or "我的操作记录" in user_input:
            memory_summary = get_memory_summary()
            print(f"Agent：{memory_summary}\n")
            continue
        
        # 【新增】处理特殊指令：记忆统计
        if "记忆统计" in user_input or "显示记忆数据" in user_input or "统计数据" in user_input:
            stats = get_memory_stats()
            if stats.get('total_items', 0) == 0:
                print("Agent：📊 暂无记忆数据\n")
            else:
                stats_text = f"📊 记忆统计：\n"
                stats_text += f"  - 总记忆条数：{stats['total_items']}\n"
                stats_text += f"  - 涉及场景数：{stats['unique_scenes']}\n"
                stats_text += f"  - 操作类型分布："
                ops = stats.get('operations', {})
                for op, count in ops.items():
                    stats_text += f" {op}({count})"
                stats_text += "\n"
                print(f"Agent：{stats_text}\n")
            continue
        
        # 【新增】处理特殊指令：场景推荐
        if "建议我做什么" in user_input or "有什么建议" in user_input or "推荐" in user_input or "建议我" in user_input:
            # 检查是否要详细建议
            if "详细" in user_input or "全部" in user_input or "所有" in user_input:
                prompt, memories, recently_opened = get_detailed_recommendation()
            else:
                prompt, memories, recently_opened = get_scene_recommendation()
            
            # 如果没有数据，直接返回提示
            if not memories:
                print(f"Agent：{prompt}\n")
                continue
            
            # 使用LLM进行智能分析
            model = os.getenv('MODELNAME')
            try:
                recommendation = reason(model, [
                    {"role": "system", "content": "你是一个高效的工作建议助手。根据用户的工作记录，简洁地给出最优的一个场景建议，不要冗长。"},
                    {"role": "user", "content": prompt}
                ]).strip()
                
                if recommendation:
                    print(f"Agent：{recommendation}\n")
                else:
                    print(f"Agent：{prompt}\n")
            except Exception as e:
                print(f"Agent：⚠️  生成建议失败：{e}\n")
            continue
        
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
            elif llm_result.startswith("ADD|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 添加项信息不完整"
                else:
                    scene_name = parts[1].strip()
                    item_str = parts[2].strip()
                    result = add_item_to_scene(scene_name, item_str)
            elif llm_result.startswith("REMOVE|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 删除项信息不完整"
                else:
                    scene_name = parts[1].strip()
                    item_str = parts[2].strip()
                    result = remove_item_from_scene(scene_name, item_str)
            elif llm_result.startswith("REPLACE|"):
                parts = llm_result.split("|")
                if len(parts) < 4:
                    result = "❌ 替换项信息不完整"
                else:
                    scene_name = parts[1].strip()
                    old_item = parts[2].strip()
                    new_item = parts[3].strip()
                    result = replace_item_in_scene(scene_name, old_item, new_item)
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