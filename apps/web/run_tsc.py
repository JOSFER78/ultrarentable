import subprocess
import sys
import os

print("Python version:", sys.version)
cwd = r"c:\Obsidian\proyectos\Trading\01 Ultrarentable\apps\web"
print("Working directory:", cwd)

# Try running npx tsc --noEmit
try:
    p = subprocess.run(["npx", "tsc", "--noEmit"], cwd=cwd, capture_output=True, text=True, shell=True)
    print("TSC Exit Code:", p.returncode)
    print("STDOUT:\n", p.stdout)
    print("STDERR:\n", p.stderr)
    with open(r"c:\Obsidian\proyectos\Trading\01 Ultrarentable\apps\web\tsc_output.txt", "w", encoding="utf-8") as f:
        f.write(f"EXIT_CODE: {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
except Exception as e:
    print("Error executing npx tsc:", e)
    with open(r"c:\Obsidian\proyectos\Trading\01 Ultrarentable\apps\web\tsc_output.txt", "w", encoding="utf-8") as f:
        f.write(f"EXCEPTION: {e}")
