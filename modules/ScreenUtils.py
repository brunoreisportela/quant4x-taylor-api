import platform
import subprocess
import ctypes

class ScreenUtils:
    def maximize_console_window(self):
        os_name = platform.system()

        if os_name == "Windows":
            # Windows-specific maximization
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            SW_MAXIMIZE = 3
            hWnd = kernel32.GetConsoleWindow()
            user32.ShowWindow(hWnd, SW_MAXIMIZE)
        
        elif os_name == "Darwin":
            # macOS-specific maximization using AppleScript
            script = """
            tell application "Terminal"
                activate
                tell application "System Events" to keystroke "m" using {command down, control down}
            end tell
            """
            subprocess.run(["osascript", "-e", script])
        
        elif os_name == "Linux":
            # Example for Linux, using xdotool (make sure it's installed)
            # This is less reliable and might need adjustments based on the terminal emulator.
            try:
                subprocess.run(["xdotool", "search", "--name", "terminal", "windowsize", "100%", "100%"])
            except FileNotFoundError:
                print("xdotool not found. Please install xdotool for window management.")
        else:
            print(f"OS {os_name} not recognized. Skipping window maximization.")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximize_console_window()