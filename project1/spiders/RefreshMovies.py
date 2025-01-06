import scrapy
from pymongo import MongoClient


class RefreshMoviesSpider(scrapy.Spider):
    name = "RefreshMovies"
    allowed_domains = ["www.5movierulz.best"]
    start_urls = ["https://www.5movierulz.best/category/malayalam-featured"]

    def __init__(self, *args, **kwargs):
        super(RefreshMoviesSpider, self).__init__(*args, **kwargs)
        
        # MongoDB Atlas connection
        self.client = MongoClient("YOUR_MONGO_STRING")
        self.db = self.client['movies']
        self.movies_collection = self.db['movies']

        # Load existing movies into a set for quick lookup
        self.existing_movies = self.load_existing_movies()
        self.new_movies = []  # To store new movies found during the crawl
        self.consecutive_no_new_pages = 0  # Counter for consecutive pages with no new movies
        self.max_no_new_pages = 1  # Stop after 1 consecutive page with no new movies

    def load_existing_movies(self):
        """Load existing movies from the MongoDB collection."""
        existing_movies = self.movies_collection.find({}, {"Name": 1})
        return {movie['Name'] for movie in existing_movies}

    def parse(self, response):
        """Parse the movie list from the current page."""
        movie_data = response.xpath("//ul/li/div/div/a")
        new_movies_on_page = 0  # Counter for new movies on the current page

        for movie in movie_data:
            movie_name = movie.xpath(".//@title").get()
            if movie_name:
                new_movie_name = movie_name.split("(")[0].strip()
                if new_movie_name in self.existing_movies:
                    self.logger.info(f"Skipping existing movie: {new_movie_name}")
                    continue  # Skip if the movie already exists
            else:
                continue  # Skip if no name is found

            movie_link = movie.xpath(".//@href").get()
            thumbnail_url = movie.xpath(".//img/@src").get()

            yield response.follow(
                url=movie_link,
                callback=self.parse_movie,
                meta={
                    'movie_name': new_movie_name,
                    'thumbnail_url': thumbnail_url
                }
            )
            self.existing_movies.add(new_movie_name)
            self.new_movies.append({
                'Name': new_movie_name,
                'Thumbnail': thumbnail_url,
                'Link1': None,  # Placeholder, will be updated in parse_movie
                'Link2': None  # Placeholder, will be updated in parse_movie
            })
            self.logger.info(f"New movie found: {new_movie_name}")
            new_movies_on_page += 1

        # Check if we should continue to the next page
        if new_movies_on_page == 0:
            self.consecutive_no_new_pages += 1
            self.logger.info(f"No new movies found on this page. Consecutive pages: {self.consecutive_no_new_pages}")
        else:
            self.consecutive_no_new_pages = 0

        # Stop spider if max consecutive pages without new movies is reached
        if self.consecutive_no_new_pages >= self.max_no_new_pages:
            self.logger.info("No new movies found on consecutive pages. Stopping spider.")
            self.save_new_movies()
            return

        # Follow next page
        next_page = response.xpath("//div[@class='pagination']/a[contains(text(), 'Next')]/@href").get()
        if next_page:
            yield response.follow(url=next_page, callback=self.parse)

    def parse_movie(self, response):
        """Parse the movie details from the movie page."""
        video_link1 = response.xpath("//a[@class='mv_button_css'][1]/@href").get()
        video_link2 = response.xpath("//p/strong[contains(text(), 'wish')]/following-sibling::a/@href").get()

        # Update the corresponding new movie with its links
        movie_name = response.request.meta['movie_name']
        for movie in self.new_movies:
            if movie['Name'] == movie_name:
                movie['Link1'] = video_link2.replace("\r", "") if video_link2 else None
                movie['Link2'] = video_link1
                break

        yield {
            'Name': movie_name,
            'Thumbnail': response.request.meta['thumbnail_url'],
            'Link1': video_link2.replace("\r", "") if video_link2 else None,
            'Link2': video_link1
        }

    def save_new_movies(self):
        """Save newly found movies to MongoDB."""
        if self.new_movies:
            self.logger.info(f"Saving {len(self.new_movies)} new movies to MongoDB.")
            
            # Insert new movies into MongoDB
            self.movies_collection.insert_many(self.new_movies)

            # Print the titles of newly found movies
            self.logger.info("New movies found:")
            for movie in self.new_movies:
                self.logger.info(f"- {movie['Name']}")
        else:
            self.logger.info("No new movies to save.")

    def close(self, reason):
        """Close the MongoDB connection when the spider stops."""
        self.client.close()
