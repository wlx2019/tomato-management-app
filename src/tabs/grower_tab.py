# 文件路径: src/tabs/grower_tab.py
# 版本：已更新，向 ExcelImporter 传递 db_manager

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import datetime
from ..excel_importer import ExcelImporter
from .base_tab import BaseRecordTab

class GrowerTab(BaseRecordTab):
    def __init__(self, parent, context):
        config = {
            "record_type": "grower",
            "table_name": "grower_records",
            "name_label_text": "种植户姓名:",
            "name_key": "grower_name",
            "title": "种植户结算单",
            "tree_columns": ("ID", "日期", "姓名", "规格", "毛重", "次果", "皮重", "净重", "单价", "金额", "备注")
        }
        super().__init__(parent, context, config)

    def _add_extra_buttons(self, parent_frame):
        super()._add_extra_buttons(parent_frame)
        file_op_frame = parent_frame.grid_slaves(row=0, column=3)[0]
        ttk.Button(file_op_frame, text="从Excel导入", command=self._import_from_excel).pack(fill='x', pady=(10, 0))

    def _import_worker(self, file_path):
        # --- 核心修改点：将 self.db_manager 传递给 ExcelImporter ---
        importer = ExcelImporter(file_path, self.record_type, self.db_manager)
        new_records, duplicate_count, total_rows = importer.parse_excel()
        
        if new_records is None:
            return ('error', "文件解析失败，请检查文件格式。")
        
        return ('confirm_import', (new_records, duplicate_count, total_rows))

    def _on_import_complete(self, result):
        status, data = result
        if status == 'error':
            messagebox.showerror("错误", data, parent=self)
        elif status == 'confirm_import':
            new_records, duplicate_count, total_rows = data
            
            if not new_records and duplicate_count == 0:
                 messagebox.showinfo("提示", "Excel文件中没有可导入的有效数据。", parent=self)
                 return
            
            msg_parts = [f"成功解析 {total_rows} 条记录。"]
            if duplicate_count > 0:
                msg_parts.append(f"发现 {duplicate_count} 条重复记录（已跳过）。")
            if new_records:
                msg_parts.append(f"\n是否确认导入剩余的 {len(new_records)} 条新记录？")
            else:
                msg_parts.append("\n没有新的记录需要导入。")

            msg = "\n".join(msg_parts)
            
            if new_records and messagebox.askyesno("确认导入", msg, parent=self):
                self.app.run_long_task(self._db_insert_worker, self._on_db_insert_complete, new_records)
            elif not new_records:
                 messagebox.showinfo("导入完成", msg, parent=self)


    def _db_insert_worker(self, records):
        return self.db_manager.bulk_insert_records(self.table_name, records)

    def _on_db_insert_complete(self, inserted_count):
        self.app.show_status_message(f"成功导入 {inserted_count} 条新记录！")
        self.load_paged_records()

    def _import_from_excel(self):
        file_path = filedialog.askopenfilename(title="请选择要导入的Excel文件", filetypes=[("Excel 文件", "*.xlsx")])
        if not file_path: 
            return
        self.app.run_long_task(self._import_worker, self._on_import_complete, file_path)
    
    # (其余方法保持不变, 此处省略...)
    def _create_form_fields(self):
        fields = [
            ("日期:", 'date'),
            (self.name_label_text, self.name_key),
            ("规格:", 'spec'),
            ("净重(斤):", 'net_weight'),
            ("单价:", 'unit_price'),
            ("备注:", 'notes')
        ]
        self.vars['net_weight_var'] = tk.StringVar()
        self.vars['unit_price_var'] = tk.StringVar()

        for i, (label_text, key) in enumerate(fields):
            ttk.Label(self.form_grid, text=label_text).grid(row=i, column=0, padx=5, pady=8, sticky="w")
            if key == 'date':
                self.entries[key] = DateEntry(self.form_grid, date_pattern='yyyy-mm-dd', locale='zh_CN')
            elif key in [self.name_key, 'spec']:
                self.entries[key] = ttk.Combobox(self.form_grid)
                self.entries[key].config(postcommand=lambda k=key: self._update_combobox_values(k))
            elif f"{key}_var" in self.vars:
                self.entries[key] = ttk.Entry(self.form_grid, textvariable=self.vars[f"{key}_var"])
            else:
                self.entries[key] = ttk.Entry(self.form_grid)
            self.entries[key].grid(row=i, column=1, padx=5, pady=8, sticky="ew")
        
        self.entries['date'].bind("<Return>", lambda e: self.entries[self.name_key].focus_set())
        self.entries[self.name_key].bind("<Return>", lambda e: self.entries['spec'].focus_set())
        self.entries['spec'].bind("<Return>", lambda e: self.entries['net_weight'].focus_set())
        self.entries['net_weight'].bind("<Return>", lambda e: self.entries['unit_price'].focus_set())
        self.entries['unit_price'].bind("<Return>", lambda e: self.entries['notes'].focus_set())

    def _get_form_data(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.config(style='TEntry')
        
        errors = {}
        data = {}
        try:
            data['date'] = self.entries['date'].get_date().strftime('%Y-%m-%d')
        except AttributeError:
            errors['date'] = "日期不能为空。"

        data[self.name_key] = self.entries[self.name_key].get().strip()
        if not data[self.name_key]:
            errors[self.name_key] = "姓名不能为空。"
            self.entries[self.name_key].config(style='Error.TEntry')
            
        data['spec'] = self.entries['spec'].get().strip()
        if not data['spec']:
            errors['spec'] = "规格不能为空。"
            self.entries['spec'].config(style='Error.TEntry')

        data['notes'] = self.entries['notes'].get().strip()
        
        try:
            net_weight = float(self.vars['net_weight_var'].get())
            if net_weight <= 0:
                raise ValueError("净重必须大于0")
            data['net_weight'] = net_weight
            data['gross_weight'] = net_weight
        except (ValueError, TypeError):
            errors['net_weight'] = "净重必须是大于0的数字。"
            self.entries['net_weight'].config(style='Error.TEntry')

        try:
            unit_price = float(self.vars['unit_price_var'].get())
            if unit_price < 0:
                raise ValueError("单价不能为负数")
            data['unit_price'] = unit_price
        except (ValueError, TypeError):
            errors['unit_price'] = "单价必须是有效的数字。"
            self.entries['unit_price'].config(style='Error.TEntry')

        if errors:
            error_message = "输入错误:\n" + "\n".join(f"- {key}: {msg}" for key, msg in errors.items())
            messagebox.showerror("输入错误", error_message, parent=self)
            return None
        
        data['total_amount'] = round(data['net_weight'] * data['unit_price'], 2)
        data['secondary_fruit'] = 0
        data['tare_weight'] = 0
            
        return data

    def _clear_form(self, keep_fields=False):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.config(style='TEntry')

        if not keep_fields:
            self.entries['date'].set_date(datetime.date.today())
            self.entries[self.name_key].set('')
            self.entries['spec'].set('')
        
        self.vars['net_weight_var'].set('')
        self.vars['unit_price_var'].set('')
        self.entries['notes'].delete(0, tk.END)
        self.current_record_id = None
        self.entries['net_weight'].focus_set()

    def _load_selected_to_form(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0], 'values')
        self.current_record_id = values[0]
        
        self.entries['date'].set_date(values[1])
        self.entries[self.name_key].set(values[2])
        self.entries['spec'].set(values[3])
        self.vars['net_weight_var'].set(values[7])
        self.vars['unit_price_var'].set(values[8])
        self.entries['notes'].delete(0, tk.END)
        self.entries['notes'].insert(0, values[10] if len(values) > 10 else '')