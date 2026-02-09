import pymysql
import os
from urllib.parse import urlparse

class Database:
    def __init__(self,database_name):
        self.database_name = database_name

    def get_connection(self):
        db_url = os.environ.get("DATABASE_URL")

        url = urlparse(db_url)

        connection = pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],  
            port=url.port,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        print("Database Connected Successfully")
        return connection, cursor
    
    def create_table(self, create_table_query):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(create_table_query)
            connection.commit()
            print("Table created successfully.")
        except Exception as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()

    def insert_data(self, insert_query, data):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            print("Data inserted successfully.")
            return True
        except Exception as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            connection.close()
    
    def update_data(self, insert_query, data):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            print("Data updated successfully.")
            return True
           
        except Exception as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            connection.close()

    def fetch_data(self, fetch_query, data):
        connection, cursor = self.get_connection()

        try:
            cursor.execute(fetch_query, data)
            results = cursor.fetchone()
            return results
        except Exception as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()  
            connection.close()
        
    def fetch_all_data(self, fetch_query, data):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(fetch_query, data)
            results = cursor.fetchall()
            return results
        except Exception as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()  
            connection.close()

    def fetch_data_without_value(self, fetch_query):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(fetch_query)
            results = cursor.fetchall()
            return results
        except Exception as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()  
            connection.close()   

    def delete_data(self, query, data):
        connection, cursor = self.get_connection()
        try:
            cursor.execute(query, data)
            return True
        except Exception as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()  
            connection.close()