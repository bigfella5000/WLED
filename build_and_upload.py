import subprocess
import requests
import sys
import os

IP = "192.168.1.133"
ENV = "xiao_esp32c3_wled_fix"
PIO = os.path.expanduser("~\\.platformio\\penv\\Scripts\\platformio.exe")

def get_bin_path():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    )
    branch = result.stdout.strip()
    
    if branch == "0_15_x":
        return "build_output/release/WLED_0.15.6-beta_ESP32-C3.bin"
    else:
        # glob for any matching bin so it works across dev version bumps
        import glob
        matches = glob.glob("build_output/release/WLED_*_ESP32-C3.bin")
        if not matches:
            print("No ESP32-C3 bin found in build_output/release/")
            sys.exit(1)
        # sort by modification time, take newest
        return max(matches, key=os.path.getmtime)

print("Building firmware...")
result = subprocess.run(
    [PIO, "run", "-e", ENV],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

if result.returncode != 0:
    print("Build failed, aborting upload.")
    sys.exit(1)

BIN = get_bin_path()
print(f"\nUploading {BIN} to {IP}...")
with open(BIN, "rb") as f:
    data = f.read()

try:
    r = requests.post(
        f"http://{IP}/update",
        files={"file": ("firmware.bin", data, "application/octet-stream")},
        timeout=60
    )
    print(f"Response: {r.status_code} {r.text}")
except requests.exceptions.Timeout:
    print("Upload timed out — ESP may be rebooting, that's normal.")
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")