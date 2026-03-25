import subprocess, json
def execute():
    try:
        cmd = 'osascript -e "tell application \"System Events\" to get name of window 1 of (first application process whose frontmost is true)"'
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
        return {'ok': True, 'focused_window': r.stdout.strip()}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
