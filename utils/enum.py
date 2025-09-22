class SystemIdEnum(str, Enum):
    oneC = "1C"
    feib = "ФЭИБ"
    purchases = "ЗАКУПКИ"
    contract = "ДОГОВОР"
    brif = "БРИФ"

    @classmethod
    def as_list(cls) -> list[str]:
        return [e.value for e in cls]

   @classmethod
    def as_dict(cls) -> dict[str, str]:
        return {e.name: e.value for e in cls}
