-- Файл: schema.sql (версия для MS SQL Server)

IF OBJECT_ID('dbo.players', 'U') IS NOT NULL
DROP TABLE dbo.players;

CREATE TABLE players (
    id INT IDENTITY(1,1) PRIMARY KEY,
    fsr_id BIGINT UNIQUE NOT NULL,
    fide_id BIGINT,
    full_name NVARCHAR(255) NOT NULL,
    birth_year INT,
    gender VARCHAR(10),
    local_title NVARCHAR(50),
    fsr_official_title NVARCHAR(50),
    is_classic_champion BIT DEFAULT 0,
    is_rapid_champion BIT DEFAULT 0,
    is_blitz_champion BIT DEFAULT 0,
    is_child BIT DEFAULT 0,
    current_fsr_classic_rating INT DEFAULT 0,
    previous_fsr_classic_rating INT DEFAULT 0,
    current_fsr_rapid_rating INT DEFAULT 0,
    previous_fsr_rapid_rating INT DEFAULT 0,
    current_fsr_blitz_rating INT DEFAULT 0,
    previous_fsr_blitz_rating INT DEFAULT 0,
    current_fide_classic_rating INT DEFAULT 0,
    current_fide_rapid_rating INT DEFAULT 0,
    current_fide_blitz_rating INT DEFAULT 0,
    fsr_tournaments_played_count INT DEFAULT 0,
    last_profile_update_at DATETIME2
);