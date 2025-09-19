# 文件路径: tomato V7/main.py
# 版本：已添加 ttkthemes 主题

import sys
import os
import logging
from src.database import DatabaseManager
from src.gui import LoginWindow, handle_initial_user_setup, TomatoManagementApp
from ttkthemes import ThemedTk # 导入 ThemedTk

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    
    if sys.version_info < (3, 8):
        logging.error("此程序需要 Python 3.8 或更高版本。")
        return

    db_manager = DatabaseManager()

    if not db_manager.get_all_users():
        if not handle_initial_user_setup(db_manager):
            logging.info("首次用户设置被取消，程序退出。")
            return

    # --- 核心修改：在登录窗口也应用主题 ---
    # 1. 创建带主题的登录窗口
    # 注意：我们将 LoginWindow 的父类从 tk.Tk 改为 ThemedTk
    # 为了简单起见，我们直接在这里修改主程序，让它为 LoginWindow 也设置主题
    login_window = LoginWindow(db_manager)
    # 你可以尝试不同的主题, 如 'arc', 'plastik', 'breeze', 'scidblue' 等
    login_window.set_theme("arc") 
    login_window.mainloop()
    
    login_info = login_window.login_info

    if login_info:
        logging.info(f"用户 '{login_info['username']}' (角色: {login_info['role']}) 登录成功。")
        
        # --- 核心修改：让主程序窗口继承 ThemedTk 而不是 tk.Tk ---
        # 这需要我们去 gui.py 修改 TomatoManagementApp 的父类
        # (我们已经在下面的 gui.py 代码中为您修改好了)
        app = TomatoManagementApp(current_user_info=login_info)
        app.set_theme("arc") # 设置一个漂亮的主题
        app.mainloop()
    else:
        logging.info("登录失败或窗口被关闭，程序退出。")

if __name__ == "__main__":
    main()