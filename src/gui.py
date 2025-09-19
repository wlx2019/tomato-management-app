# 文件路径: src/gui.py
# 版本：已添加异步任务处理逻辑和错误样式

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import time
import threading
import queue

from ttkthemes import ThemedTk 

from .database import DatabaseManager
from .config import ConfigManager
from .excel_exporter import ExcelExporter
from .utils import hash_password, verify_password, resource_path

from .tabs.dashboard_tab import DashboardTab
from .tabs.grower_tab import GrowerTab
from .tabs.client_tab import ClientTab
from .tabs.admin_tab import AdminTab


class LoginWindow(ThemedTk):
    def __init__(self, db_manager):
        super().__init__()
        try:
            icon_path = resource_path('tomato.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"为登录窗口加载ICO图标失败: {e}")

        self.db_manager = db_manager
        self.login_info = None
        self.title("系统登录")
        self.geometry("320x180")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('.', font=('微软雅黑', 10), background='#F0F2F5')
        self.style.configure('TButton', font=('微软雅黑', 10, 'bold'), padding=5)
        self.configure(background='#F0F2F5')

        self.center_window()

        ttk.Label(self, text="用户名:").pack(pady=(10, 2))
        self.username_entry = ttk.Entry(self, font=('微软雅黑', 10))
        self.username_entry.pack(fill="x", padx=30)
        self.username_entry.focus_set()

        ttk.Label(self, text="密码:").pack(pady=(10, 2))
        self.password_entry = ttk.Entry(self, show="*", font=('微软雅黑', 10))
        self.password_entry.pack(fill="x", padx=30)
        self.password_entry.bind("<Return>", self.attempt_login)
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        ttk.Button(self, text="登录", command=self.attempt_login).pack(pady=15)

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def attempt_login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_data = self.db_manager.get_user(username)
        if user_data:
            stored_hash = user_data[2]
            user_role = user_data[3]
            if verify_password(password, stored_hash):
                self.login_info = {'username': username, 'role': user_role}
                self.destroy()
            else:
                messagebox.showerror("登录失败", "密码错误！", parent=self)
        else:
            messagebox.showerror("登录失败", "用户不存在！", parent=self)


def handle_initial_user_setup(db_manager):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("首次运行设置", "未检测到任何用户，请创建第一个管理员账户。", parent=root)
    while True:
        username = simpledialog.askstring("创建管理员", "请输入管理员用户名:", parent=root)
        if not username:
            root.destroy()
            return False
        password = simpledialog.askstring("创建管理员", "请输入密码:", show='*', parent=root)
        if not password:
            root.destroy()
            return False
        password_hash = hash_password(password)
        if db_manager.add_user(username, password_hash, role='admin'):
            messagebox.showinfo("成功", f"管理员 '{username}' 创建成功！请使用新账户登录。", parent=root)
            root.destroy()
            return True
        else:
            messagebox.showerror("错误", "创建失败，请重试。", parent=root)
    root.destroy()
    return False


class TomatoManagementApp(ThemedTk):
    def __init__(self, current_user_info):
        super().__init__()
        
        self.current_user_info = current_user_info
        self.status_message_job_id = None

        try:
            icon_path = resource_path('tomato.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"为主程序加载ICO图标失败: {e}")
        
        username = self.current_user_info['username']
        role = self.current_user_info['role']
        self.title(f"番茄收购与发货管理系统 - 当前用户: {username} ({role})")
        self.geometry("1280x700")
        
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.excel_exporter = ExcelExporter(self.config_manager)

        self._configure_styles()
        self._create_widgets()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._update_time()

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        BG_COLOR = "#F7F8FA"
        TEXT_COLOR = "#333333"
        FONT_NORMAL = ("微软雅黑", 10)
        FONT_BOLD = ("微软雅黑", 10, "bold")
        HEADER_BG_COLOR = "#EAECEE"
        ACCENT_COLOR = "#4A90E2"
        BUTTON_FG_COLOR = "#FFFFFF"
        style.configure('.', background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_NORMAL)
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR)
        style.configure('Treeview', rowheight=28, fieldbackground=BG_COLOR, font=FONT_NORMAL)
        style.configure('Treeview.Heading', font=("微软雅黑", 11, "bold"), background=HEADER_BG_COLOR, padding=(10, 5))
        style.configure('TButton', font=FONT_BOLD, background=ACCENT_COLOR, foreground=BUTTON_FG_COLOR, padding=8)
        style.configure('TLabelframe', background=BG_COLOR)
        style.configure('TLabelframe.Label', background=BG_COLOR, font=FONT_BOLD)
        style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
        style.configure('TNotebook.Tab', font=FONT_BOLD, padding=(12, 6), background='#D5D8DC')
        style.map('TButton', background=[('active', '#357ABD'), ('pressed', '#285A8C')], foreground=[('active', BUTTON_FG_COLOR)])
        style.map("TNotebook.Tab", background=[("selected", BG_COLOR)], expand=[("selected", (1, 1, 1, 0))])
        style.map('Treeview.Heading', background=[('active', '#D5D8DC')])
        style.configure('Header.TFrame', background=HEADER_BG_COLOR)
        style.configure('Error.TEntry', fieldbackground='mistyrose')

    def _on_closing(self):
        self.db_manager.close()
        self.destroy()

    def _create_widgets(self):
        self._create_statusbar()
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both", padx=15, pady=(15, 0)) 
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill="both")
        
        shared_context = {
            "db_manager": self.db_manager,
            "config_manager": self.config_manager,
            "excel_exporter": self.excel_exporter,
            "current_user_info": self.current_user_info,
            "app": self
        }

        if self.current_user_info['role'] == 'admin':
            dashboard_frame = DashboardTab(notebook, shared_context)
            notebook.add(dashboard_frame, text=" 数据看板 ")

        grower_frame = GrowerTab(notebook, shared_context)
        notebook.add(grower_frame, text=" 种植户收购管理 ")
        
        client_frame = ClientTab(notebook, shared_context)
        notebook.add(client_frame, text=" 客户发货管理 ")
        
        if self.current_user_info['role'] == 'admin':
            admin_frame = AdminTab(notebook, shared_context)
            notebook.add(admin_frame, text=" 系统与用户管理 ")

    def _create_statusbar(self):
        status_bar = ttk.Frame(self, style='Header.TFrame')
        status_bar.pack(side="bottom", fill="x")
        
        self.status_label = ttk.Label(status_bar, text=" 欢迎使用番茄管理系统！", anchor='w')
        self.status_label.pack(side="left", padx=10, pady=2)
        
        self.time_label = ttk.Label(status_bar, anchor='e')
        self.time_label.pack(side="right", padx=10, pady=2)

    def _update_time(self):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.after(1000, self._update_time)

    def show_status_message(self, message, duration_ms=3000):
        if self.status_message_job_id:
            self.after_cancel(self.status_message_job_id)
        self.status_label.config(text=message)
        self.status_message_job_id = self.after(duration_ms, self._clear_status_message)

    def _clear_status_message(self):
        self.status_label.config(text=" 欢迎使用番茄管理系统！")
        self.status_message_job_id = None

    def _create_loading_window(self, message="正在处理，请稍候..."):
        loading_window = tk.Toplevel(self)
        loading_window.title("请稍候")
        loading_window.geometry("300x100")
        loading_window.resizable(False, False)
        
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 50
        loading_window.geometry(f"+{x}+{y}")

        loading_window.transient(self)
        loading_window.grab_set()

        ttk.Label(loading_window, text=message, font=("微软雅黑", 12)).pack(expand=True, pady=10)
        progress = ttk.Progressbar(loading_window, mode='indeterminate')
        progress.pack(pady=10, padx=20, fill='x')
        progress.start(10)
        
        return loading_window

    def run_long_task(self, task_function, on_complete=None, *args):
        loading_window = self._create_loading_window()
        result_queue = queue.Queue()

        def task_wrapper():
            try:
                result = task_function(*args)
                result_queue.put(('success', result))
            except Exception as e:
                result_queue.put(('error', e))

        thread = threading.Thread(target=task_wrapper)
        thread.daemon = True
        thread.start()

        def check_queue():
            try:
                status, result = result_queue.get_nowait()
                loading_window.destroy()
                if status == 'success':
                    if on_complete:
                        on_complete(result)
                elif status == 'error':
                    logging.error(f"线程任务出错: {result}", exc_info=True)
                    messagebox.showerror("发生错误", f"处理失败: {result}\n详情请查看日志文件。")
            except queue.Empty:
                self.after(100, check_queue)

        self.after(100, check_queue)