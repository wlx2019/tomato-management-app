# 文件路径: src/tabs/base_tab.py
# 最终PC端修正版: 已修复删除按钮的调用逻辑

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import datetime
import math
import pandas as pd
from ..excel_importer import ExcelImporter

class BaseRecordTab(ttk.Frame):
    def __init__(self, parent, context, config):
        super().__init__(parent, padding=10)
        self.context = context
        self.app = context["app"]
        self.db_manager = context["db_manager"]
        self.excel_exporter = context["excel_exporter"]
        
        self.record_type = config["record_type"]
        self.table_name = config["table_name"]
        self.name_label_text = config["name_label_text"]
        self.name_key = config["name_key"]
        self.title = config["title"]
        self.tree_columns = config["tree_columns"]
        
        self.PAGE_SIZE = 50
        self.page_info = {'current': 1, 'total': 1, 'search_params': {}}
        self.current_record_id = None
        self.entries = {}
        self.vars = {}
        
        self._create_widgets()
        self.load_paged_records()

    def _create_widgets(self):
        self.columnconfigure(1, weight=1)
        
        left_frame = ttk.Frame(self, width=380)
        left_frame.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_frame.grid_propagate(False)
        
        input_frame = ttk.LabelFrame(left_frame, text=" 添加 / 修改记录 ", padding=15)
        input_frame.pack(fill='x')
        
        self.form_grid = ttk.Frame(input_frame)
        self.form_grid.pack(fill="x")
        self.form_grid.columnconfigure(1, weight=1)
        
        self._create_form_fields()

        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        btn_config = [
            ("添加记录", self.add_record),
            ("保存并新增", lambda: self.add_record(save_and_new=True)),
            ("修改记录", self.update_record),
            ("删除选中", self.delete_selected_record),
            ("清空表单", self._clear_form)
        ]
        for text, command in btn_config:
            ttk.Button(button_frame, text=text, command=command).pack(side="left", padx=2, expand=True, fill='x')

        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        search_export_frame = ttk.LabelFrame(right_frame, text=" 搜索与导出 ", padding=15)
        search_export_frame.grid(row=0, column=0, sticky='ew')
        search_export_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_export_frame, text="姓名:").grid(row=0, column=0, padx=(0,5), pady=2, sticky='w')
        self.vars['search_name_var'] = tk.StringVar()
        search_name_combo = ttk.Combobox(search_export_frame, textvariable=self.vars['search_name_var'])
        search_name_combo.grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        search_name_combo.config(postcommand=lambda: self._update_combobox_values(self.name_key, search_name_combo))
        
        ttk.Label(search_export_frame, text="日期:").grid(row=1, column=0, padx=(0,5), pady=2, sticky='w')
        date_frame = ttk.Frame(search_export_frame)
        date_frame.grid(row=1, column=1, padx=5, pady=2, sticky='ew')
        self.vars['start_date_widget'] = DateEntry(date_frame, width=12, date_pattern='yyyy-mm-dd', locale='zh_CN')
        self.vars['start_date_widget'].pack(side='left', fill='x', expand=True)
        self.vars['start_date_widget'].set_date(None)
        ttk.Label(date_frame, text=" 至 ").pack(side='left', padx=5)
        self.vars['end_date_widget'] = DateEntry(date_frame, width=12, date_pattern='yyyy-mm-dd', locale='zh_CN')
        self.vars['end_date_widget'].pack(side='left', fill='x', expand=True)
        self.vars['end_date_widget'].set_date(None)

        search_btn_frame = ttk.Frame(search_export_frame)
        search_btn_frame.grid(row=0, column=2, rowspan=2, padx=(10, 20))
        ttk.Button(search_btn_frame, text="搜索", command=self.search_records).pack(fill='x')
        ttk.Button(search_btn_frame, text="重置", command=self._reset_search).pack(fill='x', pady=2)
        
        self._add_extra_buttons(search_export_frame)

        tree_container = ttk.Frame(right_frame)
        tree_container.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_container, columns=self.tree_columns, show="headings")
        self.tree.grid(row=0, column=0, sticky='nsew')
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.column("ID", width=0, stretch=False)
        for col in self.tree_columns[1:]:
            self.tree.column(col, width=80, anchor='center')
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_column(c, False))
        
        self.tree.bind("<<TreeviewSelect>>", self._load_selected_to_form)

        pagination_frame = ttk.Frame(tree_container)
        pagination_frame.grid(row=1, column=0, sticky='ew', pady=(5, 0))
        
        self.page_info['prev_button'] = ttk.Button(pagination_frame, text="<< 上一页", command=lambda: self.change_page(-1))
        self.page_info['prev_button'].pack(side="left", padx=10)
        
        self.page_info['label'] = ttk.Label(pagination_frame, text="第 1 / 1 页")
        self.page_info['label'].pack(side="left", padx=10)

        self.page_info['next_button'] = ttk.Button(pagination_frame, text="下一页 >>", command=lambda: self.change_page(1))
        self.page_info['next_button'].pack(side="left", padx=10)
    
    def _add_extra_buttons(self, parent_frame):
        export_buttons_frame = ttk.Frame(parent_frame)
        export_buttons_frame.grid(row=0, column=3, rowspan=2)
        ttk.Button(export_buttons_frame, text="导出选中项", command=self.export_settlement).pack(fill='x')
        ttk.Button(export_buttons_frame, text="导出所有结果", command=self.export_settlement_from_search).pack(fill='x', pady=2)
    
    def load_paged_records(self):
        self.tree.delete(*self.tree.get_children())
        total_records = self.db_manager.count_records(self.table_name, self.page_info['search_params'])
        total_pages = math.ceil(total_records / self.PAGE_SIZE) if total_records > 0 else 1
        self.page_info['total'] = total_pages
        if self.page_info['current'] > self.page_info['total']: self.page_info['current'] = self.page_info['total']
        records = self.db_manager.fetch_paged_records(self.table_name, self.page_info['current'], self.PAGE_SIZE, self.page_info['search_params'])
        for i, record in enumerate(records):
            tag = 'evenrow' if i % 2 != 0 else 'oddrow'
            self.tree.insert("", "end", values=record, tags=(tag,))
        self.page_info['label'].config(text=f"第 {self.page_info['current']} / {self.page_info['total']} 页")
        self.page_info['prev_button']['state'] = 'normal' if self.page_info['current'] > 1 else 'disabled'
        self.page_info['next_button']['state'] = 'normal' if self.page_info['current'] < self.page_info['total'] else 'disabled'
    
    def change_page(self, direction):
        new_page = self.page_info['current'] + direction
        if 1 <= new_page <= self.page_info['total']:
            self.page_info['current'] = new_page
            self.load_paged_records()

    def add_record(self, save_and_new=False):
        data = self._get_form_data()
        if not data: return
        if self.db_manager.add_record(self.table_name, data):
            self.load_paged_records()
            self._clear_form(keep_fields=save_and_new)
            self.app.show_status_message("记录已成功添加！")

    def update_record(self):
        if not self.current_record_id:
            messagebox.showwarning("提示", "请先从列表中选择要修改的记录！", parent=self)
            return
        data = self._get_form_data()
        if not data: return
        if self.db_manager.update_record(self.table_name, self.current_record_id, data):
            self.load_paged_records()
            self._clear_form()
            self.app.show_status_message("记录已成功修改！")

    def delete_selected_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("提示", "请选择要删除的记录！", parent=self)
            return
        if messagebox.askyesno("确认删除", "确定要删除选中的记录吗？", parent=self):
            record_id = self.tree.item(selected_item[0], "values")[0]
            if self.db_manager.delete_record(self.table_name, record_id):
                self.load_paged_records()
                self._clear_form()
                self.app.show_status_message("记录已删除。")
            else:
                messagebox.showerror("删除失败", "从云端删除记录时发生错误，请查看日志。", parent=self)
            
    def _update_combobox_values(self, col_name, combo_widget=None):
        if combo_widget is None: combo_widget = self.entries.get(col_name)
        if combo_widget:
            combo_widget['values'] = tuple(self.db_manager.fetch_distinct_values(self.table_name, col_name))
            
    def search_records(self):
        self.page_info['search_params'] = {
            'name': self.vars['search_name_var'].get(),
            'start_date': self.vars['start_date_widget'].get_date().strftime('%Y-%m-%d') if self.vars['start_date_widget'].get() else None,
            'end_date': self.vars['end_date_widget'].get_date().strftime('%Y-%m-%d') if self.vars['end_date_widget'].get() else None
        }
        self.page_info['current'] = 1
        self.load_paged_records()

    def _reset_search(self):
        self.vars['search_name_var'].set("")
        self.vars['start_date_widget'].set_date(None)
        self.vars['end_date_widget'].set_date(None)
        self.page_info['search_params'] = {}
        self.page_info['current'] = 1
        self.load_paged_records()
        
    def _export_worker(self, ids):
        if not ids:
            return ('warning', "没有选中任何记录用于导出。")
        df = self.db_manager.get_records_by_ids(self.table_name, ids)
        if df is None or df.empty:
            return ('warning', "没有有效数据可导出。")
        entity_names = df[self.name_key].unique()
        if len(entity_names) > 1:
            return ('warning', "导出失败！\n\n请确保所有选中的记录都属于【同一个人】。")
        entity_name = entity_names[0]
        min_date, max_date = df['date'].min(), df['date'].max()
        date_range = (min_date, max_date)
        wb, entity_name = self.excel_exporter.create_settlement_workbook(df, self.title, entity_name, self.record_type, date_range)
        return ('save', (wb, entity_name, self.title))

    def _on_export_complete(self, result):
        status, data = result
        if status == 'warning':
            messagebox.showwarning("提示", data, parent=self)
        elif status == 'save':
            wb, entity_name, title = data
            self.excel_exporter.save_and_notify(wb, entity_name, title)

    def export_settlement(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请选择至少一条记录来导出。", parent=self)
            return
        selected_ids = [self.tree.item(item, "values")[0] for item in selected_items]
        self.app.run_long_task(self._export_worker, self._on_export_complete, selected_ids)

    def export_settlement_from_search(self):
        all_items = self.tree.get_children()
        if not all_items:
            messagebox.showwarning("提示", "当前没有搜索结果可供导出。", parent=self)
            return
        all_ids = [self.tree.item(item, "values")[0] for item in all_items]
        self.app.run_long_task(self._export_worker, self._on_export_complete, all_ids)
    
    def _sort_treeview_column(self, col, reverse):
        try:
            data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
            def sort_key(item):
                try: return float(item[0])
                except (ValueError, TypeError): return str(item[0])
            data.sort(key=sort_key, reverse=reverse)
            for i, item in enumerate(data):
                self.tree.move(item[1], '', i)
            self.tree.heading(col, command=lambda: self._sort_treeview_column(col, not reverse))
        except Exception as e:
            print(f"排序时出错: {e}")

    def _create_form_fields(self):
        raise NotImplementedError("子类必须实现 _create_form_fields 方法")
    def _get_form_data(self):
        raise NotImplementedError("子类必须实现 _get_form_data 方法")
    def _clear_form(self, keep_fields=False):
        raise NotImplementedError("子类必须实现 _clear_form 方法")
    def _load_selected_to_form(self, event=None):
        raise NotImplementedError("子类必须实现 _load_selected_to_form 方法")