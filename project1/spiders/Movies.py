import scrapy


class MoviesSpider(scrapy.Spider):
    name = "Movies"
    allowed_domains = ["www.5movierulz.best"]
    start_urls = ["https://www.5movierulz.best/category/malayalam-featured"]
    
    def parse(self, response):
        movie_data = response.xpath("//ul/li/div/div/a")

        for movie in movie_data:
            movie_name = movie.xpath(".//@title").get()
            if movie_name:
                new_movie_name = movie_name.split("(")[0].strip()
            movie_link = movie.xpath(".//@href").get()

            thumbnail_url = movie.xpath(".//img/@src").get()

            yield response.follow(url=movie_link, callback = self.parse_movie, meta={
                'movie_name': new_movie_name,
                'thumbnail_url': thumbnail_url
            })

            

        next_page = response.xpath("//div[@class='pagination']/a[contains(text(), 'Next')]/@href").get()

        if next_page:
            yield response.follow(url=next_page, callback = self.parse, meta={'movie_name':new_movie_name})

            

    def parse_movie(self,response):

        video_link1= response.xpath("//a[@class='mv_button_css'][1]/@href").get()
        video_link2= response.xpath("//p/strong[contains(text(), 'wish')]/following-sibling::a/@href").get()



        yield{
            'Name':response.request.meta['movie_name'],
            'Thumbnail':response.request.meta['thumbnail_url'],
            
            'Link1':video_link2.replace("\r", ""),
            'Link2':video_link1
        } 


       
