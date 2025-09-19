# 文件路径: src/tabs/client_tab.py
# 最终修正版: 已修复客户端金额计算公式的BUG

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import datetime
from .base_tab import BaseRecordTab

class ClientTab(BaseRecordTab):
    def __init__(self, parent, context):
        config = {
            "record_type": "client",
            "table_name": "client_records",
            "name_label_text": "客户名称:",
            "name_key": "client_name",
            "title": "客户发货结算单",
            "tree_columns": ("ID", "日期", "客户名称", "规格", "件数", "重量(斤)", "单价", "金额", "备注")
        }
        super().__init__(parent, context, config)
    
    def _create_form_fields(self):
        fields = [
            ("日期:", 'date'),
            (self.name_label_text, self.name_key),
            ("规格:", 'spec'),
            ("件数:", 'pieces'),
            ("重量(斤):", 'weight'),
            ("单价:", 'unit_price'),
            ("备注:", 'notes')
        ]

        self.vars['pieces_var'] = tk.StringVar()
        self.vars['weight_var'] = tk.StringVar()
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
        self.entries['spec'].bind("<Return>", lambda e: self.entries['pieces'].focus_set())
        self.entries['pieces'].bind("<Return>", lambda e: self.entries['weight'].focus_set())
        self.entries['weight'].bind("<Return>", lambda e: self.entries['unit_price'].focus_set())
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
            errors[self.name_key] = "客户名称不能为空。"
            self.entries[self.name_key].config(style='Error.TEntry')
            
        data['spec'] = self.entries['spec'].get().strip()
        if not data['spec']:
            errors['spec'] = "规格不能为空。"
            self.entries['spec'].config(style='Error.TEntry')

        data['notes'] = self.entries['notes'].get().strip()

        for key, var_name, label in [('pieces', 'pieces_var', '件数'), ('weight', 'weight_var', '重量'), ('unit_price', 'unit_price_var', '单价')]:
            try:
                value = float(self.vars[var_name].get())
                if key in ['pieces', 'weight'] and value <= 0:
                    raise ValueError(f"{label}必须大于0")
                if key == 'unit_price' and value < 0:
                    raise ValueError("单价不能为负数")
                data[key] = value
            except (ValueError, TypeError):
                errors[key] = f"{label}必须是有效的数字。"
                self.entries[key].config(style='Error.TEntry')

        if errors:
            error_message = "输入错误:\n" + "\n".join(f"- {msg}" for msg in errors.values())
            messagebox.showerror("输入错误", error_message, parent=self)
            return None

        # --- 核心修改点：更新金额计算公式 ---
        # 之前的错误公式: data['weight'] * data['unit_price']
        # 现在的正确公式:
        data['total_amount'] = round(data['pieces'] * data['weight'] * data['unit_price'], 2)
        
        return data
            
    def _clear_form(self, keep_fields=False):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.config(style='TEntry')

        if not keep_fields:
            self.entries['date'].set_date(datetime.date.today())
            self.entries[self.name_key].set('')
            self.entries['spec'].set('')
        
        self.vars['pieces_var'].set('')
        self.vars['weight_var'].set('')
        self.vars['unit_price_var'].set('')
        self.entries['notes'].delete(0, tk.END)
        self.current_record_id = None
        self.entries['pieces'].focus_set()

    def _load_selected_to_form(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0], 'values')
        self.current_record_id = values[0]
        
        self.entries['date'].set_date(values[1])
        self.entries[self.name_key].set(values[2])
        self.entries['spec'].set(values[3])
        self.vars['pieces_var'].set(values[4])
        self.vars['weight_var'].set(values[5])
        self.vars['unit_price_var'].set(values[6])
        self.entries['notes'].delete(0, tk.END)
        self.entries['notes'].insert(0, values[8] if len(values) > 8 else '')