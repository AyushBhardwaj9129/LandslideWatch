import os
 
target_dir = os.path.join("app", "api", "v1")
 
for root, dirs, files in os.walk(target_dir):
    for f in sorted(files):
        if f.endswith(".py"):
            path = os.path.join(root, f)
            print(f"===== {path} =====")
            with open(path, "r", encoding="utf-8") as file:
                print(file.read())
            print()
 