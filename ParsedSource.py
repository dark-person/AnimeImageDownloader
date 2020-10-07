from pysaucenao import GenericSource


class ParsedSource(object):
    # Due to complex return of saucenao api, some redundant operation may appear
    # input     :   source      - the item in results.results of Saucenao result
    #               only_flag   - if the source is the only result that return, the flag will be True
    def __init__(self, source: GenericSource):
        self.data = source.data

        # Essential Element
        self.similarity = source.similarity
        self.author = source.author_name
        self.urls_list = []

        # Set urls
        if source.url:
            self.urls_list.append(source.url)
        if 'ext_urls' in source.data:
            self.urls_list.extend(source.data['ext_urls'])
        if 'source' in source.data and 'http' in source.data['source']:
            self.urls_list.append(source.data['source'])

        # Pixiv id and danbooru post id
        self.danbooru_id = source.data['danbooru_id'] if 'danbooru_id' in source.data else ""
        self.pixiv_id = source.data['pixiv_id'] if 'pixiv_id' in source.data else ""
        self.yandere_id = source.data['yandere_id'] if 'yandere_id' in source.data else ""
        self.gelbooru_id = source.data['gelbooru_id'] if 'gelbooru_id' in source.data else ""
        self.sankaku_id = source.data['sankaku_id'] if 'sankaku_id' in source.data else ""

        # identify source reference and set final source url and it's backup
        self.source_reference = "unknown"
        self.backup_reference = []
        self.primary_url = ""
        self.backup_urls = []

        self.identify_primary_source(self.urls_list)
        self.identify_backup_reference()

    def __repr__(self):
        string = "<Parsed Source (" + str(self.similarity) + ")[" + str(self.source_reference)
        string += "]> : " + str(self.primary_url) + ", [backup : " + str(self.backup_reference) + "]" + \
                  ", addition info (pixiv " + str(self.pixiv_id) + ") (danbooru " + str(self.danbooru_id) + ") " + \
                  "(yandere " + str(self.yandere_id) + ") (gelbooru " + str(self.gelbooru_id) + ")" + \
                  "(sankaku " + str(self.sankaku_id) + ")" + "(By " + str(self.author) + ")"
        return string

    def __gt__(self, other):
        return self.similarity > other.similarity

    def is_primary_pixiv(self):
        return self.source_reference == "pixiv"

    def is_primary_twitter(self):
        return self.source_reference == "twitter"

    def is_backup_danbooru(self):
        return "danbooru" in self.backup_reference

    def is_backup_yandere(self):
        return "yandere" in self.backup_reference

    def is_backup_gelbooru(self):
        return "gelbooru" in self.backup_reference

    def is_backup_sankakucomplex(self):
        return "sankakucomplex" in self.backup_reference

    # function  - identify_primary_source
    #           -> set the source reference and backup urls and source url of ParsedSource
    #           -> it will not affect the input self.urls_list
    # input     - urls_list     : list, all url retrieved from source
    # output    - None
    def identify_primary_source(self, urls_list):
        for url in urls_list:
            if 'pixiv' in url:
                self.source_reference = "pixiv"
                self.primary_url = url
                urls_list.remove(url)
                self.backup_urls = urls_list
                return
        for url in urls_list:
            if 'twitter' in url:
                self.source_reference = "twitter"
                self.primary_url = url
                urls_list.remove(url)
                self.backup_urls = urls_list
                return
        self.source_reference = "unknown"
        self.primary_url = ""
        self.backup_urls = urls_list

    def identify_backup_reference(self):
        for url in self.backup_urls:
            if 'danbooru' in url:
                self.backup_reference.append("danbooru")
            if 'gelbooru' in url:
                self.backup_reference.append("gelbooru")
            if 'yande.re' in url:
                self.backup_reference.append('yandere')
            if 'sankakucomplex' in url:
                self.backup_reference.append('sankakucomplex')
