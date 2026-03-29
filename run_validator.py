from marc_factory import get_record_generator
from bib_validator import validate_marcxml_record, nightly_validation_checks
from sys import argv

def process_file(filename):
    # Get the generator (factory doesn't load the file yet)
    records = get_record_generator(filename)
    
    for i, record in enumerate(records, 1):
        print(f"Processing record {i}")
        print(f"Record leader: {record.get_field('LDR').data}")

        # Pass the record (which implements BaseRecord) to the validators

        # Test the main validation routine
        success, errors = validate_marcxml_record(record)
        
        # Test the nightly checks
        nightly_errors = nightly_validation_checks(record)
                
        all_errors = errors + nightly_errors
                
        if success:
            print(f"  Status: Executed successfully.")
            print(f"  Errors found: {len(all_errors)}")
            for err in all_errors:
                print(f"    - {err}")
        else:
            print(f"  Status: Record skipped (expected behavior).")

# Works for both!
if len(argv) > 1:
    process_file(argv[1])
else:
    print("Usage: python filerunner.py <filename>")