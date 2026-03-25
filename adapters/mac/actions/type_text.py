import subprocess
def execute(text):
    try:
        cmd = f'osascript -e "tell application \"System Events\" to keystroke \\"{text}\\""'
        subprocess.run(cmd, shell=True, timeout=2, check=True)
        return {'ok': True, 'typed': text}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
