def extract_main_items():
    # Set to store unique items
    main_items = set()
    
    # Read keywords.txt and extract items
    with open('keywords.txt', 'r') as f:
        lines = f.readlines()
        
        # Process each line
        for line in lines:
            line = line.strip()
            # Skip empty lines and category headers
            if not line or line in ('Truck:', 'Van:', 'Truck Accesories:', 'Van Accessories:', '4x4:', '4x4 Accessories:'):
                continue
                
            # Remove any trailing colons and clean up the item name
            item = line.split(':')[0].strip()
            # Remove any trailing dash and description (e.g., "- Short", "- Front")
            if ' - ' in item:
                item = item.split(' - ')[0].strip()
            
            # Skip category words
            if item.lower() in ('truck', 'van', 'accessory', 'accessories'):
                continue
                
            if item:
                main_items.add(item)

    # Read existing items from materials.txt to avoid duplicates
    existing_items = set()
    try:
        with open('materials.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    existing_items.add(line[1:-1])
    except FileNotFoundError:
        pass

    # Find new items that aren't in materials.txt
    new_items = main_items - existing_items

    print(f"Found {len(new_items)} new items to add:")
    for item in sorted(new_items):
        print(f"- {item}")

    # If there are new items, append them to materials.txt
    if new_items:
        with open('materials.txt', 'a') as f:
            for item in sorted(new_items):
                f.write(f'\n[{item}]\n')
                f.write('Aluminum\n')  # Default materials as placeholders
                f.write('Steel\n\n')

if __name__ == '__main__':
    extract_main_items()
    print("\nFinished extracting main items to materials.txt")
