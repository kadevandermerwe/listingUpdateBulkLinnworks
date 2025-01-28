def check_duplicates():
    # Dictionary to store items and their line numbers
    items = {}
    similar_items = {}
    
    with open('materials.txt', 'r') as f:
        lines = f.readlines()
        
    current_item = None
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            current_item = line[1:-1]
            # Check for exact duplicates
            if current_item in items:
                print(f"Duplicate item found: '{current_item}'")
                print(f"  First occurrence: line {items[current_item]}")
                print(f"  Second occurrence: line {i}")
            else:
                items[current_item] = i
                
            # Check for similar items (case insensitive, plurals)
            lower_item = current_item.lower()
            for existing_item in items:
                if current_item != existing_item:  # Skip exact matches
                    lower_existing = existing_item.lower()
                    # Check for plurals and case differences
                    if (lower_item.rstrip('s') == lower_existing.rstrip('s') or
                        lower_item == lower_existing):
                        if lower_item not in similar_items:
                            similar_items[lower_item] = []
                        similar_items[lower_item].append((existing_item, items[existing_item]))
                        similar_items[lower_item].append((current_item, i))

    if similar_items:
        print("\nPotentially similar items found:")
        for _, occurrences in similar_items.items():
            # Remove duplicates while preserving order
            seen = set()
            unique_occurrences = []
            for item in occurrences:
                if item[0] not in seen:
                    seen.add(item[0])
                    unique_occurrences.append(item)
            
            if len(unique_occurrences) > 1:
                print("\nSimilar items:")
                for item, line_num in unique_occurrences:
                    print(f"  '{item}' on line {line_num}")

if __name__ == '__main__':
    check_duplicates()
