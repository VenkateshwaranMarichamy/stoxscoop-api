from __future__ import annotations

import enum


class EventType(str, enum.Enum):
    stake_transaction = "STAKE_TRANSACTION"
    contract = "CONTRACT"
    buyback = "BUYBACK"
    acquisition = "ACQUISITION"
    pledge = "PLEDGE"
    insider_trading = "INSIDER_TRADING"
    sebi_action = "SEBI_ACTION"
    fii_dii = "FII_DII"
    mutual_fund = "MUTUAL_FUND"
    credit_rating = "CREDIT_RATING"
    auditor_resignation = "AUDITOR_RESIGNATION"
    board_change = "BOARD_CHANGE"


class Priority(str, enum.Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"

