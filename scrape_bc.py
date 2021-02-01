import time, psycopg2, datetime, os
import pandas as pd

from bs4 import BeautifulSoup as bs4
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


class CaseData:

	province = "C.-B."
	id_listing = list()

	max_date = datetime.date(2000, 1, 2)
	min_date = datetime.date(2030, 1, 1)

	def __init__(self, key, gender, age, name, date):
		self.key = int(key)
		self.gender = gender
		self.age = age
		self.name = name
		self.date = date

		CaseData.id_listing.append(self.key)

		if self.date > CaseData.max_date:
			CaseData.max_date = self.date
		if self.date < CaseData.min_date:
			CaseData.min_date = self.date

	def to_dict(self):
		return {
			'name': self.name,
			'date': self.date,
			'count': 1
		}


def scrape_bc():

	driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

	bc_listings = r'https://governmentofbc.maps.arcgis.com/home/item.html?id=b8a2b437ccc24f04b975f76df6814cb1#data'
	driver.get(bc_listings)

	time.sleep(5)

	driver.execute_script("document.querySelector('.dgrid-scroller').scrollTo(0, 90000000)")

	time.sleep(3)

	cases = dict()


	def get_date(li):
		split_list = li.split(', ')
		dt = datetime.datetime.strptime(split_list[0], '%m/%d/%Y')

		return dt.date()


	def get_page():

		soup = bs4(driver.page_source, 'lxml')
		
		all_tables = soup.find_all('table', {'class': "dgrid-row-table"})
		
		for table in all_tables:
			pull_data = list()
			table_data = table.find_all('td')

			for td in table_data:
				pull_data.append(td.string)

			if len(pull_data) == 0:
				continue
			elif int(pull_data[4]) in CaseData.id_listing:
				continue
			else:
				cases[pull_data[4]] = CaseData(pull_data[4], pull_data[2], pull_data[3], pull_data[1], get_date(pull_data[0]))


	get_page()

	d_ten_days = CaseData.max_date - datetime.timedelta(10)

	while CaseData.min_date > d_ten_days:
		driver.execute_script("document.querySelector('.dgrid-scroller').scrollBy(0, -1000)")
		time.sleep(1)
		get_page()
	

	return cases



def groupby_name(cases):

	df = pd.DataFrame.from_records([cases[c].to_dict() for c in cases.keys()])
	df_grouped = df.groupby(['name', 'date'])['count'].sum()

	return df_grouped.to_dict()


def update_sql(cases):

	conn = psycopg2.connect(host=config.host, 
							database=config.database,
							user=config.user, 
							password=config.password)	

	cursor = conn.cursor()
	cursor.execute('truncate CB')

	past_week = CaseData.max_date - datetime.timedelta(8)

	key = 1
	return_dict = groupby_name(cases)
	
	for item in return_dict.keys():
		name, date = item
		new_cases = return_dict[item]

		if date >= past_week:
			cursor.execute('''INSERT INTO CB (key, prov, name, active_cases, d_date) 
					  		  VALUES (%s, %s, %s, %s, %s)''', 
					  		  	(key, CaseData.province, name, new_cases, date))
			conn.commit()
			key+=1

		else:
			continue

			

if __name__=="__main__":
	
	update_sql(scrape_bc())
