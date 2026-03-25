import subprocess
def execute(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return {'ok': True, 'returncode': r.returncode, 'stdout': r.stdout[:1000], 'stderr': r.stderr[:500]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
