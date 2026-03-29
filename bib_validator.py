"""
Description: Full refactor of metadata validation logic using the MARC Data Access Layer.
             Removes all XML-specific coupling and handles "missingness" via Null Objects.
"""

from urllib.parse import urlparse
from marc_interfaces import BaseRecord, BaseField, BaseSubfield
# Resource imports
from marc_validation_resources import unicode_embeddings_to_remove

# Global variables
atlas_like_values = [
    'Atlas', 'Book Illustrations', 'Caricature', 'Cartoon', 'Comic Book', 
    'Graphic Novel', 'Infographic', 'Drawing', 'Map', 'Portrait', 
    'Photograph', 'Photomechanical Print', 'Postcard', 'Poster', 'Pictorial Work'
]

def format_error(error_message: str, field: BaseField, subfield: BaseSubfield):
    """
    Format an error message with field and subfield identifiers from DAL objects.
    """
    # DAL objects are falsey if they are Null Objects
    field_id = getattr(field, 'id', "unknown") if field else "unknown"
    subfield_id = getattr(subfield, 'id', "unknown") if subfield else "unknown"

    return {
        "error": error_message,
        "datafield_id": field_id,
        "subfield_id": subfield_id
    }

def validate_marcxml_record(record: BaseRecord, record_type: str = "regular"):
    """
    Core validation routine using the DAL interface.
    """
    errors = []
    
    # 1. 999 subfield check (Record Type Inference & Skip Logic)
    skip_values = {'BRF', 'ACC', 'BDW', 'IDM', 'NLM', 'SMC', 'WDN'}
    
    for field in record.get_fields('999'):
        val_999a = field.get_subfield('a').value
        if val_999a == "IDX":
            record_type = "indexcat"
        if val_999a in skip_values:
            errors.append(f"Validator doesn't work on records with a 999 $a value of: {val_999a}")
            return False, errors

    # 2. Presence Checks
    for tag in ['336', '337', '338']:
        if not record.get_field(tag):
            errors.append(f"Missing {tag} field in the record.")

    # 3. Leader & 008 (Safe slicing handled by DAL)
    leader = record.get_field('leader')
    if not leader or len(leader.value) < 24:
        errors.append("Leader is missing or malformed.")
    elif leader.value[7] not in ['a', 'm', 's', 'c', 'i']:
        errors.append("Leader Byte 07 not 'a', 'm', 's', 'c', or 'i'.")

    f008 = record.get_field('008')
    if not f008:
        errors.append("Missing 008 field.")
    elif len(f008.value) != 40:
        errors.append(f"Length of the 008 field is {len(f008.value)}, should be 40 characters.")

    # 4. Conditional Business Logic
    has_042 = bool(record.get_field('042'))
    has_postcard = any(sf.value.strip().lower() == 'postcard' 
                       for f in record.get_fields('655') 
                       for sf in f.get_subfields('a'))
    has_noc_999 = any(sf.value.strip() == 'NOC' 
                      for f in record.get_fields('999') 
                      for sf in f.get_subfields('a'))

    if leader.value[17:18] == ' ' and not has_042 and not has_postcard and not has_noc_999:
        errors.append("Leader Byte 17 is blank and 042 field is not present. Do you want to add 042 pcc?")

    # 5. Language Cross-Check
    lang_041 = record.get_field('041').get_subfield('a').value.strip()
    lang_008 = f008.value[35:38].strip()
    if lang_041 and lang_008 and lang_041 != lang_008:
        errors.append("008 language and 041 $a do not match.")

    # 6. Specialized Logic
    if record_type == "indexcat":
        errors += validate_indexcat_specific(record)
    
    errors += validate_illustration_codes(record)

    return True, errors

