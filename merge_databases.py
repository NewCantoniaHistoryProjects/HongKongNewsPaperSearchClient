import sqlite3
import os

def merge_databases(output_db='newspapers.db', num_splits=4):
    # 如果目标数据库已存在，先删除
    if os.path.exists(output_db):
        os.remove(output_db)
    
    # 创建目标数据库
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # 创建表结构
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            paper_name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_titles_title ON titles (title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_titles_date ON titles (date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_titles_paper_id ON titles (paper_id)')
    
    # 合并数据
    for i in range(num_splits):
        split_db_name = f'newspapers_part_{i+1}.db'
        if not os.path.exists(split_db_name):
            print(f"Warning: {split_db_name} not found, skipping...")
            continue
        
        # 连接分片数据库
        split_conn = sqlite3.connect(split_db_name)
        split_cursor = split_conn.cursor()
        
        # 合并 papers 表（仅插入不重复的记录）
        split_cursor.execute("SELECT * FROM papers")
        papers_data = split_cursor.fetchall()
        cursor.executemany("INSERT OR IGNORE INTO papers VALUES (?, ?)", papers_data)
        
        # 合并 titles 表
        split_cursor.execute("SELECT paper_id, date, page, title, url FROM titles")
        titles_data = split_cursor.fetchall()
        cursor.executemany("INSERT INTO titles (paper_id, date, page, title, url) VALUES (?, ?, ?, ?, ?)", titles_data)
        
        split_conn.close()
    
    # 提交并关闭
    conn.commit()
    conn.close()
    print(f"Merged {num_splits} parts into {output_db}")

if __name__ == "__main__":
    merge_databases()