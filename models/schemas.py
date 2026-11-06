from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="forbid")
    @field_validator("*", mode="after")
    @classmethod
    def finite(cls, value):
        if isinstance(value, Decimal) and not value.is_finite():
            raise ValueError("유한한 숫자만 허용됩니다")
        return value

class Evidence(Model):
    document_id: str = ""
    page: int = 1
    text: str = ""
    bbox: list[float] = Field(default_factory=list)
    ocr: bool = False
    confidence: float | None = None

class Fact(Model):
    field: str
    value: str = ""
    raw: str = ""
    status: Literal["추출됨", "사용자 확인 필요", "누락", "충돌", "사용자 확정"] = "추출됨"
    evidence: Evidence = Field(default_factory=Evidence)

class PageResult(Model):
    number: int
    text: str = ""
    words: list[dict] = Field(default_factory=list)
    ocr: bool = False
    confidence: float | None = None
    error: str | None = None
    rotation: int = 0

class Right(Model):
    id: str
    document_id: str = ""
    section: str = ""
    rank: str = ""
    received: str = ""
    kind: str = ""
    amount_raw: str = ""
    amount_won: Decimal | None = Field(default=None, ge=0)
    amount_thousand: Decimal | None = Field(default=None, ge=0)
    amount_not_applicable: bool = False
    creditor: str = ""
    debtor: str = ""
    cancellation: Literal["유효 추정", "말소", "검토 필요"] = "검토 필요"
    related_rank: str = ""
    deduction: bool = False
    reviewed: bool = False
    note: str = ""
    evidence: list[Evidence] = Field(default_factory=list)

class Registry(Model):
    document_id: str
    facts: list[Fact] = Field(default_factory=list)
    rights: list[Right] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class Request(Model):
    repeat: str = "최초"
    store: str = ""
    contract: str = "가맹A타입"
    purpose: str = "신규담보"
    amount: Decimal | None = Field(default=None, ge=0)
    considerations: str = ""

class Owner(Model):
    name: str = ""
    share: str = ""

class Target(Model):
    kind: str = "토지"
    address: str = ""
    debtor: str = ""
    owners: list[Owner] = Field(default_factory=list)
    duplicate: str = "미확인"
    related_store: str = ""

class Valuation(Model):
    kind: Literal["토지", "건물", "집합건물"] = "토지"
    address: str = ""
    category: str = ""
    area: Decimal | None = Field(default=None, ge=0)
    public_price: Decimal | None = Field(default=None, ge=0)
    rate: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)
    basis: str = ""
    reviewed: bool = False

class Deposits(Model):
    collective: Decimal | None = Field(default=None, ge=0)
    residential: Decimal | None = Field(default=None, ge=0)
    stores: int | None = Field(default=None, ge=0)
    commercial: Decimal | None = Field(default=None, ge=0)
    tenancy: Literal["미확인", "있음", "없음"] = "미확인"
    attachments: str = ""
    basis: str = ""
    reviewed: bool = False

class Audit(Model):
    field: str
    before: str = ""
    after: str = ""
    at: str

class Report(Model):
    schema_version: str = "1.0"
    evaluation_type: Literal["토지·건물", "집합건물"] = "토지·건물"
    written_on: date = Field(default_factory=date.today)
    request: Request = Field(default_factory=Request)
    targets: list[Target] = Field(default_factory=list)
    valuations: list[Valuation] = Field(default_factory=list)
    rights: list[Right] = Field(default_factory=list)
    deposits: Deposits = Field(default_factory=Deposits)
    duplicate: str = "미확인"
    opinion: str = ""
    completion: Literal["최종", "임차 미반영"] = "임차 미반영"
    rounding: Literal["미정", "정확값 유지", "절사", "반올림"] = "미정"
    registry_reviewed: bool = False
    attachments_reviewed: bool = False
    confirmed: bool = False
    facts: list[Fact] = Field(default_factory=list)
    audit: list[Audit] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)

class Totals(Model):
    valuation: Decimal | None = None
    senior: Decimal | None = None
    deposits: Decimal | None = None
    collateral: Decimal | None = None
    capacity: Decimal | None = None
    blockers: list[str] = Field(default_factory=list)
