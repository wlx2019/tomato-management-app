# 文件路径: web_app/server.py
# 版本：已为种植户页面增加完整的搜索和分页功能

from flask import Flask, render_template, request, redirect, url_for
import sys
import os
import datetime
import math # 引入 math 用于计算总页数

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager

app = Flask(__name__, static_folder='static')
app.secret_key = 'some_secret_key_for_flash_messages' 

try:
    db_manager = DatabaseManager()
    print("成功连接到Supabase数据库。")
except Exception as e:
    print(f"连接数据库失败: {e}")
    db_manager = None

PAGE_SIZE = 50 # 定义每页显示的记录数

# --- 核心修改点：主页路由现在处理搜索和分页 ---
@app.route('/')
def index():
    if not db_manager: return "数据库未连接。", 500
    
    # 从URL获取当前页码，默认为第一页
    page = request.args.get('page', 1, type=int)
    
    # 从URL获取搜索参数
    search_params = {
        'name': request.args.get('name', '').strip(),
        'start_date': request.args.get('start_date', '').strip(),
        'end_date': request.args.get('end_date', '').strip()
    }
    # 清理空的参数，避免传给数据库
    clean_search_params = {k: v for k, v in search_params.items() if v}

    # 获取符合搜索条件的总记录数和总页数
    total_records = db_manager.count_records('grower_records', clean_search_params)
    total_pages = math.ceil(total_records / PAGE_SIZE) if total_records > 0 else 1

    # 获取当前页的数据
    records = db_manager.fetch_paged_records('grower_records', page, PAGE_SIZE, clean_search_params)
    
    # 将所有需要的信息传递给HTML模板
    return render_template('index.html', 
                           records=records,
                           page=page, 
                           total_pages=total_pages,
                           search_params=search_params)


@app.route('/clients')
def clients_page():
    # (此函数保持不变)
    if not db_manager: return "数据库未连接。", 500
    records = db_manager.fetch_paged_records('client_records', 1, 100)
    return render_template('clients.html', records=records)

# --- 添加、编辑、删除等路由保持不变 (此处省略) ---
@app.route('/add_grower', methods=['GET', 'POST'])
def add_grower():
    if not db_manager: return "数据库未连接。", 500
    if request.method == 'POST':
        try:
            data = { 'date': request.form['date'], 'grower_name': request.form['grower_name'].strip(), 'spec': request.form['spec'].strip(), 'gross_weight': float(request.form['gross_weight']), 'secondary_fruit': float(request.form.get('secondary_fruit', 0)), 'tare_weight': float(request.form.get('tare_weight', 0)), 'unit_price': float(request.form['unit_price']), 'notes': request.form.get('notes', '').strip() }
            if not data['grower_name'] or not data['spec']: return "姓名和规格不能为空！", 400
            data['net_weight'] = data['gross_weight'] - data['secondary_fruit'] - data['tare_weight']
            data['total_amount'] = round(data['net_weight'] * data['unit_price'], 2)
            db_manager.add_record('grower_records', data)
            return redirect(url_for('index'))
        except (ValueError, TypeError) as e: return f"数据格式错误: {e}", 400
    today = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('add_grower.html', today_date=today)

@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if not db_manager: return "数据库未连接。", 500
    if request.method == 'POST':
        try:
            data = { 'date': request.form['date'], 'client_name': request.form['client_name'].strip(), 'spec': request.form['spec'].strip(), 'pieces': int(request.form['pieces']), 'weight': float(request.form['weight']), 'unit_price': float(request.form['unit_price']), 'notes': request.form.get('notes', '').strip() }
            if not data['client_name'] or not data['spec']: return "客户名称和规格不能为空！", 400
            data['total_amount'] = round(data['pieces'] * data['weight'] * data['unit_price'], 2)
            db_manager.add_record('client_records', data)
            return redirect(url_for('clients_page'))
        except (ValueError, TypeError) as e: return f"数据格式错误: {e}", 400
    today = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('add_client.html', today_date=today)

@app.route('/edit_grower/<int:record_id>', methods=['GET', 'POST'])
def edit_grower(record_id):
    if not db_manager: return "数据库未连接。", 500
    if request.method == 'POST':
        try:
            data = { 'date': request.form['date'], 'grower_name': request.form['grower_name'].strip(), 'spec': request.form['spec'].strip(), 'gross_weight': float(request.form['gross_weight']), 'secondary_fruit': float(request.form.get('secondary_fruit', 0)), 'tare_weight': float(request.form.get('tare_weight', 0)), 'unit_price': float(request.form['unit_price']), 'notes': request.form.get('notes', '').strip() }
            data['net_weight'] = data['gross_weight'] - data['secondary_fruit'] - data['tare_weight']
            data['total_amount'] = round(data['net_weight'] * data['unit_price'], 2)
            db_manager.update_record('grower_records', record_id, data)
            return redirect(url_for('index'))
        except (ValueError, TypeError) as e: return f"数据格式错误: {e}", 400
    response = db_manager.supabase.table('grower_records').select("*").eq('id', record_id).single().execute()
    return render_template('edit_grower.html', record=response.data)

@app.route('/edit_client/<int:record_id>', methods=['GET', 'POST'])
def edit_client(record_id):
    if not db_manager: return "数据库未连接。", 500
    if request.method == 'POST':
        try:
            data = { 'date': request.form['date'], 'client_name': request.form['client_name'].strip(), 'spec': request.form['spec'].strip(), 'pieces': int(request.form['pieces']), 'weight': float(request.form['weight']), 'unit_price': float(request.form['unit_price']), 'notes': request.form.get('notes', '').strip() }
            data['total_amount'] = round(data['pieces'] * data['weight'] * data['unit_price'], 2)
            db_manager.update_record('client_records', record_id, data)
            return redirect(url_for('clients_page'))
        except (ValueError, TypeError) as e: return f"数据格式错误: {e}", 400
    response = db_manager.supabase.table('client_records').select("*").eq('id', record_id).single().execute()
    return render_template('edit_client.html', record=response.data)

@app.route('/delete_grower/<int:record_id>', methods=['POST'])
def delete_grower(record_id):
    if not db_manager: return "数据库未连接。", 500
    db_manager.delete_record('grower_records', record_id)
    return redirect(url_for('index'))

@app.route('/delete_client/<int:record_id>', methods=['POST'])
def delete_client(record_id):
    if not db_manager: return "数据库未连接。", 500
    db_manager.delete_record('client_records', record_id)
    return redirect(url_for('clients_page'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)