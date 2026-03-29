-- =============================================================================
-- STOXSCOOP — EVENT CLASSIFICATION SCHEMA
-- Version: 1.1.0
-- Updated: 2026-03-21
-- Changes: Added event_subtypes lookup table + full seed data (68 rows).
--          Composite FK on events(event_type, event_subtype) now DB-enforced.
--          Added v_subtype_catalogue view for backend dropdown APIs.
-- =============================================================================


-- =============================================================================
-- SECTION 1: ENUM TYPES
-- =============================================================================

CREATE TYPE event_type_enum AS ENUM (
    'corporate_action',
    'disclosure',
    'insider',
    'business',
    'governance',
    'credit_rating',
    'financials',
    'fundraising',
    'legal'
);

CREATE TYPE signal_type_enum AS ENUM (
    'BULLISH',
    'BEARISH',
    'NEUTRAL',
    'MIXED'
);

CREATE TYPE priority_enum AS ENUM (
    'low',
    'medium',
    'high'
);

CREATE TYPE sentiment_enum AS ENUM (
    'positive',
    'negative',
    'neutral'
);

CREATE TYPE ingestion_source_enum AS ENUM (
    'manual',
    'rss',
    'api',
    'scraper',
    'exchange_feed'
);

CREATE TYPE contract_type_enum AS ENUM (
    'MOU',
    'LOI',
    'CONFIRMED',
    'PARTNERSHIP',
    'RENEWAL',
    'AMENDMENT'
);

CREATE TYPE transaction_type_enum AS ENUM (
    'buy',
    'sell',
    'increase',
    'decrease',
    'pledge',
    'revoke'
);

CREATE TYPE transaction_mode_enum AS ENUM (
    'bulk_deal',
    'block_deal',
    'open_market',
    'off_market'
);

CREATE TYPE investor_category_enum AS ENUM (
    'superinvestor',
    'fii',
    'dii',
    'hni',
    'mutual_fund',
    'insurance',
    'corporate_body',
    'other'
);

CREATE TYPE rating_agency_enum AS ENUM (
   'CRISIL',
    'ICRA',
    'CARE',
    'INDIA_RATINGS',
    'FITCH',
    'MOODYS',
    'SP_GLOBAL'
);

CREATE TYPE outcome_enum AS ENUM (
    'favorable',
    'adverse',
    'pending',
    'settled'
);

CREATE TYPE beat_miss_enum AS ENUM (
    'beat',
    'miss',
    'inline'
);


-- =============================================================================
-- SECTION 2: SUBTYPE LOOKUP TABLE
-- Replaces ENUM for event_subtype entirely.
-- Composite UNIQUE (event_type, subtype_code) enforces valid pairs.
-- The FK in events references this — DB validates every insert.
-- Adding a new subtype = one INSERT, zero migrations, zero downtime.
-- =============================================================================

CREATE TABLE event_subtypes (
    id              SERIAL              PRIMARY KEY,
    event_type      event_type_enum     NOT NULL,
    subtype_code    VARCHAR(80)         NOT NULL,
    label           VARCHAR(120)        NOT NULL,
    description     TEXT,
    default_signal  signal_type_enum    NOT NULL DEFAULT 'NEUTRAL',
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ,

    CONSTRAINT uq_event_subtype UNIQUE (event_type, subtype_code)
);

COMMENT ON TABLE event_subtypes IS
    'Reference table for all valid event subtypes per event_type. '
    'Composite UNIQUE enforces that e.g. dividend is only valid under '
    'corporate_action.';

COMMENT ON COLUMN event_subtypes.default_signal IS
    'Starting signal_type for the ingestion pipeline. AI classifier '
    'overrides this only where evidence warrants. Saves the model from '
    'having to learn obvious defaults like auditor_resignation=BEARISH.';

COMMENT ON COLUMN event_subtypes.subtype_code IS
    'Snake_case code stored in events.event_subtype. Never rename after '
    'first use — historical rows reference this value. Add a new row instead.';


-- =============================================================================
-- SECTION 3: CORE TABLES
-- =============================================================================

