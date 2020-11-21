from container import *
from pygelbooru import Gelbooru, GelbooruException
from exception import *
import requests
import logging
from pathlib import Path

gelbooru_logger = logging.getLogger("main.downloader.gelbooru")


# https://gelbooru.com/index.php?page=dapi&s=post&q=index
class GelbooruModule(Module):
    BASE_URL = "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1"

    # Due to api not return the tags in category,
    # Therefore not consider copyright and character tags implementation

    def __init__(self, width=0, height=0, module_name=""):
        super().__init__(module_name="gelbooru")
        gelbooru_logger.info("%-20s ===> Gelbooru Module Init", "[Gelbooru Module]")
        self.gelbooru = Gelbooru()
        self.width, self.height = 0, 0
        self.gelbooru_id = ""
        self.original_url = ""
        gelbooru_logger.info("%-20s ===> Gelbooru Module Completed", "[Gelbooru Module]")

    def change_id(self, item_id):
        gelbooru_logger.info("%-20s ===> Gelbooru Module, init id..", "[Gelbooru Module]")
        self.clear()
        self.gelbooru_id = str(item_id)
        gelbooru_logger.info("%-20s ===>    ID : %s ", "[Gelbooru Module]", self.gelbooru_id)
        self.get_post_info()
        gelbooru_logger.info("%-20s ===> Gelbooru Module, init id completed.", "[Gelbooru Module]")

    def clear(self):
        super().clear()
        self.gelbooru_id = ""
        self.original_url = ""

    def get_post_info(self):
        gelbooru_logger.info("%-20s [Get Post info] Start.", "[Gelbooru Module]")

        if not self.gelbooru_id:
            gelbooru_logger.error("%-20s [Get Post info] No Id.", "[Gelbooru Module]")
            raise GelbooruEmptyPostId

        response = requests.get(self.BASE_URL + "&id=" + str(self.gelbooru_id))

        if response.status_code != 200:
            gelbooru_logger.error("%-20s [get post info] response failed. End.", "[Gelbooru Module]")
            gelbooru_logger.debug("%-20s [get post info] %s", "[Gelbooru Module]",
                                  self.BASE_URL + "&id=" + str(self.gelbooru_id))
            gelbooru_logger.debug("%-20s [get post info] %s", "[Gelbooru Module]", response.__dict__)
            raise GelbooruRequestFailed

        gelbooru_json = response.json()
        self.width = gelbooru_json['width'] if 'width' in gelbooru_json else 0
        self.height = gelbooru_json['height'] if 'height' in gelbooru_json else 0
        self.original_url = gelbooru_json['file_url'] if 'file_url' in gelbooru_json else ""

        gelbooru_logger.info("%-20s [Get Post info] Completed. Image Size : %sx%s", "[Gelbooru Module]",
                             str(self.width),
                             str(self.height))
        return self.get_dict()

    def download_original_image(self):
        gelbooru_logger.info("%-20s [Download Original] Start.", "[Gelbooru Module]")

        if not self.original_url:
            gelbooru_logger.error("%-20s [Download Original] Empty Original Image URL, End.", "[Gelbooru Module]")
            raise GelbooruEmptyImageURL

        image_name = self.original_url.split('/')[-1]

        # download the temp image
        gelbooru_logger.info("%-20s [Download Original] downloading base image[%s]..", "[Gelbooru Module]",
                             self.original_url)
        image_response = requests.get(self.original_url)
        # print(image_response.__dict__)
        if image_response.status_code != 200:
            gelbooru_logger.error("%-20s [Download Original] Image Request Failed", "[Gelbooru Module]")
            raise GelbooruRequestFailed

        filepath = "output/gelbooru_" + image_name
        file = open(filepath, "wb")
        file.write(image_response.content)
        file.close()
        gelbooru_logger.info("%-20s [Download Original] image downloaded, in %s", "[Gelbooru Module]", filepath)

        return filepath

    def download(self, directory="output/unknown", filename=""):
        temp_img_path = self.download_original_image()

        if not filename:
            filename = Path(temp_img_path).stem
        if filename[0] == "_":
            filename = Path(temp_img_path).stem + filename

        path_obj = Path(directory)
        path_obj.mkdir(exist_ok=True, parents=True)

        item = Path(temp_img_path)
        new_img_path = directory + "/" + filename + item.suffix
        gelbooru_logger.info("%-20s [Download] New image Path : %s", "[Gelbooru Module]", new_img_path)

        # Clear Destination File to ensure it is empty
        destination_item = Path(new_img_path)
        if destination_item.exists():
            destination_item.unlink()

        item.rename(new_img_path)
        gelbooru_logger.info("%-20s [Download] Completed.", "[Gelbooru Module]")

    def get_dict(self):
        return {"gelbooru_id": self.gelbooru_id, "width": self.width, "height": self.height,
                "original": self.original_url}
