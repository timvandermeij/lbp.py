import sys
import os
from BeautifulSoup import BeautifulSoup
import urllib2
import imghdr
import argparse

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
        output_file = '{}/{}'.format(self.target, self.downloaded + 1)
        output = open('{}.tmp'.format(output_file), 'wb')
        total_size = int(connection.info().getheaders("Content-Length")[0])
        
        while True:
            buffer = connection.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            output.write(buffer)
            percentage = int(float(downloaded_size * 100) / total_size)
            message = r"Downloading image {} [{:3d}%]".format(self.downloaded + 1, percentage)
            message = message + chr(8) * len(message) # Clear the previous message
            sys.stdout.write(message)

        sys.stdout.write('\n')
        output.close()
        self.downloaded += 1

        # Rename the temporary file extension to the actual file extension
        file_type = imghdr.what('{}.tmp'.format(output_file))
        os.rename('{}.tmp'.format(output_file), '{}.{}'.format(output_file, file_type))

def main(argv):
    # Argument parsing
    parser = argparse.ArgumentParser(description='Scrape images from Unsplash.com.')
    parser.add_argument('--limit', dest='limit', type=int, default=10, help='maximum number of images to scrape')
    parser.add_argument('--target', dest='target', type=str, default='images', help='name of the folder for storing the downloaded images')
    arguments = parser.parse_args()

    # Make sure that the target directory exists
    if not os.path.exists(arguments.target):
        os.makedirs(arguments.target)

    scraper = Scraper(arguments.target, arguments.limit)
    scraper.scrape()

if __name__ == "__main__":
    main(sys.argv[1:])
