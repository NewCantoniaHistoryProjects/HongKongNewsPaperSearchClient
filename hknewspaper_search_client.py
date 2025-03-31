# newspaper_search_client.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

class NewspaperSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Newspaper Search")
        self.root.geometry("1200x600")
        
        self.conn = sqlite3.connect('newspapers.db')
        self.cursor = self.conn.cursor()
        
        # 搜尋框
        tk.Label(root, text="Search Keyword:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_entry.bind('<Return>', lambda event: self.search())  # 綁定回車鍵
        
        # 日期範圍（年份和月份下拉選單）
        self.load_date_ranges()  # 從數據庫加載日期範圍
        
        tk.Label(root, text="Start Date:").grid(row=1, column=0, padx=5, pady=5)
        self.start_year = ttk.Combobox(root, values=self.years, width=6)
        self.start_year.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.start_month = ttk.Combobox(root, values=[''] + self.months, width=4)
        self.start_month.grid(row=1, column=1, padx=(70, 5), pady=5, sticky='w')
        self.start_year.set(self.years[0])  # 默認選最早年份
        self.start_month.set('')  # 默認不選月份
        tk.Button(root, text="Clear", command=self.clear_start_date).grid(row=1, column=1, padx=(120, 5), pady=5, sticky='w')
        
        tk.Label(root, text="End Date:").grid(row=2, column=0, padx=5, pady=5)
        self.end_year = ttk.Combobox(root, values=self.years, width=6)
        self.end_year.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.end_month = ttk.Combobox(root, values=[''] + self.months, width=4)
        self.end_month.grid(row=2, column=1, padx=(70, 5), pady=5, sticky='w')
        self.end_year.set(self.years[-1])  # 默認選最晚年份
        self.end_month.set('')  # 默認不選月份
        tk.Button(root, text="Clear", command=self.clear_end_date).grid(row=2, column=1, padx=(120, 5), pady=5, sticky='w')
        
        # 報紙選擇
        tk.Label(root, text="Newspapers:").grid(row=3, column=0, padx=5, pady=5)
        self.paper_frame = ttk.Frame(root)
        self.paper_frame.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.paper_vars = {}
        self.paper_checkboxes = {}
        self.load_paper_checkboxes()
        
        # 全選和反選按鈕
        tk.Button(self.paper_frame, text="Select All", command=self.select_all).grid(row=0, column=3, padx=5)
        tk.Button(self.paper_frame, text="Invert Selection", command=self.invert_selection).grid(row=1, column=3, padx=5)
        
        # 搜尋按鈕
        self.search_button = tk.Button(root, text="Search", command=self.search)
        self.search_button.grid(row=4, column=1, padx=5, pady=5)
        
        # 排序切換
        self.sort_asc = tk.BooleanVar(value=True)
        tk.Button(root, text="Toggle Sort Order", command=self.toggle_sort).grid(row=4, column=2, padx=5, pady=5)
        
        # 結果顯示
        self.results_tree = ttk.Treeview(root, columns=('Paper', 'Date', 'Page', 'Title'), show='headings')
        self.results_tree.heading('Paper', text='Newspaper')
        self.results_tree.heading('Date', text='Date')
        self.results_tree.heading('Page', text='Page')
        self.results_tree.heading('Title', text='Title')
        self.results_tree.column('Paper', width=150)
        self.results_tree.column('Date', width=100)
        self.results_tree.column('Page', width=50)
        self.results_tree.column('Title', width=400)
        self.results_tree.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')
        
        # 滾動條
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.results_tree.yview)
        scrollbar.grid(row=5, column=3, sticky='ns')
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # 雙擊事件
        self.results_tree.bind('<Double-1>', self.open_url)
        
        # 調整佈局
        root.grid_rowconfigure(5, weight=1)
        root.grid_columnconfigure(1, weight=1)
    
    def load_date_ranges(self):
        self.cursor.execute('SELECT DISTINCT SUBSTR(date, 1, 4) FROM titles ORDER BY date')
        self.years = [row[0] for row in self.cursor.fetchall()]
        self.months = [f'{i:02d}' for i in range(1, 13)]  # 01-12
    
    def load_paper_checkboxes(self):
        self.cursor.execute('SELECT paper_name FROM papers')
        paper_names = [row[0] for row in self.cursor.fetchall()]
        for i, name in enumerate(paper_names):
            var = tk.BooleanVar(value=False)  # 默認不選中
            self.paper_vars[name] = var
            cb = tk.Checkbutton(self.paper_frame, text=name, variable=var)
            cb.grid(row=i//3, column=i%3, sticky='w')
            self.paper_checkboxes[name] = cb
    
    def select_all(self):
        for var in self.paper_vars.values():
            var.set(True)
    
    def invert_selection(self):
        for var in self.paper_vars.values():
            var.set(not var.get())
    
    def clear_start_date(self):
        self.start_year.set(self.years[0])
        self.start_month.set('')
    
    def clear_end_date(self):
        self.end_year.set(self.years[-1])
        self.end_month.set('')
    
    def search(self):
        query = self.search_entry.get().strip()
        start_year = self.start_year.get()
        start_month = self.start_month.get()
        end_year = self.end_year.get()
        end_month = self.end_month.get()
        selected_papers = [name for name, var in self.paper_vars.items() if var.get()]
        
        if not selected_papers:
            messagebox.showwarning("Warning", "Please select at least one newspaper.")
            return
        
        # 構建日期範圍，默認從最早到最晚
        if not start_year and not start_month:
            start_date = self.years[0] + '01'
        else:
            start_date = start_year + (start_month if start_month else '01')
        
        if not end_year and not end_month:
            end_date = self.years[-1] + '12'
        else:
            end_date = end_year + (end_month if end_month else '12')
        
        # 如果數據是 YYYYMMDD 格式，補全日期
        if len(start_date) == 6:
            start_date += '01'
        if len(end_date) == 6:
            end_date += '31'
        
        sql = '''
            SELECT t.paper_id, p.paper_name, t.date, t.page, t.title, t.url
            FROM titles t
            JOIN papers p ON t.paper_id = p.paper_id
            WHERE 1=1
        '''
        params = []
        
        if query:
            if query.startswith('"') and query.endswith('"'):
                # 精確匹配（使用引號）
                sql += ' AND t.title = ?'
                params.append(query[1:-1])
            else:
                # 模糊匹配（不使用引號），大小寫不敏感
                sql += ' AND UPPER(t.title) LIKE UPPER(?)'
                params.append(f'%{query}%')
        
        sql += ' AND t.date >= ?'
        params.append(start_date)
        sql += ' AND t.date <= ?'
        params.append(end_date)
        
        if selected_papers:
            placeholders = ','.join('?' for _ in selected_papers)
            sql += f' AND p.paper_name IN ({placeholders})'
            params.extend(selected_papers)
        
        sql += ' ORDER BY t.date' + (' ASC' if self.sort_asc.get() else ' DESC')
        try:
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error executing query: {str(e)}")
            return
        
        self.results_tree.delete(*self.results_tree.get_children())
        for result in results:
            paper_id, paper_name, date, page, title, url = result
            self.results_tree.insert('', 'end', values=(paper_name, date, page, title), tags=(url,))
    
    def toggle_sort(self):
        self.sort_asc.set(not self.sort_asc.get())
        self.search()
    
    def open_url(self, event):
        item = self.results_tree.selection()[0]
        url = self.results_tree.item(item, 'tags')[0]
        page = self.results_tree.item(item, 'values')[2]
        webbrowser.open(f'{url}/page/n{page}')
    
    def __del__(self):
        self.conn.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = NewspaperSearchApp(root)
    root.mainloop()