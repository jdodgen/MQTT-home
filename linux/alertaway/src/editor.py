import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import toml
import os

class TOMLEditor(tk.Tk):
    def __init__(self, file_list):
        super().__init__()
        self.title("TOML File Editor")
        self.geometry("800x600")
        self.file_list = file_list
        self.current_file = None

        # Text Area
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, undo=True)
        self.text_area.pack(expand=True, fill='both')

        # Menu Bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open File from List", command=self.open_file_dialog)
        self.file_menu.add_command(label="Save", command=self.save_file)

        # Basic Tag Configuration for Syntax Highlighting
        self.text_area.tag_config('key', foreground='blue')
        self.text_area.tag_config('string', foreground='red')
        self.text_area.tag_config('comment', foreground='green')
        self.text_area.tag_config('table', foreground='purple', font=('Arial', 10, 'bold'))

    def open_file_dialog(self):
        # In a real app, you might use a listbox, here using askopenfilename
        file_path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select TOML file",
                                               filetypes=(("TOML files", "*.toml"), ("all files", "*.*")))
        if file_path and os.path.basename(file_path) in self.file_list:
            self.load_file(file_path)
        elif file_path:
            messagebox.showerror("Error", "Selected file is not in the specified list.")

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', content)
            self.current_file = file_path
            self.colorize_toml()
        except Exception as e:
            messagebox.showerror("Error loading file", f"Could not load file: {e}")

    def save_file(self):
        if not self.current_file:
            messagebox.showerror("Error", "No file currently loaded.")
            return

        content = self.text_area.get('1.0', tk.END)
        if self.validate_toml(content):
            try:
                # Use toml.dump to format and save the content (requires dict input)
                # Alternative: write the raw string if you trust the user input
                data = toml.loads(content)
                with open(self.current_file, 'w') as f:
                    toml.dump(data, f)
                messagebox.showinfo("Success", "File saved and validated successfully.")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save file: {e}")
        else:
            messagebox.showerror("Validation Error", "Cannot save file: Invalid TOML format.")

    def validate_toml(self, content):
        try:
            toml.loads(content)
            return True
        except toml.TomlDecodeError as e:
            # Display error message for user
            messagebox.showerror("TOML Validation Failed", f"Error: {e}")
            return False

    def colorize_toml(self):
        # Basic syntax highlighting function using tags
        self.text_area.tag_remove("key", "1.0", tk.END)
        self.text_area.tag_remove("string", "1.0", tk.END)
        self.text_area.tag_remove("comment", "1.0", tk.END)
        self.text_area.tag_remove("table", "1.0", tk.END)

        content = self.text_area.get('1.0', tk.END).splitlines()
        for i, line in enumerate(content):
            line_num = i + 1
            # Highlight comments
            if '#' in line:
                comment_start = line.find('#')
                self.text_area.tag_add("comment", f"{line_num}.{comment_start}", f"{line_num}.{len(line)}")

            # Highlight tables (e.g., [section] or [[section.subsection]])
            if line.strip().startswith('[') and line.strip().endswith(']'):
                self.text_area.tag_add("table", f"{line_num}.0", f"{line_num}.{len(line)}")

            # Highlight keys and strings (basic key="value" or key='value')
            if '=' in line and not line.strip().startswith('#'):
                parts = line.split('=', 1)
                key = parts[0].strip()
                self.text_area.tag_add("key", f"{line_num}.{line.find(key)}", f"{line_num}.{line.find(key) + len(key)}")

                value_part = parts[1].strip()
                if value_part.startswith('"') or value_part.startswith("'"):
                    # Basic string highlight: start from first quote to end of line
                    string_start = line.find(value_part[0], line.find('=') + 1)
                    self.text_area.tag_add("string", f"{line_num}.{string_start}", f"{line_num}.{len(line)}")


if __name__ == "__main__":
    # Example list of valid files in your application
    # Ensure these files exist for the example to work
    valid_files = ["config.toml", "settings.toml"]
    
    # Create dummy TOML files for testing if they don't exist
    for f in valid_files:
        if not os.path.exists(f):
            with open(f, 'w') as df:
                df.write(f"[{f.split('.')[0]}]\nkey = \"value\"\n# This is a comment\n")

    editor = TOMLEditor(valid_files)
    editor.mainloop()
