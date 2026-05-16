from pathlib import Path
import runpy

def main():
    script = Path(__file__).resolve().parents[2] / "scripts" / "arc_apache.py"
    ns = runpy.run_path(str(script))
    return ns["main"]()
