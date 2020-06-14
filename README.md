# Data Engineer Capstone Project: Videogame Streaming Data Warehouse

This is the capstone project of the Udacity Data Engineer course, showing the
range of skills and knowledge developed through the course.

The idea behind this project is to simulate the construction of a Data
Warehouse containing information about videogame streams. In particular, we
simulate a mock company *Twitchy* which would, if existed, be affiliated with
[Twitch](http://twitch.tv/) to help them build this Data Warehouse to analyze
their streams, together with enriched game information obtained from a the RAWG
Video Games Database API.

## Data sources

The data used in this project was provdided from the following sites, visited
at date *2020/06*:

- [Twitch Dataset - Clivecast Github](https://clivecast.github.io/) which
    comprises a set of TSV (tab separated .txt) files containing information
    about streams and broadcasters.

- [RAWG Video Games Database API](https://rawg.io/apidocs) which exposes HTTP
    endpoints which allow to search for games by name and obtain the game's
    details.

## Data Warehouse design

Given that the focus of this DW would be to analyze streams, we design a star
schema centered around a single fact table **Streams** which will hold the
information of a single stream, the associated broadcaster, game, time, views
and stream details.

Around this fact table, we design three dimensional tables which represent
entities in the fact table that can be repeated and combined independently.
These are the dimensional tables **Broadcasters** capturing the users who
perform the streams, their followers and partner status; **Time** that stores
the timestamps and extracted time measures for the streams, to help filter when
analyzing the streams; and finally **Games** which hold information about the
streamed game, title, release and ratings.

To help ensure integrity between tables, we enforce Foreign Key constraints on
the fact tables when referencing the Primary Keys of the dimensional tables.
In addition, to ensure data quality we perform integrity checks when loading
the data into our DW.

# ETL design

For the ETL to load data into our DW, we proceed with an staging table approach:

- We load the Twitch streams data into a staging table using COPY commands.

- We use INSERT INTO commands with subsets of the staging table, along with
    transformations, to load the data into the dimensional tables
    *Broadcasters* and *Time*.

- We take the staging table's game titles and enrich them with calls to the
    *RAWG API*, then load the information into the *Games* dimensional table.

- We use INSERT INTO commands with subsets of the staging table, alogn with
    integrity constraints from the games in the dimensional table (*INNER JOIN*)
    to load the fact table *Streams*.

This process allows us to scale the DW design to other architectures such as
a distibuted DB with Spark, by bulk loading the information from the data files
into the stagin table and then performing different MapReduce operations to
load the tables.

The only inconvenience of this approach is the overhead introduced by querying
the API endpoints to get the game's information, which delays the whole loading
operation.

## Project structure

The project is divided in four parts:

- Python scripts *create_tables.py* and *etl.py* that respectively create and
    fill our **twitchy** database, by using helper scripts *queries.py*,
    *rawg.py* and *sql.py*.

- Configuration file **config.json**, user provided, with credentials and
    execution details to connect to DB.

- Project related files, such as README Markdown file with project description
    or .gitignore file with project's version control ignores.

- Jupyter Notebook *Capstone Project Template.ipynb* with project summary and sample
    execution.

## Project execution

There are two ways to run the project. Both rely on parameters in the
configuration file *config.JSON*:

- Execution through Jupyter Notebook *Capstone Project Template.ipynb*.

- Execution through Python Scripts, executing:
    ```bash
    python create_tables.py
    ```
    to create the tables and database, and then:
    ```bash
    python etl.py
    ```
    to execute the ETL.

## Query examples

This section shows two simple query examples to exploit the data in our DW.

- TOP 10 most viewed broadcasters with their total views for a given
    month:
    ```sql
    SELECT b.broadcaster_name, t.year, t.month, SUM(s.views) AS views
    FROM streams s, broadcasters b, time t
    WHERE s.broadcaster_id = b.broadcaster_id
        AND s.time_id = t.time_id
    GROUP BY b.broadcaster_name, t.year, t.month
    ORDER BY views DESC
    LIMIT 10
    ```

- TOP 10 most streamed games with their total views for a given
    day:
    ```sql
    SELECT g.game_title, t.year, t.month, COUNT(s.stream_id) AS streams
    FROM streams s, games g, time t
    WHERE s.game_id = g.game_id
        AND s.time_id = t.time_id
    GROUP BY g.game_title, t.year, t.month
    ORDER BY streams DESC
    LIMIT 10
    ```
