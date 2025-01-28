def consolidate_materials():
    # Read all lines
    with open('materials.txt', 'r') as f:
        lines = f.readlines()
    
    # Process the file
    consolidated = []
    current_item = None
    current_materials = []
    items_seen = set()
    
    for line in lines:
        line = line.strip()
        if not line:  # Keep blank lines
            if current_item:
                # Add current item and its materials before blank line
                consolidated.extend([f'[{current_item}]'] + current_materials + [''])
                current_item = None
                current_materials = []
            consolidated.append('')
        elif line.startswith('[') and line.endswith(']'):
            if current_item:  # Save previous item if exists
                consolidated.extend([f'[{current_item}]'] + current_materials + [''])
                current_materials = []
            
            # Get new item name and convert to singular
            item = line[1:-1]
            item = item.strip()
            # Convert to title case for consistency
            item = ' '.join(word.capitalize() for word in item.split())
            # Convert to singular if plural
            if item.lower().endswith('s') and not item.lower().endswith('ss'):  # avoid words like 'glass'
                item = item[:-1]
            
            # Skip if we've seen this item before
            singular_form = item.lower()
            if singular_form not in items_seen:
                items_seen.add(singular_form)
                current_item = item
            else:
                current_item = None
        elif current_item:  # Material line
            current_materials.append(line)
    
    # Add the last item if exists
    if current_item:
        consolidated.extend([f'[{current_item}]'] + current_materials)
    
    # Write back to file
    with open('materials.txt', 'w') as f:
        f.write('\n'.join(consolidated))

if __name__ == '__main__':
    consolidate_materials()
    print("Materials file has been consolidated to singular forms.")
