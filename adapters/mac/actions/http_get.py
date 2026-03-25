import subprocess, json
def execute(url):
    try:
        r = subprocess.run(['curl', '-sf', '--max-time', '5', url], capture_output=True, text=True, timeout=6)
        return {'ok': True, 'status': 200, 'url': url, 'body': r.stdout[:500]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
