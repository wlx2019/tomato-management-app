# 文件路径: src/database.py
# 最终PC端修正版: 已修复云端删除和添加的BUG

import os
import logging
import pandas as pd
from supabase import create_client, Client
from .config import ConfigManager
from tkinter import messagebox # 引入messagebox用于在PC端弹窗报错

class DatabaseManager:
    def __init__(self, db_name=None):
        config = ConfigManager()
        url: str = config.get("supabase_url")
        key: str = config.get("supabase_key")
        
        if not url or not key or "YOUR_URL" in url:
            logging.error("Supabase URL或Key未在config.json中配置！")
            raise ValueError("请在config.json中配置好Supabase的URL和Key")
            
        self.supabase: Client = create_client(url, key)
        logging.info("成功连接到Supabase云数据库。")

    def close(self):
        logging.info("数据库会话结束。")
        pass

    def get_user(self, username):
        try:
            response = self.supabase.table('users').select("*").eq('username', username).execute()
            if response.data:
                user = response.data[0]
                return (user['id'], user['username'], user['password_hash'], user['role'])
            return None
        except Exception as e:
            logging.error(f"获取用户 '{username}' 失败: {e}")
            return None

    def get_all_users(self):
        try:
            response = self.supabase.table('users').select("id, username, role").execute()
            return [(user['id'], user['username'], user['role']) for user in response.data]
        except Exception as e:
            logging.error(f"获取所有用户失败: {e}")
            return []

    def add_user(self, username, password_hash, role='user'):
        if self.get_user(username):
            return False
        try:
            self.supabase.table('users').insert({
                "username": username,
                "password_hash": password_hash,
                "role": role
            }).execute()
            return True
        except Exception as e:
            logging.error(f"添加用户 '{username}' 失败: {e}")
            return False

    def delete_user(self, user_id):
        try:
            self.supabase.table('users').delete().eq('id', user_id).execute()
            return True
        except Exception as e:
            logging.error(f"删除用户ID '{user_id}' 失败: {e}")
            return False

    def fetch_paged_records(self, table_name, page, page_size, search_params={}):
        offset = (page - 1) * page_size
        try:
            query = self.supabase.table(table_name).select("*", count='exact').order('date', desc=True).order('id', desc=True).range(offset, offset + page_size - 1)
            name_col = 'grower_name' if table_name == 'grower_records' else 'client_name'
            if search_params.get('name'):
                query = query.like(name_col, f"%{search_params['name']}%")
            if search_params.get('start_date'):
                query = query.gte('date', search_params['start_date'])
            if search_params.get('end_date'):
                query = query.lte('date', search_params['end_date'])
            response = query.execute()
            records = []
            if table_name == 'grower_records':
                for r in response.data:
                    records.append((r['id'], r['date'], r['grower_name'], r['spec'], r['gross_weight'], r['secondary_fruit'], r['tare_weight'], r['net_weight'], r['unit_price'], r['total_amount'], r['notes']))
            else:
                for r in response.data:
                    records.append((r['id'], r['date'], r['client_name'], r['spec'], r['pieces'], r['weight'], r['unit_price'], r['total_amount'], r['notes']))
            return records
        except Exception as e:
            logging.error(f"分页获取 {table_name} 记录失败: {e}")
            return []

    def count_records(self, table_name, search_params={}):
        try:
            query = self.supabase.table(table_name).select("id", count='exact')
            name_col = 'grower_name' if table_name == 'grower_records' else 'client_name'
            if search_params.get('name'):
                query = query.like(name_col, f"%{search_params['name']}%")
            if search_params.get('start_date'):
                query = query.gte('date', search_params['start_date'])
            if search_params.get('end_date'):
                query = query.lte('date', search_params['end_date'])
            response = query.execute()
            return response.count
        except Exception as e:
            logging.error(f"统计 {table_name} 记录数失败: {e}")
            return 0

    def add_record(self, table_name, data):
        clean_data = {k: v for k, v in data.items() if v is not None}
        try:
            self.supabase.table(table_name).insert(clean_data).execute()
            return True
        except Exception as e:
            logging.error(f"向 {table_name} 添加记录失败: {e}")
            messagebox.showerror("云端错误", f"添加记录失败: \n{e}")
            return False

    def update_record(self, table_name, record_id, data):
        try:
            self.supabase.table(table_name).update(data).eq('id', record_id).execute()
            return True
        except Exception as e:
            logging.error(f"更新 {table_name} 记录ID {record_id} 失败: {e}")
            messagebox.showerror("云端错误", f"更新记录失败: \n{e}")
            return False
            
    def delete_record(self, table_name, record_id):
        try:
            self.supabase.table(table_name).delete().eq('id', record_id).execute()
            return True
        except Exception as e:
            logging.error(f"删除记录ID '{record_id}' 失败: {e}")
            return False

    def fetch_distinct_values(self, table_name, column_name):
        try:
            response = self.supabase.table(table_name).select(column_name).execute()
            if response.data:
                distinct_values = sorted(list(set(item[column_name] for item in response.data if item[column_name])))
                return distinct_values
            return []
        except Exception as e:
            logging.error(f"获取 {table_name} 的 {column_name} 列唯一值失败: {e}")
            return []
            
    def get_records_by_ids(self, table_name, ids):
        try:
            response = self.supabase.table(table_name).select("*").in_('id', ids).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logging.error(f"根据IDs获取 {table_name} 记录失败: {e}")
            return pd.DataFrame()

    def get_custom_summary(self, record_type, start_date, end_date, name=None):
        table_name = f"{record_type}_records"
        name_column = 'grower_name' if record_type == 'grower' else 'client_name'
        try:
            query = self.supabase.table(table_name).select('date', 'total_amount', 'net_weight' if record_type == 'grower' else 'weight').gte('date', start_date).lte('date', end_date)
            if name and name != '全部':
                query = query.eq(name_column, name)
            response = query.execute()
            if not response.data:
                return pd.DataFrame()
            df = pd.DataFrame(response.data)
            df['date'] = pd.to_datetime(df['date'])
            weight_col = 'net_weight' if record_type == 'grower' else 'weight'
            df.rename(columns={weight_col: 'total_weight'}, inplace=True)
            summary_df = df.groupby('date').agg(total_revenue=('total_amount', 'sum'), total_weight=('total_weight', 'sum')).reset_index()
            return summary_df
        except Exception as e:
            logging.error(f"获取自定义汇总数据失败: {e}")
            return pd.DataFrame()

    def check_existing_records(self, table_name, records_to_check):
        if not records_to_check:
            return [], 0
        name_col = 'grower_name' if table_name == 'grower_records' else 'client_name'
        new_records = []
        duplicate_count = 0
        try:
            for record in records_to_check:
                response = self.supabase.table(table_name).select("id", count='exact').eq('date', record['date']).eq(name_col, record[name_col]).eq('spec', record['spec']).execute()
                if response.count > 0:
                    duplicate_count += 1
                else:
                    new_records.append(record)
            return new_records, duplicate_count
        except Exception as e:
            logging.error(f"检查重复记录失败: {e}")
            return records_to_check, 0 # 出错时返回所有记录，避免数据丢失

    def bulk_insert_records(self, table_name, records):
        if not records:
            return 0
        try:
            self.supabase.table(table_name).insert(records).execute()
            return len(records)
        except Exception as e:
            logging.error(f"批量插入失败: {e}")
            messagebox.showerror("云端错误", f"批量导入失败: \n{e}")
            return 0