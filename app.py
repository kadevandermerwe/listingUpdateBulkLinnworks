from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import os
import re
import json
import requests
import openpyxl as px
import logging
import datetime

# Set up logging
logging.basicConfig(
    filename='title_processing.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    filemode='w'  # Overwrite the file each time
)

def log_debug(msg):
    """Write debug message to log file"""
    logging.debug(msg)
    print(msg)  # Also print to console

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['DROPBOX_URL'] = 'https://www.dropbox.com/scl/fi/h52wh2zokq6j055tag5c2/SKU-Creator-Formating-MONSTER-COPY.xlsx?rlkey=r3r0ocp8lggvbx2zs1xnogvcp&e=2&st=bmf5lxzo&dl=1'

#global variable for storing possible years 
yearsList = [str(year) for year in range(1900, 2025)]

class VehicleQuery:
    def __init__(self):
        self.makes = []
        self.models = []
        self.makes_models_map = {}  # Dictionary to store make->models mapping
        self.model_type_map = {}    # Dictionary to store model->type mapping
        self.all_terms = set()      # Set of all terms to match (makes, models, and combinations)

    def load_makes_and_models(self, dropbox_url):
        """
        Load makes and models from the Excel file.
        """
        # Ensure the upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Temporary file path for the downloaded file
        xlfile_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_file.xlsx')

        # Download the file from Dropbox
        try:
            response = requests.get(dropbox_url)
            if response.status_code == 200:
                with open(xlfile_path, 'wb') as temp_file:
                    temp_file.write(response.content)
                log_debug("File downloaded successfully from Dropbox.")
            else:
                raise Exception(f"Failed to download file. Status code: {response.status_code}")
        except Exception as e:
            log_debug(f"Error downloading the file from Dropbox: {e}")
            return

        try:
            # Read the Excel file
            df = pd.read_excel(xlfile_path)
            log_debug(f"Excel file loaded with {len(df)} rows")
            
            # Initialize sets for makes and models
            makes = set()
            models = set()
            makes_models = {}
            model_types = {}  # New dictionary for model->type mapping
            all_terms = set()  # Set to store all possible terms to match

            # Process each row
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row[0]):
                    continue

                # Clean the data
                make = str(row[0]).strip() if pd.notna(row[0]) else None
                model = str(row[1]).strip() if pd.notna(row[1]) else None
                vehicle_type = str(row[2]).strip() if pd.notna(row[2]) else '4x4'  # Default to 4x4 if not specified

                if make and model:
                    log_debug(f"Processing make: '{make}', model: '{model}'")
                    
                    # Add complete make and model terms
                    makes.add(make)
                    makes.add(make.lower())
                    models.add(model)
                    models.add(model.lower())
                    
                    # Add make+model combinations
                    make_model = f"{make} {model}"
                    all_terms.add(make_model.lower())
                    log_debug(f"Added make+model combination: '{make_model.lower()}'")
                    
                    # Add complete terms only
                    all_terms.add(make.lower())
                    all_terms.add(model.lower())
                    log_debug(f"Added complete terms: '{make.lower()}', '{model.lower()}'")
                    
                    # Update makes_models mapping
                    if make not in makes_models:
                        makes_models[make] = set()
                    makes_models[make].add(model)
                    
                    # Also add lowercase mapping
                    if make.lower() not in makes_models:
                        makes_models[make.lower()] = set()
                    makes_models[make.lower()].add(model.lower())
                    
                    # Store the vehicle type for this model (both normal and lowercase)
                    model_types[model] = vehicle_type
                    model_types[model.lower()] = vehicle_type

            # Update class attributes
            self.makes = sorted(list(makes))
            self.models = sorted(list(models))
            self.makes_models_map = {make: sorted(list(models)) for make, models in makes_models.items()}
            self.model_type_map = model_types
            self.all_terms = all_terms

            log_debug(f"Loaded {len(self.makes)} makes and {len(self.models)} models successfully")
            log_debug(f"Total matchable terms: {len(self.all_terms)}")
            log_debug("All loaded terms:")
            for term in sorted(self.all_terms):
                log_debug(f"  - {term}")

        except Exception as e:
            log_debug(f"Error processing Excel file: {e}")
            raise

def load_makes_models():
    """Load makes and models from the CSV files"""
    makes = set()
    models = set()
    
    try:
        # Load makes
        if os.path.exists('makes.csv'):
            with open('makes.csv', 'r') as f:
                for line in f:
                    make = line.strip()
                    if make:
                        makes.add(make)
        
        # Load models
        if os.path.exists('models.csv'):
            with open('models.csv', 'r') as f:
                for line in f:
                    model = line.strip()
                    if model:
                        models.add(model)
    except Exception as e:
        print(f"Error loading makes/models: {e}")
    
    return makes, models

