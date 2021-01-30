import psycopg2
import config

conn = psycopg2.connect(host=config.host, 
						database=config.database,
						user=config.user, 
						password=config.password)

cursor = conn.cursor()

# Add Website Registrants Table
cursor.execute('''DROP TABLE IF EXISTS regions''')

cursor.execute('''CREATE TABLE regions (
				  key INT,
				  name TEXT,
				  classification TEXT,
				  measures TEXT,
				  active_cases INT,
				  population INT,
				  active_rate INT,
				  d_date DATE,
				  hour INT)''')

conn.commit()

cursor.close()