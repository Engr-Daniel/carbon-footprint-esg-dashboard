-- Relational schema for the carbon accounting data model (PostgreSQL / SQLite compatible)

CREATE TABLE IF NOT EXISTS sites (
    site_id     INTEGER PRIMARY KEY,
    site_name   VARCHAR(100) NOT NULL UNIQUE,
    city        VARCHAR(100),
    country     VARCHAR(100) DEFAULT 'Nigeria'
);

CREATE TABLE IF NOT EXISTS emission_factors (
    activity_type     VARCHAR(60) NOT NULL,
    component         VARCHAR(20) NOT NULL DEFAULT 'primary',  -- primary | wtt | td_losses
    scope             SMALLINT NOT NULL CHECK (scope IN (1, 2, 3)),
    category          VARCHAR(100) NOT NULL,
    unit              VARCHAR(30) NOT NULL,
    kgco2e_per_unit   NUMERIC(12, 4) NOT NULL,
    factor_year       SMALLINT NOT NULL,
    gwp_basis         VARCHAR(10) DEFAULT 'AR5',
    source            VARCHAR(300) NOT NULL,
    source_url        VARCHAR(300),
    verification      VARCHAR(60),
    notes             TEXT,
    PRIMARY KEY (activity_type, component, factor_year)
);

CREATE TABLE IF NOT EXISTS activity_data (
    activity_id     INTEGER PRIMARY KEY,
    period          DATE NOT NULL,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    activity_type   VARCHAR(60) NOT NULL,
    quantity        NUMERIC(14, 2) NOT NULL CHECK (quantity >= 0),
    unit            VARCHAR(30) NOT NULL
);

-- US CPI-U deflators: nominal USD spend -> constant 2022 USD (EPA v1.3 factors are per 2022 USD)
CREATE TABLE IF NOT EXISTS usd_deflators (
    year            SMALLINT PRIMARY KEY,
    cpi_u           NUMERIC(10, 3) NOT NULL,
    factor_vs_2022  NUMERIC(10, 5),
    source          VARCHAR(200)
);

-- Emissions view: tCO2e per activity record
CREATE VIEW IF NOT EXISTS v_emissions AS
WITH act AS (   -- deflate nominal USD spend to 2022 USD (SQLite date syntax; use EXTRACT(YEAR ...) in PostgreSQL)
    SELECT a.*,
           CASE WHEN a.unit = 'USD'
                THEN a.quantity * (SELECT cpi_u FROM usd_deflators WHERE year = 2022)
                     / (SELECT cpi_u FROM usd_deflators d WHERE d.year = CAST(strftime('%Y', a.period) AS INTEGER))
                ELSE a.quantity END AS quantity_adj,
           CASE WHEN a.unit = 'USD' THEN 'USD2022' ELSE a.unit END AS unit_adj
    FROM activity_data a
)
SELECT
    a.period,
    s.site_name,
    f.scope,
    f.category,
    a.activity_type,
    f.component,
    a.quantity_adj AS quantity,
    a.unit_adj     AS unit,
    a.quantity_adj * f.kgco2e_per_unit / 1000.0 AS tco2e
FROM act a
JOIN sites s            ON s.site_id = a.site_id
-- one activity row joins ALL its factor components (e.g. combustion + WTT upstream)
JOIN emission_factors f ON f.activity_type = a.activity_type
 AND f.unit = a.unit_adj
 AND f.factor_year = (SELECT MAX(factor_year) FROM emission_factors x
                      WHERE x.activity_type = a.activity_type AND x.component = f.component);

-- Example analysis queries
-- 1) Total emissions by scope and year
-- SELECT strftime('%Y', period) AS year, scope, ROUND(SUM(tco2e), 1) AS tco2e
-- FROM v_emissions GROUP BY 1, 2 ORDER BY 1, 2;

-- 2) Top 5 emission hotspots
-- SELECT category, ROUND(SUM(tco2e), 1) AS tco2e
-- FROM v_emissions GROUP BY category ORDER BY tco2e DESC LIMIT 5;
