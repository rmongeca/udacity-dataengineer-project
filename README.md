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


## Data quality checks

To help ensure integrity between tables, we enforce Foreign Key constraints on
the fact tables when referencing the Primary Keys of the dimensional tables.


In addition, we also ensure integrity within each table by loading only rows
which have the main table fields NOT NULL and with the proper data type.

Finally, we ensure resolution of insertion conflicts for the different tables,
updating selected changing fields (*views* or *followers* in *streams* and
*broadcasters*) and not updating existing data on non-changing fields (rows in
*time* table).


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

- Project related files, such as README Markdown file with project description,
    .gitignore file with project's version control ignores and requirements.txt
    file with Python environment needed packages.

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

> Note: the execution of the sample data could take great amount of time
> (~20 min) due to the RAWG API endpoint requests for game data.

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

## Tool choice

The decided tools for this project, together with the reason for the choice are
the following:

- *PostgreSQL* as the database engine to create and load data into. The decision
    for this engine was due to its simplicity and ease of use, specially for a
    quick demo with sample data. In addition, its similarity with Amazon
    Redshift makes it easier to port from the local solution to a bigger, more
    robust cloud-based solution.

- *Python* as the programming language to automate the DW creation and ETL
    procedures. The choice for this language was due to the simplicity for a
    local solution together with the availability and ease of packages to
    connect to PostgreSQL, wrangle data and IO operations. In addition, the
    development of the procedures in Python may allow for faster migration to
    orchestrated procedures through Airflow, together with quick integration
    with AWS Infrastructure as Code (IaC) automation of future cloud-based
    implementations.


## Future scenarios

This section describes the changes and developments needed to address the
specified future scenarios.

### Data increased 100x

The project described acts as a Proof of Concept of the DW design to analyze
videogame stream data. In our local solution, we load the data for a day
2015-02-01 from 00:00 to 07:00 having over 1M streams. In a real case, we would
have data for multiple days, easily increasing the amount over a facto 100x.

Dealing with such amount of data would not change the main design or process for
the DW, apart from needing a more robust, orchestrated process for the ETL such
as a scalable cloud-based approach for example using AWS S3 storage together
with a Redshift DW.

However, a main change that would need to be addressed is the connection
between the streamed videogame and the game's data from RAWG, as individual
request to the search endpoint would not be viable. In this case, one approach
could be to previously load a list of games from RAWG database, perhaps with
and incremental approach loading each day/week the newly realsed games that
are more prone to being played. Afterwards, we would need to find a way to match
the games provided by the stream data with the already loaded games in the
dimension table. One way would be to use Levenshtein distance or other fuzzy
string matching methods or Machine Learning techniques to perform the entity
matching between tables.

### Periodical ETL executions

In a real case scenario when we have continously increasing amounts of data,
the need for periodical automatic ETL executions arises.

In this case, it is a logical approach to use an orchestrator to schedule the
ETL executions, for instance on a daily bases loading the data from the previous
day. Moreover, the use of an orchestrator like Airflow will allow us to trigger
alarms in case of failure, schedule retries, data quality checks or abort the
pipelines without compromising the already stored data.

When executing the incremental loading process we would need to load the new
data separated from the already stored, coherent data. Once the loading
process of the new data finishes, and the consistency and correctness of the
new data is ensured, it will be loaded into the final tables. This will ensure
the related analysis, queries and dashboards function correctly through the
whole process even if there is a failure in the ETL, without having to use
space for backups or copies of our DW.

### Concurrent access to the DW

In a real case DW, we would need to provide access to the data for different
amounts of people. From a Data Science team of around ~20 to a whole department
with +100 people, we would need to provide them with updated, consisten data.
In order to do that, we can choose to approaches.

The first approach would be to perpare analitical dashboards or
materialized views extracted from the DW and updated every time the DW is.
This ensures the data is ready for fast querying and use. Nevertheless,
this approach limits the available information to the agreed upon views between
data engineers and data scientist, and can make analysis slower.

The second approach would be to provide direct access to the DW for querying.
While this allows for flexible consumption of the DW data, the infrastructure
of the DW would need to support it. Although this may be easier when dealing
with auto-scalable cloud-based infrastructures, this may not be cost-effective.

All in all, the main idea to keep in mind is that a DW is thought of as a place
to store data for posterior analysis but not to query directly, being materialized
views or specific data extracted to data marts the best option to expose the data.
