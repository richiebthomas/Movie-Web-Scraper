import os
import requests
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from project1.spiders.Movies import MoviesSpider
from project1.spiders.RefreshMovies import RefreshMoviesSpider

def run_spider():
    if os.path.exists('movies.json'):
        pass
        # os.remove('movies.json')
    settings = get_project_settings()
    # settings.set('FEEDS', {
    #     'movies.json': {
    #         'format': 'json',
    #         'encoding': 'utf8',
    #         'store_empty': False,
    #         'indent': 4,
    #     },
    # })
    process = CrawlerProcess(settings=settings)
    process.crawl(RefreshMoviesSpider)
    process.start()
    
    # Notify the Flask app
    requests.get('http://127.0.0.1:5000/update_notification')

if __name__ == "__main__":
    run_spider()
