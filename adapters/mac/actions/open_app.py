import subprocess
def execute(app_name):
    try:
        subprocess.run(['open', '-a', app_name], timeout=2, check=True)
        return {'ok': True, 'app': app_name}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
