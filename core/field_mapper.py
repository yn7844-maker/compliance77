from models.schemas import Report, Registry, Target, Owner, Valuation

def map_registries(registries: list[Registry], evaluation_type: str) -> Report:
    report=Report(evaluation_type=evaluation_type)
    for registry in registries:
        report.facts.extend(registry.facts)
        report.rights.extend(registry.rights)
        def unique(field):
            values=list(dict.fromkeys(f.value for f in registry.facts if f.field==field and f.value))
            return values[0] if len(values)==1 else ""
        kind="집합건물" if evaluation_type=="집합건물" else ("토지" if unique("지목") else "건물")
        owners=[]
        for f in registry.facts:
            if f.field=="소유자":
                name,_,share=f.value.partition(" | ")
                if (name,share) not in [(o.name,o.share) for o in owners]: owners.append(Owner(name=name,share=share))
        report.targets.append(Target(kind=kind,address=unique("소재지"),owners=owners))
        report.valuations.append(Valuation(kind=kind,address=unique("소재지"),category=unique("지목"),area=unique("면적") or None))
    return report
