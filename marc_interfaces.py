import abc


class BaseField(abc.ABC):
    @property
    @abc.abstractmethod
    def tag(self) -> str:
        return ""

    @property
    @abc.abstractmethod
    def indicator1(self) -> str:
        return " "

    @property
    @abc.abstractmethod
    def indicator2(self) -> str:    
        return " "

    @property
    @abc.abstractmethod
    def is_control_field(self) -> bool:
        return False

    @property
    @abc.abstractmethod
    def is_data_field(self) -> bool:
        return False

    @property
    @abc.abstractmethod
    def data(self) -> str   :
        return ""

    @abc.abstractmethod
    def get_subfield(self, code) -> BaseSubfield:
        return NullSubfield()

    @abc.abstractmethod
    def get_subfields(self, code=None) -> list[BaseSubfield]:
        return []

    @property
    @abc.abstractmethod
    def value(self) -> str:
        return ""

    @abc.abstractmethod
    def __bool__(self) -> bool:
        return False


class NullField(BaseField):
    @property
    def tag(self):
        return ""

    @property
    def indicator1(self):
        return " "

    @property
    def indicator2(self):
        return " "

    @property
    def is_control_field(self):
        return False

    @property
    def is_data_field(self):
        return False

    @property
    def data(self):
        return ""

    def get_subfield(self, code) -> BaseSubfield:
        return NullSubfield()

    def get_subfields(self, code=None) -> list[BaseSubfield]:
        return []

    @property
    def value(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return False


class BaseSubfield(abc.ABC):
    @property
    @abc.abstractmethod
    def code(self) -> str:
        return ""

    @property
    @abc.abstractmethod
    def value(self) -> str:
        return ""

    @abc.abstractmethod
    def __bool__(self) -> bool:
        return False

class NullSubfield(BaseSubfield):
    @property
    def code(self):
        return ""

    @property
    def value(self):
        return ""

    def __bool__(self):
        return False
    

    
class BaseRecord(abc.ABC):
    @abc.abstractmethod
    def get_field(self, tag: str) -> BaseField:
        return NullField()

    @abc.abstractmethod
    def get_fields(self, tag: str) -> list[BaseField]:
        return []

    @abc.abstractmethod
    def get_datafields(self) -> list[BaseField]:
        return []

    @abc.abstractmethod
    def get_controlfields(self) -> list[BaseField]:
        return []
