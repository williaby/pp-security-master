-- Benchmark Security Management Tables
-- Supports synthetic benchmark securities for Portfolio Performance integration

-- Add benchmark flag to securities master
ALTER TABLE securities_master 
ADD COLUMN IF NOT EXISTS is_synthetic_benchmark BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS benchmark_metadata JSONB;

-- Create index for benchmark securities
CREATE INDEX IF NOT EXISTS idx_securities_master_benchmark 
ON securities_master(is_synthetic_benchmark) WHERE is_synthetic_benchmark = true;

-- Benchmark Securities Configuration
CREATE TABLE IF NOT EXISTS benchmark_securities (
    id SERIAL PRIMARY KEY,
    security_uuid UUID NOT NULL UNIQUE,
    benchmark_type VARCHAR(30) NOT NULL, -- 'reference_portfolio', 'custom_index', 'blended'
    
    -- Base configuration
    base_date DATE NOT NULL,
    base_price DECIMAL(15,6) NOT NULL DEFAULT 100.00,
    rebalance_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly',
    
    -- Portfolio tracking (for reference_portfolio type)
    underlying_portfolio_id VARCHAR(255),
    
    -- Custom index configuration (for custom_index type)
    underlying_securities TEXT[], -- Array of security IDs
    static_weights DECIMAL(8,6)[], -- Corresponding static weights
    
    -- Composition and performance data
    composition_data JSONB, -- Historical composition and weights
    performance_data JSONB, -- Performance metrics and attribution
    
    -- Management
    is_active BOOLEAN DEFAULT TRUE,
    last_calculated DATE,
    calculation_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (security_uuid) REFERENCES securities_master(uuid),
    
    -- Constraints
    CHECK (benchmark_type IN ('reference_portfolio', 'custom_index', 'blended')),
    CHECK (base_price > 0),
    CHECK (
        (benchmark_type = 'reference_portfolio' AND underlying_portfolio_id IS NOT NULL) OR
        (benchmark_type = 'custom_index' AND underlying_securities IS NOT NULL AND static_weights IS NOT NULL) OR
        (benchmark_type = 'blended')
    )
);

-- Benchmark Rebalancing Schedule
CREATE TABLE IF NOT EXISTS benchmark_rebalance_schedule (
    id SERIAL PRIMARY KEY,
    benchmark_security_id INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    rebalance_type VARCHAR(20) NOT NULL, -- 'automatic', 'manual', 'event_driven'
    
    -- Pre-rebalance composition
    pre_rebalance_weights JSONB,
    pre_rebalance_value DECIMAL(15,2),
    
    -- Post-rebalance composition
    post_rebalance_weights JSONB,
    post_rebalance_value DECIMAL(15,2),
    
    -- Execution details
    executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP,
    execution_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (benchmark_security_id) REFERENCES benchmark_securities(id),
    UNIQUE(benchmark_security_id, scheduled_date)
);

-- Benchmark Performance Attribution
CREATE TABLE IF NOT EXISTS benchmark_performance_attribution (
    id SERIAL PRIMARY KEY,
    benchmark_security_id INTEGER NOT NULL,
    attribution_date DATE NOT NULL,
    
    -- Overall performance
    benchmark_return DECIMAL(10,6) NOT NULL,
    benchmark_price DECIMAL(15,6) NOT NULL,
    
    -- Attribution breakdown by underlying security
    security_attributions JSONB NOT NULL, -- {security_id: {weight, return, contribution}}
    
    -- Sector/asset class attribution
    sector_attributions JSONB,
    asset_class_attributions JSONB,
    
    -- Risk attribution
    systematic_contribution DECIMAL(10,6),
    idiosyncratic_contribution DECIMAL(10,6),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (benchmark_security_id) REFERENCES benchmark_securities(id),
    UNIQUE(benchmark_security_id, attribution_date)
);

