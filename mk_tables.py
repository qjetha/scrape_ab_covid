import psycopg2
import config

alberta = 1
bc = 1

conn = psycopg2.connect(host=config.host, 
						database=config.database,
						user=config.user, 
						password=config.password)

cursor = conn.cursor()



# Add Alberta Province Data Table
if alberta==1:
	cursor.execute('''DROP TABLE IF EXISTS Alb''')

	cursor.execute('''CREATE TABLE Alb (
					  key INT,
					  prov TEXT,
					  name TEXT,
					  classification TEXT,
					  measures TEXT,
					  active_cases INT,
					  population INT,
					  active_rate INT,
					  d_date DATE,
					  hour INT)''')

	conn.commit()



# Add BC Province Data Table
if bc==1:
	cursor.execute('''DROP TABLE IF EXISTS CB''')

	cursor.execute('''CREATE TABLE CB (
					  key INT,
					  prov TEXT,
					  name TEXT,
					  active_cases INT,
					  d_date DATE)''')

	conn.commit()


cursor.close()