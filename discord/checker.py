import subprocess, sys

result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True).stdout

print(result)
