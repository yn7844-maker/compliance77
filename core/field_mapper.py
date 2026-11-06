from decimal import Decimal
from models.schemas import Extraction, Target, Valuation

def unique_value(extraction: Extraction, field: str) -> str:
    values={x.value for x in extraction.candidates if x.field==field}
    return next(iter(values)) if len(values)==1 else ''

def suggest(extraction: Extraction, kind: str) -> tuple[Target,Valuation]:
    address=unique_value(extraction,'address')
    area=unique_value(extraction,'area')
    return (Target(kind=kind,address=address,owners=extraction.owners),
            Valuation(kind=kind,address=address,category=unique_value(extraction,'category'),area=Decimal(area) if area else None))
