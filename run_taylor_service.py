import subprocess

def run_application():
    while True:
        try:
            process = subprocess.Popen(f'TaylorService.exe', shell=True)
            process.wait()
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_application()