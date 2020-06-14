"""
Queries Script.
This script contains the queries that are executed in the other scripts
"""


DATABASE = "twitchy"

# Creation table queries
STAGING_TWITCH_CREATION = """
CREATE TABLE staging_twitch_dataset (
    stream_id bigint,
    views bigint,
    stream_time varchar,
    game_title varchar,
    broadcaster_id bigint,
    broadcaster_name varchar,
    delay_setting integer,
    broadcaster_followers bigint,
    partner_status varchar,
    broadcaster_language varchar,
    broadcaster_total_views bigint,
    stream_language varchar,
    broadcaster_created_time varchar,
    playback_bitrate bigint,
    source_resolution varchar,
    empty_col varchar
)
"""
GAMES_CREATION = """
CREATE TABLE games (
    game_id varchar PRIMARY KEY,
    game_slug varchar NOT NULL,
    game_title varchar NOT NULL,
    release_date date,
    rating numeric,
    rating_count int
)
"""
BROADCASTERS_CREATION = """
CREATE TABLE broadcasters (
    broadcaster_id bigint PRIMARY KEY,
    broadcaster_name varchar NOT NULL,
    broadcaster_followers bigint,
    broadcaster_language varchar,
    partner_status boolean
)
"""
TIME_CREATION = """
CREATE TABLE time (
    time_id timestamp PRIMARY KEY,
    hour int NOT NULL,
    day int NOT NULL,
    week int NOT NULL,
    month int NOT NULL,
    year int NOT NULL,
    weekday int NOT NULL
)
"""
STREAMS_CREATION = """
CREATE TABLE streams (
    stream_id bigint PRIMARY KEY,
    broadcaster_id bigint REFERENCES broadcasters(broadcaster_id),
    game_id varchar REFERENCES games(game_id),
    time_id timestamp REFERENCES time(time_id),
    views bigint,
    delay_setting integer,
    playback_bitrate bigint,
    source_resolution varchar
)
"""

# Tables list
TABLES = ["staging_twitch_dataset", "games", "broadcasters", "time", "streams"]
CREATE_TABLES_QUERIES = [
    STAGING_TWITCH_CREATION,
    GAMES_CREATION, BROADCASTERS_CREATION, TIME_CREATION, STREAMS_CREATION]

# Copy data query
STAGING_TWITCH_COPY = """
COPY staging_twitch_dataset
FROM '{path}' DELIMITER '{delimiter}' CSV {header} QUOTE E'\\b'
"""

# Insert data queries
GAMES_INSERT = """
INSERT INTO games
    (game_id, game_slug, game_title, release_date, rating, rating_count)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (game_id) DO UPDATE SET
    game_slug = EXCLUDED.game_slug,
    game_title = EXCLUDED.game_title,
    release_date = EXCLUDED.release_date,
    rating = EXCLUDED.rating,
    rating_count = EXCLUDED.rating_count
"""
BROADCASTERS_INSERT = """
INSERT INTO broadcasters
SELECT
    broadcaster_id,
    broadcaster_name,
    broadcaster_followers,
    CASE WHEN broadcaster_language = '-1' THEN NULL
        ELSE LOWER(broadcaster_language)
    END broadcaster_language,
    CASE WHEN partner_status = '-1' THEN FALSE ELSE TRUE END partner_status
FROM (
    SELECT *,
        ROW_NUMBER() OVER(
            PARTITION BY broadcaster_id, broadcaster_name
            ORDER BY broadcaster_followers DESC, partner_status DESC
        ) nrow
    FROM staging_twitch_dataset
) s
WHERE nrow = 1
    AND broadcaster_id IS NOT NULL
    AND broadcaster_name IS NOT NULL
ON CONFLICT (broadcaster_id) DO UPDATE SET
    broadcaster_followers = EXCLUDED.broadcaster_followers,
    broadcaster_language = EXCLUDED.broadcaster_language,
    partner_status = EXCLUDED.partner_status
"""
TIME_INSERT = """
INSERT INTO time
SELECT
    time_id,
    EXTRACT(hour FROM time_id) AS hour,
    EXTRACT(day FROM time_id) AS day,
    EXTRACT(week FROM time_id) AS week,
    EXTRACT(month FROM time_id) AS month,
    EXTRACT(year FROM time_id) AS year,
    EXTRACT(dow FROM time_id) AS weekday
FROM (
    SELECT
        TO_TIMESTAMP(stream_time, 'YYYY-MM-DDTHH:MI:SSZ') time_id
    FROM staging_twitch_dataset
    WHERE stream_time IS NOT NULL
) t
ON CONFLICT (time_id) DO NOTHING
"""
STREAMS_INSERT = """
INSERT INTO streams
SELECT
    s.stream_id,
    s.broadcaster_id,
    g.game_id,
    TO_TIMESTAMP(s.stream_time, 'YYYY-MM-DDTHH:MI:SSZ') time_id,
    s.views,
    s.delay_setting,
    s.playback_bitrate,
    s.source_resolution
FROM (
    SELECT *,
        ROW_NUMBER() OVER(
            PARTITION BY stream_id
            ORDER BY views DESC
        ) nrow
    FROM staging_twitch_dataset
    WHERE stream_id IS NOT NULL
        AND game_title IS NOT NULL
        AND broadcaster_id IS NOT NULL
        AND broadcaster_name IS NOT NULL
        AND stream_time IS NOT NULL
) s
INNER JOIN games g ON g.game_title = s.game_title
WHERE nrow = 1
ON CONFLICT (stream_id) DO UPDATE SET
    views = EXCLUDED.views
"""

# Select queries
GAME_TITLE_SELECT = """
SELECT DISTINCT game_title FROM staging_twitch_dataset
WHERE game_title IS NOT NULL
"""
