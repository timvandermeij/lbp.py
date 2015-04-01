import sys
import os
from BeautifulSoup import BeautifulSoup
import urllib2

class Scraper:
    MAIN_URL = 'https://unsplash.com'
    GRID_URL = 'https://unsplash.com/grid?page={}'

    def __init__(self, target, limit):
        self.target = target
        self.limit = limit
        self.downloaded = 0

    def scrape(self):
        page_number = 1
        while self.downloaded < self.limit:
            dates = []
            page = urllib2.urlopen(Scraper.GRID_URL.format(page_number))
            parsed_page = BeautifulSoup(page)
            for photo in parsed_page.findAll("div", {"class": "photo"}):
                source = photo.find("a").get("href")

                # Download the photo to the target directory.
                if self.downloaded >= self.limit:
                    break
                
                self.download(source)

            page_number += 1

    def download(self, source):
        downloaded_size = 0
        block_size = 8192
        connection = urllib2.urlopen(Scraper.MAIN_URL + source)
        output = open('{}/{}.jpg'.format(self.target, self.downloaded + 1), 'wb')
        total_size = int(connection.info().getheaders("Content-Length")[0])
        
        while True:
            buffer = connection.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            output.write(buffer)
            percentage = int(float(downloaded_size * 100) / total_size)
            message = r"Downloading {} [{:3d}%]".format(source, percentage)
            message = message + chr(8) * len(message) # Clear the previous message
            sys.stdout.write(message)

        sys.stdout.write('\n')
        output.close()
        self.downloaded += 1

def main(argv):
    limit = int(argv[0]) if len(argv) > 0 else 10
    target = argv[1] if len(argv) > 1 else "images"
   
    if not os.path.exists(target):
        os.makedirs(target)

    scraper = Scraper(target, limit)
    scraper.scrape()

if __name__ == "__main__":
    main(sys.argv[1:])
