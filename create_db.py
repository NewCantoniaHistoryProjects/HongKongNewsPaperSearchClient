# scan_newspapers_to_sqlite.py
import os
import re
import sqlite3
from tqdm import tqdm

def scan_newspapers_to_db(root_dir, db_path='newspapers.db', batch_size=1000):
    # 连接数据库
    conn = sqlite3.connect(db_path)
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
    
    # 文件名正则表达式
    pattern = r'^([A-Za-z]+)(\d{8}|\d{6})\.txt$'
    
    # 计算总文件数以初始化进度条
    total_files = 0
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        if os.path.isdir(folder_path):
            total_files += sum(1 for filename in os.listdir(folder_path) if re.match(pattern, filename))
    
    # 初始化批处理数据
    papers_data = []
    titles_data = []
    files_processed = 0
    
    # 使用 tqdm 创建进度条
    print("Processing files and building database...")
    with tqdm(total=total_files, desc="Progress", unit="file") as pbar:
        for folder_name in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder_name)
            if os.path.isdir(folder_path):
                for filename in os.listdir(folder_path):
                    match = re.match(pattern, filename)
                    if match:
                        paper_id = match.group(1)
                        date_str = match.group(2)
                        file_path = os.path.join(folder_path, filename)
                        
                        # 收集 papers 数据
                        papers_data.append((paper_id, folder_name))
                        
                        # 读取并处理文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines:
                                if line.strip():
                                    parts = line.strip().split('\t', 1)
                                    if len(parts) == 2:
                                        page_str, title = parts
                                        try:
                                            page_num = int(page_str.split()[1]) 
                                            url = f'https://archive.org/details/{paper_id}{date_str}'
                                            titles_data.append((paper_id, date_str, page_num, title, url))
                                        except ValueError as e:
                                            print(f"Warning: Skipping malformed line in '{filename}': {line.strip()} (Error: {e})")
                                    else:
                                        print(f"Warning: Skipping malformed line in '{filename}': {line.strip()}")
                        
                        files_processed += 1
                        pbar.update(1)
                        
                        # 每处理 batch_size 个文件提交一次
                        if files_processed % batch_size == 0:
                            print(f"Committing batch of {batch_size} files (total processed: {files_processed})...")
                            cursor.executemany('INSERT OR IGNORE INTO papers VALUES (?, ?)', papers_data)
                            cursor.executemany('INSERT INTO titles (paper_id, date, page, title, url) VALUES (?, ?, ?, ?, ?)', titles_data)
                            conn.commit()
                            papers_data = []  # 清空批处理数据
                            titles_data = []
    
    # 提交剩余的数据
    if papers_data or titles_data:
        print(f"Committing final batch (remaining {files_processed % batch_size or batch_size} files)...")
        cursor.executemany('INSERT OR IGNORE INTO papers VALUES (?, ?)', papers_data)
        cursor.executemany('INSERT INTO titles (paper_id, date, page, title, url) VALUES (?, ?, ?, ?, ?)', titles_data)
        conn.commit()
    
    # 关闭数据库
    conn.close()
    print(f"\nDatabase creation completed: Saved to '{db_path}'")

if __name__ == "__main__":
    root_dir = r'hknewspaper_title/'
    scan_newspapers_to_db(root_dir, batch_size=1000)