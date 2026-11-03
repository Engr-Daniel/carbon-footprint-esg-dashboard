-- Relational schema for the carbon accounting data model (PostgreSQL / SQLite compatible)

CREATE TABLE IF NOT EXISTS sites (
    site_id     INTEGER PRIMARY KEY,
    site_name   VARCHAR(100) NOT NULL UNIQUE,
    city        VARCHAR(100),
    country     VARCHAR(100) DEFAULT 'Nigeria'
);

CREATE TABLE IF NOT EXISTS emission_factors (
    activity_type     VARCHAR(60) PRIMARY KEY,
    scope             SMALLINT NOT NULL CHECK (scope IN (1, 2, 3)),
    category          VARCHAR(100) NOT NULL,
    unit              VARCHAR(30) NOT NULL,
    kgco2e_per_unit   NUMERIC(12, 4) NOT NULL,
    source            VARCHAR(200),
    valid_year        SMALLINT
);

CREATE TABLE IF NOT EXISTS activity_data (
    activity_id     INTEGER PRIMARY KEY,
    period          DATE NOT NULL,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    activity_type   VARCHAR(60) NOT NULL REFERENCES emission_factors(activity_type),
    quantity        NUMERIC(14, 2) NOT NULL CHECK (quantity >= 0),
    unit            VARCHAR(30) NOT NULL
);

-- Emissions view: tCO2e per activity record
CREATE VIEW IF NOT EXISTS v_emissions AS
SELECT
    a.period,
    s.site_name,
    f.scope,
    f.category,
    a.activity_type,
    a.quantity,
    a.unit,
    a.quantity * f.kgco2e_per_unit / 1000.0 AS tco2e
FROM activity_data a
JOIN sites s            ON s.site_id = a.site_id
JOIN emission_factors f ON f.activity_type = a.activity_type;

-- Example analysis queries
-- 1) Total emissions by scope and year
-- SELECT strftime('%Y', period) AS year, scope, ROUND(SUM(tco2e), 1) AS tco2e
-- FROM v_emissions GROUP BY 1, 2 ORDER BY 1, 2;

-- 2) Top 5 emission hotspots
-- SELECT category, ROUND(SUM(tco2e), 1) AS tco2e
-- FROM v_emissions GROUP BY category ORDER BY tco2e DESC LIMIT 5;
