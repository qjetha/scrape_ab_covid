import requests, time, psycopg2, datetime, os

from bs4 import BeautifulSoup as bs4
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_agrument("--headless")
chrome_options.add_agrument("--disable-dev-shm-usage")
chrome_options.add_agrument("--no-sandbox")


class RegionData:

	region_count = 1
	min_active = 1000000
	max_active = 0

	def __init__(self, name, classification, measures, active_cases, population):
		self.name = name
		self.classification = classification
		self.measures = measures
		self.active_cases = int(active_cases)
		self.population = int(population)

		self.key = RegionData.region_count

		if self.population != 0:
			self.active_rate = (100000/self.population) * self.active_cases
		else:
			self.active_rate = 0

		if self.active_rate > RegionData.max_active:
			RegionData.max_active = self.active_rate

		if self.active_rate < RegionData.min_active:
			RegionData.min_active = self.active_rate
		
		RegionData.region_count += 1



def scrape_alberta():

	driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

	alberta_listings = r"https://www.alberta.ca/maps/covid-19-status-map.htm"

	# time.sleep(3)

	# driver.get(alberta_listings)

	# regions = dict()

	# def get_page():

	# 	soup = bs4(driver.page_source, 'lxml')

	# 	full_tr = soup.find_all('tr', {'class': 'odd'})

	# 	def get_table_data(class_name):
	# 		for tr in soup.find_all('tr', {'class': class_name}):
	# 			pull_data = list()
	# 			for td in tr.findAll('td'):
	# 				pull_data.append(td.string)
			
	# 			regions[pull_data[1]] = RegionData(pull_data[1], pull_data[2], pull_data[3], pull_data[5], pull_data[6])
		
	# 	get_table_data('odd')
	# 	get_table_data('even')


	# def click_page():
	# 	time.sleep(1)
	# 	elem = driver.find_element_by_link_text('Next')
	# 	driver.execute_script("window.scrollTo(0, 1000)")

	# 	elem.click()


	# # 3 pages of region data. Let's just loop over them.
	# for page in range(0, 3):
	# 	if page==0:
	# 		get_page()
	# 	else:
	# 		click_page()
	# 		get_page()

	# return regions



def update_sql(regions):

	time_now = datetime.datetime.now()
	today_date = time_now.date()
	this_hour = time_now.hour

	conn = psycopg2.connect()

	cursor = conn.cursor(os.environ.get("DATABASE_URL"))

	# check if entry in DB for today's date
	cursor.execute('SELECT key FROM regions WHERE d_date = (%s)', (today_date,))

	if cursor.fetchone() == None:
		
		# if no entry then: (1) insert new data into db
		for region in regions.keys():
			
			cursor.execute('''INSERT INTO regions (key, name, classification, measures, active_cases, population, active_rate, d_date, hour) 
					  		  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
					  		  	(regions[region].key, regions[region].name, 
					  		  	regions[region].classification, regions[region].measures, regions[region].active_cases, 
					  		  	regions[region].population, regions[region].active_rate, today_date, this_hour))
			conn.commit()

		# if no entry then: (2) delete data from a week ago
		week_ago = today_date - datetime.timedelta(7)

		cursor.execute('DELETE FROM regions WHERE d_date = (%s)', (week_ago,))

		conn.commit()


	else:
		
		for region in regions.keys():

			# if entry than update the data for today
			cursor.execute('''UPDATE regions 
							  SET (classification, measures, active_cases, population, active_rate, d_date, hour) =
							  (%s, %s, %s, %s, %s, %s, %s) 
							  WHERE name = (%s)''',
							  	(regions[region].classification, regions[region].measures, regions[region].active_cases,
							  	regions[region].population, regions[region].active_rate, today_date, this_hour, region))

			conn.commit()

	cursor.close()



scrape_alberta()
