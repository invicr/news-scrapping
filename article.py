# article.py
class Article:
    def __init__(self, title: str, url: str, date: str, content: str):
        self.title = title
        self.url = url
        self.date = date
        self.content = content

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "date": self.date,
            "content": self.content
        }
