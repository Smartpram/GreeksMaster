import zipfile
import os

# Extract
z = zipfile.ZipFile('SecurityMaster.zip')
z.extractall()

# List files
print("Files extracted:")
for f in os.listdir():
    if 'Master' in f or 'Scrip' in f:
        print(f"  {f}")

# Read first file with header
nse_file = 'NSEScripMaster.txt'
if os.path.exists(nse_file):
    print(f"\nReading {nse_file}...")
    with open(nse_file, 'r', encoding='utf-8', errors='ignore') as f:
        for i in range(5):
            line = f.readline()
            print(f"Line {i}: {line[:200]}")
            if i == 0:
                # Try to parse header
                parts = line.strip().split('|')
                print(f"\nHeader columns ({len(parts)}):")
                for j, col in enumerate(parts[:10]):
                    print(f"  {j}: {col}")
                break
