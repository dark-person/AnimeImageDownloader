import abc
from urllib.parse import urlparse
from exception import *
import logging


def replace_multi_character(char_string, text):
    for c in char_string:
        if c in text:
            text = text.replace(c, "_")
    return text


def replace_reserved_character(text):
    return replace_multi_character("/\\?%*:|\"<>.,;= ", text)


class Module(abc.ABC):
    module_logger = logging.getLogger("main.module")

    # Module Cycle :
    # Module.__init__ -> Module.change_id -> Module.download_original_image -> Module.clear
    # (Next Image)    -> Module.change_id -> Module.download_original_image -> Module.clear ...
    @abc.abstractmethod
    def __init__(self, width=0, height=0, module_name=""):
        self.width = width
        self.height = height
        self.img_size = 0
        self.module_name = module_name

    def __gt__(self, other):
        # Possible matching:
        # 1. A.width > B.width, A.height > B.height
        if self.width > other.width and self.height > other.height:
            return True

        # 2. A.width < B.width, A.height < B.height
        if self.width < other.width and self.height < other.height:
            return False

        # 3. A.width = B.width, A.height = B.height
        if self.width == other.width and self.height == other.width:
			self.module_logger.debug("%-20s [Compare Module] Width Height Equal", "[Module]")
			self.module_logger.debug("%-20s [Compare Module] pixiv : %s %s", "[Module]", self.module_name == "pixiv", other.module_name == "pixiv")
			self.module_logger.debug("%-20s [Compare Module] danbooru : %s %s", "[Module]", self.module_name == "danbooru", other.module_name == "danbooru")
			self.module_logger.debug("%-20s [Compare Module] inpit : %s %s", "[Module]", self.module_name == "input", other.module_name == "input")
			self.module_logger.debug("%-20s [Compare Module] sankaku : %s %s", "[Module]", self.module_name == "sankaku", other.module_name == "sankaku")
            if self.module_name == "pixiv":
                return True
            elif other.module_name == "pixiv":
                return False
            elif self.module_name == "danbooru":
                return True
            elif other.module_name == "danbooru":
                return False
            elif self.module_name == "input":
                return True
            elif other.module_name == "input":
                return False
            elif self.module_name == "sankaku":
                return True
            elif other.module_name == "sankaku":
                return False

        # 4. A.width > B.width, A.height = B.height
        # 5. A.width > B.width, A.height < B.height
        # 6. A.width = B.width, A.height > B.height
        # 7. A.width = B.width, A.height < B.height
        # 8. A.width < B.width, A.height > B.height
        # 9. A.width < B.width, A.height = B.height
        # --> Image Bended

        self.module_logger.warning("%-20s [Compare Module] Possible Image Bending..", "[Module]")
        self.module_logger.warning("%-20s [Compare Module] %s : %s x %s (%s)", "[Module]", self.module_name, self.width,
                                   self.height, self.img_size)
        self.module_logger.warning("%-20s [Compare Module] %s : %s x %s (%s)", "[Module]", other.module_name,
                                   other.width, other.height, other.img_size)

        # Possible Module Name: Input, Pixiv, Danbooru, Sankaku
        # Input: Maybe wrong source
        # Pixiv: Cannot get image size

        if self.module_name == "input":
            return False
        elif other.module_name == "input":
            return True
        elif self.module_name == "pixiv":
            return True
        elif other.module_name == "pixiv":
            return False

        if self.img_size > other.img_size:
            return True
        elif self.img_size <= other.img_size:
            return False

        raise NotComparableException

    @abc.abstractmethod
    def change_id(self, item_id):
        pass

    @abc.abstractmethod
    def clear(self):
        self.width = 0
        self.height = 0
        self.img_size = 0

    def is_empty(self):
        return self.width == 0 and self.height == 0 and self.img_size == 0

    @staticmethod
    def identify_image_extension(url):
        t = urlparse(url)
        extension = "." + t.path.split(".")[-1]
        return extension

    @abc.abstractmethod
    def get_post_info(self):
        # Expected Return : the dict of the module
        return NotImplemented

    @abc.abstractmethod
    def download_original_image(self):
        # Expected Return : the file path of the temp image
        return NotImplemented

    @abc.abstractmethod
    def get_dict(self):
        # Expected Return : A dict that record all detail of variable
        return NotImplemented
