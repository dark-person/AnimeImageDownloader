import logging
import os
from datetime import datetime
from pathlib import Path

from pixivpy3 import *

from container import Module
from exception import *

pixiv_logger = logging.getLogger("main.downloader.pixiv")


# Image That can use in testcase
# More than one page : 84557321
# Lost : 719484852
# Test : 59580629
# Lost : 56851730


class PixivModule(Module):
    output_root_directory = Path("output2")

    def __init__(self, username, password, bookmark_option=False):
        super().__init__(module_name="pixiv")
        pixiv_logger.info("%-20s ===> Pixiv Module Init", "[Pixiv Module]")
        self.pixiv_id = ""
        self.original_urls = []

        self.username = username
        self.password = password
        self.bookmark_option = bookmark_option

        self.api = AppPixivAPI()
        try:
            self.api.login(username, password)
            pixiv_logger.info("%-20s ===>     Pixiv Login Success", "[Pixiv Module]")
        except PixivError:
            raise PixivApiLoginException
        pixiv_logger.info("%-20s ===> Pixiv Module Completed", "[Pixiv Module]")

    def clear(self):
        super().clear()
        self.pixiv_id = ""
        self.original_urls = []

    def change_id(self, pixiv_id):
        self.clear()
        self.pixiv_id = str(pixiv_id)

        self.get_post_info()

    def get_post_info(self):
        pixiv_logger.info("%-20s [Get Post Info] Start..", "[Pixiv Module]")
        if self.pixiv_id == "":
            raise PixivIdMissingException

        json_result = self.api.illust_detail(self.pixiv_id)
        pixiv_logger.debug("%-20s [Get Post Info] Json: %s", "[Pixiv Module]", json_result)

        if 'illust' not in json_result:
            raise PixivIllustrationLostException

        illust = json_result['illust']

        if not illust['title'] and not illust['tags']:
            raise PixivIllustrationLostException

        if illust['meta_single_page']:
            self.original_urls.append(illust['meta_single_page']["original_image_url"])
        elif illust['meta_pages']:
            urls = list(map(lambda item: item['image_urls']['original'], illust['meta_pages']))
            self.original_urls.extend(urls)

        self.width = illust['width']
        self.height = illust['height']

        pixiv_logger.info("%-20s [Get Post Info] Completed. Image Size : %sx%s", "[Pixiv Module]", self.width,
                          self.height)

    def download_original_image(self, directory="output/unknown", filename=""):
        pixiv_logger.info("%-20s [Download Original] Start..", "[Pixiv Module]")

        if not filename:
            time_string = datetime.today().strftime('%Y%m%d_%H%M%S')
            filename = "illust_" + str(self.pixiv_id) + "_" + time_string

        # Download Image
        for i in range(0, len(self.original_urls)):
            single_image_url = self.original_urls[i]

            # Get extension of file
            url_basename = os.path.basename(single_image_url)
            extension = os.path.splitext(url_basename)[1]

            # Generate filename (app format)
            if len(self.original_urls) > 1:
                filename_single = filename + "_p" + str(i) + extension
            else:
                filename_single = filename + extension

            self.api.download(single_image_url, path=directory, fname=filename_single)

        if self.bookmark_option:
            self.api.illust_bookmark_add(self.pixiv_id)
            pixiv_logger.info("%-20s [Download Original] %s Bookmarked.", "[Pixiv Module]", self.pixiv_id)

        pixiv_logger.info("%-20s [Download Original] Completed.", "[Pixiv Module]")

    # Alternative of download
    def download(self, directory="output/unknown", filename=""):
        self.download_original_image(directory=directory, filename=filename)

    def get_dict(self):
        result_dict = {
            'height': self.height,
            'width': self.width,
            'img_size': self.img_size,
            'original_urls': self.original_urls,
            'pixiv_id': self.pixiv_id
        }
        return result_dict
