"""
Description: pymarc implementation of the MARC Data Access Layer.
             Wraps native pymarc objects to match the BaseRecord interface.
"""

from marc_interfaces import BaseRecord, BaseField, BaseSubfield, NullField, NullSubfield
import pymarc

class PymarcSubfield(BaseSubfield):
    def __init__(self, code: str, value: str):
        self._code = code
        self._value = value

    @property
    def code(self) -> str:
        return self._code

    @property
    def value(self) -> str:
        return self._value if self._value is not None else ""

    def __bool__(self) -> bool:
        return True

class PymarcField(BaseField):
    def __init__(self, field: pymarc.Field):
        self.field = field

    @property
    def tag(self) -> str:
        return self.field.tag

    @property
    def is_control_field(self) -> bool:
        return self.field.is_control_field()

    @property
    def is_data_field(self) -> bool:
        return not self.field.is_control_field()

    @property
    def indicator1(self) -> str:
        if self.is_control_field:
            return " "
        return self.field.indicator1

    @property
    def indicator2(self) -> str:
        if self.is_control_field:
            return " "
        return self.field.indicator2

    @property
    def value(self) -> str:
        # For control fields, pymarc.Field.data holds the string
        if self.is_control_field:
            return self.field.data if self.field.data else ""
        # For data fields, formatted string of all subfields
        return self.field.format_field()

    @property
    def data(self) -> str:
        """
        Alias for value to match pymarc's ControlField interface.
        """
        return self.value

    def get_subfield(self, code: str) -> BaseSubfield:
        val = self.field.get_subfields(code)
        if val:
            return PymarcSubfield(code, val[0])
        return NullSubfield()

    def get_subfields(self, code: str = None) -> list[BaseSubfield]:
        if self.is_control_field:
            return []
        
        # If code is provided, filter; otherwise return all
        results = []
        if code:
            values = self.field.get_subfields(code)
            results = [PymarcSubfield(code, v) for v in values]
        else:
            for sf in self.field.subfields:
                results.append(PymarcSubfield(sf.code, sf.value))
        return results

    def __bool__(self) -> bool:
        return True

class PymarcRecord(BaseRecord):
    def __init__(self, record: pymarc.Record):
        self.record = record

    def get_field(self, tag: str) -> BaseField:
        # Handle Leader as a special case if tag is 'LDR' or 'leader'
        if tag.lower() in ['leader', 'ldr']:
            # pymarc records have a .leader attribute
            # We wrap it in a mock Field object to keep the interface consistent
            return PymarcLeaderField(str(self.record.leader))
            
        field = self.record.get_fields(tag)
        if field:
            return PymarcField(field[0])
        return NullField()

    def get_fields(self, tag: str) -> list[BaseField]:
        fields = self.record.get_fields(tag)
        return [PymarcField(f) for f in fields]

    def get_controlfields(self) -> list[BaseField]:
        """
        Returns the Leader and all fields with tags 001-009.
        """
        control_fields = [PymarcLeaderField(self.record.leader)]
        # pymarc.Record.fields contains all fields in order
        for field in self.record.fields:
            if field.is_control_field():
                control_fields.append(PymarcField(field))
        return control_fields

    def get_datafields(self) -> list[BaseField]:
        """
        Returns all fields with tags 010-999.
        """
        return [PymarcField(f) for f in self.record.fields if not f.is_control_field()]

    def __bool__(self) -> bool:
        return True

class PymarcLeaderField(BaseField):
    """
    Specialized wrapper for the Leader string to treat it as a Control Field.
    """
    def __init__(self, leader_str: str):
        self._leader = leader_str
    
    @property
    def tag(self) -> str: return "LDR"
    
    @property
    def value(self) -> str: return self._leader

    @property
    def data(self) -> str:
        """
        Alias for value to match pymarc's ControlField interface.
        """
        return self._leader
    
    @property
    def is_control_field(self) -> bool: return True
    
    @property
    def is_data_field(self) -> bool: return False
    
    @property
    def indicator1(self) -> str: return " "
    
    @property
    def indicator2(self) -> str: return " "
    
    def get_subfield(self, code): return NullSubfield()
    
    def get_subfields(self, code=None): return []
    
    def __bool__(self): return True