
-- ipo master

CREATE TABLE IF NOT EXISTS ipos (

    id BIGSERIAL PRIMARY KEY,

    external_id TEXT UNIQUE NOT NULL,

    symbol TEXT,

    name TEXT NOT NULL,

    isin TEXT,

    issue_type TEXT,

    industry TEXT,

    issue_size DOUBLE PRECISION,

    price_min DOUBLE PRECISION,

    price_max DOUBLE PRECISION,

    face_value DOUBLE PRECISION,

    lot_size INTEGER,

    minimum_quantity INTEGER,

    cutoff_price DOUBLE PRECISION,

    listing_price DOUBLE PRECISION,

    listing_exchange TEXT,

    status TEXT,

    bidding_start TIMESTAMPTZ,

    bidding_end TIMESTAMPTZ,

    allotment_date TIMESTAMPTZ,

    refund_date TIMESTAMPTZ,

    listing_date TIMESTAMPTZ,

    registrar TEXT,

    registrar_email TEXT,

    registrar_phone TEXT,

    registrar_website TEXT,

    rhp_url TEXT,

    drhp_url TEXT,

    subscription TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ

);



CREATE INDEX IF NOT EXISTS idx_ipos_status ON ipos(status);

CREATE INDEX IF NOT EXISTS idx_ipos_registrar ON ipos(registrar);

CREATE INDEX IF NOT EXISTS idx_ipos_name ON ipos(name);



-- gmp current

CREATE TABLE IF NOT EXISTS ipo_gmp (

    id BIGSERIAL PRIMARY KEY,

    ipo_id BIGINT NOT NULL REFERENCES ipos(id) ON DELETE CASCADE,

    gmp_price DOUBLE PRECISION,

    gmp_percentage DOUBLE PRECISION,

    estimated_listing_price DOUBLE PRECISION,

    source TEXT NOT NULL,

    source_updated_at TIMESTAMPTZ,

    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS idx_ipo_gmp_ipo_id ON ipo_gmp(ipo_id);

CREATE INDEX IF NOT EXISTS idx_ipo_gmp_fetched_at ON ipo_gmp(fetched_at);



-- gmp history (keep all snapshots for trend analysis)

CREATE TABLE IF NOT EXISTS ipo_gmp_history (

    id BIGSERIAL PRIMARY KEY,

    ipo_id BIGINT NOT NULL REFERENCES ipos(id) ON DELETE CASCADE,

    gmp_price DOUBLE PRECISION,

    gmp_percentage DOUBLE PRECISION,

    estimated_listing_price DOUBLE PRECISION,

    source TEXT NOT NULL,

    source_updated_at TIMESTAMPTZ,

    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS idx_ipo_gmp_history_ipo_id ON ipo_gmp_history(ipo_id);

CREATE INDEX IF NOT EXISTS idx_ipo_gmp_history_fetched_at ON ipo_gmp_history(fetched_at);

