from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

Status = Literal['추출됨', '사용자 확인 필요', '누락', '충돌', '사용자 확정']
Money = Decimal

class Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

class Evidence(Model):
    document: str = ''
    page: int = 1
    text: str = ''
    bbox: list[float] | None = None

class Candidate(Model):
    field: str
    raw: str
    value: str
    status: Status = '사용자 확인 필요'
    evidence: Evidence

class Owner(Model):
    name: str
    share: str = ''
    evidence: Evidence | None = None

class Right(Model):
    id: str
    section: str = ''
    rank: str = ''
    receipt_date: str = ''
    kind: str = ''
    amount_raw: str = ''
    amount_won: Decimal | None = None
    creditor: str = ''
    debtor: str = ''
    status: Literal['유효 여부 검토', '말소', '변경 검토', '유효 확인'] = '유효 여부 검토'
    target_rank: str = ''
    decision: Literal['미검토', '공제', '제외'] = '미검토'
    confirmed: bool = False
    notes: str = ''
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator('amount_won')
    @classmethod
    def valid_amount(cls, v):
        if v is not None and (not v.is_finite() or v < 0):
            raise ValueError('채권금액은 0 이상의 유한수여야 합니다.')
        return v

class Valuation(Model):
    kind: Literal['토지', '건물', '집합건물'] = '토지'
    address: str = ''
    category: str = ''
    area: Decimal | None = None
    public_price: Decimal | None = None
    rate: Decimal | None = None
    amount: Decimal | None = None
    basis: str = ''
    confirmed: bool = False

class Deposit(Model):
    a: Decimal | None = None
    b: Decimal | None = None
    c: Decimal | None = None
    shops: int | None = None
    tenancy: Literal['미확인', '있음', '없음'] = '미확인'
    reviewed: bool = False
    decision: Literal['미검토', '공제', '공제 없음'] = '미검토'
    basis: str = ''
    attachments: str = ''
    attachment_review: Literal['미검토', '확인', '해당 없음'] = '미검토'

class Target(Model):
    kind: str = '토지'
    address: str = ''
    debtor: str = ''
    owners: list[Owner] = Field(default_factory=list)
    duplicate: Literal['미확인', '있음', '없음'] = '미확인'
    stores: str = ''
    confirmed: bool = False

class Report(Model):
    evaluation_type: Literal['토지·건물', '집합건물'] = '토지·건물'
    re_request: str = ''
    store: str = ''
    contract: str = ''
    purpose: str = ''
    requested: Decimal | None = None
    considerations: str = ''
    targets: list[Target] = Field(default_factory=list)
    valuations: list[Valuation] = Field(default_factory=list)
    rights: list[Right] = Field(default_factory=list)
    rights_reviewed: bool = False
    deposit: Deposit = Field(default_factory=Deposit)
    opinion: str = ''
    completion: Literal['최종', '임차 미반영 비최종'] = '임차 미반영 비최종'
    reviewer: str = ''
    reviewed: bool = False
    rounding: Literal['정밀 유지', '절사', '반올림'] = '정밀 유지'
    rounding_confirmed: bool = False
    empty_tables: Literal['유지', '제거'] = '유지'
    evidence_reviewed: bool = False
    extraction_issues: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)

class PageResult(Model):
    number: int
    text: str = ''
    blocks: list[dict] = Field(default_factory=list)
    used_ocr: bool = False
    confidence: float | None = None
    rotation: int = 0
    error: str = ''

class Extraction(Model):
    document: str
    pages: list[PageResult] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
    owners: list[Owner] = Field(default_factory=list)
    rights: list[Right] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
