from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep
from mangadexsecrets import username,password
import requests
import re

# Global Variables
list_of_follows = {}
manga_dict = {}
data = []
url = "https://mangadex.org/title/"
hrefs = []
whitelist = ' -'
manga_urls = []
chapter_count = 100
page_num = 1
language = 1 # English
chapters = [] # List of Chapter classes
testing = []

class Chapter:
    def __init__(self, id, title, chapter, volume, comments, read, lang, group, uploader, views, timestamp, manga_id, text):
        self.id = id
        self.title = title
        self.chapter = chapter
        self.volume = volume
        self.comments = comments
        self.read = read
        self.lang = lang
        self.group = group
        self.uploader = uploader
        self.views = views
        self.timestamp = timestamp
        self.manga_id = manga_id
        self.text = text

    def format(self):
        print(self.text)

class MangaDex:
    def __init__(self):
        # Create Instance
        self.driver = webdriver.Chrome()
        self.driver.get("https://mangadex.org/login")
        sleep(2)

        # Login 
        self.driver.find_element_by_name("login_username").send_keys(username)
        self.driver.find_element_by_name("login_password").send_keys(password)
        sleep(2)

        #rmbr_me = self.driver.find_element_by_xpath("//*[@id='remember_me']").click()
        login_page_buttons = self.driver.find_elements_by_tag_name("button")
        login_button = login_page_buttons[3]
        login_button.click()
        sleep(5)

        # Navigate to Follows
        #follows = self.driver.find_element_by_xpath("//*[@id='follows']/a").click()
        navi_dropdown = self.driver.find_element_by_xpath("//*[@id='navbarSupportedContent']/ul[2]/li[2]/a").click()
        follows = self.driver.find_element_by_xpath("//*[@id='navbarSupportedContent']/ul[2]/li[2]/div/a[4]").click()
        sleep(5)

        # Gather List of Manga that User Follows
        container = self.driver.find_element_by_xpath("//*[@id='content']/div[4]")
        titles = container.find_elements_by_tag_name('a')

        # Configure Each Mangas ID
        manga_ids = []
        for ids in titles:
            id_num = ids.get_attribute('href')
            if ("title" in id_num):
                id_num = id_num[27:]
                count = 0
                for char in id_num:
                    if char == '/':
                        id_num = id_num[:count]
                        if int(id_num) not in manga_ids:
                            manga_ids.append(int(id_num))
                    else:
                        count = count + 1
        print("Getting Manga IDs ...")

        # Configure Each Mangas Title
        temp_follows = []
        for item in titles:
            temp_follows.append(item.text)
        placeholder = 0
        count = len(temp_follows)
        global data
        while (placeholder < count):
            if (not(temp_follows[placeholder] == '') and not(temp_follows[placeholder+1] == '')):
                data.append(temp_follows[placeholder])
            placeholder = placeholder + 1
        print("Getting Manga Titles ...")
        
        # Create Dictionary for Webscraping
        counter = 0
        global list_of_follows
        for manga in data:
            list_of_follows[manga] = manga_ids[counter]
            counter = counter + 1

        # Creating URLs for Each Manga
        global manga_urls
        global manga_dict
        for title, num in list_of_follows.items():
            temp = title
            temp = re.sub(r'[^\w'+whitelist+']', '', temp)
            temp = temp.replace(' ', '-')
            page_url = url + str(num) + '/' + temp
            manga_urls.append(page_url)
            manga_dict[title] = page_url
        
    # Scrape All Chapters in the Given Language for Each Manga User Follows
    def GetAllChapters(self):
        print("Getting Chapters for each Manga ...")
        for url in manga_urls:
            temp_list = []
            manga_page = requests.get(url)
            soup = BeautifulSoup(manga_page.text, features = 'lxml')
            results = soup.find(id = 'content')
            div = results.find_all('div', class_ = 'chapter-row d-flex row no-gutters p-2 align-items-center border-bottom odd-row')

            # Determine Number of Pages
            edit_tab = results.find('div', class_ = 'edit tab-content')
            get_chapters = edit_tab.find('p', class_ = 'mt-3 text-center')
            if (not(type(get_chapters) == None) and not(get_chapters == None)):
                chapter_count = [int(x) for x in re.findall(r'\b\d+\b', get_chapters.text)][-1]
            page_num = -(- chapter_count // 100)

            # Iterate through pages
            for page in range(1, page_num + 1):
                page_url = url + f'/chapters/{page}/'
                page_req = requests.get(page_url)
                page_soup = BeautifulSoup(page_req.text,features='lxml')
                page_results = page_soup.find(id = 'content')
                page_div = page_results.find_all('div', class_ = 'chapter-row d-flex row no-gutters p-2 align-items-center border-bottom odd-row')

                # Find Each Chapter in Given Language
                for data in page_div[1:]:
                    if int(data.get('data-lang')) == language:
                        chapter_name = data.find('div', class_ = 'col col-lg-5 row no-gutters align-items-center flex-nowrap text-truncate pr-1 order-lg-2')
                        if not(chapter_name == None):
                            title = chapter_name.find('a', class_ = 'text-truncate')
                            chapter_title = title.text
                            temp = Chapter(data.get('data-id'), data.get('data-title'), 
                                data.get('data-chapter'), data.get('data-volume'), data.get('data-comments'), 
                                data.get('data-read'), data.get('data-lang'), data.get('data-group'), 
                                data.get('data-uploader'), data.get('data-views'), data.get('data-timestamp'), 
                                data.get('data-manga-id'), str(chapter_title))
                            temp_list.append(temp)

            # Place All Chapters in a List
            if not(temp_list == []):
                testing.append(temp_list[0].text)
                testing.append(temp_list[0].manga_id)     
                chapters.append(temp_list)

    # Finds Latest Chapter in Set Language
    def ReturnRecentChapter(self):
        print("Returning Latest Chapters ...")
        for manga, url in manga_dict.items():
            first = True
            manga_page = requests.get(url)
            soup = BeautifulSoup(manga_page.text, features = 'lxml')
            results = soup.find(id = 'content')
            div = results.find_all('div', class_ = 'chapter-row d-flex row no-gutters p-2 align-items-center border-bottom odd-row')
            for data in div[1:]:
                if int(data.get('data-lang')) == language:
                    chapter_name = data.find('div', class_ = 'col col-lg-5 row no-gutters align-items-center flex-nowrap text-truncate pr-1 order-lg-2')
                    if (first == True):
                        if not(chapter_name == None):
                            title = chapter_name.find('a', class_ = 'text-truncate')
                            chapter_title = title.text
                            print(f'Latest Chapter for {manga} - {chapter_title}')
                            first = False
                else:
                    if (first == True):
                        print(f'No Recent Chapter Found for {manga} in Set Language')
                        first = False

    # Finds Most Recent List of Featured Mangas
    def GetFeaturedManga(self):
        print("Getting Featured Mangas ...")
        featured_url = 'https://mangadex.org/featured'
        featured_page = requests.get(featured_url)
        soup = BeautifulSoup(featured_page.text, features = 'lxml')
        results = soup.find(id = 'content')
        chapter_container = results.find_all('div', class_ = 'manga-entry col-lg-6 border-bottom pl-0 my-1')
        for data in chapter_container:
            chapter_name = data.find('a', class_ = 'ml-1 manga_title text-truncate')
            print(chapter_name.text)

    # Finds Latest Updated Manga and Most Recent Chapter
    def GetLatestUpdates(self):
        print("Getting Latest Updates ...")
        url = 'https://mangadex.org'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, features = 'lxml')
        results = soup.find(id = 'content')
        container = results.find_all('div', class_ = 'col-md-6 border-bottom p-2')
        for data in container:
            manga_name = data.find('a', class_ = 'text-truncate')
            manga_class = data.find('div', class_ = 'py-0 mb-1 row no-gutters align-items-center flex-nowrap')
            manga_chapter = manga_class.find('a', class_ = 'text-truncate')
            print(f'{manga_name.text} - {manga_chapter.text}')
    
MangaDex()