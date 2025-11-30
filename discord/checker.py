import subprocess, sys, json

result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True).stdout

result = result.replace("'",'"')
result = json.loads(result)

for event in result:
    new_vals = []
    if 'actual' in event:
        new_vals.append((event['actual'], 'actual'))
    if 'forecast' in event: 
        new_vals.append((event['forecast'], 'forecast'))
    if 'previous' in event: 
        new_vals.append((event['previous'], 'previous'))
    
    print(new_vals, "<-- new vals")



print(type(result))
print(result)
print(result[0], type(result[0]))
