import logging
from datetime import datetime
from pathlib import Path

from CombinedSource import CombinedSource
from DanbooruModule import DanbooruModule
from InputImageModule import InputImageModule
from PixivModule import PixivModule
from SankakuModule import SankakuModule
from GelbooruModule import GelbooruModule
from exception import *
from container import *
downloader2_logger = logging.getLogger("main.downloader")


class Downloader2(object):
    # Usage : get_new_downloader -> download -> terminate
    def __init__(self,
                 combined_source: CombinedSource,
                 input_image,
                 input_image_module: InputImageModule,
                 pixiv_module: PixivModule,
                 danbooru_module: DanbooruModule,
                 sankaku_module: SankakuModule,
                 gelbooru_module: GelbooruModule):
        downloader2_logger.info("%-20s [Init] ->> Downloader Initialize..", "[Downloader2]")

        # Module Set up
        self.pixiv_module = pixiv_module
        self.danbooru_module = danbooru_module
        self.sankaku_module = sankaku_module
        self.input_image_module = input_image_module
        self.gelbooru_module = gelbooru_module

        self.input_image_module.set_image(input_image)
        downloader2_logger.info("%-20s [Init] Input Resolution : %sx%s (%s)", "[Downloader2]",
                                str(self.input_image_module.width),
                                str(self.input_image_module.height), self.input_image_module.img_size)

        self.combined_source = combined_source
        if combined_source.is_empty():
            raise EmptyCombinedSourceInputException

        self.danbooru_id = combined_source.danbooru_id
        self.pixiv_id = combined_source.pixiv_id
        self.sankaku_id = combined_source.sankaku_id
        self.gelbooru_id = combined_source.gelbooru_id

        # TODO: yandere module
        self.yandere_id = combined_source.yandere_id

        self.twitter_author = combined_source.twitter_author
        self.twitter_id = combined_source.twitter_id

        self.character_tag = []
        self.copyright_tag = []

        # Pixiv Module Change Id
        if self.pixiv_id:
            try:
                self.pixiv_module.change_id(self.pixiv_id)
            except PixivModuleException:
                self.pixiv_module.clear()
                downloader2_logger.warning("%-20s [Init] Pixiv Module Broken, Module Cleared.", "[Downloader2]")
            downloader2_logger.debug("%-20s [Init] Pixiv : %s", "[Downloader2]", self.pixiv_module.get_dict())

        # Danbooru Module Change Id
        if self.danbooru_id:
            try:
                self.danbooru_module.change_id(self.danbooru_id)
            except DanbooruModuleException:
                self.danbooru_module.clear()
                downloader2_logger.warning("%-20s [Init] Danbooru Module Broken, Module Cleared.", "[Downloader2]")
            downloader2_logger.debug("%-20s [Init] Danbooru : %s", "[Downloader2]", self.danbooru_module.get_dict())

        # Sankaku Module Change Id
        if self.sankaku_id:
            try:
                self.sankaku_module.change_id(self.sankaku_id)
            except SankakuModuleException:
                self.sankaku_module.clear()
                downloader2_logger.warning("%-20s [Init] Sankaku Module Broken, Module Cleared.", "[Downloader2]")
            downloader2_logger.debug("%-20s [Init] Sankaku : %s", "[Downloader2]", self.sankaku_module.get_dict())

        # Gelbooru Module Change Id
        if self.gelbooru_id:
            try:
                self.gelbooru_module.change_id(self.gelbooru_id)
            except GelbooruModuleException:
                self.gelbooru_module.clear()
                downloader2_logger.warning("%-20s [Init] Gelbooru Module Broken, Module Cleared.", "[Downloader2]")
            downloader2_logger.debug("%-20s [Init] Gelbooru : %s", "[Downloader2]", self.gelbooru_module.get_dict())

        self.set_tags()
        self.priority = self.get_priority()
        downloader2_logger.info("%-20s [Init] ->> Downloader Initialized.", "[Downloader2]")

    def is_twitter_only(self):
        return self.combined_source.is_twitter_only()

    def is_pixiv_only(self):
        return self.combined_source.is_pixiv_only()

    def get_directory_and_filename(self, module=""):
        # Filename not include extension
        if self.character_tag and self.copyright_tag:
            directory = Path("output/" + " ".join(self.copyright_tag) + "/" + " ".join(self.character_tag))
            directory.mkdir(parents=True, exist_ok=True)
        else:
            directory = Path("output/unknown")
            directory.mkdir(parents=True, exist_ok=True)

        filename = ""

        downloader2_logger.debug("%-20s [Get Directory and Filename] Decision 1 : %s", "[Downloader2]",
                                 self.pixiv_id and not self.is_twitter_only())
        downloader2_logger.debug("%-20s [Get Directory and Filename] Decision 2 : %s", "[Downloader2]",
                                 self.combined_source.is_twitter_only())
        downloader2_logger.debug("%-20s [Get Directory and Filename] Decision 3 : %s", "[Downloader2]",
                                 self.pixiv_module.is_empty() and self.danbooru_module.is_empty()
                                 and self.sankaku_module.is_empty() and self.pixiv_id)

        if self.pixiv_id and not self.is_twitter_only():
            time_string = datetime.today().strftime('%Y%m%d_%H%M%S')
            filename = "illust_" + str(self.pixiv_id) + "_" + time_string
        if self.combined_source.is_twitter_only():
            filename = "twitter_" + self.twitter_author + "_" + self.twitter_id

        if self.pixiv_module.is_empty() and self.danbooru_module.is_empty() \
                and self.sankaku_module.is_empty() and self.gelbooru_module.is_empty():
            filename += "_lost"

        if all(module < self.input_image_module and not module.is_empty() for module in
               (self.pixiv_module, self.sankaku_module, self.danbooru_module, self.gelbooru_module)):
            filename += "_high"

        if module != "pixiv":
            filename += "_" + module

        return str(directory), filename

    def get_priority(self):
        module_list = [self.input_image_module, self.pixiv_module, self.danbooru_module, self.sankaku_module,
                       self.gelbooru_module]
        downloader2_logger.info(
            "%-20s [Get Priority] Input : {%sx%s}, Pixiv : {%sx%s}, Danbooru: {%sx%s}, Sankaku: {%sx%s}, Gelbooru: {%sx%s}",
            "[Downloader2]", self.input_image_module.width, self.input_image_module.height,
            self.pixiv_module.width, self.pixiv_module.height, self.danbooru_module.width, self.danbooru_module.height,
            self.sankaku_module.width, self.sankaku_module.height, self.gelbooru_module.width,
            self.gelbooru_module.height)
        module_list.sort(reverse=True)
        filtered_list = list(filter(lambda module: not module.is_empty(), module_list))
        priority_list = list(map(lambda module: module.module_name, filtered_list))

        return priority_list

    def set_tags(self):
        if self.danbooru_id:
            self.character_tag.extend(self.danbooru_module.character_tag)
            self.copyright_tag.extend(self.danbooru_module.copyright_tag)
        if self.sankaku_id:
            self.character_tag.extend(self.sankaku_module.character_tag)
            self.copyright_tag.extend(self.sankaku_module.copyright_tag)

        self.character_tag = list(dict.fromkeys(self.character_tag))
        self.copyright_tag = list(dict.fromkeys(self.copyright_tag))

        self.character_tag = list(map(lambda item: replace_reserved_character(item), self.character_tag))
        self.copyright_tag = list(map(lambda item: replace_reserved_character(item), self.copyright_tag))

        downloader2_logger.info("%-20s [Set Tags] Character : %s", "[Downloader2]", self.character_tag)
        downloader2_logger.info("%-20s [Set Tags] Copyright : %s", "[Downloader2]", self.copyright_tag)

    def download_decision(self, module_name: str):
        directory, filename = self.get_directory_and_filename(module_name)
        downloader2_logger.info("%-20s [Download Decision] Module : %s, Path : %s/%s", "[Downloader2]", module_name,
                                directory, filename)

        if module_name == "pixiv":
            self.pixiv_module.download(directory=directory, filename=filename)
            return True
        if module_name == "danbooru":
            self.danbooru_module.download(directory=directory, filename=filename)
            return True
        if module_name == "sankaku":
            self.sankaku_module.download(directory=directory, filename=filename)
            return True
        if module_name == "input":
            self.input_image_module.download(directory=directory, filename=filename)
            return True
        if module_name == "gelbooru":
            self.gelbooru_module.download(directory=directory, filename=filename)
            return True

    def download(self):
        for i in range(0, len(self.priority)):
            try:
                result = self.download_decision(self.priority[i])
                if result:
                    downloader2_logger.info("%-20s [Download] Download Completed.", "[Downloader2]")
                    return True
            except PixivModuleException:
                downloader2_logger.error("%-20s [Download] Pixiv Failed. Try Remaining : %s", "[Downloader2]",
                                         self.priority[(i + 1):])
            except DanbooruModuleException:
                downloader2_logger.error("%-20s [Download] Danbooru Failed. Try Remaining : %s ", "[Downloader2]",
                                         self.priority[i + 1:])
            except SankakuModuleException:
                downloader2_logger.error("%-20s [Download] Sankaku Failed. Try Remaining : %s", "[Downloader2]",
                                         self.priority[i + 1:])
            except GelbooruModuleException:
                downloader2_logger.error("%-20s [Download] Gelbooru Failed. Try Remaining : %s", "[Downloader2]",
                                         self.priority[i + 1:])
        return False

    def terminate(self):
        self.pixiv_module.clear()
        self.sankaku_module.clear()
        self.input_image_module.clear()
        self.danbooru_module.clear()
        self.gelbooru_module.clear()
        downloader2_logger.info("%-20s [Terminate] All Module in Downloader Clear.", "[Downloader2]")


class Downloader2Manager(object):
    def __init__(self, pixiv_username, pixiv_password, bookmark_option=False):
        self.username = pixiv_username
        self.password = pixiv_password
        self.bookmark_option = bookmark_option

        self.pixiv_module = PixivModule(pixiv_username, pixiv_password, bookmark_option=bookmark_option)
        self.danbooru_module = DanbooruModule()
        self.sankaku_module = SankakuModule()
        self.gelbooru_module = GelbooruModule()
        self.input_image_module = InputImageModule()

    def get_new_downloader(self, combined_source: CombinedSource, input_image) -> Downloader2:
        downloader = Downloader2(combined_source, input_image,
                                 self.input_image_module, self.pixiv_module,
                                 self.danbooru_module, self.sankaku_module, self.gelbooru_module)
        return downloader
