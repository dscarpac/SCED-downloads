import json
from pathlib import Path

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR.parent / "downloadable"
SEARCH_TEXT = "-- Utility memory bag by Directsun"

# We go up twice to the 'git' folder, then down into 'SCED'
MB_SCRIPT_FILE = SCRIPT_DIR.parents[1] / "SCED" / "src" / "MemoryBag.ttslua"
MB_WRAPPER_FILE = SCRIPT_DIR / "memory-bag-template.ttslua"

class TTSUpdater:
    def __init__(self, search_text, script_path, wrapper_path):
        self.search_text = search_text
        # Generate the full Lua string once at the start
        # Python's json.dump will handle the escaping later!
        script_content = script_path.read_text(encoding="utf-8")
        self.replacement_content = wrapper_path.read_text(encoding="utf-8").replace(
            "--<<PLACEHOLDER>>", script_content
        )

    def process_node(self, node):
        """Recursively searches for 'LuaScript' keys."""
        changed = False

        if isinstance(node, dict):
            if "LuaScript" in node and isinstance(node["LuaScript"], str):
                if self.search_text in node["LuaScript"]:
                    node["LuaScript"] = self.replacement_content
                    changed = True

            for value in node.values():
                if self.process_node(value):
                    changed = True

        elif isinstance(node, list):
            for item in node:
                if self.process_node(item):
                    changed = True

        return changed

    def run(self, target_dir):
        if not target_dir.exists():
            print(f"Error: {target_dir} not found.")
            return

        for file_path in target_dir.rglob("*.json"):
            try:
                # Load the JSON object
                data = json.loads(file_path.read_text(encoding="utf-8"))

                if self.process_node(data):
                    print(f"Updating: {file_path.relative_to(target_dir.parent)}")
                    # json.dumps automatically escapes newlines into \n
                    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            except (json.JSONDecodeError, IOError) as e:
                print(f"Skipping {file_path.name} due to error: {e}")


if __name__ == "__main__":
    updater = TTSUpdater(SEARCH_TEXT, MB_SCRIPT_FILE, MB_WRAPPER_FILE)
    updater.run(INPUT_DIR)
    print("\nProcess complete.")
