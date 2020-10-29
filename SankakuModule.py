import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image
from fake_headers import Headers

import exception
from container import replace_reserved_character, Module

sankaku_logger = logging.getLogger("main.downloader.sankaku")


class SankakuModule(Module):
    # For sankaku complex, there are a time limit between request of same original image, about 60s
    def __init__(self, sankaku_id=000000):
        super().__init__(module_name="sankaku")
        sankaku_logger.info("%-20s ===> Sankaku Module Init", "[Sankaku Module]")

        self.sankaku_id = str(sankaku_id)
        self.width, self.height = 0, 0
        self.original_url = ""
        self.copyright_tag = []
        self.character_tag = []
        self.last_request_time = datetime.min

        self.header = Headers(os="mac", headers=False).generate()
        if sankaku_id != 000000:
            self.get_post_info()
        sankaku_logger.info("%-20s ===> Sankaku Module Init Completed", "[Sankaku Module]")

    def change_id(self, sankaku_id):
        sankaku_logger.info("%-20s ===> Sankaku Module, init id..", "[Sankaku Module]")
        self.clear()
        self.sankaku_id = str(sankaku_id)

        self.get_post_info()
        sankaku_logger.info("%-20s ===> Sankaku Module, init id completed.", "[Sankaku Module]")

    def clear(self):
        super().clear()
        self.sankaku_id = ""
        self.original_url = ""
        self.copyright_tag = []
        self.character_tag = []
        self.header = Headers(headers=True).generate()

    @staticmethod
    def identify_image_extension(url):
        t = urlparse(url)
        extension = "." + t.path.split(".")[-1]
        return extension

    def get_last_image_request(self) -> datetime:
        return self.last_request_time

    def get_post_info(self):
        sankaku_logger.info("%-20s [Get Post info] Start.", "[Sankaku Module]")
        response = requests.get("https://capi-v2.sankakucomplex.com/posts/" + self.sankaku_id, headers=self.header)
        sankaku_logger.debug("%-20s [Get Post Info] Response : %s", "[Sankaku Module]", response.__dict__)

        if response.status_code != 200:
            sankaku_logger.error("%-20s [Get Post info] Request Failed.", "[Sankaku Module]")
            raise exception.SankakuRequestFailed

        result_json = response.json()

        self.original_url = result_json['file_url'] if 'file_url' in result_json else ""
        self.width = result_json['width'] if 'width' in result_json else 0
        self.height = result_json['height'] if 'height' in result_json else 0
        self.img_size = result_json['file_size'] if 'file_size' in result_json else 0

        if 'tags' in result_json:
            for item in result_json['tags']:
                if item['type'] == 3:
                    self.copyright_tag.append(replace_reserved_character(item['name_en']))
                elif item['type'] == 4:
                    self.character_tag.append(replace_reserved_character(item['name_en']))

        sankaku_logger.info("%-20s [Get Post info] Complete. Image Size : %sx%s (%s)", "[Sankaku Module]",
                            str(self.width), str(self.height), self.img_size)
        return self.get_dict()

    # TODO: download_original_image should be include tags and pixiv id
    def download_original_image(self, retry_count=0) -> str:

        if retry_count != 0:
            sankaku_logger.info("%-20s [Download Original] Retry Counter : %s", "[Sankaku Module]", str(retry_count))

        if retry_count % 3 == 0 and retry_count != 0:
            sankaku_logger.info("%-20s [Download Original] Long Sleep..", "[Sankaku Module]")
            time.sleep(90)
            sankaku_logger.info("%-20s [Download Original] Long Sleep Finished.", "[Sankaku Module]")

        if retry_count > 10:
            sankaku_logger.error("%-20s [Download Original] Retry Limit Reached.", "[Sankaku Module]")
            raise exception.SankakuTooManyDummyPicDownloaded

        if self.original_url == "":
            sankaku_logger.error("%-20s [Download Original] Empty Original Url", "[Sankaku Module]")
            raise exception.SankakuEmptyOriginalURL

        # TODO:Not sure about the time interval between request, may need sleep
        difference = (datetime.today() - self.last_request_time).total_seconds()
        sankaku_logger.info("%-20s [Download Original] Time difference of last request: %s", "[Sankaku Module]",
                            str(difference))
        if difference < 30:
            sankaku_logger.info("%-20s [Download Original] Sleeping...", "[Sankaku Module]")
            time.sleep(30)
            sankaku_logger.info("%-20s [Download Original] Sleep Finished.", "[Sankaku Module]")

        sankaku_logger.info("%-20s [Download Original] Start download in %s", "[Sankaku Module]", self.original_url)
        response2 = requests.get(self.original_url, headers=self.header, stream=True)
        sankaku_logger.debug("%-20s [Download Original] Response : %s", "[Sankaku Module]", str(response2.__dict__))

        self.last_request_time = datetime.today()
        time_string = self.last_request_time.strftime('%Y%m%d_%H%M%S')
        extension = self.identify_image_extension(self.original_url)
        filepath = "output/sankaku_" + self.sankaku_id + "_" + time_string + extension

        with open(filepath, "wb") as file:
            shutil.copyfileobj(response2.raw, file)
        del response2
        sankaku_logger.info("%-20s [Download Original] Download Complete.", "[Sankaku Module]")

        img = Image.open(filepath)
        width, height = img.size
        sankaku_logger.info("%-20s [Download Original] Width, Height : %sx%s ", "[Sankaku Module]", width, height)
        if width == 392 and height == 150:
            sankaku_logger.info("%-20s [Download Original] Downloaded Dummy Pic.", "[Sankaku Module]")
            Path(filepath).unlink()
            self.header = Headers(headers=True).generate()
            sankaku_logger.info("%-20s [Download Original] Switched Header, Ready to retry..", "[Sankaku Module]")
            sankaku_logger.info("%-20s [Download Original] =====================", "[Sankaku Module]")
            return self.download_original_image(retry_count=retry_count + 1)

        return filepath

    def download(self, directory="output/unknown", filename=""):
        # TODO

        temp_img_path = self.download_original_image()

        if not filename:
            filename = temp_img_path.split("/")[-1]

        sankaku_logger.info("%-20s [Download] Filename = %s ", "[Sankaku Module]", filename)

        item = Path(temp_img_path)
        new_img_path = directory + "/" + filename + item.suffix
        sankaku_logger.info("%-20s [Download] New image Path : %s", "[Sankaku Module]", new_img_path)

        Path(new_img_path).unlink(missing_ok=True)
        item.rename(new_img_path)
        sankaku_logger.info("%-20s [Download] Completed.", "[Sankaku Module]")

    def get_dict(self):
        result_dict = {'height': self.height, 'width': self.width, 'sankaku_id': self.sankaku_id,
                       'img_size': self.img_size,
                       'original_url': self.original_url, 'copyright_tag': self.copyright_tag,
                       'character_tag': self.character_tag}
        return result_dict

# obj = SankakuModule()
# obj.change_id(21079756)
# obj.download_original_image()
# print(obj.get_dict())
# print("++++++++++++++++++=")
# obj.change_id(21700573)
# obj.download_original_image()
# print(obj.get_dict())
