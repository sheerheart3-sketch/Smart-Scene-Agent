"""
智能Agent记忆管理模块
功能：
1. 记忆范围控制：只记录核心信息（场景名、操作类型）
2. 记忆过期机制：7天未使用的记忆自动清理
3. 兼容无记忆场景：失败时自动降级
4. 手动清空记忆：允许用户重置上下文
"""

import os
import json
import datetime
from pathlib import Path

MEMORY_FILE = "memory_history.json"
MEMORY_CONFIG = {
    "enabled": True,
    "expiry_days": 7,  # 过期天数
    "max_items": 100  # 最多保存的记忆条目数
}


def _ensure_memory_file():
    """确保记忆文件存在，如果不存在则创建"""
    if not os.path.exists(MEMORY_FILE):
        try:
            initial_data = {
                "memory_items": [],
                "config": MEMORY_CONFIG,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️  创建记忆文件失败：{e}")
            return False
    return True


def load_memory():
    """
    加载记忆文件（带故障降级）
    返回：(memory_items, success_flag)
    """
    try:
        # 确保文件存在
        if not _ensure_memory_file():
            return [], False
        
        # 加载文件
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            memory_items = data.get("memory_items", [])
            
            # 清理过期的记忆项
            memory_items = _clean_expired_memories(memory_items)
            
            return memory_items, True
    except Exception as e:
        print(f"⚠️  加载记忆失败，降级为原有指令模式：{e}")
        return [], False


def save_memory(memory_items):
    """
    保存记忆到文件（带故障降级）
    返回：操作是否成功
    """
    try:
        # 限制记忆条目数量（防止文件过大）
        if len(memory_items) > MEMORY_CONFIG["max_items"]:
            memory_items = memory_items[-MEMORY_CONFIG["max_items"]:]
        
        data = {
            "memory_items": memory_items,
            "config": MEMORY_CONFIG,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️  保存记忆失败：{e}")
        return False


def _clean_expired_memories(memory_items):
    """
    清理过期的记忆项（7天未使用自动删除）
    """
    try:
        expiry_days = MEMORY_CONFIG.get("expiry_days", 7)
        current_time = datetime.datetime.now()
        cleaned_items = []
        
        for item in memory_items:
            try:
                timestamp_str = item.get("timestamp", "")
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # 计算时间差
                time_diff = (current_time - timestamp).days
                
                # 如果未超过过期天数，保留该记忆
                if time_diff <= expiry_days:
                    cleaned_items.append(item)
                else:
                    print(f"🗑️  清理过期记忆：{item.get('scene_name')} ({time_diff}天未使用)")
            except:
                # 如果时间格式异常，保留该项
                cleaned_items.append(item)
        
        return cleaned_items
    except Exception as e:
        print(f"⚠️  清理过期记忆失败：{e}")
        return memory_items


def add_memory(scene_name, operation_type):
    """
    添加新的记忆项（完整记录模式：每次都创建新记录）
    参数：
    - scene_name: 场景名称（str）
    - operation_type: 操作类型（CREATE/START/DELETE/UPDATE）
    返回：是否成功
    """
    try:
        # 验证输入
        if not scene_name or not operation_type:
            return False
        
        # 加载现有记忆
        memory_items, _ = load_memory()
        
        # 创建新的记忆项（完整记录每一次操作）
        new_memory = {
            "scene_name": scene_name.strip(),
            "operation": operation_type.upper(),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 总是添加新记录（不再检查是否存在）
        memory_items.append(new_memory)
        
        # 保存记忆
        return save_memory(memory_items)
    except Exception as e:
        print(f"⚠️  添加记忆失败：{e}")
        return False


def get_memory_summary(scene_name=None):
    """
    获取记忆摘要
    参数：
    - scene_name: 指定场景名（可选），如果为None则返回全部记忆摘要
    返回：记忆摘要字符串
    """
    try:
        memory_items, success = load_memory()
        
        if not success or not memory_items:
            return "📚 暂无记忆数据"
        
        if scene_name:
            # 获取特定场景的记忆
            scene_memories = [m for m in memory_items if m["scene_name"] == scene_name]
            if not scene_memories:
                return f"📚 场景「{scene_name}」暂无记忆"
            
            summary = f"📚 场景「{scene_name}」的记忆：\n"
            for m in scene_memories:
                summary += f"  - {m['operation']} ({m['timestamp']})\n"
        else:
            # 获取全部记忆摘要
            unique_scenes = {}
            for m in memory_items:
                scene = m["scene_name"]
                if scene not in unique_scenes:
                    unique_scenes[scene] = []
                unique_scenes[scene].append(m["operation"])
            
            summary = f"📚 记忆摘要 (共{len(memory_items)}条)：\n"
            for scene, ops in unique_scenes.items():
                ops_str = ", ".join(set(ops))  # 去重
                summary += f"  - 【{scene}】{ops_str}\n"
        
        return summary
    except Exception as e:
        print(f"⚠️  获取记忆摘要失败：{e}")
        return "📚 记忆数据异常"


def clear_memory():
    """
    清空所有记忆（用户手动指令）
    返回：是否成功
    """
    try:
        data = {
            "memory_items": [],
            "config": MEMORY_CONFIG,
            "cleared_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("🧠 记忆已清空")
        return True
    except Exception as e:
        print(f"⚠️  清空记忆失败：{e}")
        return False


def get_scene_frequency(limit=5):
    """
    获取最常用的场景（按访问频率排序）
    参数：
    - limit: 返回前N个最常用的场景
    返回：场景频率列表
    """
    try:
        memory_items, success = load_memory()
        
        if not success or not memory_items:
            return []
        
        # 统计场景访问频率
        scene_freq = {}
        for item in memory_items:
            scene = item["scene_name"]
            scene_freq[scene] = scene_freq.get(scene, 0) + 1
        
        # 按频率排序
        sorted_scenes = sorted(scene_freq.items(), key=lambda x: x[1], reverse=True)
        return sorted_scenes[:limit]
    except Exception as e:
        print(f"⚠️  获取场景频率失败：{e}")
        return []


def export_memory(export_file="memory_export.json"):
    """
    导出记忆到文件（用于备份或分析）
    параметр：
    - export_file: 导出文件名
    返回：是否成功
    """
    try:
        memory_items, success = load_memory()
        
        if not success:
            return False
        
        export_data = {
            "export_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_items": len(memory_items),
            "memory_items": memory_items
        }
        
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 记忆已导出到：{export_file}")
        return True
    except Exception as e:
        print(f"⚠️  导出记忆失败：{e}")
        return False


def get_memory_stats():
    """
    获取记忆统计信息
    返回：统计信息字典
    """
    try:
        memory_items, success = load_memory()
        
        if not success or not memory_items:
            return {
                "total_items": 0,
                "unique_scenes": 0,
                "operations": {}
            }
        
        # 统计操作类型
        op_count = {}
        scenes = set()
        
        for item in memory_items:
            op = item.get("operation", "UNKNOWN")
            op_count[op] = op_count.get(op, 0) + 1
            scenes.add(item.get("scene_name"))
        
        return {
            "total_items": len(memory_items),
            "unique_scenes": len(scenes),
            "operations": op_count
        }
    except Exception as e:
        print(f"⚠️  获取记忆统计失败：{e}")
        return {}


# ========== 智能推荐系统 ==========

def get_7day_raw_memory():
    """
    获取过去7天的原始记忆数据（包含完整时间戳）
    用于LLM进行智能分析
    返回：原始记忆列表
    """
    try:
        memory_items, success = load_memory()
        
        if not success or not memory_items:
            return []
        
        # 获取过去7天的记忆
        current_time = datetime.datetime.now()
        seven_days_ago = current_time - datetime.timedelta(days=7)
        
        seven_day_memories = []
        for item in memory_items:
            try:
                timestamp_str = item.get("timestamp", "")
                if not timestamp_str:
                    continue
                
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # 只分析过去7天的记忆
                if timestamp < seven_days_ago:
                    continue
                
                seven_day_memories.append({
                    "scene_name": item.get("scene_name", "未知"),
                    "operation": item.get("operation", ""),
                    "timestamp": timestamp_str
                })
            except:
                continue
        
        return seven_day_memories
    except Exception as e:
        print(f"⚠️  获取7天记忆失败：{e}")
        return []


def get_recently_opened(hours=1):
    """
    获取最近N小时内打开过的场景（仅限START操作）
    用于避免重复建议
    参数：
    - hours: 时间范围（小时）
    返回：最近打开的场景名称列表
    """
    try:
        memory_items, success = load_memory()
        
        if not success or not memory_items:
            return []
        
        current_time = datetime.datetime.now()
        time_threshold = current_time - datetime.timedelta(hours=hours)
        
        recently_opened = []
        for item in memory_items:
            try:
                # 只看START操作的场景
                if item.get("operation") != "START":
                    continue
                
                timestamp_str = item.get("timestamp", "")
                if not timestamp_str:
                    continue
                
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # 检查是否在时间范围内
                if timestamp >= time_threshold:
                    recently_opened.append(item.get("scene_name", ""))
            except:
                continue
        
        # 去重并返回
        return list(set(recently_opened))
    except Exception as e:
        print(f"⚠️  获取最近打开的场景失败：{e}")
        return []


def get_scene_recommendation():
    """
    根据过去7天的记忆，生成LLM分析所需的提示词
    包含最近1小时内已打开的场景列表
    返回：(提示词, 原始记忆数据, 最近打开列表)元组
    """
    try:
        # 获取原始7天记忆
        memories = get_7day_raw_memory()
        recently_opened = get_recently_opened(hours=1)
        
        if not memories:
            return ("暂无过去7天的记忆数据用于分析", [], [])
        
        # 构建提示词
        prompt = f"""基于用户过去7天的工作历史记录，推荐用户现在最应该打开的工作场景。

【用户的过去7天工作记录】
"""
        
        for mem in memories:
            scene = mem.get("scene_name", "")
            op = mem.get("operation", "")
            timestamp = mem.get("timestamp", "")
            prompt += f"- {timestamp}: {scene} ({op})\n"
        
        prompt += f"""
【最近1小时内已打开的场景】{", ".join(recently_opened) if recently_opened else "无"}

请只推荐用户现在应该打开的一个场景（TOP 1）。
- 不要推荐最近1小时内已打开过的场景
- 简洁回答，不需要详细理由，格式：【推荐】场景名 理由
"""
        
        return (prompt, memories, recently_opened)
    except Exception as e:
        print(f"⚠️  生成推荐提示词失败：{e}")
        return (f"生成推荐失败：{e}", [], [])


def get_detailed_recommendation():
    """
    获取详细的推荐分析（用于向用户展示原始记忆）
    返回：(提示词, 原始记忆数据, 最近打开列表)元组
    """
    try:
        # 获取原始7天记忆
        memories = get_7day_raw_memory()
        recently_opened = get_recently_opened(hours=1)
        
        if not memories:
            return ("暂无过去7天的记忆数据用于分析", [], [])
        
        # 构建详细分析提示词
        prompt = f"""基于用户过去7天的工作历史数据，分析工作模式并给出最佳建议。

【用户的过去7天完整工作记录】
"""
        
        for mem in memories:
            scene = mem.get("scene_name", "")
            op = mem.get("operation", "")
            timestamp = mem.get("timestamp", "")
            prompt += f"- {timestamp}: {scene} ({op})\n"
        
        prompt += f"""
【最近1小时内已打开的场景】{", ".join(recently_opened) if recently_opened else "无"}

请分析用户的工作模式和时间分布规律，然后只推荐最应该打开的一个场景。
分析格式：
【工作模式】简要说明主要工作类型和频率
【当前推荐】只推荐TOP 1，格式：场景名 - 理由
【注意】不要推荐最近1小时内已打开的场景
"""
        
        return (prompt, memories, recently_opened)
    except Exception as e:
        print(f"⚠️  生成详细分析提示词失败：{e}")
        return (f"生成详细分析失败：{e}", [], [])


# 初始化记忆系统
_ensure_memory_file()
