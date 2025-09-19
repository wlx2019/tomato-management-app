# 文件路径: src/excel_importer.py
# 版本：已升级，返回新记录、重复数和总行数

import pandas as pd
from tkinter import messagebox

class ExcelImporter:
    def __init__(self, file_path, record_type, db_manager): # 添加 db_manager
        self.file_path = file_path
        self.record_type = record_type
        self.db_manager = db_manager # 保存 db_manager 实例
        self.expected_columns = []
        self.rename_map = {}

    def _prepare_columns(self):
        if self.record_type == "grower":
            self.expected_columns = ['日期', '姓名', '规格', '毛重(斤)', '次果(斤)', '皮重(斤)', '单价', '备注']
            self.rename_map = {
                '日期': 'date',
                '姓名': 'grower_name',
                '规格': 'spec',
                '毛重(斤)': 'gross_weight',
                '次果(斤)': 'secondary_fruit',
                '皮重(斤)': 'tare_weight',
                '单价': 'unit_price',
                '备注': 'notes'
            }
        elif self.record_type == "client":
            self.expected_columns = ['日期', '姓名', '规格', '件数', '重量(斤)', '单价', '备注']
            self.rename_map = {
                '日期': 'date',
                '姓名': 'client_name',
                '规格': 'spec',
                '件数': 'pieces',
                '重量(斤)': 'weight',
                '单价': 'unit_price',
                '备注': 'notes'
            }

    def parse_excel(self):
        self._prepare_columns()
        try:
            df = pd.read_excel(self.file_path)
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取Excel文件。\n错误: {e}")
            return None, 0, 0

        if not all(col in df.columns for col in self.expected_columns):
            missing_cols = [col for col in self.expected_columns if col not in df.columns]
            messagebox.showerror("格式错误", f"Excel文件缺少必要的列: {', '.join(missing_cols)}")
            return None, 0, 0
        
        df = df[self.expected_columns]
        df.rename(columns=self.rename_map, inplace=True)
        
        valid_records = []
        for index, row in df.iterrows():
            record = row.to_dict()
            
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = '' if key in ['notes', 'spec'] else 0

            try:
                if self.record_type == 'grower':
                    gross = float(record.get('gross_weight', 0))
                    secondary = float(record.get('secondary_fruit', 0))
                    tare = float(record.get('tare_weight', 0))
                    price = float(record.get('unit_price', 0))
                    
                    net_weight = gross - secondary - tare
                    record['net_weight'] = net_weight
                    record['total_amount'] = round(net_weight * price, 2)
                else: # client
                    record['total_amount'] = round(float(record['weight']) * float(record['unit_price']), 2)

            except (ValueError, TypeError):
                messagebox.showwarning("数据警告", f"第 {index + 2} 行的重量或单价不是有效数字，该行将被跳过。")
                continue

            if isinstance(record.get('date'), pd.Timestamp):
                record['date'] = record['date'].strftime('%Y-%m-%d')
            
            valid_records.append(record)
        
        # --- 核心修改点：调用数据库检查重复项 ---
        table_name = f"{self.record_type}_records"
        new_records, duplicate_count = self.db_manager.check_existing_records(table_name, valid_records)
            
        return new_records, duplicate_count, len(df)