def validate_indexcat_specific(record: BaseRecord):
    """
    Perform IndexCat-specific validation using adjacent subfield checks.
    """
    errors = []
    
    # Helper for punctuation patterns (245, 264, 300)
    def check_subfield_punctuation(tag, follow_map):
        for field in record.get_fields(tag):
            sfs = field.get_subfields() # Get all subfield objects in order
            if not sfs: continue
            
            codes = [s.code for s in sfs]
            for i in range(len(sfs) - 1):
                curr_sf, next_sf = sfs[i], sfs[i+1]
                required_punctuation = follow_map.get((curr_sf.code, next_sf.code))
                if required_punctuation and not curr_sf.value.strip().endswith(required_punctuation):
                    errors.append(f"INDEXCAT: {tag} ${curr_sf.code} should end with '{required_punctuation}' when followed by ${next_sf.code}")
            
            # Final subfield specific punctuation (e.g., 264 $c)
            if tag == '264' and sfs[-1].code == 'c':
                val = sfs[-1].value.strip()
                if not any(val.endswith(p) for p in ['.', '?', '!', ']', ')']):
                    errors.append("INDEXCAT: 264 $c should end with a period or other punctuation")

    # Mapping logic for punctuation
    check_subfield_punctuation('245', {('a', 'b'): ' :', ('a', 'c'): ' /', ('b', 'c'): ' /'})
    check_subfield_punctuation('264', {('a', 'b'): ' :', ('a', 'c'): ',', ('b', 'c'): ','})
    check_subfield_punctuation('300', {('a', 'b'): ' :', ('a', 'c'): ' ;', ('b', 'c'): ' ;'})

    # Academic Dissertation / 008 logic
    has_dissertation = any(sf.value == "Academic Dissertation" 
                           for f in record.get_fields('655') for sf in f.get_subfields('a'))
    if has_dissertation and record.get_field('008').value[24:25] != 'm':
        errors.append("INDEXCAT: 655 'Academic Dissertation' present but 008/24 is not 'm'")

    # Content-based checks
    for field in record.get_fields('590'):
        for sf in field.get_subfields('a'):
            if '[' in sf.value and ']' in sf.value:
                errors.append("INDEXCAT: 590 $a contains bracketed content which should be removed")

    if record.get_field('650'):
        errors.append("INDEXCAT: 650 field should not exist in IndexCat records")

    for sf in record.get_field('300').get_subfields():
        if "cm." in sf.value:
            errors.append("INDEXCAT: 300 field contains 'cm.' which should be 'cm'")

    # Field 044 specific logic
    for field in record.get_fields('044'):
        if any(sf.code not in ['a', '9'] for sf in field.get_subfields()):
            errors.append("INDEXCAT: 044 field has subfields other than $a or $9")
        for sf in field.get_subfields('a'):
            errors.append(format_error("INDEXCAT: 044 field uses $a instead of $9", field, sf))

    return errors

def validate_illustration_codes(record: BaseRecord):
    """
    Compare 300 field terminology to 008/18-21 codes.
    """
    errors = []
    field300_text = " ".join([sf.value.lower() for f in record.get_fields('300') for sf in f.get_subfields()])
    if not field300_text: return errors

    mapping = [ (["illustration", "chart"], "a"), (["map"], "b"), (["portrait"], "c"), (["plate"], "af") ]
    codes_found = ""
    for terms, code in mapping:
        if any(t in field300_text for t in terms):
            if code == "a" and "af" in codes_found: continue
            if code == "af" and "a" in codes_found: codes_found = codes_found.replace("a", "")
            if code not in codes_found: codes_found += code

    if not codes_found: return errors
    
    expected = codes_found.ljust(4, " ")[:4]
    actual = record.get_field('008').value[18:22]
    if expected != actual:
        errors.append(f"INDEXCAT: Illustration codes in 008/18-21 should be '{expected}' based on 300 field, but found '{actual}'")
    
    return errors

def nightly_validation_checks(record: BaseRecord, record_type: str = "regular"):
    """
    Consolidated nightly checks using the DAL.
    """
    errors = []
    
    # 001 and 008 Presence
    f001 = record.get_field('001')
    f008 = record.get_field('008')

    if record_type != "indexcat" and not f001:
        errors.append("001 is missing")
    if not f008:
        errors.append("008 is missing")

    # 001 Numeric/Length validation
    if record_type != "indexcat" and f001:
        val = f001.value
        if not (8 <= len(val) <= 19):
            errors.append("001 field length is invalid")
        if not val.isdigit():
            errors.append("Invalid character in 001 field")

    # 035 Checks
    fields_035 = record.get_fields('035')
    if not fields_035:
        errors.append("035 field is missing")
    
    has_sub9 = any(f.get_subfield('9') for f in fields_035)
    if record_type != "indexcat" and not has_sub9:
        errors.append("035 $9 field is missing")
    
    for field in fields_035:
        for sf in field.get_subfields('9'):
            if not sf.value.isalnum():
                errors.append(format_error("Invalid character in 035 $9 field", field, sf))

    # CITVIDEO Check
    has_citrel = any(f.get_subfield('a').value == 'CITREL' for f in record.get_fields('998'))
    if has_citrel:
        valid_035 = any(sf.value.startswith('(DNLM)CIT') for f in fields_035 for sf in f.get_subfields('a'))
        if not valid_035:
            errors.append("CITVIDEO is missing 035 $a beginning with (DNLM)CIT")

    # 995 Length Check
    for field in record.get_fields('995'):
        for code in ['b', 'd']:
            for sf in field.get_subfields(code):
                if len(sf.value) != 8:
                    errors.append(format_error(f"995 ${code} should contain 8 characters", field, sf))

    return errors