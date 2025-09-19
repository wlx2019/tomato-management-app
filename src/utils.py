# 文件路径: tomato V7/src/utils.py
# 版本：已升级到 passlib 用于密码安全

import os
import sys
from passlib.context import CryptContext # 导入 passlib

# --- 新增：创建密码哈希上下文 ---
# 我们将使用推荐的 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """验证明文密码是否与哈希值匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    """对密码进行哈希处理"""
    return pwd_context.hash(password)

def resource_path(relative_path):
    """ 获取资源的绝对路径, 兼容开发模式和PyInstaller打包后的模式 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)