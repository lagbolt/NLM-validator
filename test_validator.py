import xml.etree.ElementTree as ET
from marc_xml_impl import XMLRecord
from bib_validator import validate_marcxml_record, nightly_validation_checks

def run_test_suite(xml_file):
    print(f"--- Starting Validation Test on {xml_file} ---")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Handle MARCXML namespace
        ns = {'marc': 'http://www.loc.gov/MARC21/slim'}
        records = root.findall('marc:record', ns)
        if not records:
            # Fallback if no namespace is used in the file
            records = root.findall('record')

        print(f"Found {len(records)} records to process.\n")

        for i, record_elem in enumerate(records, 1):
            # Wrap raw XML element in our DAL
            dal_record = XMLRecord(record_elem)
            
            print(f"Processing Record #{i}...")
            
            try:
                # Test the main validation routine
                success, errors = validate_marcxml_record(dal_record)
                
                # Test the nightly checks
                nightly_errors = nightly_validation_checks(dal_record)
                
                all_errors = errors + nightly_errors
                
                if success:
                    print(f"  Status: Executed successfully.")
                    print(f"  Errors found: {len(all_errors)}")
                    for err in all_errors:
                        print(f"    - {err}")
                else:
                    print(f"  Status: Record skipped (expected behavior).")
                    
            except Exception as e:
                print(f"  CRITICAL FAILURE on Record #{i}: {type(e).__name__} - {e}")
            
            print("-" * 30)

    except FileNotFoundError:
        print(f"Error: Could not find {xml_file}")
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML: {e}")

if __name__ == "__main__":
    # Ensure sample_records.xml exists before running
    run_test_suite('sample_records.xml')