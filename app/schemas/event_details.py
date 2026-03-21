from __future__ import annotations

from datetime import date
import enum
from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class ContractType(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    MOU = "MOU"
    STRATEGIC_PARTNERSHIP = "STRATEGIC_PARTNERSHIP"


class StakeTransactionDetailsIn(BaseModel):
    investor_name: str = Field(min_length=1, max_length=255)
    transaction_type: str = Field(min_length=1, max_length=100)
    stake_percentage: float | None = None
    transaction_value: float | None = None
    price_per_share: float | None = None
    transaction_date: date | None = None


class ContractDetailsIn(BaseModel):
    client_name: str = Field(min_length=1, max_length=255)
    contract_type: ContractType = Field(min_length=1, max_length=50)
    contract_value: float | None = None
    duration_years: int | None = None
    description: str | None = None


class BuybackDetailsIn(BaseModel):
    buyback_type: str | None = Field(default=None, max_length=100)
    buyback_price: float | None = None
    total_size: float | None = None
    record_date: date | None = None


class AcquisitionDetailsIn(BaseModel):
    target_company: str = Field(min_length=1, max_length=255)
    deal_value: float | None = None
    stake_percentage: float | None = None


class PledgeDetailsIn(BaseModel):
    promoter_name: str = Field(min_length=1, max_length=255)
    before_percentage: float | None = None
    after_percentage: float | None = None
    change_type: str | None = Field(default=None, max_length=100)


class InsiderTradingDetailsIn(BaseModel):
    insider_name: str = Field(min_length=1, max_length=255)
    designation: str | None = Field(default=None, max_length=255)
    transaction_type: str = Field(min_length=1, max_length=100)
    quantity: int | None = None
    price: float | None = None


class SebiActionDetailsIn(BaseModel):
    action_type: str = Field(min_length=1, max_length=255)
    description: str | None = None
    penalty_amount: float | None = None


class FiiDiiDetailsIn(BaseModel):
    investor_type: str = Field(min_length=1, max_length=50)
    transaction_type: str = Field(min_length=1, max_length=100)
    amount: float | None = None


class MutualFundDetailsIn(BaseModel):
    fund_name: str = Field(min_length=1, max_length=255)
    transaction_type: str = Field(min_length=1, max_length=100)
    stake_change: float | None = None


class CreditRatingDetailsIn(BaseModel):
    agency: str = Field(min_length=1, max_length=255)
    rating_before: str | None = Field(default=None, max_length=50)
    rating_after: str | None = Field(default=None, max_length=50)


class AuditorResignationDetailsIn(BaseModel):
    auditor_name: str = Field(min_length=1, max_length=255)
    reason: str | None = None


class BoardChangeDetailsIn(BaseModel):
    person_name: str = Field(min_length=1, max_length=255)
    designation: str | None = Field(default=None, max_length=255)
    event_type: str | None = Field(default=None, max_length=100)


class StakeTransactionDetailsRead(APIModel):
    investor_name: str
    transaction_type: str
    stake_percentage: float | None
    transaction_value: float | None
    price_per_share: float | None
    transaction_date: date | None


class ContractDetailsRead(APIModel):
    client_name: str
    contract_type: ContractType | None
    contract_value: float | None
    duration_years: int | None
    description: str | None


class BuybackDetailsRead(APIModel):
    buyback_type: str | None
    buyback_price: float | None
    total_size: float | None
    record_date: date | None


class AcquisitionDetailsRead(APIModel):
    target_company: str
    deal_value: float | None
    stake_percentage: float | None


class PledgeDetailsRead(APIModel):
    promoter_name: str
    before_percentage: float | None
    after_percentage: float | None
    change_type: str | None


class InsiderTradingDetailsRead(APIModel):
    insider_name: str
    designation: str | None
    transaction_type: str
    quantity: int | None
    price: float | None


class SebiActionDetailsRead(APIModel):
    action_type: str
    description: str | None
    penalty_amount: float | None


class FiiDiiDetailsRead(APIModel):
    investor_type: str
    transaction_type: str
    amount: float | None


class MutualFundDetailsRead(APIModel):
    fund_name: str
    transaction_type: str
    stake_change: float | None


class CreditRatingDetailsRead(APIModel):
    agency: str
    rating_before: str | None
    rating_after: str | None


class AuditorResignationDetailsRead(APIModel):
    auditor_name: str
    reason: str | None


class BoardChangeDetailsRead(APIModel):
    person_name: str
    designation: str | None
    event_type: str | None

