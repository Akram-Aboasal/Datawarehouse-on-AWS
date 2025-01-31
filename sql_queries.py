import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')
IAM_ROLE = config['IAM_ROLE']["ARN"]
LOG_DATA = config['S3']["LOG_DATA"]
LOG_JSONPATH = config['S3']["LOG_JSONPATH"]
SONG_DATA = config['S3']["SONG_DATA"]
# DROP TABLES

staging_events_table_drop = "DROP table IF EXISTS staging_events"
staging_songs_table_drop = "DROP table IF EXISTS staging_songs"
songplay_table_drop = "DROP table IF EXISTS songplay_table"
user_table_drop = "DROP table IF EXISTS user_table"
song_table_drop = "DROP table IF EXISTS song_table"
artist_table_drop = "DROP table IF EXISTS artist_table"
time_table_drop = "DROP table IF EXISTS time_table"

# CREATE TABLES

staging_events_table_create= (""" CREATE TABLE IF NOT EXISTS staging_events 
                                                                            (artist       VARCHAR(MAX),
                                                                            auth          VARCHAR,
                                                                            firstName     VARCHAR,
                                                                            gender        VARCHAR,
                                                                            ItemInSession int,
                                                                            lastName      VARCHAR,
                                                                            length        DOUBLE PRECISION,
                                                                            level         VARCHAR,
                                                                            location      Text,
                                                                            method        VARCHAR,
                                                                            page          VARCHAR,
                                                                            regestration  DOUBLE PRECISION,
                                                                            SessionId     int,
                                                                            song          VARCHAR,
                                                                            status        int,
                                                                            ts            BIGINT,
                                                                            userAgent     VARCHAR,
                                                                            user_id       int
                                                                            );  """)



staging_songs_table_create = (""" CREATE TABLE IF NOT EXISTS staging_songs
                                                                            ( song_id          VARCHAR,
                                                                            num_songs        int,
                                                                            artist_id        VARCHAR(MAX),
                                                                            artist_name      VARCHAR,
                                                                            title            VARCHAR(MAX),
                                                                            artist_latitude  DOUBLE PRECISION,
                                                                            artist_longitude DOUBLE PRECISION,
                                                                            artist_location  TEXT,
                                                                            duration         DOUBLE PRECISION,
                                                                            year             int
                                                                            );
""")

songplay_table_create = ("""CREATE TABLE IF NOT EXISTS fact_songplay (
                                                            songplay_id int IDENTITY(0,1) NOT NULL PRIMARY KEY, 
                                                            start_time timestamp NOT NULL SORTKEY,
                                                            user_id int NOT NULL DISTKEY, 
                                                            level VARCHAR,
                                                            song_id VARCHAR NOT NULL,
                                                            artist_id VARCHAR(MAX) NOT NULL,
                                                            session_id int,
                                                            location TEXT,
                                                            user_agent VARCHAR)diststyle key;
""")

user_table_create = (""" CREATE TABLE IF NOT EXISTS dim_user(
                                                          user_id int NOT NULL PRIMARY KEY SORTKEY,
                                                          first_name VARCHAR NOT NULL,
                                                          last_name VARCHAR NOT NULL,
                                                          gender VARCHAR,
                                                          level VARCHAR )diststyle all;
""")

song_table_create = (""" CREATE TABLE IF NOT EXISTS dim_song(
                                                         song_id VARCHAR NOT NULL PRIMARY KEY SORTKEY,
                                                         title VARCHAR(MAX) NOT NULL,
                                                         artist_id VARCHAR(MAX) NOT NULL DISTKEY,
                                                         year int NOT NULL,
                                                         duration DOUBLE PRECISION NOT NULL)diststyle key;
""")

artist_table_create = (""" CREATE TABLE IF NOT EXISTS dim_artist(
                                                         artist_id VARCHAR(MAX) NOT NULL PRIMARY KEY SORTKEY,
                                                         name VARCHAR(MAX) NOT NULL,
                                                         location TEXT,
                                                         artist_latitude DOUBLE PRECISION,
                                                         artist_longitude DOUBLE PRECISION)diststyle all;
""")

time_table_create = ("""CREATE TABLE IF NOT EXISTS dim_time(
                                                         start_time TIMESTAMP NOT NULL PRIMARY KEY SORTKEY,
                                                         hour int,
                                                         day int,
                                                         week int,
                                                         month int,
                                                         year int DISTKEY,
                                                         weekday int)diststyle key;
""")

# STAGING TABLES

staging_events_copy = ("""COPY staging_events FROM {}
                         Credentials 'aws_iam_role={}'
                         region 'us-west-2'
                         FORMAT AS JSON {};
""").format(LOG_DATA, IAM_ROLE, LOG_JSONPATH)

staging_songs_copy = ("""COPY staging_songs FROM {}
                        Credentials 'aws_iam_role={}'
                      region 'us-west-2'
                        json 'auto' 
                        TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL;
""").format(SONG_DATA, IAM_ROLE)

# FINAL TABLES

songplay_table_insert = (""" INSERT INTO fact_songplay(start_time, user_id, level, song_id, artist_id,
                          session_id, location, user_agent)
                          
                          SELECT DISTINCT  timestamp 'epoch' + (eve.ts/1000) * interval '1 second' AS start_time,
                          eve.user_id, eve.level, son.song_id, son.artist_id, 
                          eve.SessionId AS session_id, eve.location, eve.userAgent
                          FROM staging_events eve
                          JOIN staging_songs son ON (eve.song = son.title AND 
                                                     eve.artist = son.artist_name)
                          WHERE eve.page = 'NextSong';    
""")

user_table_insert = (""" INSERT INTO dim_user(user_id, first_name, last_name, gender, level)
                         SELECT DISTINCT user_id, firstName, lastName, gender, level
                         FROM staging_events eve
                         WHERE user_id IS NOT NULL;
""")

song_table_insert = ("""INSERT INTO dim_song(song_id, title, artist_id, year, duration)
                         SELECT DISTINCT son.song_id, son.title, son.artist_id, son.year, son.duration
                         FROM staging_songs son
                         WHERE song_id IS NOT NULL;
""")

artist_table_insert = (""" INSERT INTO dim_artist(artist_id, name, location, artist_latitude, artist_longitude)
                           SELECT DISTINCT artist_id, artist_name AS name, artist_location AS location,
                           artist_latitude AS latitude, artist_longitude AS longitude
                           FROM staging_songs;
""")

time_table_insert = (""" INSERT INTO dim_time (start_time, hour, day, week, month, year, weekday)
                         SELECT DISTINCT timestamp 'epoch' + eve.ts/1000 * interval '1 second' AS start_time,
                         EXTRACT(hour FROM start_time)     AS hour,
                         EXTRACT(day FROM start_time)      AS day,
                         EXTRACT(week FROM start_time)     AS week,
                         EXTRACT(month FROM start_time)    AS month,
                         EXTRACT(year FROM start_time)     AS year,
                         EXTRACT(week FROM start_time)     AS weekday
                         FROM staging_events eve
                         WHERE start_time IS NOT NULL;
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]