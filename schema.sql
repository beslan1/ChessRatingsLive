-- Файл: schema.sql (безопасная версия)

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    fsr_id BIGINT UNIQUE NOT NULL,
    fide_id BIGINT,
    full_name TEXT NOT NULL,
    birth_year INTEGER,
    gender VARCHAR(10),
    local_title VARCHAR(50),
    fsr_official_title VARCHAR(50),
    is_classic_champion BOOLEAN DEFAULT FALSE,
    is_rapid_champion BOOLEAN DEFAULT FALSE,
    is_blitz_champion BOOLEAN DEFAULT FALSE,
    is_child BOOLEAN DEFAULT FALSE,
    current_fsr_classic_rating INTEGER DEFAULT 0,
    previous_fsr_classic_rating INTEGER DEFAULT 0,
    current_fsr_rapid_rating INTEGER DEFAULT 0,
    previous_fsr_rapid_rating INTEGER DEFAULT 0,
    current_fsr_blitz_rating INTEGER DEFAULT 0,
    previous_fsr_blitz_rating INTEGER DEFAULT 0,
    current_fide_classic_rating INTEGER DEFAULT 0,
    current_fide_rapid_rating INTEGER DEFAULT 0,
    current_fide_blitz_rating INTEGER DEFAULT 0,
    fsr_tournaments_played_count INTEGER DEFAULT 0,
    last_profile_update_at TIMESTAMP
);