import subprocess
import argparse
import time
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", default="C:\\MT4", help="Set MT4 main path")

args = parser.parse_args()

mt_path = args.path

def run_application(path_param):
    while True:
        try:
            # Replace 'your_app.exe' with the name of your executable file
            # Use f-string to format the command with the provided path_param
            process = subprocess.Popen(f'quant4x-monitoring.exe -p "{path_param}"', shell=True)
            process.wait()
            
        except Exception as e:
            print(f"Error: {e}")
        # Adjust the sleep time as needed; this determines how often the application will be restarted

        time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the path parameter.")
    else:
        run_application(mt_path)