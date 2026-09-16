import json
from collections import Counter

with open("landcover_raw.json", "r") as f:
    data = json.load(f)

elements = data["elements"]
print("Total features:", len(elements))

# Count how many times each tag key/value combo appears
tag_counts = Counter()

for el in elements:
    tags = el.get("tags", {})
    for key in ["landuse", "natural", "leisure"]:
        if key in tags:
            tag_counts[f"{key}={tags[key]}"] += 1

print("\nTag value breakdown:")
for tag, count in tag_counts.most_common():
    print(f"  {tag}: {count}")