import ast
import os
import sys


def extract_imports_from_file(file_path):
    """Parses a Python file and extracts top-level module imports."""
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            # Handles: import x, y, z
            if isinstance(node, ast.Import):
                for name in node.names:
                    base_module = name.name.split(".")[0]
                    imports.add(base_module)
            # Handles: from x import y
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:  # Absolute imports only
                    base_module = node.module.split(".")[0]
                    imports.add(base_module)
    except (SyntaxError, ValueError) as e:
        print(f"Skipping {file_path} due to parsing error: {e}", file=sys.stderr)

    return imports


def scan_directory_and_generate_requirements(target_dir):
    """Scans Python files, filters out standard library modules, and saves requirements.txt."""
    all_imports = set()
    file_count = 0

    print(f"Scanning directory: {os.path.abspath(target_dir)}\n")

    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py"):
                # Avoid analyzing this script itself
                if file == os.path.basename(__file__):
                    continue
                # Skip files containing the string "dodgen"
                if "dodgen" in file:
                    continue
                if "Dodgen" in file:
                    continue
                file_path = os.path.join(root, file)
                file_count += 1
                all_imports.update(extract_imports_from_file(file_path))

    # Fetch built-in standard library modules available in Python 3.10+
    stdlib_names = getattr(sys, "stdlib_module_names", set(["os", "sys", "time", "json", "math", "re"]))

    third_party_or_local = []

    for imp in all_imports:
        if imp not in stdlib_names and imp != "":
            third_party_or_local.append(imp)

    sorted_requirements = sorted(third_party_or_local)

    print(f"Analyzed {file_count} Python files.")
    print("-" * 50)
    print(f"Found {len(sorted_requirements)} external package imports.")

    # Write out the requirements.txt file
    output_file = "requirements.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for item in sorted_requirements:
                f.write(f"{item}\n")
        print(f"✅ Successfully created: {os.path.abspath(output_file)}")
        print("-" * 50)
        print("File contents:")
        for item in sorted_requirements:
            print(f"  {item}")
    except IOError as e:
        print(f"❌ Error writing requirements.txt: {e}", file=sys.stderr)


if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_directory_and_generate_requirements("../")
