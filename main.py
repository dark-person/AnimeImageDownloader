import asyncio
import logging
import os
import time
from configparser import ConfigParser

from pysaucenao import SauceNao, errors

from Downloader import *
from ParsedSource import ParsedSource
import sys
import shutil
import exception

# Can Change this later
OPTION_MOVE_FILE = True

# =================================
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('activity.log', encoding='utf-8')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)-8s : %(message)s")
formatter2 = logging.Formatter("%(asctime)s - %(levelname)-8s : %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter2)

logger.addHandler(ch)
logger.addHandler(fh)

logger.propagate = False

# Config Part===================================

config = ConfigParser()
config_filename = "private_config.ini" if Path("private_config.ini").exists() else "config.ini"
config.read(config_filename)

SAUCENAO_API_KEY = config.get('Saucenao API', "KEY")
USERNAME = config.get('Pixiv Info', "USERNAME")
PASSWORD = config.get('Pixiv Info', "PASSWORD")
BOOKMARK = config.getboolean('Pixiv Info', 'BOOKMARK')

if not USERNAME and not PASSWORD:
    logger.error("%-20s Pixiv Account and Password must be provided.", "[Main]")
    exit(1)

if not BOOKMARK:
    BOOKMARK = False


def move_file(original_filepath, new_directory):
    if not OPTION_MOVE_FILE:
        return
    else:
        file = Path(original_filepath)
        file.rename(new_directory + file.name)
        logger.info("%-20s Original File {%s} Moved to %s/ folder", "[Main]", original_filepath, new_directory)
        return


async def search_and_download(original_path, download_manager: Downloader2Manager):
    logger.info("%-20s Start.. image path = %s", "[Main]", original_path)

    transparency = has_transparency_by_path(original_path)
    logger.info("%-20s Image Transparency checking : %s", "[Main]", transparency)

    if transparency:
        temp_path = Path(original_path)
        Path("transparent").mkdir(exist_ok=True)
        filename = temp_path.stem + "_white" + temp_path.suffix

        logger.info("%-20s Start creating temp image..", "[Main]")

        image = Image.open(original_path)
        temp_img = Image.new("RGBA", image.size, "WHITE")
        temp_img.paste(image, (0, 0), image)
        temp_img.convert("RGB").save("transparent/" + filename, "JPEG")

        path = "transparent/" + filename

        logger.info("%-20s Temp image created. Save in : %s", "[Main]", path)
    else:
        path = original_path

    sauce = SauceNao(
        results_limit=10,
        api_key=SAUCENAO_API_KEY,
        min_similarity=75.0)
    results = await sauce.from_file(path)
    logger.info("%-20s short limit : %s, long limit : %s", "[Main]", str(results.short_remaining),
                str(results.long_remaining))

    if len(results.results) <= 0:
        logger.error("No sauce is found.")
        move_file(original_path, "NotFound")
        return

    combined_source = CombinedSource()
    for source in results.results:
        logger.debug("%-20s Source : %s", "[Main]", source.__repr__())
        logger.debug("%-20s -> Contain %s", "[Main]", str(source.data))

        ps = ParsedSource(source)
        logger.debug("%-20s Parsed Source : %s ", "[Main]", ps.__repr__())

        combined_source.append(ps)

    logger.info("%-20s Start analysis...", "[Main]")
    combined_source.combine()
    combined_source.print_info()
    logger.info("%-20s Analysis Completed.", "[Main]")

    try:
        downloader = download_manager.get_new_downloader(combined_source, original_path)
        result = downloader.download()
        downloader.terminate()

        if result:
            move_file(original_path, "Searched")
        else:
            move_file(original_path, "NotFound")

        if path != original_path:
            shutil.rmtree("transparent", ignore_errors=True)
            logger.info("%-20s Temp Directory Removed.", "[Main]")

        logger.info("%-20s Image Search and Download Complete.", "[Main]")

    except EmptyCombinedSourceInputException:
        logger.exception("%-20s Combined Source Empty. Move file to NotFound/")
        move_file(original_path, "NotFound")


async def main():
    try:
        Path("Searched").mkdir(parents=True, exist_ok=True)
        Path("NotFound").mkdir(parents=True, exist_ok=True)
        Path("output").mkdir(parents=True, exist_ok=True)
        Path("Exception_Log").mkdir(parents=True, exist_ok=True)

        filelist = get_input_filelist()
        download_manager = Downloader2Manager(USERNAME, PASSWORD, bookmark_option=BOOKMARK)
        for i in range(0, len(filelist)):
            item = filelist[i]
            logger.info("%-20s =======================", '[Main]')
            logger.info("%-20s item = {%s}", '[Main]', item)
            try:
                await search_and_download(item, download_manager)
                logger.info("%-20s Item Completed : %s / %s", '[Main]', i + 1, len(filelist))

                if i + 1 < len(filelist):
                    logger.info("%-20s Start sleeping 15s..", "[Main]")
                    time.sleep(15)
                    logger.info("%-20s Sleep complete.", "[Main]")
            except errors.ShortLimitReachedException:
                logger.error("%-20s Short Limited used. Sleep.", "[Main]")
                time.sleep(30)
                await search_and_download(item, download_manager)
            except errors.DailyLimitReachedException:
                logger.error("%-20s 24hr limited used. Terminated", "[Main]")
                input("24hr limited used. Terminated.")
                sys.exit(1)
            except:
                logger.exception("%-20s Unknown Exception. Packing..", "[Main]")

                # Exception Information Packing
                Path("Exception Package").mkdir(exist_ok=True, parents=True)
                shutil.copy("activity.log", "Exception Package")
                shutil.copy(item, "Exception Package")

                time_string = datetime.today().strftime('%Y%m%d%H%M%S')
                package_name = "Exception_Log/" + "Exception_" + time_string
                shutil.make_archive(package_name, 'zip', "Exception Package")
                logger.info("%-20s Package completed.", "[Main]")

                shutil.rmtree("Exception Package", ignore_errors=True)
                move_file(item, "NotFound")

    except:
        import traceback
        traceback.print_exc()
        logger.exception("Unknown Exception")
        input("Program Crashed. Enter to Exit")

    logger.info("%-20s All image processed. Program will terminated.", "[Main]")


def get_input_filelist():
    suffix_list = ["jpg", "jpeg", "png"]

    image_list = []
    for file in os.listdir('input'):
        if file.split('.')[-1].lower() in suffix_list:
            image_list.append('input/' + file)
    image_list.sort()

    logger.info("%-20s Image List : %s", "[Main]", str(image_list))

    return image_list


# testing purpose, comment
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    r = loop.run_until_complete(main())

# Known Issue
# 1. Image not found in both pixiv and danbooru
#       -> other website api?
# 2. If a illustration contain multiple character in multiple page, it will download all and category it wrongly
# =======
# 3. Lost image mark as high resolution
