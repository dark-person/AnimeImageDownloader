import shutil
import sys
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
from pixivapi import Client as PixivClient
from pixivapi import Size
from pixivapi import errors as pixiv_api_errors

from CombinedSource import CombinedSource
from container import replace_reserved_character


class Downloader:
    def __init__(self, combined_source: CombinedSource, input_image, pixiv_client):
        print("->> Downloader Initialize..")

        self.input = input_image
        img = Image.open(input_image)
        self.input_width, self.input_height = img.size
        print("Input Resolution : ", self.input_width, "x", self.input_height)

        self.combined_source = combined_source
        if combined_source.is_empty():
            print("Empty Exception")
            raise Exception("No supported source link in container.")

        self.danbooru_id = combined_source.danbooru_id
        self.danbooru_image_url = ""
        self.danbooru_image_width, self.danbooru_image_height = 0, 0

        self.pixiv_client = pixiv_client
        self.pixiv_id = combined_source.pixiv_id
        self.pixiv_width, self.pixiv_height = 0, 0
        self.pixiv_illustration = None

        self.twitter_author = combined_source.twitter_author
        self.twitter_id = combined_source.twitter_id

        self.gelbooru_image_url = ""
        self.gelbooru_id = combined_source.gelbooru_id
        self.gelbooru_image_width, self.gelbooru_image_height = 0, 0

        self.yandere_id = combined_source.yandere_id
        self.yandere_image_url = ""
        self.yandere_image_width, self.yandere_image_height = 0, 0

        self.sankaku_id = combined_source.sankaku_id
        self.sankaku_image_url = ""
        self.sankaku_image_width, self.sankaku_image_height = 0, 0

        self.character_tag = ""
        self.copyright_tag = ""

        if self.danbooru_id:
            result = self.get_danbooru_info()
            print("Retrieve Danbooru info : ", result)

        if self.pixiv_id:
            result = self.get_pixiv_info()
            print("Retrieve Pixiv info : ", result)

        print("->> Downloader Initialized.")

    def is_twitter_only(self):
        return self.combined_source.is_twitter_only()

    def get_filename_without_extension(self):
        if self.pixiv_id:
            time_string = datetime.today().strftime('%Y%m%d_%H%M%S')
            filename = "illust_" + str(self.pixiv_id) + "_" + time_string
            return filename
        if self.combined_source.is_twitter_only():
            filename = "twitter_" + self.twitter_author + "_" + self.twitter_id
            return filename
        if self.danbooru_image_url:
            filename = self.danbooru_image_url.split("/")[-1]
            return filename
        return "Error"

    def get_larger_source(self):
        # input > pixiv and danbooru
        # pixiv > danbooru and input
        # danbooru > input and pixiv

        if self.compare_resolution(self.pixiv_width, self.pixiv_height, self.danbooru_image_width,
                                   self.danbooru_image_height) \
                and self.compare_resolution(self.pixiv_width, self.pixiv_height, self.input_width, self.input_height):
            return "pixiv"
        elif self.compare_resolution(self.danbooru_image_width, self.danbooru_image_height, self.input_width,
                                     self.input_height) and \
                self.compare_resolution(self.danbooru_image_width, self.danbooru_image_height, self.pixiv_width,
                                        self.pixiv_height):
            return "danbooru"
        elif self.compare_resolution(self.input_width, self.input_height, self.pixiv_width, self.pixiv_height) and \
                self.compare_resolution(self.input_width, self.input_height, self.danbooru_image_width,
                                        self.danbooru_image_height):
            return "input"
        else:
            return "error"

    @staticmethod
    def compare_resolution(image1_width, image1_height, image2_width, image2_height):
        # Return true if image1 >= image2
        return image1_width >= image2_width and image1_height >= image2_height

    def get_danbooru_info(self):
        # function  get_danbooru_info : get the character and copyright tag
        # input     None
        # output    flag  : imply the get successful or not
        #
        # set value :   character_tag, copyright_tag : the character name and copyright
        #               danbooru_image_url : the large image of backup site danbooru
        if not self.danbooru_id:
            print("[Downloader][get danbooru info] Id Missing, End.")
            return False

        response = requests.get("https://danbooru.donmai.us/posts/" + str(self.danbooru_id) + ".json")

        if response.status_code != 200:
            print("[Downloader][get danbooru info] response failed. End.")
            return False

        danbooru_json = response.json()
        self.danbooru_image_url = danbooru_json['large_file_url'] if 'large_file_url' in danbooru_json else ""
        self.danbooru_image_width = danbooru_json['image_width'] if 'image_width' in danbooru_json else 0
        self.danbooru_image_height = danbooru_json['image_height'] if 'image_height' in danbooru_json else 0
        print("[Downloader][get danbooru info] Danbooru Resolution : ", self.danbooru_image_width, "x",
              self.danbooru_image_height)

        self.character_tag = replace_reserved_character(str(danbooru_json['tag_string_character']))
        self.copyright_tag = replace_reserved_character(str(danbooru_json['tag_string_copyright']))

        return True

    def get_pixiv_info(self):
        if not self.pixiv_id:
            return False

        try:
            self.pixiv_illustration = self.pixiv_client.fetch_illustration(int(self.pixiv_id))
        except pixiv_api_errors.BadApiResponse:
            print(sys.exc_info()[0])
            print("[Downloader][get pixiv info] The illustration is not exist.")
            return False

        if not self.pixiv_illustration.title and not self.pixiv_illustration.user.name and \
                not self.pixiv_illustration.tags:
            print("[Downloader][get pixiv info] The illustration is removed.")
            return False

        # Get info from pixiv...
        self.pixiv_width, self.pixiv_height = self.pixiv_illustration.width, self.pixiv_illustration.height
        print("[Downloader][get pixiv info] Pixiv Resolution : ", self.pixiv_width, "x", self.pixiv_height)
        return True

    def download(self):
        larger = self.get_larger_source()
        print("[Downloader][download] larger source : ", larger)

        if self.pixiv_id and larger == "pixiv":
            print("[Downloader][download] Download - Pixiv first priority")
            result = self.download_pixiv_image()
            if not result:
                print("[Downloader][download] Pixiv download failed. Loading image from backup..")
                backup_result = self.download_danbooru_image()
                if backup_result:
                    print("[Downloader][download] Danbooru download success.")
                    return True
                else:
                    print("[Downloader][download] Danbooru download failed. Copy Image start.")
                    self.copy_input_image(lost_flag=True)
                    return False
            else:
                print("[Downloader][download] Pixiv download success.")
                return True
        elif self.pixiv_id and larger == "danbooru":
            print("[Downloader][download] Download - Danbooru first priority")
            result = self.download_danbooru_image()
            if not result:
                print("[Downloader][download] Danbooru download failed. Loading image from pixiv..")
                pixiv_result = self.download_pixiv_image()
                if pixiv_result:
                    print("[Downloader][download] Pixiv Download success.")
                    return True
                else:
                    print("[Downloader][download] Pixiv Download Failed. Copy Image start.")
                    self.copy_input_image(lost_flag=True)
                    return False
            else:
                print("[Downloader][download] Danbooru download success.")
                return True
        elif self.pixiv_id and larger == "input":
            print("[Downloader][download] Download - Input first priority")
            self.copy_input_image(high_flag=True)
            return True

        if self.is_twitter_only() and larger == "danbooru":
            print("[Downloader][download] Download - Twitter only.")
            print("[Downloader][download] Start getting in danbooru...")
            result = self.download_danbooru_image()
            if not result:
                print("[Downloader][download] Danbooru download failed. Copy Image start.")
                self.copy_input_image(lost_flag=True)
                return False
            else:
                print("[Downloader][download] Download Completed.")
                return True
        elif self.is_twitter_only() and larger == "input":
            print("[Downloader][download] Download - input first priority")
            self.copy_input_image(high_flag=True)
            return True

        return False

    def copy_input_image(self, high_flag=False, lost_flag=False):
        print("[Downloader][Copy input image] Start copy input image..")
        print("[Downloader][Copy input image] High Flag :", high_flag, ", Lost Flag :", lost_flag)
        if self.character_tag and self.copyright_tag:
            directory = Path("output/" + self.copyright_tag + "/" + self.character_tag)
            directory.mkdir(parents=True, exist_ok=True)
        elif (not self.character_tag or not self.copyright_tag) and lost_flag:
            directory = Path("output/Lost")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            directory = Path("output/unknown")
            directory.mkdir(parents=True, exist_ok=True)

        shutil.copy2(self.input, directory)
        print("[Downloader][Copy input image] Copy input image finished.")

        print("[Downloader][Copy input image] Start rename the image...")
        new_file = directory / self.input.split('/')[-1]
        filename = self.get_filename_without_extension()
        filename += "_high" if high_flag else ""
        filename += "_lost" if lost_flag else ""
        filename += new_file.suffix
        new_file.rename(directory / filename)
        print("[Downloader][Copy input image] Image rename finished. Filename = ", directory / filename)

    def download_danbooru_image(self):
        print("[Downloader][download danbooru image] Start.")

        if not self.danbooru_image_url:
            print("[Downloader][download danbooru image] image lost in danbooru, End.")
            return False

        image_name = self.danbooru_image_url.split('/')[-1]

        # download the image
        print("[Downloader][download danbooru image] downloading base image[", self.danbooru_image_url, "]..")
        image_response = requests.get(self.danbooru_image_url)
        file = open("output/" + image_name, "wb")
        file.write(image_response.content)
        file.close()
        print("[Downloader][download danbooru image] image downloaded.")

        # rename and rearrange the file
        filename = self.get_filename_without_extension()

        item = Path("output/" + image_name)
        if self.character_tag and self.copyright_tag:
            folder = Path("output/" + self.copyright_tag + "/" + self.character_tag)
            folder.mkdir(parents=True, exist_ok=True)
            new_filename = "output/" + self.copyright_tag + "/" + self.character_tag + "/" + filename + \
                           "_booru" + item.suffix
            print("[Downloader][download danbooru image] New filename = ", new_filename)
            item.rename(new_filename)
        else:
            folder = Path("output/unknown")
            folder.mkdir(parents=True, exist_ok=True)
            new_filename = "output/unknown/" + filename + "_booru" + item.suffix
            print("[Downloader][download danbooru image] New filename = ", new_filename)
            item.rename(new_filename)
        print("[Downloader][download danbooru image] Image rename and transfer to suitable folder")

        print("[Downloader][download danbooru image] End.")
        return True

    def download_pixiv_image(self):
        print("[Downloader][download pixiv image] Start")

        if not self.pixiv_id:
            print("[Downloader][download pixiv image] Pixiv Source Lost, End.")
            return False
        elif not self.pixiv_illustration:
            print("[Downloader][download pixiv image] Pixiv Illustration Error, End.")
            return False

        # generate filename
        filename = self.get_filename_without_extension()

        # set target directory
        if not self.character_tag or not self.copyright_tag:
            directory = Path("output") / "unknown"
        else:
            directory = Path("output") / self.copyright_tag / self.character_tag

        print("[Downloader][download pixiv image] Directory : '", directory, "'")

        # download the illustration
        self.pixiv_illustration.download(
            directory=directory,
            size=Size.ORIGINAL,
            filename=filename
        )
        print("[Downloader][download pixiv image] illust ", self.pixiv_id, " download complete, saved in ", directory)

        # handle multiple page illustration
        if self.pixiv_illustration.page_count > 1:
            print("[Downloader][download pixiv image] More than one page : ", filename)

            target_directory = directory / filename
            print("[Downloader][download pixiv image] target directory : ", target_directory)

            file_glob = list(target_directory.glob("*.*"))
            for item in file_glob:
                temp_name = filename + "_" + item.stem.split("_")[1] + item.suffix
                temp_file = directory / temp_name
                print("[Downloader][download pixiv image] New filename", temp_file)
                item.rename(temp_file)

            target_directory.rmdir()
            print("[Downloader][download pixiv image] File rearrange completed")

        # bookmark illustration
        self.pixiv_client.add_bookmark(int(self.pixiv_id))
        print("[Downloader][download pixiv image] illust ", self.pixiv_id, " bookmarked")
        print("[Downloader][download pixiv image] End")
        return True


class DownloadManager:
    def __init__(self, pixiv_username, pixiv_password):
        self.pixiv_username = pixiv_username
        self.pixiv_password = pixiv_password

        self.pixiv_client = PixivClient()
        self.pixiv_client.login(pixiv_username, pixiv_password)
        self.pixiv_authenticate_key = self.pixiv_client.refresh_token

    def get_new_downloader(self, combined_source: CombinedSource, input_image) -> Downloader:
        downloader = Downloader(combined_source, input_image, self.pixiv_client)
        return downloader
