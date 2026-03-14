import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import sys
import os

# 导入Agent模块
from agent import (
    load_scenes, save_scene, delete_scene, update_scene,
    llm_understand, start_scene, open_target
)

class AgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("智能工作场景 Agent")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")
        
        # 设置窗口图标和样式
        self.root.resizable(True, True)
        self.setup_ui()
    
    def setup_ui(self):
        """构建用户界面"""
        # ========== 顶部标题区域 ==========
        title_frame = tk.Frame(self.root, bg="#2c3e50")
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 智能工作场景启动器",
            font=("微软雅黑", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # ========== 主体区域（左右分布） ==========
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== 左侧：对话区域 ==========
        left_frame = tk.Frame(main_frame, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 对话历史标签
        dialog_label = tk.Label(
            left_frame,
            text="对话记录",
            font=("微软雅黑", 11, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        dialog_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 对话历史文本框（只读）
        self.dialog_text = scrolledtext.ScrolledText(
            left_frame,
            height=15,
            width=50,
            font=("微软雅黑", 9),
            bg="white",
            fg="#2c3e50",
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.dialog_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 配置文本标签样式
        self.dialog_text.tag_config("user", foreground="#3498db", font=("微软雅黑", 9, "bold"))
        self.dialog_text.tag_config("agent", foreground="#27ae60", font=("微软雅黑", 9))
        self.dialog_text.tag_config("error", foreground="#e74c3c", font=("微软雅黑", 9))
        self.dialog_text.tag_config("system", foreground="#95a5a6", font=("微软雅黑", 8, "italic"))
        
        # 输入框标签
        input_label = tk.Label(
            left_frame,
            text="输入你的需求",
            font=("微软雅黑", 10, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输入框
        input_frame = tk.Frame(left_frame, bg="white", relief=tk.SUNKEN, bd=1)
        input_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=("微软雅黑", 10),
            bg="white",
            fg="#2c3e50",
            relief=tk.FLAT
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 发送按钮
        send_btn = tk.Button(
            left_frame,
            text="发送 (Ctrl+Enter)",
            font=("微软雅黑", 10, "bold"),
            bg="#3498db",
            fg="white",
            height=1,
            command=self.send_message,
            relief=tk.FLAT,
            cursor="hand2"
        )
        send_btn.pack(fill=tk.X)
        
        # 绑定Ctrl+Enter快捷键
        self.input_text.bind("<Control-Return>", lambda e: self.send_message())
        
        # ========== 右侧：场景管理区域 ==========
        right_frame = tk.Frame(main_frame, bg="#f0f0f0", width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # 场景列表标签
        scene_label = tk.Label(
            right_frame,
            text="📋 已保存的场景",
            font=("微软雅黑", 11, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        scene_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 场景列表框
        scene_frame = tk.Frame(right_frame, bg="white", relief=tk.SUNKEN, bd=1)
        scene_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(scene_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.scene_listbox = tk.Listbox(
            scene_frame,
            font=("微软雅黑", 9),
            bg="white",
            fg="#2c3e50",
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.scene_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.scene_listbox.yview)
        
        # 绑定双击启动场景
        self.scene_listbox.bind("<Double-Button-1>", self.on_double_click_scene)
        
        # 快速操作按钮框
        quick_frame = tk.Frame(right_frame, bg="#f0f0f0")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 刷新按钮
        refresh_btn = tk.Button(
            quick_frame,
            text="🔄 刷新场景",
            font=("微软雅黑", 9),
            bg="#95a5a6",
            fg="white",
            height=1,
            command=self.refresh_scenes,
            relief=tk.FLAT,
            cursor="hand2"
        )
        refresh_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 创建场景按钮
        create_btn = tk.Button(
            quick_frame,
            text="➕ 新建场景",
            font=("微软雅黑", 9),
            bg="#27ae60",
            fg="white",
            height=1,
            command=self.create_scene_dialog,
            relief=tk.FLAT,
            cursor="hand2"
        )
        create_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 删除场景按钮
        delete_btn = tk.Button(
            quick_frame,
            text="🗑️ 删除选中",
            font=("微软雅黑", 9),
            bg="#e74c3c",
            fg="white",
            height=1,
            command=self.delete_selected_scene,
            relief=tk.FLAT,
            cursor="hand2"
        )
        delete_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 编辑场景按钮
        edit_btn = tk.Button(
            quick_frame,
            text="✏️ 编辑选中",
            font=("微软雅黑", 9),
            bg="#f39c12",
            fg="white",
            height=1,
            command=self.edit_selected_scene,
            relief=tk.FLAT,
            cursor="hand2"
        )
        edit_btn.pack(fill=tk.X)
        
        # 初始化场景列表
        self.refresh_scenes()
    
    def add_dialog_message(self, role, message, tag=""):
        """向对话框添加消息"""
        self.dialog_text.config(state=tk.NORMAL)
        
        if role == "user":
            self.dialog_text.insert(tk.END, f"你：{message}\n\n", "user")
        elif role == "agent":
            self.dialog_text.insert(tk.END, f"Agent：{message}\n\n", tag or "agent")
        elif role == "system":
            self.dialog_text.insert(tk.END, f"[系统] {message}\n", tag or "system")
        
        self.dialog_text.see(tk.END)
        self.dialog_text.config(state=tk.DISABLED)
    
    def send_message(self):
        """发送消息"""
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("提示", "请输入需求内容")
            return
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 显示用户消息
        self.add_dialog_message("user", user_input)
        
        # 在后台线程处理（避免界面卡死）
        threading.Thread(target=self._process_message, args=(user_input,), daemon=True).start()
    
    def _process_message(self, user_input):
        """后台处理用户消息"""
        try:
            # 让LLM理解用户指令
            llm_result = llm_understand(user_input)
            
            # 显示Agent的思考过程
            if not llm_result.startswith(("<!DOCTYPE", "<html", "UNKNOWN|")):
                self.add_dialog_message("system", f"思考结果: {llm_result}")
            
            # 执行对应操作
            if llm_result.startswith(("<!DOCTYPE", "<html")):
                result = "❌ API服务异常，请检查网络和API密钥"
                self.add_dialog_message("agent", result, "error")
            elif llm_result.startswith("UNKNOWN|"):
                result = llm_result.replace("UNKNOWN|", "❌ ")
                self.add_dialog_message("agent", result, "error")
            elif llm_result.startswith("CREATE|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 场景信息格式不完整"
                else:
                    scene_name = parts[1].strip()
                    targets_str = parts[2].strip()
                    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
                    result = save_scene(scene_name, targets)
                    self.refresh_scenes()
                self.add_dialog_message("agent", result)
            elif llm_result.startswith("START|"):
                parts = llm_result.split("|")
                if len(parts) < 2:
                    result = "❌ 场景名称信息不完整"
                else:
                    scene_name = parts[1].strip()
                    result = start_scene(scene_name)
                self.add_dialog_message("agent", result)
            elif llm_result.startswith("DELETE|"):
                parts = llm_result.split("|")
                if len(parts) < 2:
                    result = "❌ 场景名称信息不完整"
                else:
                    scene_name = parts[1].strip()
                    result = delete_scene(scene_name)
                    self.refresh_scenes()
                self.add_dialog_message("agent", result)
            elif llm_result.startswith("UPDATE|"):
                parts = llm_result.split("|")
                if len(parts) < 3:
                    result = "❌ 场景信息格式不完整"
                else:
                    scene_name = parts[1].strip()
                    targets_str = parts[2].strip()
                    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
                    result = update_scene(scene_name, targets)
                    self.refresh_scenes()
                self.add_dialog_message("agent", result)
            elif llm_result == "LIST":
                scenes = load_scenes()
                if not scenes:
                    result = "📋 暂无已保存的场景！"
                else:
                    result = "📋 已保存的场景：\n"
                    for name, info in scenes.items():
                        count = len(info.get("targets", []))
                        result += f"• {name} ({count}个项)\n"
                self.add_dialog_message("agent", result.strip())
            else:
                self.add_dialog_message("agent", "❌ 无法理解的指令", "error")
        
        except Exception as e:
            self.add_dialog_message("agent", f"❌ 处理失败: {str(e)}", "error")
    
    def refresh_scenes(self):
        """刷新场景列表"""
        self.scene_listbox.delete(0, tk.END)
        scenes = load_scenes()
        
        if not scenes:
            self.scene_listbox.insert(tk.END, "（暂无场景）")
            self.scene_listbox.itemconfig(0, fg="#95a5a6")
        else:
            for name, info in scenes.items():
                count = len(info.get("targets", []))
                self.scene_listbox.insert(tk.END, f"{name} ({count}个项)")
    
    def on_double_click_scene(self, event):
        """双击启动场景"""
        selection = self.scene_listbox.curselection()
        if selection:
            index = selection[0]
            scene_name = self.scene_listbox.get(index).split(" (")[0]
            
            # 发送启动命令
            self.add_dialog_message("user", f"打开 {scene_name}")
            threading.Thread(target=self._process_message, args=(f"启动 {scene_name}",), daemon=True).start()
    
    def create_scene_dialog(self):
        """创建场景对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新建场景")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # 场景名称
        tk.Label(dialog, text="场景名称：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        scene_name_var = tk.StringVar()
        scene_name_entry = tk.Entry(dialog, textvariable=scene_name_var, font=("微软雅黑", 10), width=30)
        scene_name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)
        scene_name_entry.focus()
        
        # 打开项
        tk.Label(dialog, text="打开项（逗号分隔）：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.NW, padx=10, pady=10)
        targets_text = tk.Text(dialog, font=("微软雅黑", 10), height=6, width=30)
        targets_text.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)
        
        # 保存按钮
        def save():
            scene_name = scene_name_var.get().strip()
            targets_str = targets_text.get("1.0", tk.END).strip()
            
            if not scene_name:
                messagebox.showwarning("提示", "场景名称不能为空")
                return
            
            if not targets_str:
                messagebox.showwarning("提示", "打开项不能为空（用逗号分隔）")
                return
            
            targets = [t.strip() for t in targets_str.split(",") if t.strip()]
            result = save_scene(scene_name, targets)
            messagebox.showinfo("结果", result)
            self.refresh_scenes()
            dialog.destroy()
        
        save_btn = tk.Button(dialog, text="保存", font=("微软雅黑", 10, "bold"), bg="#27ae60", fg="white", command=save, width=10)
        save_btn.grid(row=2, column=1, sticky=tk.E, padx=10, pady=10)
        
        dialog.columnconfigure(1, weight=1)
    
    def delete_selected_scene(self):
        """删除选中的场景"""
        selection = self.scene_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个场景")
            return
        
        scene_name = self.scene_listbox.get(selection[0]).split(" (")[0]
        
        if messagebox.askyesno("确认", f"确定要删除场景「{scene_name}」吗？"):
            result = delete_scene(scene_name)
            messagebox.showinfo("结果", result)
            self.refresh_scenes()
    
    def edit_selected_scene(self):
        """编辑选中的场景"""
        selection = self.scene_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个场景")
            return
        
        scene_name = self.scene_listbox.get(selection[0]).split(" (")[0]
        scenes = load_scenes()
        
        if scene_name not in scenes:
            messagebox.showerror("错误", "场景不存在")
            return
        
        old_targets = scenes[scene_name].get("targets", [])
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑场景：{scene_name}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # 打开项
        tk.Label(dialog, text="打开项（逗号分隔）：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.NW, padx=10, pady=10)
        targets_text = tk.Text(dialog, font=("微软雅黑", 10), height=8, width=30)
        targets_text.insert("1.0", ",".join(old_targets))
        targets_text.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)
        
        # 保存按钮
        def save():
            targets_str = targets_text.get("1.0", tk.END).strip()
            
            if not targets_str:
                messagebox.showwarning("提示", "打开项不能为空")
                return
            
            targets = [t.strip() for t in targets_str.split(",") if t.strip()]
            result = update_scene(scene_name, targets)
            messagebox.showinfo("结果", result)
            self.refresh_scenes()
            dialog.destroy()
        
        save_btn = tk.Button(dialog, text="保存", font=("微软雅黑", 10, "bold"), bg="#27ae60", fg="white", command=save, width=10)
        save_btn.grid(row=1, column=1, sticky=tk.E, padx=10, pady=10)
        
        dialog.columnconfigure(1, weight=1)

if __name__ == "__main__":
    root = tk.Tk()
    gui = AgentGUI(root)
    root.mainloop()
