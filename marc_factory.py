"""
Description: Factory to provide a unified generator for MARC records, 
             automatically detecting format (XML vs. Binary) by extension.
"""

import pymarc
import xml.etree.ElementTree as ET
from marc_xml_impl import XMLRecord
from marc_pymarc_impl import PymarcRecord

def get_record_generator(filename: str):
    """
    Factory function that returns a generator yielding DAL Record objects.
    """
    
    def xml_generator():
        # Using iterparse to keep memory usage low for large XML files
        context = ET.iterparse(filename, events=('end',))
        # Namespace handling
        ns = "http://www.loc.gov/MARC21/slim"
        for event, elem in context:
            if elem.tag == f"{{{ns}}}record" or elem.tag == "record":
                yield XMLRecord(elem)
                # Clear the element from memory after yielding
                elem.clear()

    def binary_generator():
        with open(filename, 'rb') as fh:
            reader = pymarc.MARCReader(fh)
            for record in reader:
                if record:
                    yield PymarcRecord(record)

    # Simple extension-based detection
    ext = filename.lower().split('.')[-1]
    
    if ext in ['xml', 'marcxml']:
        return xml_generator()
    elif ext in ['mrc', 'marc', 'dat']:
        return binary_generator()
    else:
        raise ValueError(f"Unsupported file extension: {ext}")