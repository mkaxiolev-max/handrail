import subprocess, json
def execute():
    try:
        cmd = 'osascript -e "tell application \"System Events\" to get name of every window of every process"'
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
        windows = r.stdout.strip().split(', ') if r.stdout else []
        return {'ok': True, 'windows': windows, 'count': len(windows)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
