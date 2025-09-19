# 文件路径: src/tabs/admin_tab.py
# 版本：已更新为使用状态栏消息

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import datetime
from ..utils import hash_password

class AdminTab(ttk.Frame):
    def __init__(self, parent, context):
        super().__init__(parent, padding=10)
        self.context = context
        self.app = context["app"] # 获取主应用的实例
        self.db_manager = context["db_manager"]
        self.config_manager = context["config_manager"]
        self.current_user_info = context["current_user_info"]
        
        self._create_widgets()

    # _create_widgets, _load_config_to_form 等界面函数与上一版本完全相同
    # ... (省略未修改的代码)
    def _create_widgets(self):
        config_form_frame = ttk.LabelFrame(self, text=" 系统配置 ", padding=15)
        config_form_frame.pack(side="top", fill="x", pady=(0, 10), anchor='n')
        config_form_frame.columnconfigure(1, weight=1)
        labels = ["公司名称:", "联系电话:", "结算单页脚文本:", "Excel导出文件夹:"]
        self.config_entries = {}
        for i, text in enumerate(labels):
            ttk.Label(config_form_frame, text=text).grid(row=i, column=0, padx=5, pady=8, sticky="w")
        self.config_entries['company_name'] = ttk.Entry(config_form_frame)
        self.config_entries['company_name'].grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.config_entries['phone_number'] = ttk.Entry(config_form_frame)
        self.config_entries['phone_number'].grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        self.config_entries['footer_text'] = ttk.Entry(config_form_frame)
        self.config_entries['footer_text'].grid(row=2, column=1, padx=5, pady=8, sticky="ew")
        dir_frame = ttk.Frame(config_form_frame)
        dir_frame.grid(row=3, column=1, columnspan=2, sticky='ew', padx=5, pady=8)
        dir_frame.columnconfigure(0, weight=1)
        self.config_entries['excel_output_dir'] = ttk.Entry(dir_frame, state='readonly')
        self.config_entries['excel_output_dir'].grid(row=0, column=0, sticky="ew")
        ttk.Button(dir_frame, text="选择文件夹", command=self._browse_output_dir, width=12).grid(row=0, column=1, padx=(10, 0))
        self._load_config_to_form()
        config_button_frame = ttk.Frame(config_form_frame)
        config_button_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
        ttk.Button(config_button_frame, text="保存配置", command=self._save_config_from_form).pack(side="left", padx=5)
        ttk.Button(config_button_frame, text="立即备份数据库", command=self._backup_database).pack(side="left", padx=5)
        ttk.Button(config_button_frame, text="从备份恢复", command=self._restore_database).pack(side="left", padx=5)
        user_frame = ttk.LabelFrame(self, text=" 用户管理 ", padding=15)
        user_frame.pack(side="top", fill="both", expand=True, pady=(10, 0))
        user_list_frame = ttk.Frame(user_frame)
        user_list_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))
        self.user_tree = ttk.Treeview(user_list_frame, columns=("ID", "用户名", "角色"), show="headings")
        self.user_tree.pack(expand=True, fill="both")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("用户名", text="用户名")
        self.user_tree.heading("角色", text="角色")
        self.user_tree.column("ID", width=50, stretch=False)
        self._load_users_to_tree()
        user_action_frame = ttk.Frame(user_frame)
        user_action_frame.pack(side="left", fill="y", padx=(15, 0), anchor='n')
        ttk.Label(user_action_frame, text="新用户名:").pack(anchor="w", pady=(0, 5))
        self.new_username_entry = ttk.Entry(user_action_frame)
        self.new_username_entry.pack(fill="x", pady=(0, 10))
        ttk.Label(user_action_frame, text="新密码:").pack(anchor="w", pady=(0, 5))
        self.new_password_entry = ttk.Entry(user_action_frame, show="*")
        self.new_password_entry.pack(fill="x", pady=(0, 10))
        ttk.Label(user_action_frame, text="角色:").pack(anchor="w", pady=(0, 5))
        self.new_user_role_var = tk.StringVar(value='user')
        self.new_user_role_combo = ttk.Combobox(user_action_frame, textvariable=self.new_user_role_var, values=['user', 'admin'], state='readonly')
        self.new_user_role_combo.pack(fill="x", pady=(0, 10))
        ttk.Button(user_action_frame, text="添加用户", command=self._add_user).pack(fill="x", pady=5)
        ttk.Button(user_action_frame, text="删除选中用户", command=self._delete_user).pack(fill="x", pady=5)
    def _load_config_to_form(self):
        for key, entry in self.config_entries.items():
            is_readonly = entry.cget('state') == 'readonly'
            if is_readonly: entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, self.config_manager.get(key, ''))
            if is_readonly: entry.config(state='readonly')
    def _browse_output_dir(self):
        new_dir = filedialog.askdirectory(title="选择Excel导出文件夹", parent=self)
        if new_dir:
            self.config_manager.set('excel_output_dir', new_dir)
            self._load_config_to_form()
    def _restore_database(self):
        pass
    def _load_users_to_tree(self):
        self.user_tree.delete(*self.user_tree.get_children())
        users = self.db_manager.get_all_users()
        for i, user in enumerate(users):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.user_tree.insert("", "end", values=user, tags=(tag,))

    # --- 以下是修改过的函数 ---

    def _save_config_from_form(self):
        for key, entry in self.config_entries.items():
            self.config_manager.set(key, entry.get())
        self.app.show_status_message("系统配置已保存！") # <--- 修改点

    def _backup_database(self):
        backup_dir = "db_backups"
        if not os.path.exists(backup_dir): os.makedirs(backup_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{os.path.splitext(self.db_manager.db_name)[0]}_backup_{timestamp}.db")
        try:
            shutil.copyfile(self.db_manager.db_name, backup_path)
            self.app.show_status_message(f"数据库已成功备份到 {backup_dir}") # <--- 修改点
        except Exception as e:
            messagebox.showerror("备份失败", f"备份数据库时发生错误: {e}", parent=self)

    def _add_user(self):
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get()
        role = self.new_user_role_var.get()
        if not username or not password:
            messagebox.showwarning("输入错误", "用户名和密码不能为空！", parent=self)
            return
        password_hash = hash_password(password)
        if self.db_manager.add_user(username, password_hash, role):
            self.app.show_status_message(f"用户 '{username}' 添加成功！") # <--- 修改点
            self._load_users_to_tree()
            self.new_username_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("失败", f"用户名 '{username}' 已存在！", parent=self)
            
    def _delete_user(self):
        selected_item = self.user_tree.selection()
        if not selected_item:
            messagebox.showwarning("提示", "请选择要删除的用户！", parent=self)
            return
        
        user_id, username, role = self.user_tree.item(selected_item[0], "values")

        if username == self.current_user_info['username']:
            messagebox.showerror("错误", "不能删除当前登录的用户！", parent=self)
            return
        
        if messagebox.askyesno("确认", f"确定要删除用户 '{username}' 吗?", parent=self):
            self.db_manager.delete_user(user_id)
            self._load_users_to_tree()
            self.app.show_status_message(f"用户 '{username}' 已被删除。") # <--- 修改点