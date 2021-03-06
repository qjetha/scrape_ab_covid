import time, psycopg2, datetime, os

from bs4 import BeautifulSoup as bs4
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


class RegionData:

	province = "Alb."
	region_count = 1

	def __init__(self, name, measures, active_cases, population):
		self.name = name
		self.measures = measures
		self.active_cases = int(active_cases)
		self.population = int(population)

		self.key = RegionData.region_count

		if self.population != 0:
			self.active_rate = (100000/self.population) * self.active_cases
		else:
			self.active_rate = 0
		
		RegionData.region_count += 1



def scrape_alb():
	driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

	alb_listings = r"https://www.alberta.ca/maps/covid-19-status-map.htm"

	time.sleep(3)

	driver.get(alb_listings)

	regions = dict()

	def get_page():

		soup = bs4(driver.page_source, 'lxml')

		full_tr = soup.find_all('tr', {'class': 'odd'})

		def get_table_data(class_name):
			for tr in soup.find_all('tr', {'class': class_name}):
				pull_data = list()
				for td in tr.findAll('td'):
					pull_data.append(td.string)
			
				regions[pull_data[1]] = RegionData(pull_data[1], pull_data[2], pull_data[4], pull_data[5])
		
		get_table_data('odd')
		get_table_data('even')


	def click_page():
		time.sleep(1)
		elem = driver.find_element_by_link_text('Next')
		driver.execute_script("window.scrollTo(0, 1000)")

		elem.click()


	# 3 pages of region data. Let's just loop over them.
	for page in range(0, 3):
		if page==0:
			get_page()
		else:
			click_page()
			get_page()

	return regions



def update_sql(regions):

	now_utc = datetime.datetime.today()
	now_alb = now_utc - datetime.timedelta(hours=7)

	now_alb_date = now_alb.date()
	now_alb_hour = now_alb.hour

	conn = psycopg2.connect(os.environ.get("DATABASE_URL"))

	cursor = conn.cursor()

	# check if entry in DB for today's date
	cursor.execute('SELECT key FROM alb WHERE d_date = (%s)', (now_alb_date,))

	if cursor.fetchone() == None:
		
		# if no entry then: (1) insert new data into db
		for region in regions.keys():
			
			cursor.execute('''INSERT INTO alb (key, prov, name, measures, active_cases, population, active_rate, d_date, hour) 
					  		  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
					  		  	(regions[region].key, RegionData.province, regions[region].name, 
					  		  	regions[region].measures, regions[region].active_cases, 
					  		  	regions[region].population, regions[region].active_rate, now_alb_date, now_alb_hour))
			conn.commit()

		# if no entry then: (2) delete data from a week ago
		week_ago = now_alb_date - datetime.timedelta(8)

		cursor.execute('DELETE FROM alb WHERE d_date = (%s)', (week_ago,))

		conn.commit()


	else:
		
		for region in regions.keys():

			# if entry than update the data for today
			cursor.execute('''UPDATE alb 
							  SET (measures, active_cases, population, active_rate, d_date, hour) =
							  (%s, %s, %s, %s, %s, %s) 
							  WHERE name = (%s) AND d_date = (%s) AND prov = (%s)''',
							  	(regions[region].measures, regions[region].active_cases,
							  	regions[region].population, regions[region].active_rate, now_alb_date, now_alb_hour, 
							  	region, now_alb_date, RegionData.province))

			conn.commit()

	cursor.close()



if __name__ == "__main__":

	update_sql(scrape_alb())
