try:
    from plyer import filechooser

    def select_song_folder():
        """Opens a dialog to select the song folder using plyer."""
        try:
            path = filechooser.choose_dir(title="Select Song Folder")
            if path:
                return path[0]
        except Exception as e:
            print(f"Plyer file chooser failed: {e}. Falling back to tkinter.")
            return _select_song_folder_tkinter()
        return None

except ImportError:
    print("Plyer not available. Falling back to tkinter for folder selection.")
    
    def select_song_folder():
        """Fallback function when plyer is not available."""
        return _select_song_folder_tkinter()


def _select_song_folder_tkinter():
    """Opens a dialog to select the song folder using tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        folder_path = filedialog.askdirectory(title="Select Song Folder")
        root.destroy()
        return folder_path
    except ImportError:
        print("tkinter is not available, cannot open file dialog.")
        return None
