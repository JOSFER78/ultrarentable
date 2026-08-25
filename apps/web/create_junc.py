import os
import sys
import _winapi

apps_web = r"c:\Obsidian\proyectos\Trading\01 Ultrarentable\apps\web"
traderbot_nm = r"C:\Users\yo\Documents\TRADERBOT\node_modules"
target_nm = os.path.join(apps_web, "node_modules")

if not os.path.exists(target_nm):
    try:
        _winapi.CreateJunction(traderbot_nm, target_nm)
        print("Created junction via _winapi.")
    except Exception as e:
        print("Junction error:", e)

# Write output directly
log_file = os.path.join(apps_web, "direct_out.txt")
with open(log_file, "w", encoding="utf-8") as f:
    f.write("Junction done. Ready for tsc.")
