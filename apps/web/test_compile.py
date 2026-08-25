import os
import subprocess
import sys

apps_web = r"c:\Obsidian\proyectos\Trading\01 Ultrarentable\apps\web"
traderbot_nm = r"C:\Users\yo\Documents\TRADERBOT\node_modules"
target_nm = os.path.join(apps_web, "node_modules")

if not os.path.exists(target_nm):
    try:
        # Create directory junction on Windows
        subprocess.run(f'mklink /J "{target_nm}" "{traderbot_nm}"', shell=True, check=True)
        print("Created node_modules junction successfully.")
    except Exception as e:
        print("Error creating junction:", e)

# Run tsc directly via node
tsc_path = os.path.join(traderbot_nm, "typescript", "bin", "tsc")
cmd = ["node", tsc_path, "--noEmit"]
print("Running:", " ".join(cmd), "in", apps_web)
p = subprocess.run(cmd, cwd=apps_web, capture_output=True, text=True)

print("Return code:", p.returncode)
print("STDOUT:\n", p.stdout)
print("STDERR:\n", p.stderr)

with open(os.path.join(apps_web, "tsc_result.txt"), "w", encoding="utf-8") as f:
    f.write(f"RETURN_CODE={p.returncode}\n")
    f.write(f"STDOUT:\n{p.stdout}\n")
    f.write(f"STDERR:\n{p.stderr}\n")
