import time
import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# https://twitter.com/search?f=tweets&q=from%3Adatasci_blogs%20since%3A2015-05-12%20until%3A2015-08010&src=typd
browser = webdriver.Chrome()
base_url = "https://twitter.com/search?f=tweets&q=from%3A"
user = "datasci_blogs"
since = "2013-12-18"
until = "2014-02-18"
url = base_url + user + "%20since%3A" + since + "%20until%3A" + until + "&src=typed"

browser.get(url)
time.sleep(1)

body = browser.find_element_by_tag_name('body')

for _ in range(300):
    body.send_keys(Keys.PAGE_DOWN)
    time.sleep(0.2)

status_ids = browser.find_elements_by_class_name('js-stream-item')
time_stamps = browser.find_elements_by_class_name('_timestamp')
statuses = browser.find_elements_by_class_name('tweet-text')

i = 0
with open('datasci_blogs_raw2.tsv', 'a') as f:
    for tweet in statuses:
        time_stamp = datetime.datetime.fromtimestamp(int(time_stamps[i].get_attribute("data-time")))
        f.write(str(status_ids[i].get_attribute("data-item-id"))+'\t'+str(time_stamp)+'\t'+str(tweet.text.replace('\n',''))+'\n')
        i += 1


