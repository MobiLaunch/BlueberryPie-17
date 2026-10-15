"""Window operations the bridge accepts. Kept apart from `windows` so the command-line
parser can list them without importing the whole window module."""
OPERATIONS = ("focus", "close", "minimize", "restore", "maximize", "float", "snap-left", "snap-right")
