import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries


def load_staging_tables(cur, conn):
    """
       This function loads data from AWS S3 to the staging tables in AWS Redshift using COPY command
    Args:
        cur: the cursor object.
         conn = connection to Redshift DB.
    """
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    """
       This function insert data from staging tables to the final tables (fact+dimensions) in AWS Redshift using select command
    Args:
        cur: the cursor object.
         conn = connection to Redshift DB.
    """
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()