-- Benchmark Validation and Quality Checks
CREATE TABLE IF NOT EXISTS benchmark_quality_checks (
    id SERIAL PRIMARY KEY,
    benchmark_security_id INTEGER NOT NULL,
    check_date DATE NOT NULL,
    check_type VARCHAR(30) NOT NULL, -- 'price_validation', 'weight_sum', 'return_calculation', 'composition_drift'
    
    -- Check results
    passed BOOLEAN NOT NULL,
    check_value DECIMAL(15,6),
    expected_value DECIMAL(15,6),
    tolerance DECIMAL(15,6),
    
    -- Details
    error_message TEXT,
    check_data JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (benchmark_security_id) REFERENCES benchmark_securities(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_benchmark_securities_portfolio ON benchmark_securities(underlying_portfolio_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_securities_type ON benchmark_securities(benchmark_type);
CREATE INDEX IF NOT EXISTS idx_benchmark_securities_active ON benchmark_securities(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_benchmark_rebalance_date ON benchmark_rebalance_schedule(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_benchmark_rebalance_pending ON benchmark_rebalance_schedule(executed) WHERE executed = false;

CREATE INDEX IF NOT EXISTS idx_benchmark_attribution_date ON benchmark_performance_attribution(attribution_date);
CREATE INDEX IF NOT EXISTS idx_benchmark_attribution_benchmark ON benchmark_performance_attribution(benchmark_security_id);

CREATE INDEX IF NOT EXISTS idx_benchmark_quality_date ON benchmark_quality_checks(check_date);
CREATE INDEX IF NOT EXISTS idx_benchmark_quality_failed ON benchmark_quality_checks(passed) WHERE passed = false;

-- Update trigger for benchmark_securities
CREATE TRIGGER update_benchmark_securities_updated_at 
BEFORE UPDATE ON benchmark_securities 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Benchmark price validation function
CREATE OR REPLACE FUNCTION validate_benchmark_price_consistency(
    p_benchmark_security_id INTEGER,
    p_check_date DATE DEFAULT CURRENT_DATE
) RETURNS BOOLEAN AS $$
DECLARE
    v_calculated_price DECIMAL(15,6);
    v_stored_price DECIMAL(15,6);
    v_tolerance DECIMAL(15,6) := 0.01; -- 1 cent tolerance
    v_benchmark_uuid UUID;
BEGIN
    -- Get benchmark UUID
    SELECT security_uuid INTO v_benchmark_uuid
    FROM benchmark_securities 
    WHERE id = p_benchmark_security_id;
    
    IF v_benchmark_uuid IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Get stored price from price history
    SELECT close_price INTO v_stored_price
    FROM pp_price_history ph
    JOIN securities_master sm ON ph.security_master_id = sm.id
    WHERE sm.uuid = v_benchmark_uuid 
    AND ph.date = p_check_date;
    
    -- Calculate expected price based on attribution data
    SELECT benchmark_price INTO v_calculated_price
    FROM benchmark_performance_attribution
    WHERE benchmark_security_id = p_benchmark_security_id
    AND attribution_date = p_check_date;
    
    -- Check consistency
    IF v_stored_price IS NULL OR v_calculated_price IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Log validation result
    INSERT INTO benchmark_quality_checks (
        benchmark_security_id, check_date, check_type,
        passed, check_value, expected_value, tolerance
    ) VALUES (
        p_benchmark_security_id, p_check_date, 'price_validation',
        ABS(v_stored_price - v_calculated_price) <= v_tolerance,
        v_stored_price, v_calculated_price, v_tolerance
    );
    
    RETURN ABS(v_stored_price - v_calculated_price) <= v_tolerance;
END;
$$ LANGUAGE plpgsql;

-- Function to get benchmark composition for a date
CREATE OR REPLACE FUNCTION get_benchmark_composition(
    p_benchmark_security_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS JSONB AS $$
DECLARE
    v_composition JSONB;
    v_benchmark_record RECORD;
BEGIN
    -- Get benchmark configuration
    SELECT * INTO v_benchmark_record
    FROM benchmark_securities 
    WHERE id = p_benchmark_security_id;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Extract composition for the specific date
    IF v_benchmark_record.composition_data IS NOT NULL THEN
        -- Find closest composition date
        SELECT value INTO v_composition
        FROM jsonb_array_elements(v_benchmark_record.composition_data) 
        WHERE (value->>'date')::date <= p_date
        ORDER BY (value->>'date')::date DESC
        LIMIT 1;
    END IF;
    
    RETURN v_composition;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate benchmark return for period
CREATE OR REPLACE FUNCTION calculate_benchmark_return(
    p_benchmark_security_id INTEGER,
    p_start_date DATE,
    p_end_date DATE
) RETURNS DECIMAL(10,6) AS $$
DECLARE
    v_start_price DECIMAL(15,6);
    v_end_price DECIMAL(15,6);
    v_return DECIMAL(10,6);
    v_benchmark_uuid UUID;
BEGIN
    -- Get benchmark UUID
    SELECT security_uuid INTO v_benchmark_uuid
    FROM benchmark_securities 
    WHERE id = p_benchmark_security_id;
    
    IF v_benchmark_uuid IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Get start price
    SELECT close_price INTO v_start_price
    FROM pp_price_history ph
    JOIN securities_master sm ON ph.security_master_id = sm.id
    WHERE sm.uuid = v_benchmark_uuid 
    AND ph.date = p_start_date;
    
    -- Get end price
    SELECT close_price INTO v_end_price
    FROM pp_price_history ph
    JOIN securities_master sm ON ph.security_master_id = sm.id
    WHERE sm.uuid = v_benchmark_uuid 
    AND ph.date = p_end_date;
    
    -- Calculate return
    IF v_start_price IS NULL OR v_end_price IS NULL OR v_start_price = 0 THEN
        RETURN NULL;
    END IF;
    
    v_return := (v_end_price - v_start_price) / v_start_price;
    
    RETURN v_return;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing
INSERT INTO benchmark_securities (
    security_uuid, benchmark_type, base_date, base_price,
    underlying_portfolio_id, rebalance_frequency
) 
SELECT 
    uuid, 'reference_portfolio', '2024-01-01'::date, 100.00,
    'sample-portfolio-uuid', 'monthly'
FROM securities_master 
WHERE symbol LIKE 'PBEN_%' 
LIMIT 1
ON CONFLICT (security_uuid) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE benchmark_securities IS 'Configuration and metadata for synthetic benchmark securities';
COMMENT ON COLUMN benchmark_securities.benchmark_type IS 'Type of benchmark: reference_portfolio, custom_index, or blended';
COMMENT ON COLUMN benchmark_securities.composition_data IS 'Historical composition and weights as JSON array';
COMMENT ON COLUMN benchmark_securities.performance_data IS 'Performance metrics and attribution data';

COMMENT ON TABLE benchmark_performance_attribution IS 'Daily performance attribution for benchmark securities';
COMMENT ON COLUMN benchmark_performance_attribution.security_attributions IS 'Per-security weight, return, and contribution data';

COMMENT ON TABLE benchmark_quality_checks IS 'Validation and quality control checks for benchmark calculations';

COMMENT ON FUNCTION validate_benchmark_price_consistency IS 'Validates that stored prices match calculated attribution prices';
COMMENT ON FUNCTION get_benchmark_composition IS 'Returns benchmark composition for a specific date';
COMMENT ON FUNCTION calculate_benchmark_return IS 'Calculates total return for benchmark over specified period';