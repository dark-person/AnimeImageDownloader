import logging
import os
import shutil
from pathlib import Path

from PIL import Image

from container import *

input_logger = logging.getLogger("main.downloader.input")


# TODO

class InputImageModule(Module):
    def __init__(self):
        input_logger.info("%-20s [Init] ->> Start..", "[Input Image Module]")
        super().__init__(module_name="input")
        self.image_path = ""
        input_logger.info("%-20s [Init] ->> Finished.", "[Input Image Module]")

    def change_id(self, item_id):
        raise MethodNotApplicableException

    def set_image(self, image_path: str):
        self.image_path = image_path
        img = Image.open(image_path)
        self.width, self.height = img.size
        self.img_size = os.stat(image_path).st_size
        input_logger.info("%-20s [Set Image] Image Size : %sx%s (%s)", "[Input Image Module]", str(self.width),
                          self.height, self.img_size)

    def clear(self):
        super().clear()
        self.image_path = ""

    def get_post_info(self):
        raise MethodNotApplicableException

    def download_original_image(self):
        raise MethodNotApplicableException

    def download(self, directory="output/unknown", filename=""):
        if not self.image_path:
            raise InputImageEmptyException
        if not filename:
            filename = self.image_path.split('/')[-1]

        item = Path(self.image_path)

        destination = directory + "/" + filename + item.suffix
        input_logger.info("%-20s [Download] destination : %s", "[Input Image Module]", destination)
        shutil.copy2(self.image_path, destination)
        input_logger.info("%-20s [Download] Complete.", "[Input Image Module]")

    def get_dict(self):
        result_dict = {'height': self.height, 'width': self.width,
                       'img_size': self.img_size, 'image_path': self.image_path}
        return result_dict
