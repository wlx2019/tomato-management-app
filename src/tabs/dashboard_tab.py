# 文件路径: src/tabs/dashboard_tab.py
# 版本：已更新为只显示种植户数据报表

import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

class DashboardTab(ttk.Frame):
    def __init__(self, parent, context):
        super().__init__(parent)
        self.parent = parent
        self.context = context
        self.db_manager = self.context["db_manager"]
        self.chart_canvas = None
        
        # --- 优化点：报表类型固定为种植户 ---
        self.report_type = "grower"
        
        self._create_widgets()
        # 初始化时直接加载种植户数据
        self._update_name_combobox_values()
        self._generate_custom_chart()

    def _create_widgets(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(side="top", fill="x", pady=5, padx=5)
        
        # --- 优化点：移除了报表类型选择框 ---
        
        self.name_label = ttk.Label(control_frame, text="种植户:")
        self.name_label.pack(side="left", padx=(0, 5))
        self.name_var = tk.StringVar(value='全部')
        self.name_combo = ttk.Combobox(control_frame, textvariable=self.name_var, width=15)
        self.name_combo.pack(side="left", padx=5)
        self.name_combo.config(postcommand=self._update_name_combobox_values)

        ttk.Label(control_frame, text="从:").pack(side="left", padx=(15, 5))
        self.start_date_entry = DateEntry(control_frame, width=12, date_pattern='yyyy-mm-dd', locale='zh_CN')
        self.start_date_entry.pack(side="left")
        
        ttk.Label(control_frame, text="至:").pack(side="left", padx=5)
        self.end_date_entry = DateEntry(control_frame, width=12, date_pattern='yyyy-mm-dd', locale='zh_CN')
        self.end_date_entry.pack(side="left")

        today = datetime.date.today()
        first_day_of_month = today.replace(day=1)
        self.start_date_entry.set_date(first_day_of_month)
        self.end_date_entry.set_date(today)
        
        # --- 优化点：生成图表按钮绑定了新的响应函数 ---
        ttk.Button(control_frame, text="生成图表", command=self._generate_custom_chart).pack(side="left", padx=20)

        stats_frame = ttk.LabelFrame(self, text=" 数据总览 ", padding=15)
        stats_frame.pack(side="top", fill="x", pady=10, padx=5)
        
        FONT_BOLD = ("微软雅黑", 10, "bold")
        self.total_revenue_label = ttk.Label(stats_frame, text="总金额: 0.00 元", font=FONT_BOLD)
        self.total_revenue_label.pack(side="left", padx=20)
        
        self.total_weight_label = ttk.Label(stats_frame, text="总净重: 0.00 斤", font=FONT_BOLD)
        self.total_weight_label.pack(side="left", padx=20)

        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(expand=True, fill="both", pady=10, padx=5)

    # --- 优化点：移除了 _on_report_type_change 函数 ---

    def _update_name_combobox_values(self):
        # 直接使用固定的表名和列名
        table_name = "grower_records"
        name_column = 'grower_name'
        names = self.db_manager.fetch_distinct_values(table_name, name_column)
        self.name_combo['values'] = ['全部'] + names
        
    def _generate_custom_chart(self):
        name = self.name_var.get()
        try:
            start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')
        except AttributeError:
            return

        # 直接调用数据库查询，类型固定为 grower
        df = self.db_manager.get_custom_summary(self.report_type, start_date, end_date, name)
        
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(10, 6), dpi=100)
        ax1 = fig.add_subplot(111)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            total_revenue = df['total_revenue'].sum()
            total_weight = df['total_weight'].sum()
            self.total_revenue_label.config(text=f"总金额: {total_revenue:,.2f} 元")
            self.total_weight_label.config(text=f"总净重: {total_weight:,.2f} 斤")
            
            ax1.bar(df['date'], df['total_revenue'], label='日收购金额 (元)', width=0.8)
            ax2 = ax1.twinx()
            ax2.plot(df['date'], df['total_weight'], color='r', marker='o', linestyle='--', label='日收购净重 (斤)')
            
            name_text = "全部种植户" if name == '全部' else name
            chart_title = f"{name_text} 从 {start_date} 到 {end_date} 的收购数据趋势"
            
            # 尝试使用中文宋体，如果失败则使用默认字体
            try:
                font_prop = {'family': 'SimHei', 'size': 12}
                title_font_prop = {'family': 'SimHei', 'size': 16}
                ax1.set_title(chart_title, fontproperties=title_font_prop)
                ax1.set_ylabel('总金额 (元)', fontproperties=font_prop)
                ax2.set_ylabel('总净重 (斤)', fontproperties=font_prop)
                fig.legend(prop={'family': 'SimHei', 'size': 10})
            except Exception:
                ax1.set_title(chart_title)
                ax1.set_ylabel('Total Amount (Yuan)')
                ax2.set_ylabel('Total Net Weight (Jin)')
                fig.legend()
        else:
            self.total_revenue_label.config(text="总金额: 0.00 元")
            self.total_weight_label.config(text="总净重: 0.00 斤")
            # 同样尝试使用中文字体
            try:
                ax1.text(0.5, 0.5, '当前筛选条件下无数据', ha='center', va='center', fontproperties={'family': 'SimHei', 'size': 16})
            except Exception:
                ax1.text(0.5, 0.5, 'No data for the current filter', ha='center', va='center')

        fig.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)