"""
This module contains the extended properties configuration based on analyze.csv
"""

# Dictionary mapping property names to their possible values and rules
EXTENDED_PROPERTIES = {
    'ALTERATION': {'type': 'text', 'required': False},
    'Bar length': {'type': 'text', 'required': False},
    'Brackets': {'type': 'text', 'required': False},
    'BTS-NOTSOLD': {'type': 'text', 'required': False},
    'Bullet1': {'type': 'text', 'required': False},
    'Bullet2': {'type': 'text', 'required': False},
    'Bullet3': {'type': 'text', 'required': False},
    'Bullet4': {'type': 'text', 'required': False},
    'Bullet5': {'type': 'text', 'required': False},
    'Diameter of bar': {'type': 'text', 'required': False},
    'eBay ID': {'type': 'text', 'required': False},
    'eBay Store ID': {'type': 'text', 'required': False},
    'eBay1 Store ID': {'type': 'text', 'required': False},
    'Filter Attribute': {'type': 'text', 'required': False},
    'Finish': {'type': 'text', 'required': False},
    'Fitment Type': {'type': 'text', 'required': False},
    'Fitting Link': {'type': 'text', 'required': False},
    'Fitting link video': {'type': 'text', 'required': False},
    'google_product_category': {'type': 'text', 'required': False},
    'HS Code': {'type': 'text', 'required': False},
    'Included in sale': {'type': 'text', 'required': False},
    'Instructions': {'type': 'text', 'required': False}
}

def get_extended_property_names():
    """Return a list of all extended property names"""
    return list(EXTENDED_PROPERTIES.keys())

def get_extended_property_config(property_name):
    """Get the configuration for a specific extended property"""
    return EXTENDED_PROPERTIES.get(property_name, None)

def is_valid_property(property_name):
    """Check if a property name is valid"""
    return property_name in EXTENDED_PROPERTIES

def validate_property_value(property_name, value):
    """Validate a property value against its configuration"""
    config = get_extended_property_config(property_name)
    if not config:
        return False
        
    if value is None or value == '':
        return not config['required']
        
    return True  # For now, accept any non-empty value for text fields
