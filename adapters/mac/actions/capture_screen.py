import subprocess, os
def execute(output_path='/tmp/screenshot.png'):
    try:
        subprocess.run(['screencapture', '-x', output_path], timeout=3, check=True)
        return {'ok': True, 'file': output_path, 'size': os.path.getsize(output_path)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
