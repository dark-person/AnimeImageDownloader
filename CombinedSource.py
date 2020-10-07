from ParsedSource import ParsedSource


class CombinedSource:
    def __init__(self):
        self.source_list = []
        self.pixiv_id = ""
        self.danbooru_id = ""
        self.twitter_author = ""
        self.twitter_id = ""
        self.yandere_id = ""
        self.gelbooru_id = ""
        self.sankaku_id = ""

    def __repr__(self):
        string = "<Combined Source> "
        string += "[only] " if self.is_only() else ""
        string += ("pixiv : " + str(self.pixiv_id) + " ") if self.pixiv_id else ""
        string += ("twitter : [" + str(self.twitter_id) + " by " + str(
            self.twitter_author) + "] ") if self.twitter_author else ""
        string += ("danbooru : " + str(self.danbooru_id) + " ") if self.danbooru_id else ""
        string += ("yandere : " + str(self.yandere_id) + " ") if self.yandere_id else ""
        string += ("gelbooru : " + str(self.gelbooru_id) + " ") if self.gelbooru_id else ""
        string += ("sankakucomplex : " + str(self.sankaku_id) + " ") if self.sankaku_id else ""
        return string

    def is_empty(self):
        is_not_empty = self.pixiv_id or self.twitter_author or self.danbooru_id or self.yandere_id or self.gelbooru_id
        return not is_not_empty

    @staticmethod
    def parsed_twitter(twitter_url):
        back = twitter_url.split("twitter.com/")[1]
        author, twitter_id = back.split("/status/")
        return author, twitter_id

    def append(self, parsed_source: ParsedSource):
        self.source_list.append(parsed_source)

    def combine(self):
        self.source_list.sort(reverse=True)
        print(self.source_list)
        for item in self.source_list:
            if item.is_primary_pixiv() and not self.pixiv_id:
                self.pixiv_id = item.pixiv_id
            if item.is_primary_twitter() and not self.twitter_author:
                self.twitter_author, self.twitter_id = self.parsed_twitter(item.primary_url)
            if item.is_backup_danbooru():
                self.danbooru_id = item.danbooru_id
            if item.is_backup_yandere():
                self.yandere_id = item.yandere_id
            if item.is_backup_gelbooru():
                self.gelbooru_id = item.gelbooru_id
            if item.is_backup_sankakucomplex():
                self.sankaku_id = item.sankaku_id

    def is_only(self):
        return self.is_pixiv_only() or self.is_twitter_only()

    def is_pixiv_only(self):
        return self.pixiv_id and not self.twitter_author

    def is_twitter_only(self):
        return not self.pixiv_id and self.twitter_author

    def get_backup_site_list(self):
        new_list = []
        if self.danbooru_id:
            new_list.append("danbooru")
        if self.yandere_id:
            new_list.append("yandere")
        if self.gelbooru_id:
            new_list.append("gelbooru")
        if self.sankaku_id:
            new_list.append("sankakucomplex")
        return new_list

    def print_info(self):
        print(self.__repr__())
