import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--account_id", default="2", help="Account ID")
args = parser.parse_args()

ACCOUNT_ID = int(args.account_id)

def run_application():
    while True:
        try:
            process = subprocess.Popen(f'market_sentiment.exe', shell=True)
            process.wait()
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_application()