def remove_existing_make_model(title, makes, models):
    """Remove existing make, model, and year from the title"""
    log_debug(f"\nRemoving make/model/year from title: '{title}'")
    
    # First, find and remove any existing make/model after "for", "to fit", or "compatible with"
    title_lower = title.lower()
    prefixes = ["for", "to fit", "compatible with"]
    
    # Find the first prefix and its position
    first_prefix_pos = len(title)  # Default to end of string
    found_prefix = None
    for prefix in prefixes:
        pos = title_lower.find(prefix)
        if pos != -1 and pos < first_prefix_pos:
            first_prefix_pos = pos
            found_prefix = prefix
    
    # If we found a prefix, remove everything after it
    if found_prefix:
        title = title[:first_prefix_pos].strip()
        log_debug(f"Removed text after '{found_prefix}': '{title}'")
    
    # Now process any remaining make/model mentions in the main part
    # First try to match longer terms before shorter ones
    result = title
    result_lower = result.lower()
    
    if vehicle_query_instance.all_terms:
        # Sort terms by length (longest first) to ensure we match longer terms before shorter ones
        sorted_terms = sorted(vehicle_query_instance.all_terms, key=len, reverse=True)
        
        for term in sorted_terms:
            # Look for the term with word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, result_lower):
                # Find the actual case-preserved term in the original text
                matches = re.finditer(pattern, result_lower)
                # Convert to list to get all matches
                matches = list(matches)
                # Process matches in reverse order to not affect positions of earlier matches
                for match in reversed(matches):
                    start, end = match.span()
                    log_debug(f"Found make/model match: '{result[start:end]}'")
                    # Remove the term and any extra spaces
                    result = result[:start].rstrip() + " " + result[end:].lstrip()
                    result = result.strip()
                    # Update lowercase version for next iteration
                    result_lower = result.lower()
    
    # Remove years (YYYY or YY format) and pre/post indicators
    year_pattern = r'\b(19|20)\d{2}\b|\b\d{2}\b|\bpre\b|\bpost\b'
    result = re.sub(year_pattern, '', result, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    result = ' '.join(result.split())
    
    log_debug(f"Final title after make/model/year removal: '{result}'")
    return result.strip()

def load_vehicle_keywords():
    """Load keywords for each vehicle type and specific items from keywords.txt"""
    keywords = {
        '4x4': {
            'general': ['4x4', 'Car', 'Accessories', 'Accessory', 'Styling']
        },
        'truck': {
            'general': ['Truck', 'Accessory', 'Accessories']
        },
        'van': {
            'general': ['Van', 'Accessory', 'Accessories']
        }
    }
    
    current_type = None
    current_section = None
    
    try:
        with open('keywords.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
        for line in lines:
            # Skip empty lines
            if not line:
                continue
                
            # Check if this is a vehicle type line (e.g., "4x4:")
            if line.lower().rstrip(':') in ['4x4', 'truck', 'van']:
                current_type = line.lower().rstrip(':')
                current_section = None
                # Add any general keywords that appear right after the vehicle type
                continue
                
            # Check if this is an accessories section (e.g., "4x4 Accessories:")
            if line.lower().endswith('accessories:'):
                current_section = 'accessories'
                continue
                
            # Process general keywords if we're not in accessories section
            if current_type and current_section is None:
                # Add to general keywords
                keywords[current_type]['general'].append(line.strip())
                continue
                
            # Process items within the accessories section
            if current_type and current_section == 'accessories':
                # Check if line contains item-specific keywords (has a colon)
                if ':' in line:
                    item, keywords_str = line.split(':', 1)
                    item = item.strip()
                    # Split keywords by comma and strip whitespace
                    item_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    keywords[current_type][item] = item_keywords
                else:
                    # Items without keywords
                    item = line.strip()
                    keywords[current_type][item] = []
    
    except Exception as e:
        log_debug(f"Error loading keywords: {str(e)}")
        # Return default keywords if there's an error
        return keywords
    
    log_debug(f"Loaded keywords: {keywords}")
    return keywords

def find_matching_item(main_item, vehicle_type, keywords):
    """Find the matching item in the keywords dictionary and its specific keywords"""
    # Convert vehicle_type to lowercase for case-insensitive matching
    vehicle_type = vehicle_type.lower()
    
    # If vehicle type not in keywords, default to '4x4'
    if vehicle_type not in keywords:
        vehicle_type = '4x4'
    
    # Get the keywords dictionary for this vehicle type
    vehicle_keywords = keywords[vehicle_type]
    
    # Normalize the main item name
    main_item = normalize_item_name(main_item)
    
    # Find the best matching item
    best_match = None
    best_match_keywords = []
    
    # Check each item in the keywords
    for item in vehicle_keywords:
        if item != 'general':  # Skip the general keywords
            # Normalize the item name from keywords
            normalized_item = normalize_item_name(item)
            
            # If we find a match
            if normalized_item in main_item or main_item in normalized_item:
                # If we haven't found a match yet, or this match is longer
                if not best_match or len(normalized_item) > len(normalize_item_name(best_match)):
                    best_match = item
                    best_match_keywords = vehicle_keywords[item]
    
    return best_match, best_match_keywords

def normalize_item_name(name):
    """Normalize an item name for better matching"""
    # Remove common variations and clean up the name
    name = name.lower()
    name = name.replace('-', ' ').replace('/', ' ').replace('+', ' ')
    name = name.replace('(', '').replace(')', '')
    name = name.replace('f&r', '').replace('x1', '')
    
    # Remove common suffixes/prefixes that might interfere with matching
    suffixes = [' - full set', ' - front', ' - rear', ' - short']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    return name.strip()

def extract_main_item_and_extras(title):
    """Extract the main item and any additional items from a title"""
    log_debug(f"\nProcessing title: '{title}'")
    
    # Remove any color at the end (- BLACK)
    title = re.sub(r'\s*-\s*(black|chrome|silver)\s*$', '', title, flags=re.IGNORECASE)
    
    # Split on + but keep the + symbol
    parts = re.split(r'\s*\+\s*', title)
    
    # The first part is the main item
    main_part = parts[0].strip()
    log_debug(f"Main part: '{main_part}'")
    
    # Remove any text after "for", "to fit", or "compatible with" from main part
    prefixes = ["for", "to fit", "compatible with"]
    for prefix in prefixes:
        if prefix in main_part.lower():
            main_part = main_part[:main_part.lower().index(prefix)].strip()
            break
    
    # The main item is everything up to any connector words
    main_item = main_part
    log_debug(f"Main item: '{main_item}'")
    
    # Any remaining parts are extras
    extras = parts[1:] if len(parts) > 1 else []
    log_debug(f"Extras: {extras}")
    
    return main_item, extras

def detect_vehicle_type(title):
    """Detect the vehicle type from the title"""
    title = title.lower()
    if 'van' in title:
        return 'van'
    elif 'truck' in title:
        return 'truck'
    else:
        return '4x4'

def load_item_materials():
    """Load materials for each item type from materials.txt"""
    materials = {}
    current_item = None
    
    try:
        with open('materials.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                # Check if this is an item header
                if line.startswith('[') and line.endswith(']'):
                    current_item = line[1:-1]  # Remove brackets
                    materials[current_item] = []
                elif current_item:  # This is a material for the current item
                    materials[current_item].append(line)
                    
        return materials
    except Exception as e:
        log_debug(f"Error loading materials: {str(e)}")
        return {}

def get_item_materials(item_type, materials_dict):
    """Get materials for a specific item type"""
    if not item_type:
        return []
        
    # Try exact match first
    if item_type in materials_dict:
        return materials_dict[item_type]
        
    # Try case-insensitive match
    item_lower = item_type.lower()
    for key in materials_dict:
        if key.lower() == item_lower:
            return materials_dict[key]
            
    return []

def format_title_with_keywords(title, make, model, year, material=None, wheelbase=None, cab_type=None, channel='ebay1', vehicle_type='4x4'):
    """Common function to format title with keywords"""
    log_debug(f"\nStarting title formatting with input: '{title}'")
    log_debug(f"Make: {make}, Model: {model}, Year: {year}, Vehicle Type: {vehicle_type}")
    
    # First, remove any existing make/model from the title
    try:
        if not vehicle_query_instance.makes or not vehicle_query_instance.models:
            vehicle_query_instance.load_makes_and_models(app.config['DROPBOX_URL'])
        title = remove_existing_make_model(title, vehicle_query_instance.makes, vehicle_query_instance.models)
        log_debug(f"Title after removing make/model: '{title}'")
    except Exception as e:
        log_debug(f"Error loading makes/models from Dropbox: {str(e)}")
        title = remove_existing_make_model(title, [], [])

    # Extract main item and extras
    main_item, extras = extract_main_item_and_extras(title)
    
    # Load keywords based on the vehicle type from form data
    keywords = load_vehicle_keywords()
    log_debug(f"Using vehicle type from form data: {vehicle_type}")
    
    # Load materials
    materials_dict = load_item_materials()
    
    # Start building the formatted title
    components = []
    log_debug("\nBuilding title components:")
    
    # Add color if present
    color_match = re.search(r'black|chrome|silver', title.lower())
    if color_match:
        color = color_match.group().upper()
        components.append(color)
        title = re.sub(r'(?i)' + color_match.group(), '', title).strip()
        main_item = re.sub(r'(?i)' + color_match.group(), '', main_item).strip()
        log_debug(f"Added color: {color}")
    
    # Add Bragan for Amazon
    if channel == 'amazon':
        components.append("Bragan")
        log_debug("Added Bragan")
    
    # Add main item and extras
    item_type = None
    for item in ["Grill Bar", "Side Bar", "Side Step", "Roof Bar", "Running Board", "Bull Bar", "Bumper Bar", "Window Deflector"]:
        if item.lower() in main_item.lower():
            item_type = item
            main_item = re.sub(r'(?i)' + re.escape(item), '', main_item).strip()
            break
    
    if item_type:
        components.append(item_type)
        log_debug(f"Added item type: {item_type}")
    
    if main_item:
        components.append(main_item)
        log_debug(f"Added remaining main item: {main_item}")
    
    if extras:
        components.extend(['+' + extra.strip() for extra in extras])
        log_debug(f"Added extras: {extras}")
    
    # Add the appropriate connector
    if channel == 'ebay0':
        components.append("To Fit")
        log_debug("Added connector: 'To Fit'")
    elif channel == 'amazon':
        components.append("Compatible With")
        log_debug("Added connector: 'Compatible With'")
    else:
        components.append("For")
        log_debug("Added connector: 'For'")
    
    # Add vehicle information
    vehicle_parts = []
    if make and str(make).lower() != 'nan':
        vehicle_parts.append(str(make).strip())
    if model and str(model).lower() != 'nan':
        vehicle_parts.append(str(model).strip())
    if year and str(year).lower() != 'nan' and str(year).strip() != '':
        vehicle_parts.append(str(year).strip())
    
    formatted_vehicle = " ".join(vehicle_parts)
    if formatted_vehicle:
        components.append(formatted_vehicle)
        log_debug(f"Added vehicle info: '{formatted_vehicle}'")
    
    # Add material keywords based on item type
    if item_type:
        item_materials = get_item_materials(item_type, materials_dict)
        if item_materials:
            components.extend(item_materials)
            log_debug(f"Added material keywords: {item_materials}")
    
    # For non-magento channels, add item-specific and general keywords
    if channel != 'magento':
        # Find matching item and its specific keywords
        _, item_keywords = find_matching_item(main_item, vehicle_type, keywords)
        if item_keywords:
            components.extend(item_keywords)
            log_debug(f"Added item-specific keywords: {item_keywords}")
        
        # Add general vehicle type keywords
        if vehicle_type in keywords and 'general' in keywords[vehicle_type]:
            general_keywords = keywords[vehicle_type]['general']
            components.extend(general_keywords)
            log_debug(f"Added general keywords: {general_keywords}")
    
    # Join components
    formatted_title = " ".join(filter(None, components))
    log_debug(f"\nComponents joined: '{formatted_title}'")
    
    # Add XSKU for Amazon
    if channel == 'amazon':
        formatted_title += " - XSKU"
        log_debug("Added XSKU")
    
    # Enforce character limits
    if channel == 'ebay1':
        formatted_title = enforce_character_limit(formatted_title, min_len=78, max_len=80)
    elif channel == 'ebay0':
        formatted_title = enforce_character_limit(formatted_title, min_len=78, max_len=80)
    elif channel == 'magento':
        formatted_title = enforce_character_limit(formatted_title, min_len=0, max_len=200)
    elif channel == 'amazon':
        formatted_title = enforce_character_limit(formatted_title, min_len=80, max_len=200)
    
    log_debug(f"Final title: '{formatted_title}'")
    return formatted_title

def format_ebay1_title(title, make, model, year, material=None, wheelbase=None, cab_type=None, vehicle_type='4x4'):
    return format_title_with_keywords(title, make, model, year, material, wheelbase, cab_type, 'ebay1', vehicle_type)

def format_ebay0_title(title, make, model, year, material=None, wheelbase=None, cab_type=None, vehicle_type='4x4'):
    return format_title_with_keywords(title, make, model, year, material, wheelbase, cab_type, 'ebay0', vehicle_type)

def format_magento_title(title, make, model, year, material=None, wheelbase=None, cab_type=None, vehicle_type='4x4'):
    """Format title for magento - only include base components and material"""
    # Extract main item and extras
    main_item, extras = extract_main_item_and_extras(title)
    
    # Build base components
    components = []
    
    # Add color if present
    color_match = re.search(r'black|chrome|silver', title.lower())
    if color_match:
        color = color_match.group().upper()
        components.append(color)
    
    # Add item type
    item_type = None
    for item in ["Grill Bar", "Side Bar", "Side Step", "Roof Bar", "Running Board", "Bull Bar", "Bumper Bar", "Window Deflector"]:
        if item.lower() in main_item.lower():
            item_type = item
            main_item = re.sub(r'(?i)' + re.escape(item), '', main_item).strip()
            break
    
    if item_type:
        components.append(item_type)
    
    # Add remaining main item parts
    if main_item:
        components.append(main_item)
    
    # Add extras
    if extras:
        components.extend(['+' + extra.strip() for extra in extras])
    
    # Add "For" and vehicle info
    components.append("For")
    
    # Add vehicle information
    vehicle_parts = []
    if make and str(make).lower() != 'nan':
        vehicle_parts.append(str(make).strip())
    if model and str(model).lower() != 'nan':
        vehicle_parts.append(str(model).strip())
    if year and str(year).lower() != 'nan' and str(year).strip() != '':
        vehicle_parts.append(str(year).strip())
    
    formatted_vehicle = " ".join(vehicle_parts)
    if formatted_vehicle:
        components.append(formatted_vehicle)
    
    # Add "Truck" at the end
    components.append("Truck")
    
    # Add material if present
    if material and str(material).lower() != 'nan':
        components.append(str(material).strip())
    
    # Join components and enforce character limit
    formatted_title = " ".join(filter(None, components))
    formatted_title = enforce_character_limit(formatted_title, min_len=0, max_len=200)
    return formatted_title

def format_amazon_title(title, make, model, year, material=None, wheelbase=None, cab_type=None, vehicle_type='4x4'):
    return format_title_with_keywords(title, make, model, year, material, wheelbase, cab_type, 'amazon', vehicle_type)

def enforce_character_limit(title, min_len=78, max_len=80):
    """
    Enforce character limits on a title, adhering to the rules.
    If the title is too short, add keywords until it meets the minimum length.
    """
    # First try to meet minimum length by adding keywords
    if len(title) < min_len:
        # Load keywords
        vehicle_keywords = load_vehicle_keywords()
        vehicle_type = detect_vehicle_type(title)  # Pass empty model since we're just checking title
        
        if vehicle_type:
            keywords = vehicle_keywords.get(vehicle_type, {}).get('general', [])
            
            # Add keywords one by one until we meet the minimum length
            for keyword in keywords:
                if len(title) >= min_len:
                    break
                if keyword not in title.lower():
                    title = f"{title} {keyword}"

    # If over maximum length, try to reduce without breaking words
    while len(title) > max_len:
        words = title.split()
        if len(words) > 1:
            title = " ".join(words[:-1])
        else:
            break
    
    # If still under minimum length, try removing spaces between + signs
    if len(title) > max_len:
        title = title.replace(" + ", "+")
    
    # If still over maximum length, try removing spaces between years
    if len(title) > max_len:
        # Look for years in the format YYYY or 'Pre YYYY'
        year_pattern = r'(?:Pre )?(?:19|20)\d{2}'
        years = re.findall(year_pattern, title)
        for year in years:
            title = title.replace(f" {year} ", f"{year}")
    
    # If over maximum length, try to reduce without breaking words
    while len(title) > max_len:
        words = title.split()
        if len(words) > 1:
            title = " ".join(words[:-1])
        else:
            break
    
    return title

def process_description(description_template, year=None, user_make='', user_model='', user_description='', main_item='', context='ebay1'):
    """Process and format the description using the template."""
    try:
        log_debug(f"\nProcessing description for context {context} with:")
        log_debug(f"Year: {year}")
        log_debug(f"Make: {user_make}")
        log_debug(f"Model: {user_model}")
        log_debug(f"User Description: {user_description}")
        log_debug(f"Main Item: {main_item}")
        
        # Load the description template if a string wasn't provided
        if not description_template:
            template_file = f'description_template_{context}.txt'
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    description_template = f.read()
                log_debug(f"Loaded description template from {template_file}")
            except FileNotFoundError:
                # Fall back to default template if context-specific one doesn't exist
                try:
                    with open('description_template.txt', 'r', encoding='utf-8') as f:
                        description_template = f.read()
                    log_debug("Loaded default description template")
                except Exception as e:
                    log_debug(f"Error loading default template: {str(e)}")
                    return ""
        
        # Split template into main content and styling
        parts = description_template.split('<!-- Required Styling -->')
        main_content = parts[0]
        styling = parts[1] if len(parts) > 1 else ''
        
        # Process main content
        description = main_content
        
        # First, remove any existing make/model from the main_item
        if main_item:
            try:
                # Only reload if the lists are empty
                if not vehicle_query_instance.makes or not vehicle_query_instance.models:
                    vehicle_query_instance.load_makes_and_models(app.config['DROPBOX_URL'])
                main_item = remove_existing_make_model(main_item, vehicle_query_instance.makes, vehicle_query_instance.models)
                log_debug(f"Main item after removing make/model: {main_item}")
            except Exception as e:
                log_debug(f"Error loading makes/models from Dropbox: {str(e)}")
                # Continue with empty lists rather than failing
                main_item = remove_existing_make_model(main_item, [], [])

        # Replace the main item description and main_item placeholders
        main_item_desc = user_description if user_description else main_item
        if main_item_desc:
            # Wrap the main item in a paragraph with specific styling if not already wrapped
            if not re.search(r'<p[^>]*>', main_item_desc):
                main_item_desc = f'<p style="margin: 0px; padding: 5px 0px;">{main_item_desc}</p>'
            
            # Replace both [MAIN_ITEM_DESCRIPTION] and {main_item}
            description = re.sub(r'\[MAIN_ITEM_DESCRIPTION\]', main_item_desc, description, flags=re.IGNORECASE)
            description = description.replace('{main_item}', main_item)
            log_debug(f"Replaced main item placeholders with: {main_item}")
        
        # Replace make/model/year placeholders (both bracket styles)
        if user_make:
            description = re.sub(r'\[MAKE\]', user_make, description, flags=re.IGNORECASE)
            description = description.replace('{make}', user_make)
            log_debug(f"Replaced make with: {user_make}")
        
        if user_model:
            description = re.sub(r'\[MODEL\]', user_model, description, flags=re.IGNORECASE)
            description = description.replace('{model}', user_model)
            log_debug(f"Replaced model with: {user_model}")
        
        if year:
            # Store the original year input
            original_year = str(year)
            
            # Create two versions of the year text
            header_year = original_year.replace('+', ' - present')  # For the top description
            list_year = original_year.replace('models', '') # For the bullet points
            
            # First, handle the year in the bullet point list
            if '<ul>' in description:
                list_start = description.find('<ul>')
                list_end = description.find('</ul>', list_start) + 5
                list_content = description[list_start:list_end]
                
                # Replace year placeholder in list with list_year
                updated_list = list_content.replace('{year}', list_year)
                updated_list = re.sub(r'\[YEAR\]', list_year, updated_list, flags=re.IGNORECASE)
                #replace models in list with ''
                updated_list = re.sub(r'\bmodels\b', '', updated_list, flags=re.IGNORECASE)
                
                # Replace the original list with updated list
                description = description[:list_start] + updated_list + description[list_end:]
                
                # Now replace remaining year placeholders (outside list) with header_year
                description = description[:list_start].replace('{year}', header_year) + \
                            updated_list + \
                            description[list_end:].replace('{year}', header_year)
                
                # Do the same for [YEAR] placeholders
                description = description[:list_start].replace('[YEAR]', header_year) + \
                            updated_list + \
                            description[list_end:].replace('[YEAR]', header_year)
            else:
                # If no list found, replace all year placeholders with header_year
                description = description.replace('{year}', header_year)
                description = re.sub(r'\[YEAR\]', header_year, description, flags=re.IGNORECASE)
            
            log_debug(f"Replaced years - Header: {header_year}, List: {list_year}")
        
        # Handle extras placeholder if present
        extras = ''  # You might want to pass extras as a parameter if needed
        description = description.replace('{extras}', extras)
        
        # Clean up any remaining placeholders and fix formatting
        description = re.sub(r'\[.*?\]', '', description)  # Remove any remaining square bracket placeholders
        description = re.sub(r'\{.*?\}', '', description)  # Remove any remaining curly bracket placeholders
        description = re.sub(r'\s+', ' ', description)  # Clean up whitespace
        description = description.strip()
        
        # Ensure paragraphs have the correct styling
        description = re.sub(r'<p(?![^>]*style=)', '<p style="margin: 0px; padding: 5px 0px;"', description)
        
        # Add any required styling
        if styling:
            description += styling
        
        log_debug(f"Final description for {context}: {description}")
        return description
        
    except Exception as e:
        log_debug(f"Error processing description: {str(e)}")
        return ""

def process_data(df, update_type, context, vehicle_type='4x4', form_data={}):
    """Process the data based on update type and context"""
    # Create a copy of the dataframe to store results
    result_df = df.copy()
    
    try:
        update_type = update_type.lower().strip()
        
        if update_type == 'all':
            # Process all: titles, descriptions, extended properties, and price
            result_df = process_titles(result_df, context, vehicle_type, form_data)
            result_df = process_descriptions(result_df, context, form_data)
            result_df = process_extended_properties(result_df, form_data)
            if 'price' in form_data and form_data['price'].strip():
                result_df['price'] = form_data['price']
            
        elif update_type == 'titles':
            # Process only titles
            result_df = process_titles(result_df, context, vehicle_type, form_data)
            
        elif update_type == 'description':
            # Process only descriptions
            result_df = process_descriptions(result_df, context, form_data)
            
        elif update_type == 'titles + description':
            # Process both titles and descriptions
            result_df = process_titles(result_df, context, vehicle_type, form_data)
            result_df = process_descriptions(result_df, context, form_data)
            
        elif update_type == 'titles + description + properties':
            # Process titles, descriptions and extended properties
            result_df = process_titles(result_df, context, vehicle_type, form_data)
            result_df = process_descriptions(result_df, context, form_data)
            result_df = process_extended_properties(result_df, form_data)
            
        elif update_type == 'extended properties':
            # Process only extended properties
            result_df = process_extended_properties(result_df, form_data)
            
        elif update_type == 'price':
            # Process only price
            if 'price' in form_data and form_data['price'].strip():
                result_df['price'] = form_data['price']
                
    except Exception as e:
        log_debug(f"Error in process_data: {str(e)}")
    
    return result_df

EXTENDED_PROPERTIES = [
    "ALTERATION_Attribute",
    "Bar length_Attribute",
    "Brackets_Attribute",
    "BTS-NOTSOLD_Attribute",
    "Bullet1_Attribute",
    "Bullet2_Attribute",
    "Bullet3_Attribute",
    "Bullet4_Attribute",
    "Bullet5_Attribute",
    "Diameter of bar_Attribute",
    "Dimension_Attribute",
    "eBay ID_Attribute",
    "eBay Store ID_Attribute",
    "eBay1 Store ID_Attribute",
    "Filter Attribute_Attribute",
    "Finish_Attribute",
    "Fitment Type_Attribute",
    "Fitting Link_Attribute",
    "Fitting link video_Attribute",
    "google_product_category_Attribute",
    "HS Code_Attribute",
    "Included in sale_Attribute",
    "Instructions_Attribute"
]

def process_extended_properties(df, form_data):
    # Map form field names to CSV column names
    field_to_column = {
        'alteration': 'ALTERATION_Attribute',
        'bar_length': 'Bar length_Attribute',
        'brackets': 'Brackets_Attribute',
        'bts_notsold': 'BTS-NOTSOLD_Attribute',
        'bullet1': 'Bullet1_Attribute',
        'bullet2': 'Bullet2_Attribute',
        'bullet3': 'Bullet3_Attribute',
        'bullet4': 'Bullet4_Attribute',
        'bullet5': 'Bullet5_Attribute',
        'diameter_of_bar': 'Diameter of bar_Attribute',
        'dimension': 'Dimension_Attribute',
        'ebay_id': 'eBay ID_Attribute',
        'ebay_store_id': 'eBay Store ID_Attribute',
        'ebay1_store_id': 'eBay1 Store ID_Attribute',
        'filter_attribute': 'Filter Attribute_Attribute',
        'finish': 'Finish_Attribute',
        'fitment_type': 'Fitment Type_Attribute',
        'fitting_link': 'Fitting Link_Attribute',
        'fitting_link_video': 'Fitting link video_Attribute',
        'google_product_category': 'google_product_category_Attribute',
        'hs_code': 'HS Code_Attribute',
        'included_in_sale': 'Included in sale_Attribute',
        'instructions': 'Instructions_Attribute',
        'url': 'URL_Attribute'
    }

    # Update each column if a value was provided in the form
    for form_field, column_name in field_to_column.items():
        # Check if the field was submitted in the form
        if form_field in form_data:
            user_input = form_data[form_field].strip()
            
            # If user provided input, use it
            if user_input:
                if column_name not in df.columns:
                    df[column_name] = ''  # Create column if it doesn't exist
                df[column_name] = user_input
            # If no input provided:
            # - If column exists in CSV, keep its original value
            # - If column doesn't exist in CSV, it will remain empty or not be created

    return df

def process_titles(df, context, vehicle_type='4x4', form_data={}):
    """Process titles based on context"""
    try:
        # Make a copy of the input dataframe
        result_df = df.copy()
        
        # Check for ItemTitle or Item_Title column
        title_column = None
        if 'ItemTitle' in result_df.columns:
            title_column = 'ItemTitle'
        elif 'Item_Title' in result_df.columns:
            title_column = 'Item_Title'
            result_df = result_df.rename(columns={'Item_Title': 'ItemTitle'})
        else:
            log_debug("Error: No title column found in DataFrame")
            return df
        
        # Get make, model, year from form data
        make = form_data.get('make', '')
        model = form_data.get('model', '')
        year = form_data.get('year', '')
        
        # Process each row
        for index, row in result_df.iterrows():
            try:
                # Get the original title
                title = str(row.get(title_column, ''))
                
                # Get material, wheelbase, cab_type from row if available
                material = str(row.get('Material', ''))
                wheelbase = str(row.get('Wheelbase', ''))
                cab_type = str(row.get('Cab_Type', ''))
                
                # Format title for each context
                if 'ebay1' in context:
                    result_df.at[index, 'Processed_ebay1_Title'] = format_ebay1_title(
                        title, make, model, year, material, wheelbase, cab_type, vehicle_type)
                
                if 'ebay0' in context:
                    result_df.at[index, 'Processed_ebay0_Title'] = format_ebay0_title(
                        title, make, model, year, material, wheelbase, cab_type, vehicle_type)
                
                if 'magento' in context:
                    result_df.at[index, 'Processed_magento_Title'] = format_magento_title(
                        title, make, model, year, material, wheelbase, cab_type, vehicle_type)
                
                if 'amazon' in context:
                    result_df.at[index, 'Processed_amazon_Title'] = format_amazon_title(
                        title, make, model, year, material, wheelbase, cab_type, vehicle_type)
                
            except Exception as e:
                log_debug(f"Error processing row {index}: {str(e)}")
                continue
                
        return result_df
        
    except Exception as e:
        log_debug(f"Error in process_titles: {str(e)}")
        return df

def process_descriptions(df, context, form_data={}):
    """Process descriptions for each context"""
    try:
        # Make a copy of the input dataframe
        result_df = df.copy()
        
        # Get the description template
        try:
            with open('description_template.txt', 'r', encoding='utf-8') as f:
                description_template = f.read()
        except Exception as e:
            log_debug(f"Error reading description template: {str(e)}")
            return df
        
        # Get make, model, year from form data
        make = form_data.get('make', '')
        model = form_data.get('model', '')
        year = form_data.get('year', '')
        user_description = form_data.get('user_description', '')
        
        # Process each row
        for index, row in result_df.iterrows():
            try:
                # Get the title and remove existing make/model if user provided new ones
                title = str(row.get('ItemTitle', row.get('Item_Title', '')))
                if make or model:
                    title = remove_existing_make_model(title, [make] if make else [], [model] if model else [])
                
                # Get the main item from the cleaned title
                main_item = extract_main_item_and_extras(title)[0] if title else ''
                log_debug(f"Extracted main item for description: '{main_item}'")
                
                # Process description for each context
                if 'ebay1' in context:
                    result_df.at[index, 'Processed_ebay1_Description'] = process_description(
                        description_template, year, make, model, user_description, main_item, 'ebay1')
                
                if 'ebay0' in context:
                    result_df.at[index, 'Processed_ebay0_Description'] = process_description(
                        description_template, year, make, model, user_description, main_item, 'ebay0')
                
                if 'magento' in context:
                    result_df.at[index, 'Processed_magento_Description'] = process_description(
                        description_template, year, make, model, user_description, main_item, 'magento')
                
                if 'amazon' in context:
                    result_df.at[index, 'Processed_amazon_Description'] = process_description(
                        description_template, year, make, model, user_description, main_item, 'amazon')
                
            except Exception as e:
                log_debug(f"Error processing description for row {index}: {str(e)}")
                continue
                
        return result_df
        
    except Exception as e:
        log_debug(f"Error in process_descriptions: {str(e)}")
        return df

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/how-to-use')
def how_to_use():
    return render_template('how_to_use.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
            
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file'})
        
        # Get form data
        update_type = request.form.get('update_type', 'titles + description')
        
        # Get context as a list
        context = request.form.getlist('context[]')
        if not context:  # If empty, try single value
            context = [request.form.get('context', 'ebay1')]
            
        vehicle_type = request.form.get('vehicle_type', '4x4').lower()
        form_data = request.form
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read the CSV file
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            return jsonify({'error': f'Error reading CSV file: {str(e)}'})
        
        # Process the data
        try:
            result_df = process_data(df, update_type, context, vehicle_type, form_data)
        except Exception as e:
            return jsonify({'error': f'Error processing data: {str(e)}'})
        
        # Save the processed file
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'processed_{timestamp}_{filename}'
            output_filepath = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            result_df.to_csv(output_filepath, index=False)
            
            return send_file(output_filepath, as_attachment=True)
        except Exception as e:
            return jsonify({'error': f'Error saving processed file: {str(e)}'})
            
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'})

@app.route('/process_titles', methods=['GET'])

def process_titles_endpoint():
    return "Process Titles Endpoint"

vehicle_query_instance = VehicleQuery()
try:
    vehicle_query_instance.load_makes_and_models(app.config['DROPBOX_URL'])
    log_debug("Successfully initialized VehicleQuery with Dropbox data")
except Exception as e:
    log_debug(f"Error initializing VehicleQuery: {str(e)}")

# Ensure the upload and processed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    app.run(debug=True)
