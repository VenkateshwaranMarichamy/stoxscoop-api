from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EventType, Priority
from app.schemas.common import APIModel
from app.schemas.event_details import (
    AcquisitionDetailsIn,
    AcquisitionDetailsRead,
    AuditorResignationDetailsIn,
    AuditorResignationDetailsRead,
    BoardChangeDetailsIn,
    BoardChangeDetailsRead,
    BuybackDetailsIn,
    BuybackDetailsRead,
    ContractDetailsIn,
    ContractDetailsRead,
    CreditRatingDetailsIn,
    CreditRatingDetailsRead,
    FiiDiiDetailsIn,
    FiiDiiDetailsRead,
    InsiderTradingDetailsIn,
    InsiderTradingDetailsRead,
    MutualFundDetailsIn,
    MutualFundDetailsRead,
    PledgeDetailsIn,
    PledgeDetailsRead,
    SebiActionDetailsIn,
    SebiActionDetailsRead,
    StakeTransactionDetailsIn,
    StakeTransactionDetailsRead,
)


class EventBase(BaseModel):
    stock_id: int
    batch_id: int | None = None
    event_type: EventType
    title: str = Field(min_length=1, max_length=500)
    event_date: date
    priority: Priority
    impact_score: int = Field(ge=1, le=10)
    # Frontend may send real URLs or short/plain text. Keep validation permissive.
    source_url: str | None = None

    stake_transaction_details: StakeTransactionDetailsIn | None = None
    contract_details: ContractDetailsIn | None = None
    buyback_details: BuybackDetailsIn | None = None
    acquisition_details: AcquisitionDetailsIn | None = None
    pledge_details: PledgeDetailsIn | None = None
    insider_trading_details: InsiderTradingDetailsIn | None = None
    sebi_action_details: SebiActionDetailsIn | None = None
    fii_dii_details: FiiDiiDetailsIn | None = None
    mutual_fund_details: MutualFundDetailsIn | None = None
    credit_rating_details: CreditRatingDetailsIn | None = None
    auditor_resignation_details: AuditorResignationDetailsIn | None = None
    board_change_details: BoardChangeDetailsIn | None = None

    @model_validator(mode="after")
    def validate_details_match_type(self) -> "EventBase":
        mapping = {
            EventType.stake_transaction: "stake_transaction_details",
            EventType.contract: "contract_details",
            EventType.buyback: "buyback_details",
            EventType.acquisition: "acquisition_details",
            EventType.pledge: "pledge_details",
            EventType.insider_trading: "insider_trading_details",
            EventType.sebi_action: "sebi_action_details",
            EventType.fii_dii: "fii_dii_details",
            EventType.mutual_fund: "mutual_fund_details",
            EventType.credit_rating: "credit_rating_details",
            EventType.auditor_resignation: "auditor_resignation_details",
            EventType.board_change: "board_change_details",
        }
        expected = mapping.get(self.event_type)
        if expected is None:
            return self
        provided = [k for k in mapping.values() if getattr(self, k) is not None]
        if len(provided) == 0:
            raise ValueError(f"Missing details payload: expected `{expected}` for event_type={self.event_type}")
        if len(provided) > 1:
            raise ValueError(f"Provide only one details payload; got {provided}")
        if provided[0] != expected:
            raise ValueError(f"Details payload mismatch: expected `{expected}` for event_type={self.event_type}")
        return self


class EventCreate(EventBase):
    pass


class EventRead(APIModel):
    id: int
    stock_id: int
    batch_id: int | None
    event_type: EventType
    title: str
    event_date: date
    priority: Priority
    impact_score: int
    source_url: str | None
    created_at: datetime

    stake_transaction_details: StakeTransactionDetailsRead | None = None
    contract_details: ContractDetailsRead | None = None
    buyback_details: BuybackDetailsRead | None = None
    acquisition_details: AcquisitionDetailsRead | None = None
    pledge_details: PledgeDetailsRead | None = None
    insider_trading_details: InsiderTradingDetailsRead | None = None
    sebi_action_details: SebiActionDetailsRead | None = None
    fii_dii_details: FiiDiiDetailsRead | None = None
    mutual_fund_details: MutualFundDetailsRead | None = None
    credit_rating_details: CreditRatingDetailsRead | None = None
    auditor_resignation_details: AuditorResignationDetailsRead | None = None
    board_change_details: BoardChangeDetailsRead | None = None

