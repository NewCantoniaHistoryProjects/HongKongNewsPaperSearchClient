# newspaper_search_client.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from threading import Thread

class NewspaperSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Newspaper Search")
        self.root.geometry("1200x600")
        
        # Database connection
        self.conn = sqlite3.connect('newspapers.db', check_same_thread=False)
        self.conn.create_function("REGEXP", 2, self.regexp)
        self.cursor = self.conn.cursor()
        
        # Create search history table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
        # Search Frame
        search_frame = ttk.LabelFrame(root, text="Search Options")
        search_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='ew')
        
        tk.Label(search_frame, text="Search Keyword:").grid(row=0, column=0, padx=5, pady=5)
        self.search_history = self.load_search_history()
        self.search_combo = ttk.Combobox(search_frame, values=self.search_history, width=50)
        self.search_combo.grid(row=0, column=1, padx=5, pady=5)
        self.search_combo.bind('<Return>', lambda event: self.search())
        
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        tk.Checkbutton(search_frame, text="Whole Word", variable=self.whole_word_var).grid(row=0, column=2, padx=5, pady=5)
        tk.Checkbutton(search_frame, text="Regular Expression", variable=self.regex_var).grid(row=0, column=3, padx=5, pady=5)
        
        # Date Range
        self.load_date_ranges()
        tk.Label(root, text="Start Date:").grid(row=1, column=0, padx=5, pady=5)
        self.start_year = ttk.Combobox(root, values=self.years, width=6)
        self.start_year.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.start_month = ttk.Combobox(root, values=[''] + self.months, width=4)
        self.start_month.grid(row=1, column=1, padx=(70, 5), pady=5, sticky='w')
        self.start_year.set(self.years[0])
        self.start_month.set('')
        tk.Button(root, text="Clear", command=self.clear_start_date).grid(row=1, column=1, padx=(120, 5), pady=5, sticky='w')
        
        tk.Label(root, text="End Date:").grid(row=2, column=0, padx=5, pady=5)
        self.end_year = ttk.Combobox(root, values=self.years, width=6)
        self.end_year.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.end_month = ttk.Combobox(root, values=[''] + self.months, width=4)
        self.end_month.grid(row=2, column=1, padx=(70, 5), pady=5, sticky='w')
        self.end_year.set(self.years[-1])
        self.end_month.set('')
        tk.Button(root, text="Clear", command=self.clear_end_date).grid(row=2, column=1, padx=(120, 5), pady=5, sticky='w')
        
        # Newspaper Selection
        tk.Label(root, text="Newspapers:").grid(row=3, column=0, padx=5, pady=5)
        self.paper_frame = ttk.Frame(root)
        self.paper_frame.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.paper_vars = {}
        self.load_paper_checkboxes()
        
        tk.Button(self.paper_frame, text="Select All", command=self.select_all).grid(row=0, column=3, padx=5)
        tk.Button(self.paper_frame, text="Invert Selection", command=self.invert_selection).grid(row=1, column=3, padx=5)
        
        # Search Button and Sort Toggle
        self.search_button = tk.Button(root, text="Search", command=self.start_search)
        self.search_button.grid(row=4, column=1, padx=5, pady=5)
        self.sort_asc = tk.BooleanVar(value=True)
        tk.Button(root, text="Toggle Sort Order", command=self.toggle_sort).grid(row=4, column=2, padx=5, pady=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(root, mode='determinate', maximum=100)
        self.progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky='ew')
        self.progress.grid_remove()
        
        # Results Listbox with Microsoft YaHei font
        self.results_listbox = tk.Listbox(root, height=20, width=100, font=("Microsoft YaHei", 10))
        self.results_listbox.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')
        
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.results_listbox.yview)
        scrollbar.grid(row=6, column=3, sticky='ns')
        self.results_listbox.configure(yscrollcommand=scrollbar.set)
        self.results_listbox.bind('<Double-1>', self.handle_click)
        
        self.results = []  # Store results with metadata
        
        root.grid_rowconfigure(6, weight=1)
        root.grid_columnconfigure(1, weight=1)
    
    def regexp(self, expr, item):
        return re.search(expr, item, re.IGNORECASE) is not None
    
    def load_date_ranges(self):
        self.cursor.execute('SELECT DISTINCT SUBSTR(date, 1, 4) FROM titles ORDER BY date')
        self.years = [row[0] for row in self.cursor.fetchall()]
        self.months = [f'{i:02d}' for i in range(1, 13)]
    
    def load_paper_checkboxes(self):
        self.cursor.execute('SELECT paper_name FROM papers')
        paper_names = [row[0] for row in self.cursor.fetchall()]
        for i, name in enumerate(paper_names):
            var = tk.BooleanVar(value=False)
            self.paper_vars[name] = var
            cb = tk.Checkbutton(self.paper_frame, text=name, variable=var)
            cb.grid(row=i//3, column=i%3, sticky='w')
    
    def load_search_history(self):
        self.cursor.execute('SELECT query FROM search_history ORDER BY timestamp DESC LIMIT 10')
        return [row[0] for row in self.cursor.fetchall()]
    
    def update_search_history(self, query):
        if not query or query in self.search_history:
            return
        self.cursor.execute('INSERT INTO search_history (query) VALUES (?)', (query,))
        self.cursor.execute('DELETE FROM search_history WHERE id IN (SELECT id FROM search_history ORDER BY timestamp ASC LIMIT -1 OFFSET 10)')
        self.conn.commit()
        self.search_history = self.load_search_history()
        self.search_combo['values'] = self.search_history
        self.search_combo.set(query)
    
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
    
    def start_search(self):
        """Start search in a separate thread"""
        self.search_button.config(state='disabled')
        self.results_listbox.delete(0, tk.END)
        self.results = []
        Thread(target=self.search, daemon=True).start()
    
    def search(self):
        query = self.search_combo.get().strip()
        start_year = self.start_year.get()
        start_month = self.start_month.get()
        end_year = self.end_year.get()
        end_month = self.end_month.get()
        selected_papers = [name for name, var in self.paper_vars.items() if var.get()]
        
        if not selected_papers:
            self.root.after(0, lambda: messagebox.showwarning("Warning", "Please select at least one newspaper."))
            self.root.after(0, lambda: self.search_button.config(state='normal'))
            return
        
        start_date = start_year + (start_month if start_month else '01') + '01'
        end_date = end_year + (end_month if end_month else '12') + '31'
        
        sql = '''
            SELECT t.paper_id, p.paper_name, t.date, t.page, t.title, t.url
            FROM titles t
            JOIN papers p ON t.paper_id = p.paper_id
            WHERE t.date >= ? AND t.date <= ?
        '''
        params = [start_date, end_date]
        
        if selected_papers:
            placeholders = ','.join('?' for _ in selected_papers)
            sql += f' AND p.paper_name IN ({placeholders})'
            params.extend(selected_papers)
        
        if query:
            self.update_search_history(query)
            if self.regex_var.get():
                try:
                    re.compile(query)
                    sql += ' AND t.title REGEXP ?'
                    params.append(query)
                except re.error:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid regular expression."))
                    self.root.after(0, lambda: self.search_button.config(state='normal'))
                    return
            elif self.whole_word_var.get():
                sql += ' AND UPPER(t.title) LIKE UPPER(?)'
                params.append(f'% {query} %')
            elif query.startswith('"') and query.endswith('"'):
                sql += ' AND t.title = ?'
                params.append(query[1:-1])
            else:
                sql += ' AND UPPER(t.title) LIKE UPPER(?)'
                params.append(f'%{query}%')
        
        sql += ' ORDER BY t.date' + (' ASC' if self.sort_asc.get() else ' DESC') + ', t.page ASC'
        
        self.root.after(0, lambda: self.progress.grid())
        self.root.after(0, lambda: self.progress.configure(value=0))
        
        try:
            count_sql = f'SELECT COUNT(*) FROM ({sql})'
            self.cursor.execute(count_sql, params)
            total_rows = self.cursor.fetchone()[0]
            
            if total_rows == 0:
                self.root.after(0, lambda: self.results_listbox.insert(tk.END, "No results found."))
                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(0, lambda: self.progress.grid_remove())
                self.root.after(0, lambda: self.search_button.config(state='normal'))
                return
            
            # Fetch in chunks
            chunk_size = 100
            offset = 0
            current_key = None
            
            while offset < total_rows:
                chunk_sql = sql + f' LIMIT {chunk_size} OFFSET {offset}'
                self.cursor.execute(chunk_sql, params)
                chunk = self.cursor.fetchall()
                
                for row in chunk:
                    paper_id, paper_name, date, page, title, url = row
                    key = (paper_name, date)
                    
                    if key != current_key:
                        line = f"{paper_name} - {date} [Open]"
                        self.root.after(0, lambda l=line: self.results_listbox.insert(tk.END, l))
                        self.results.append(('header', url, None))
                        current_key = key
                    
                    display_title = f"- Page {page:2d} {title}"
                    self.root.after(0, lambda dt=display_title: self.results_listbox.insert(tk.END, dt))
                    self.results.append(('title', url, page))
                
                offset += chunk_size
                progress = (offset / total_rows) * 100 if offset < total_rows else 100
                self.root.after(0, lambda p=progress: self.progress.configure(value=p))
            
            self.root.after(0, lambda: self.progress.grid_remove())
            self.root.after(0, lambda: self.search_button.config(state='normal'))
        except sqlite3.Error as e:
            self.root.after(0, lambda msg=str(e): messagebox.showerror("Database Error", f"Error executing query: {msg}"))
            self.root.after(0, lambda: self.progress.grid_remove())
            self.root.after(0, lambda: self.search_button.config(state='normal'))
    
    def toggle_sort(self):
        self.sort_asc.set(not self.sort_asc.get())
        self.start_search()
    
    def handle_click(self, event):
        index = self.results_listbox.nearest(event.y)
        if index >= 0 and index < len(self.results):
            item_type, url, page = self.results[index]
            if item_type == 'header':
                webbrowser.open(url)
            elif item_type == 'title' and page is not None:
                webbrowser.open(f'{url}/page/n{page}')
    
    def __del__(self):
        self.conn.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = NewspaperSearchApp(root)
    root.mainloop()