CREATE TABLE IF NOT EXISTS ledger_rental_request (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    property_id VARCHAR(100) NOT NULL,
    property_seeker_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    message TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_message TEXT,
    response_date TIMESTAMP WITH TIME ZONE,
    rental_agreement_id VARCHAR(64)
); 