from bs4 import BeautifulSoup
import requests
import exception
from fake_headers import Headers
from urllib.parse import urlparse
import shutil
from datetime import datetime
import time
from PIL import Image
from pathlib import Path
from container import replace_reserved_character, Module
import logging

danbooru_logger = logging.getLogger("main.downloader.danbooru")


class DanbooruModule(Module):
    def clear(self):
        super().clear()
        self.danbooru_id = ""
        self.original_url = ""
        self.copyright_tag = []
        self.character_tag = []
        pass

    def __init__(self):
        super().__init__(module_name="danbooru")
        self.danbooru_id = ""
        self.width, self.height = 0, 0
        self.original_url = ""
        self.copyright_tag = []
        self.character_tag = []

    def change_id(self, danbooru_id):
        danbooru_logger.info("%-20s ===> Danbooru Module, init id..", "[Danbooru Module]")
        self.clear()
        self.danbooru_id = str(danbooru_id)
        danbooru_logger.info("%-20s ===>    ID : %s ", "[Danbooru Module]", self.danbooru_id)
        self.get_post_info()
        danbooru_logger.info("%-20s ===> Danbooru Module, init id..", "[Danbooru Module]")

    @staticmethod
    def identify_image_extension(url):
        t = urlparse(url)
        extension = "." + t.path.split(".")[-1]
        return extension

    def get_post_info(self):
        danbooru_logger.info("%-20s [Get Post info] Start.", "[Danbooru Module]")

        if not self.danbooru_id:
            danbooru_logger.error("%-20s [Get Post info] No Id.", "[Danbooru Module]")
            raise exception.DanbooruEmptyPostId

        response = requests.get("https://danbooru.donmai.us/posts/" + str(self.danbooru_id) + ".json")

        if response.status_code != 200:
            danbooru_logger.error("%-20s [get post info] response failed. End.", "[Danbooru Module]")
            danbooru_logger.debug("%-20s [get post info] https://danbooru.donmai.us/posts/%s.json", "[Danbooru Module]",
                                  str(self.danbooru_id))
            danbooru_logger.debug("%-20s [get post info] %s", "[Danbooru Module]", response.__dict__)
            raise exception.DanbooruRequestFailed

        danbooru_json = response.json()
        self.original_url = danbooru_json['file_url'] if 'file_url' in danbooru_json else ""
        self.width = danbooru_json['image_width'] if 'image_width' in danbooru_json else 0
        self.height = danbooru_json['image_height'] if 'image_height' in danbooru_json else 0
        self.img_size = danbooru_json['file_size'] if 'file_size' in danbooru_json else 0
        danbooru_logger.info("%-20s [get post info] Danbooru Resolution : %sx%s (%s)", "[Danbooru Module]",
                             str(self.width),
                             str(self.height), self.img_size)

        self.character_tag = danbooru_json['tag_string_character'].split(" ")
        self.copyright_tag = danbooru_json['tag_string_copyright'].split(" ")

        danbooru_logger.info("%-20s [Get Post info] Completed. Image Size : %sx%s", "[Danbooru Module]",
                             str(self.width),
                             str(self.height))
        return self.get_dict()

    # TODO: download_original_image should be include tags and pixiv id
    def download_original_image(self):
        danbooru_logger.info("%-20s [Download Original] Start.", "[Danbooru Module]")

        if not self.original_url:
            danbooru_logger.error("%-20s [Download Original] Empty Original Image URL, End.", "[Danbooru Module]")
            raise exception.DanbooruEmptyImageUrl

        image_name = self.original_url.split('/')[-1]

        # download the temp image
        danbooru_logger.info("%-20s [Download Original] downloading base image[%s]..", "[Danbooru Module]",
                             self.original_url)
        image_response = requests.get(self.original_url)
        # print(image_response.__dict__)
        if image_response.status_code != 200:
            danbooru_logger.error("%-20s [Download Original] Image Request Failed", "[Danbooru Module]")
            raise exception.DanbooruRequestFailed

        filepath = "output/danbooru_" + image_name
        file = open(filepath, "wb")
        file.write(image_response.content)
        file.close()
        danbooru_logger.info("%-20s [Download Original] image downloaded, in %s", "[Danbooru Module]", filepath)

        return filepath

    def download(self, directory="output/unknown", filename=""):
        temp_img_path = self.download_original_image()

        if not filename:
            filename = temp_img_path.split("/")[-1]
            filename = filename.split(".")[0]

        path_obj = Path(directory)
        path_obj.mkdir(exist_ok=True, parents=True)

        item = Path(temp_img_path)
        new_img_path = directory + "/" + filename + item.suffix
        danbooru_logger.info("%-20s [Download] New image Path : %s", "[Danbooru Module]", new_img_path)
        item.rename(new_img_path)
        danbooru_logger.info("%-20s [Download] Completed.", "[Danbooru Module]")

    def get_dict(self):
        result_dict = {'height': self.height, 'width': self.width, 'danbooru_id': self.danbooru_id,
                       'original_url': self.original_url, 'copyright_tag': self.copyright_tag,
                       'character_tag': self.character_tag, 'img_size': self.img_size, }
        return result_dict
