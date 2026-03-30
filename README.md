# A port of the NLM validator to a data access layer

The file bib_validator.py is originally taken from the [NLM Discovery Alma Tools](https://github.com/NIH-NLM/nlm-discovery-alma-tools/tree/main/Alma%20Validation/Bib%20Validator) repo.  It has been converted to use a format-independent MARC data access layer, which is provided in this repo.

The file marc_validation_resources.py is taken unchanged from the NLM repo.

The files in this repo are as follows:

### marc_interfaces.py

This is the abstract base class that any concrete implementation of the data access layer relies on.

Any code which *uses* the data access layer will call the classes and methods defined here.

### marc_xml_impl.py

The MARC/XML implementation of the data access layer.  This was created by splitting the XML-specific code out of the original bib_validator.py.

### marc_pymarc_impl.py

An implementation of the data access layer using the PyMarc library to interpret binary MARC data.

### bib_validator.py

A port of the original code to use the routines defined in marc_interfaces.py.

### marc_factory.py

Defines a utility function, get_record_generator, that reads records from a file, using either the XML or the PyMarc implementation depending on the file suffix.

### run_validator.py

Takes a filename as argument, passes the filename to get_record_generator, and passes the generated records to bib_validator.py for validation.

### Plus

Some sample files for testing.