CREATE TABLE event_batches (
    id               SERIAL                NOT NULL PRIMARY KEY,
    batch_name       VARCHAR(255)          NOT NULL,
    ingestion_source ingestion_source_enum NOT NULL DEFAULT 'manual',
    notes            TEXT,
    started_at       TIMESTAMPTZ           NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    total_events     INTEGER               DEFAULT 0,
    created_at       TIMESTAMPTZ           NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

COMMENT ON TABLE event_batches IS
    'Tracks each ingestion run — manual, RSS, API, scraper, or exchange feed.';


CREATE TABLE events (
    id                          SERIAL                NOT NULL PRIMARY KEY,
    stock_id                    INTEGER               NOT NULL,
    batch_id                    INTEGER               REFERENCES event_batches(id) ON DELETE SET NULL,

    -- Classification — composite FK enforces valid type+subtype pair
    event_type                  event_type_enum       NOT NULL,
    event_subtype               VARCHAR(80)           NOT NULL,

    -- AI signals
    signal_type                 signal_type_enum      NOT NULL DEFAULT 'NEUTRAL',
    signal_reason               TEXT,
    sentiment                   sentiment_enum        NOT NULL DEFAULT 'neutral',
    priority                    priority_enum         NOT NULL DEFAULT 'low',
    impact_score                INTEGER,
    -- CHECK confidence_score BETWEEN 0 AND 1
    confidence_score            NUMERIC(4,3),
    confidence_model_version    VARCHAR(30),

    -- Flexible labelling
    tags                        TEXT[]                DEFAULT '{}',

    -- Content
    title                       VARCHAR(500)          NOT NULL,
    summary                     TEXT,
    event_date                  DATE                  NOT NULL,

    -- Source tracking
    source_url                  TEXT,
    source_name                 VARCHAR(100),
    ingestion_source            ingestion_source_enum NOT NULL DEFAULT 'manual',

    -- Quality flag
    is_verified                 BOOLEAN               NOT NULL DEFAULT FALSE,
    is_active                   BOOLEAN               NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ           NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ,

    CONSTRAINT fk_events_stock
        FOREIGN KEY (stock_id) REFERENCES classification.ticker_symbol(id) ON DELETE CASCADE,

    -- Composite FK: ensures (event_type, event_subtype) is a seeded valid pair
    CONSTRAINT fk_events_subtype
        FOREIGN KEY (event_type, event_subtype)
        REFERENCES event_subtypes (event_type, subtype_code),

    -- confidence_model_version is mandatory whenever confidence_score is set
    CONSTRAINT chk_confidence_version
        CHECK (confidence_score IS NULL OR confidence_model_version IS NOT NULL)
);

COMMENT ON TABLE events IS
    'Central event table. event_subtype is the single source of truth — '
    'never duplicated in detail tables. Composite FK to event_subtypes '
    'ensures only seeded type+subtype pairs can be inserted.';

COMMENT ON COLUMN events.event_subtype IS
    'References event_subtypes.subtype_code. Validated at DB level via '
    'composite FK with event_type.';

COMMENT ON COLUMN events.confidence_score IS
    'AI confidence 0.000–1.000. confidence_model_version must be set '
    'when this field is populated (enforced by CHECK constraint).';

COMMENT ON COLUMN events.confidence_model_version IS
    'Model/version string that produced confidence_score, '
    'e.g. "v2.1" or "gpt4-ft-mar26". Enables cross-version comparison '
    'and targeted re-scoring after retrains.';

COMMENT ON COLUMN events.tags IS
    'Free-form text labels. Auto-populated by trigger; augmented by app '
    'after detail row insert. GIN indexed. Query: WHERE tags @> ''{bulk_deal}''';


-- =============================================================================
-- SECTION 4: EVENT DETAIL TABLES
-- Strict 1-to-1 with events via UNIQUE event_id.
-- event_subtype is NOT stored here — always read from events.event_subtype.
-- =============================================================================

-- 4a. Corporate actions
CREATE TABLE corporate_action_details (
    id                  SERIAL          NOT NULL PRIMARY KEY,
    event_id            INTEGER         NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    record_date         DATE,
    effective_date      DATE,
    ratio               VARCHAR(30),            -- '1:2' split, '1:5' bonus
    amount_per_share    NUMERIC(18,4),          -- dividend or buyback price
    total_size          NUMERIC(18,2),          -- total deal size in crores
    currency            VARCHAR(3)              DEFAULT 'INR',
    target_company      VARCHAR(255),           -- merger / demerger counterparty
    swap_ratio          VARCHAR(30),            -- share exchange ratio
    offer_price         NUMERIC(18,2),          -- open offer price per share
    stake_acquired_pct  NUMERIC(5,2),           -- % stake acquired in the transaction
    resulting_stake_pct NUMERIC(5,2),           -- % stake held after the transaction
    shares_transacted   BIGINT,                 -- number of shares acquired / tendered
    description         TEXT
);

COMMENT ON TABLE corporate_action_details IS
    'Covers: dividend, bonus, split, rights_issue, buyback, '
    'merger, demerger, open_offer.';


-- 4b. Disclosures
CREATE TABLE disclosure_details (
    id                  SERIAL                  NOT NULL PRIMARY KEY,
    event_id            INTEGER                 NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    investor_category   investor_category_enum  NOT NULL,
    investor_name       VARCHAR(255),
    investor_country    VARCHAR(100),           -- for FII — home country
    transaction_type    transaction_type_enum   NOT NULL,
    transaction_mode    transaction_mode_enum,
    shares_transacted   BIGINT,
    price_per_share     NUMERIC(18,4),
    transaction_value   NUMERIC(18,2),          -- crores
    currency            VARCHAR(3)              DEFAULT 'INR',
    stake_before        NUMERIC(8,4),
    stake_after         NUMERIC(8,4),
    stake_change        NUMERIC(8,4)            -- auto-computed, always in sync
                        GENERATED ALWAYS AS (stake_after - stake_before) STORED,
    transaction_date    DATE,
    exchange            VARCHAR(10)             -- NSE | BSE
);

COMMENT ON TABLE disclosure_details IS
    'FII/DII/HNI/Superinvestor shareholding changes and bulk/block deals. '
    'stake_change is a GENERATED column — never manually updated.';


-- 4c. Insider activity
CREATE TABLE insider_details (
    id                      SERIAL                      NOT NULL PRIMARY KEY,
    event_id                INTEGER                     NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    person_name             VARCHAR(255)                NOT NULL,
    designation             VARCHAR(100),
    relationship            VARCHAR(100),
    transaction_type        transaction_type_enum       NOT NULL,
    shares_transacted       BIGINT,
    price_per_share         NUMERIC(18,4),
    transaction_value       NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    stake_before            NUMERIC(8,4),
    stake_after             NUMERIC(8,4),
    pledge_percentage       NUMERIC(8,4),               -- % of total promoter holding pledged
    sebi_disclosure_date    DATE,
    transaction_date        DATE
);

COMMENT ON TABLE insider_details IS
    'Covers: insider_buy, insider_sell, pledge, pledge_release, '
    'acquisition, esop_exercise, creeping_acquisition.';


-- 4d. Business events
CREATE TABLE business_event_details (
    id                  SERIAL                  NOT NULL PRIMARY KEY,
    event_id            INTEGER                 NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    contract_type       contract_type_enum,
    client_name         VARCHAR(255),
    client_sector       VARCHAR(100),
    contract_value      NUMERIC(18,2),
    capex_amount        NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    duration_years      NUMERIC(5,1),
    geography           VARCHAR(100),
    project_name        VARCHAR(255),
    expected_completion DATE,
    jv_partner          VARCHAR(255),
    ownership_pct       NUMERIC(5,2),
    is_repeat_order     BOOLEAN                 DEFAULT FALSE,
    description         TEXT
);

COMMENT ON TABLE business_event_details IS
    'Covers: contract, order_win, capex, jv_partnership, new_product, '
    'expansion, plant_commissioning, divestiture.';

COMMENT ON COLUMN business_event_details.contract_type IS
    'MOU/LOI carry lower impact weight than CONFIRMED. '
    'Pipeline uses this to calibrate impact_score before AI pass.';


-- 4e. Governance
CREATE TABLE governance_details (
    id                  SERIAL          NOT NULL PRIMARY KEY,
    event_id            INTEGER         NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    person_name         VARCHAR(255),
    designation         VARCHAR(100),
    change_type         VARCHAR(30),
    effective_date      DATE,
    reason              TEXT,
    regulator           VARCHAR(50),
    action_type         VARCHAR(100),
    penalty_amount      NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    meeting_date        DATE,
    agenda_summary      TEXT
);

COMMENT ON TABLE governance_details IS
    'Covers: board_appointment, board_resignation, auditor_appointment, '
    'auditor_resignation, sebi_action, regulatory_notice, agm, egm, policy_change.';


-- 4f. Credit ratings
CREATE TABLE credit_rating_details (
    id                  SERIAL                  NOT NULL PRIMARY KEY,
    event_id            INTEGER                 NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    agency              rating_agency_enum      NOT NULL,
    instrument_type     VARCHAR(100),
    instrument_name     VARCHAR(255),
    rating_before       VARCHAR(20),
    rating_after        VARCHAR(20),
    outlook_before      VARCHAR(20),
    outlook_after       VARCHAR(20),
    rated_amount        NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    rationale           TEXT,
    rating_date         DATE
);

COMMENT ON TABLE credit_rating_details IS
    'Covers: upgrade, downgrade, watch_positive, watch_negative, affirmed, withdrawn.';


-- 4g. Financial results
CREATE TABLE financial_result_details (
    id                  SERIAL              NOT NULL PRIMARY KEY,
    event_id            INTEGER             NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    period_quarter      VARCHAR(5),
    period_year         INTEGER,
    revenue             NUMERIC(18,2),
    revenue_yoy_pct     NUMERIC(8,2),
    ebitda              NUMERIC(18,2),
    ebitda_margin       NUMERIC(8,2),
    pat                 NUMERIC(18,2),
    pat_yoy_pct         NUMERIC(8,2),
    eps                 NUMERIC(10,4),
    beat_miss           beat_miss_enum,
    guidance_revenue    VARCHAR(100),
    guidance_margin     VARCHAR(100),
    currency            VARCHAR(3)              DEFAULT 'INR',
    key_highlight       TEXT
);

COMMENT ON TABLE financial_result_details IS
    'Covers: quarterly_results, annual_results, provisional_numbers, '
    'restatement, guidance_upgrade, guidance_downgrade, guidance_maintained.';


-- 4h. Fundraising
CREATE TABLE fundraising_details (
    id                  SERIAL          NOT NULL PRIMARY KEY,
    event_id            INTEGER         NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    issue_size          NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    price_per_share     NUMERIC(18,4),
    number_of_shares    BIGINT,
    allottee_name       VARCHAR(255),
    allottee_category   VARCHAR(50),
    coupon_rate         NUMERIC(6,2),
    maturity_date       DATE,
    tenure_years        NUMERIC(5,1),
    purpose             TEXT,
    open_date           DATE,
    close_date          DATE,
    subscription_times  NUMERIC(8,2)
);

COMMENT ON TABLE fundraising_details IS
    'Covers: qip, preferential_allotment, ncd, bond, ipo, fpo, '
    'debt_repayment, rights_issue, private_placement.';


-- 4i. Legal & litigation
CREATE TABLE legal_details (
    id                      SERIAL              NOT NULL PRIMARY KEY,
    event_id                INTEGER             NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
    forum                   VARCHAR(100),
    case_number             VARCHAR(100),
    counterparty            VARCHAR(255),
    demand_amount           NUMERIC(18,2),
    penalty_amount          NUMERIC(18,2),
    currency            VARCHAR(3)              DEFAULT 'INR',
    company_stance          VARCHAR(20),
    outcome                 outcome_enum        DEFAULT 'pending',
    order_date              DATE,
    next_hearing_date       DATE,
    contingent_liability    BOOLEAN             DEFAULT FALSE,
    description             TEXT
);

COMMENT ON TABLE legal_details IS
    'Covers: court_order, arbitration, tax_demand, ibc_filing, '
    'penalty, notice, settlement.';


-- =============================================================================
-- SECTION 5: INDEXES
-- =============================================================================

-- Primary access pattern
CREATE INDEX idx_events_stock_date          ON events (stock_id, event_date DESC);

-- Classification screener
CREATE INDEX idx_events_type_subtype        ON events (event_type, event_subtype);

-- Signal / priority / sentiment filters
CREATE INDEX idx_events_signal              ON events (signal_type);
CREATE INDEX idx_events_priority            ON events (priority);
CREATE INDEX idx_events_sentiment           ON events (sentiment);

-- AI quality filter — WHERE confidence_score >= 0.75
CREATE INDEX idx_events_confidence          ON events (confidence_score);

-- Tags array containment — WHERE tags @> '{bulk_deal}'
CREATE INDEX idx_events_tags                ON events USING GIN (tags);

-- Batch + audit
CREATE INDEX idx_events_batch               ON events (batch_id, created_at DESC);
CREATE INDEX idx_events_ingestion_source    ON events (ingestion_source, created_at DESC);
CREATE INDEX idx_active_events ON events(event_date) WHERE is_active = TRUE;

-- Date range
CREATE INDEX idx_events_event_date          ON events (event_date DESC);


-- Detail table filters
CREATE INDEX idx_disclosure_category        ON disclosure_details (investor_category);
CREATE INDEX idx_disclosure_investor        ON disclosure_details (investor_name);
CREATE INDEX idx_insider_person             ON insider_details (person_name);
CREATE INDEX idx_business_contract_type     ON business_event_details (contract_type);
CREATE INDEX idx_credit_agency              ON credit_rating_details (agency);
CREATE INDEX idx_legal_outcome              ON legal_details (outcome);


-- =============================================================================
-- SECTION 6: AUTO-TAGGING TRIGGER
-- Fires BEFORE INSERT OR UPDATE on events.
-- Detail-table-level tags (repeat_order, high_value etc.)
-- are appended by application code after the detail row is written.
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_auto_tag_event()
RETURNS TRIGGER AS $$
DECLARE
    v_tags TEXT[] := COALESCE(NEW.tags, '{}');
BEGIN
    -- Confidence bands
    IF NEW.confidence_score IS NOT NULL AND NEW.confidence_score >= 0.85 THEN
        v_tags := array_append(v_tags, 'high_confidence');
    ELSIF NEW.confidence_score IS NOT NULL AND NEW.confidence_score < 0.5 THEN
        v_tags := array_append(v_tags, 'low_confidence');
    END IF;

    -- Signal direction
    IF    NEW.signal_type = 'BULLISH' THEN v_tags := array_append(v_tags, 'bullish');
    ELSIF NEW.signal_type = 'BEARISH' THEN v_tags := array_append(v_tags, 'bearish');
    END IF;

    -- Verification state (removed when verified later)
    IF NEW.is_verified = FALSE THEN
        v_tags := array_append(v_tags, 'unverified');
    ELSE
        v_tags := array_remove(v_tags, 'unverified');
    END IF;

    -- Manual entry flag
    IF NEW.ingestion_source = 'manual' THEN
        v_tags := array_append(v_tags, 'manual_entry');
    END IF;

    -- Deduplicate
    NEW.tags := ARRAY(SELECT DISTINCT unnest(v_tags) ORDER BY 1);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_tag_event
    BEFORE INSERT OR UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION fn_auto_tag_event();

-- ----------------------------------------------------------------------------
-- App-level tags — add these after writing the detail row:
--
-- business_event_details
--   is_repeat_order = TRUE              → 'repeat_order'
--   contract_value  > 100               → 'high_value'
--   contract_value  > 1000              → 'large_deal'
--   contract_type IN ('MOU','LOI')      → 'mou_only'
--   geography NOT LIKE '%Domestic%'     → 'international'
--
-- disclosure_details
--   investor_category = 'superinvestor' → 'superinvestor'
--   ABS(stake_change) > 1.0             → 'significant_stake_change'
--   transaction_mode = 'bulk_deal'      → 'bulk_deal'
--   transaction_mode = 'block_deal'     → 'block_deal'
--
-- insider_details
--   pledge_percentage > 50              → 'high_pledge'
--   transaction_type = 'pledge'         → 'pledge'
--   relationship = 'promoter'           → 'promoter_activity'
--
-- legal_details
--   contingent_liability = TRUE         → 'contingent_liability'
--   demand_amount > 100                 → 'large_demand'
--
-- credit_rating_details
--   subtype = 'downgrade'               → 'rating_downgrade'
-- ----------------------------------------------------------------------------


-- =============================================================================
-- SECTION 7: SEED DATA — event_subtypes (68 rows)
-- default_signal is the pipeline's starting signal_type before AI override.
-- sort_order controls display order in frontend dropdowns.
-- =============================================================================

INSERT INTO event_subtypes
    (event_type, subtype_code, label, description, default_signal)
VALUES

-- ── Corporate actions ────────────────────────────────────────────────────────
('corporate_action','dividend',      'Dividend',      'Cash payout to shareholders from profits',                            'BULLISH'),
('corporate_action','bonus',         'Bonus issue',   'Free shares issued proportionally to existing holders',               'BULLISH'),
('corporate_action','split',         'Stock split',   'Share face value reduced, total count increases',                     'NEUTRAL'),
('corporate_action','rights_issue',  'Rights issue',  'New shares offered to existing holders at a discount',                'MIXED'),
('corporate_action','buyback',       'Buyback',       'Company repurchases its own shares from the market',                  'BULLISH'),
('corporate_action','merger',        'Merger',        'Company merges with another entity',                                  'MIXED'),
('corporate_action','demerger',      'Demerger',      'Business unit spun off as a separate listed entity',                  'MIXED'),
('corporate_action','open_offer',    'Open offer',    'Public offer to acquire shares from minority holders',                 'MIXED'),

-- ── Disclosures ──────────────────────────────────────────────────────────────
('disclosure','bulk_deal',           'Bulk deal',             'Trade > 0.5% of equity in a single exchange session',         'NEUTRAL'),
('disclosure','block_deal',          'Block deal',            'Large off-market negotiated trade between institutions',        'NEUTRAL'),
('disclosure','shareholding_change', 'Shareholding change',   'Quarterly shareholding pattern update filed with exchange',    'NEUTRAL'),
('disclosure','fii_buy',             'FII buy',               'Foreign institutional investor increases holding',             'BULLISH'),
('disclosure','fii_sell',            'FII sell',              'Foreign institutional investor reduces holding',               'BEARISH'),
('disclosure','dii_buy',             'DII buy',               'Domestic institutional investor increases holding',            'BULLISH'),
('disclosure','dii_sell',            'DII sell',              'Domestic institutional investor reduces holding',              'BEARISH'),
('disclosure','superinvestor_buy',   'Superinvestor buy',     'Notable investor discloses purchase',                         'BULLISH'),
('disclosure','superinvestor_sell',  'Superinvestor sell',    'Notable investor discloses sale',                             'BEARISH'),
('disclosure','mutual_fund_change',  'Mutual fund change',    'Mutual fund increases or reduces holding',                    'NEUTRAL'),

-- ── Insider activity ─────────────────────────────────────────────────────────
('insider','insider_buy',            'Insider buy',           'Director / KMP buys shares in open market',                   'BULLISH'),
('insider','insider_sell',           'Insider sell',          'Director / KMP sells shares in open market',                  'BEARISH'),
('insider','pledge',                 'Pledge',                'Promoter pledges shares as collateral for a loan',            'BEARISH'),
('insider','pledge_release',         'Pledge release',        'Promoter releases previously pledged shares',                 'BULLISH'),
('insider','acquisition',            'Acquisition',           'Promoter acquires additional stake',                          'BULLISH'),
('insider','esop_exercise',          'ESOP exercise',         'Employee stock options exercised by management',              'NEUTRAL'),
('insider','creeping_acquisition',   'Creeping acquisition',  'Gradual stake increase by promoter over time',               'BULLISH'),

-- ── Business events ──────────────────────────────────────────────────────────
('business','contract',              'Contract',              'New client or supplier contract signed',                      'BULLISH'),
('business','order_win',             'Order win',             'New order received from a customer',                          'BULLISH'),
('business','capex',                 'Capex',                 'Capital expenditure announced for new assets or capacity',    'MIXED'),
('business','jv_partnership',        'JV / partnership',      'Joint venture or strategic partnership formed',               'MIXED'),
('business','new_product',           'New product',           'New product or service launched or announced',                'BULLISH'),
('business','expansion',             'Expansion',             'Geographic or manufacturing capacity expansion announced',    'BULLISH'),
('business','plant_commissioning',   'Plant commissioning',   'New manufacturing plant or facility goes live',               'BULLISH'),
('business','divestiture',           'Divestiture',           'Non-core business unit or asset sold or divested',           'MIXED'),

-- ── Governance ───────────────────────────────────────────────────────────────
('governance','board_appointment',   'Board appointment',     'New director or executive appointed to the board',           'NEUTRAL'),
('governance','board_resignation',   'Board resignation',     'Director or executive resigns from the board',               'BEARISH'),
('governance','auditor_appointment', 'Auditor appointment',   'New statutory auditor appointed by shareholders',            'NEUTRAL'),
('governance','auditor_resignation', 'Auditor resignation',   'Statutory auditor resigns — high-signal red flag',           'BEARISH'),
('governance','sebi_action',         'SEBI action',           'SEBI issues show-cause, penalty or trading restriction',     'BEARISH'),
('governance','regulatory_notice',   'Regulatory notice',     'Notice received from MCA, RBI, IRDAI or other regulator',   'BEARISH'),
('governance','agm',                 'AGM',                   'Annual general meeting held or scheduled',                   'NEUTRAL'),
('governance','egm',                 'EGM',                   'Extraordinary general meeting held or scheduled',            'NEUTRAL'),
('governance','policy_change',       'Policy change',         'Company policy, articles or memorandum amended',             'NEUTRAL'),

-- ── Credit & ratings ─────────────────────────────────────────────────────────
('credit_rating','upgrade',          'Rating upgrade',        'Credit rating improved by the rating agency',                'BULLISH'),
('credit_rating','downgrade',        'Rating downgrade',      'Credit rating reduced by the rating agency',                 'BEARISH'),
('credit_rating','watch_positive',   'Watch positive',        'Rating placed on positive credit watch',                     'BULLISH'),
('credit_rating','watch_negative',   'Watch negative',        'Rating placed on negative credit watch',                     'BEARISH'),
('credit_rating','affirmed',         'Rating affirmed',       'Rating confirmed without change by agency',                  'NEUTRAL'),
('credit_rating','withdrawn',        'Rating withdrawn',      'Rating withdrawn — issuer request or non-cooperation',       'NEUTRAL'),

-- ── Financial results ────────────────────────────────────────────────────────
('financials','quarterly_results',   'Quarterly results',     'Q1/Q2/Q3/Q4 earnings release',                              'NEUTRAL'),
('financials','annual_results',      'Annual results',        'Full year audited earnings release',                         'NEUTRAL'),
('financials','provisional_numbers', 'Provisional numbers',   'Unaudited early revenue or profit estimate',                 'NEUTRAL'),
('financials','restatement',         'Restatement',           'Prior period results restated — accounting red flag',        'BEARISH'),
('financials','guidance_upgrade',    'Guidance upgrade',      'Management raises revenue or margin guidance',               'BULLISH'),
('financials','guidance_downgrade',  'Guidance downgrade',    'Management lowers revenue or margin guidance',               'BEARISH'),
('financials','guidance_maintained', 'Guidance maintained',   'Management confirms guidance unchanged at results',          'NEUTRAL'),

-- ── Fundraising ──────────────────────────────────────────────────────────────
('fundraising','qip',                'QIP',                   'Qualified institutional placement to institutions',          'MIXED'),
('fundraising','preferential_allotment','Preferential allotment','Shares allotted to specific named investors',            'MIXED'),
('fundraising','ncd',                'NCD',                   'Non-convertible debenture issued',                           'NEUTRAL'),
('fundraising','bond',               'Bond',                  'Secured or unsecured bond issuance',                         'NEUTRAL'),
('fundraising','ipo',                'IPO',                   'Initial public offering',                                    'NEUTRAL'),
('fundraising','fpo',                'FPO',                   'Follow-on public offering by existing listed company',       'MIXED'),
('fundraising','rights_issue',       'Rights issue',          'Capital raise via rights offering to existing holders',      'MIXED'),
('fundraising','private_placement',  'Private placement',     'Off-market capital raise from select investors',             'NEUTRAL'),
('fundraising','debt_repayment',     'Debt repayment',        'Loan or bond repaid ahead of or at scheduled maturity',     'BULLISH'),

-- ── Legal & litigation ───────────────────────────────────────────────────────
('legal','court_order',              'Court order',           'Order from High Court or Supreme Court',                     'NEUTRAL'),
('legal','arbitration',              'Arbitration',           'Arbitration proceeding initiated, ongoing, or decided',      'NEUTRAL'),
('legal','tax_demand',               'Tax demand',            'Income tax or GST demand raised against the company',        'BEARISH'),
('legal','ibc_filing',               'IBC filing',            'Insolvency petition filed under IBC at NCLT',               'BEARISH'),
('legal','penalty',                  'Penalty',               'Regulatory or court penalty imposed on the company',         'BEARISH'),
('legal','notice',                   'Notice',                'Show cause or legal notice received',                        'BEARISH'),
('legal','settlement',               'Settlement',            'Legal or regulatory dispute settled out of court',           'BULLISH');

-- =============================================================================
-- END OF DDL
-- Version   : 1.1.0
-- Tables    : 11 (event_batches, event_subtypes, events, + 8 detail tables)
-- ENUMs     : 14
-- Indexes   : 18
-- Triggers  : 1  (fn_auto_tag_event)
-- Views     : 4  (v_event_feed, v_review_queue, v_model_confidence_summary,
--                 v_subtype_catalogue)
-- Seed rows : 68 (event_subtypes — 9 event types × 6–10 subtypes each)
-- =============================================================================
