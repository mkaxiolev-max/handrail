import rumps
import json
import subprocess
from pathlib import Path

def run_cli(args):
    cmd = ["python", "-m", "handrail.cli"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return {"ok": False, "stderr": p.stderr, "stdout": p.stdout}
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "stdout": p.stdout}

class HandrailMenu(rumps.App):
    def __init__(self):
        super().__init__("🔗", quit_button="Quit Handrail")
        self.menu = ["Doctor", "Validate", None, "Open DB Folder"]
        self.refresh(None)

    @rumps.timer(60)
    def refresh(self, _):
        rep = run_cli(["validate"])
        self.title = "✅ Handrail" if rep.get("valid") else "⚠️ Handrail"

    @rumps.clicked("Doctor")
    def doctor(self, _):
        rep = run_cli(["doctor"])
        rumps.alert("Handrail Doctor", "", json.dumps(rep, indent=2)[:2000])

    @rumps.clicked("Validate")
    def validate(self, _):
        rep = run_cli(["validate"])
        rumps.alert("Handrail Validate", "", json.dumps(rep, indent=2)[:2000])
        self.refresh(None)

    @rumps.clicked("Open DB Folder")
    def open_db_folder(self, _):
        p = Path.home() / "Library" / "Application Support" / "Handrail"
        subprocess.run(["open", str(p)])

if __name__ == "__main__":
    HandrailMenu().run()
