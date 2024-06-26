import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
from datetime import datetime
import glob

class FileManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Файловий менеджер")
        self.master.geometry("800x600")

        self.create_widgets()
        self.populate_drives()

    def create_widgets(self):
        drive_frame = ttk.Frame(self.master)
        drive_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(drive_frame, text="Диск:").pack(side=tk.LEFT)
        self.drive_combo = ttk.Combobox(drive_frame, state="readonly")
        self.drive_combo.pack(side=tk.LEFT)
        self.drive_combo.bind("<<ComboboxSelected>>", self.on_drive_select)

        self.drive_info = ttk.Label(drive_frame, text="")
        self.drive_info.pack(side=tk.LEFT, padx=10)

        # Фрейм для відображення дерева папок і списку файлів
        main_frame = ttk.Frame(self.master)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Дерево папок
        self.dir_tree = ttk.Treeview(main_frame)
        self.dir_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.dir_tree.bind("<<TreeviewSelect>>", self.on_dir_select)
        self.dir_tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

        # Список файлів
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        ttk.Label(file_frame, text="Розширення:").pack(fill=tk.X)
        self.ext_combo = ttk.Combobox(file_frame, state="readonly")
        self.ext_combo.pack(fill=tk.X)
        self.ext_combo.bind("<<ComboboxSelected>>", self.filter_files)

        self.file_list = tk.Listbox(file_frame)
        self.file_list.pack(expand=True, fill=tk.BOTH)
        self.file_list.bind("<<ListboxSelect>>", self.show_file_info)

        # Інформація про файл
        self.file_info = ttk.Label(file_frame, text="")
        self.file_info.pack(fill=tk.X)

        # Кнопки для операцій з файлами
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Видалити", command=self.delete_file).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Перейменувати", command=self.rename_file).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Змінити розширення", command=self.change_extension).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Пошук", command=self.open_search_window).pack(side=tk.LEFT)

    def populate_drives(self):
        drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
        self.drive_combo['values'] = drives
        if drives:
            self.drive_combo.set(drives[0])
            self.on_drive_select()

    def on_drive_select(self, event=None):
        selected_drive = self.drive_combo.get()
        self.populate_dir_tree(selected_drive)
        self.update_drive_info(selected_drive)

    def populate_dir_tree(self, path):
        self.dir_tree.delete(*self.dir_tree.get_children())
        self.add_directory_to_tree("", path)

    def add_directory_to_tree(self, parent, path, depth=0):
        if depth > 5:  # Обмежуємо глибину рекурсії
            return
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        folder = self.dir_tree.insert(parent, 'end', text=item, open=False)
                        # Додаємо фіктивний елемент, щоб показати, що папка може бути розгорнута
                        self.dir_tree.insert(folder, 'end')
                    except tk.TclError:
                        # Ігноруємо помилки Tcl, які можуть виникнути при роботі з деревом
                        pass
        except PermissionError:
            # Ігноруємо папки, до яких немає доступу
            pass
        except OSError:
            # Ігноруємо інші помилки операційної системи
            pass

    def on_tree_expand(self, event):
        item = self.dir_tree.focus()
        if self.dir_tree.parent(item):  # Не обробляємо кореневий елемент
            children = self.dir_tree.get_children(item)
            if children and self.dir_tree.item(children[0])["text"] == "":
                # Видаляємо фіктивний елемент
                self.dir_tree.delete(children[0])
                # Заповнюємо папку реальним вмістом
                path = self.get_full_path(item)
                self.add_directory_to_tree(item, path)

    def get_full_path(self, item):
        path = self.dir_tree.item(item, "text")
        parent = self.dir_tree.parent(item)
        while parent:
            path = os.path.join(self.dir_tree.item(parent, "text"), path)
            parent = self.dir_tree.parent(parent)
        return os.path.join(self.drive_combo.get(), path)

    def update_drive_info(self, drive):
        try:
            total, used, free = shutil.disk_usage(drive)
            info = f"Всього: {self.format_size(total)}, Використано: {self.format_size(used)}, Вільно: {self.format_size(free)}"
            self.drive_info.config(text=info)
        except:
            self.drive_info.config(text="Не вдалося отримати інформацію про диск")

    def on_dir_select(self, event):
        selected_item = self.dir_tree.focus()
        if selected_item:
            path = self.get_full_path(selected_item)
            self.populate_file_list(path)
            self.update_folder_info(path)

    def populate_file_list(self, path):
        self.file_list.delete(0, tk.END)
        self.ext_combo.set('')
        extensions = set()
        try:
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)):
                    self.file_list.insert(tk.END, file)
                    _, ext = os.path.splitext(file)
                    if ext:
                        extensions.add(ext)
        except PermissionError:
            messagebox.showerror("Помилка", "Немає доступу до цієї папки")
        self.ext_combo['values'] = list(extensions)

    def filter_files(self, event=None):
        selected_ext = self.ext_combo.get()
        self.file_list.delete(0, tk.END)
        path = self.get_full_path(self.dir_tree.focus())
        for file in os.listdir(path):
            if file.endswith(selected_ext):
                self.file_list.insert(tk.END, file)

    def show_file_info(self, event):
        selected_indices = self.file_list.curselection()
        if selected_indices:
            file_name = self.file_list.get(selected_indices[0])
            path = os.path.join(self.get_full_path(self.dir_tree.focus()), file_name)
            try:
                stat = os.stat(path)
                info = f"Ім'я: {file_name}\n"
                info += f"Розмір: {self.format_size(stat.st_size)}\n"
                info += f"Створено: {datetime.fromtimestamp(stat.st_ctime)}\n"
                info += f"Змінено: {datetime.fromtimestamp(stat.st_mtime)}\n"
                info += f"Атрибути: {self.get_file_attributes(stat.st_mode)}"
                self.file_info.config(text=info)
            except FileNotFoundError:
                self.file_info.config(text="Файл не знайдено")

    def update_folder_info(self, path):
        try:
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files)
            info = f"Файлів: {len(files)}, Загальний розмір: {self.format_size(total_size)}"
            self.file_info.config(text=info)
        except PermissionError:
            self.file_info.config(text="Немає доступу до цієї папки")

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    @staticmethod
    def get_file_attributes(mode):
        attributes = []
        if mode & 0o100000:  # Звичайний файл
            attributes.append('звичайний файл')
        if mode & 0o040000:  # Каталог
            attributes.append('каталог')
        if mode & 0o020000:  # Символьний пристрій
            attributes.append('символьний пристрій')
        if mode & 0o060000:  # Блоковий пристрій
            attributes.append('блоковий пристрій')
        if mode & 0o010000:  # FIFO
            attributes.append('FIFO')
        if mode & 0o140000:  # Сокет
            attributes.append('сокет')
        if mode & 0o120000:  # Символьне посилання
            attributes.append('символьне посилання')
        return ', '.join(attributes)

    def delete_file(self):
        selected_indices = self.file_list.curselection()
        if selected_indices:
            file_name = self.file_list.get(selected_indices[0])
            path = os.path.join(self.get_full_path(self.dir_tree.focus()), file_name)
            if messagebox.askyesno("Підтвердження", f"Ви впевнені, що хочете видалити {file_name}?"):
                try:
                    os.remove(path)
                    self.populate_file_list(self.get_full_path(self.dir_tree.focus()))
                except PermissionError:
                    messagebox.showerror("Помилка", "Немає прав для видалення файлу")
                except FileNotFoundError:
                    messagebox.showerror("Помилка", "Файл не знайдено")

    def rename_file(self):
        selected_indices = self.file_list.curselection()
        if selected_indices:
            old_name = self.file_list.get(selected_indices[0])
            old_path = os.path.join(self.get_full_path(self.dir_tree.focus()), old_name)
            new_name = filedialog.asksaveasfilename(initialdir=self.get_full_path(self.dir_tree.focus()),
                                                    initialfile=old_name,
                                                    title="Перейменувати файл")
            if new_name:
                try:
                    os.rename(old_path, new_name)
                    self.populate_file_list(self.get_full_path(self.dir_tree.focus()))
                except PermissionError:
                    messagebox.showerror("Помилка", "Немає прав для перейменування файлу")
                except FileNotFoundError:
                    messagebox.showerror("Помилка", "Файл не знайдено")

    def change_extension(self):
        selected_indices = self.file_list.curselection()
        if selected_indices:
            file_name = self.file_list.get(selected_indices[0])
            name, ext = os.path.splitext(file_name)
            new_ext = filedialog.asksaveasfilename(initialdir=self.get_full_path(self.dir_tree.focus()),
                                                   initialfile=name,
                                                   title="Змінити розширення")
            if new_ext:
                old_path = os.path.join(self.get_full_path(self.dir_tree.focus()), file_name)
                new_path = new_ext
                try:
                    os.rename(old_path, new_path)
                    self.populate_file_list(self.get_full_path(self.dir_tree.focus()))
                except PermissionError:
                    messagebox.showerror("Помилка", "Немає прав для зміни розширення файлу")
                except FileNotFoundError:
                    messagebox.showerror("Помилка", "Файл не знайдено")

    def open_search_window(self):
        search_window = tk.Toplevel(self.master)
        search_window.title("Пошук файлів")
        search_window.geometry("400x300")

        ttk.Label(search_window, text="Шаблон імені:").pack()
        name_pattern = ttk.Entry(search_window)
        name_pattern.pack()

        ttk.Label(search_window, text="Розмір (байт):").pack()
        size_entry = ttk.Entry(search_window)
        size_entry.pack()

        ttk.Label(search_window, text="Дата створення (YYYY-MM-DD):").pack()
        date_entry = ttk.Entry(search_window)
        date_entry.pack()

        ttk.Button(search_window, text="Пошук", command=lambda: self.search_files(
            self.get_full_path(self.dir_tree.focus()),
            name_pattern.get(),
            size_entry.get(),
            date_entry.get(),
            search_window
        )).pack()

        self.search_results = tk.Listbox(search_window)
        self.search_results.pack(expand=True, fill=tk.BOTH)

    def search_files(self, path, name_pattern, size, date, window):
        self.search_results.delete(0, tk.END)
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.match_criteria(file_path, name_pattern, size, date):
                    self.search_results.insert(tk.END, file_path)

    def match_criteria(self, file_path, name_pattern, size, date):
        if name_pattern and not glob.fnmatch.fnmatch(os.path.basename(file_path), name_pattern):
            return False
        if size:
            try:
                if os.path.getsize(file_path) != int(size):
                    return False
            except ValueError:
                return False
        if date:
            try:
                file_date = datetime.fromtimestamp(os.path.getctime(file_path)).date()
                search_date = datetime.strptime(date, "%Y-%m-%d").date()
                if file_date != search_date:
                    return False
            except ValueError:
                return False
        return True
    # Методи для операцій з файлами (видалення, перейменування, зміна розширення) та пошуку
    # можна додати тут...

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManager(root)
    root.mainloop()