import sqlite3
import os

def split_database(original_db='newspapers.db', num_splits=4):
    # 连接原始数据库
    conn = sqlite3.connect(original_db)
    cursor = conn.cursor()
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM titles")
    total_rows = cursor.fetchone()[0]
    rows_per_split = total_rows // num_splits
    remainder = total_rows % num_splits
    
    # 获取所有 papers 数据
    cursor.execute("SELECT * FROM papers")
    papers_data = cursor.fetchall()
    
    # 获取所有 titles 数据并按 date 排序（可选，按其他字段也可）
    cursor.execute("SELECT * FROM titles ORDER BY date")
    all_titles = cursor.fetchall()
    
    # 创建 4 个新数据库
    for i in range(num_splits):
        split_db_name = f'newspapers_part_{i+1}.db'
        if os.path.exists(split_db_name):
            os.remove(split_db_name)
        
        split_conn = sqlite3.connect(split_db_name)
        split_cursor = split_conn.cursor()
        
        # 创建表结构
        split_cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                paper_id TEXT PRIMARY KEY,
                paper_name TEXT NOT NULL
            )
        ''')
        split_cursor.execute('''
            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT,
                date TEXT,
                page INTEGER,
                title TEXT,
                url TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (paper_id)
            )
        ''')
        
        # 插入 papers 数据（每个数据库都需要完整的 papers 表）
        split_cursor.executemany("INSERT INTO papers VALUES (?, ?)", papers_data)
        
        # 计算当前分片的记录范围
        start_idx = i * rows_per_split
        end_idx = start_idx + rows_per_split + (1 if i < remainder else 0)
        split_titles = all_titles[start_idx:end_idx]
        
        # 插入 titles 数据
        split_cursor.executemany("INSERT INTO titles (id, paper_id, date, page, title, url) VALUES (?, ?, ?, ?, ?, ?)", split_titles)
        
        # 提交并关闭
        split_conn.commit()
        split_conn.close()
    
    conn.close()
    print(f"Database split into {num_splits} parts: newspapers_part_1.db to newspapers_part_{num_splits}.db")

if __name__ == "__main__":
    split_database()