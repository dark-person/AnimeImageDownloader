import asyncio
import logging
import os
import time
from configparser import ConfigParser

from pysaucenao import SauceNao, errors

from Downloader import *
from ParsedSource import ParsedSource
import sys

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

if not USERNAME and not PASSWORD:
    logger.error("%-20s Pixiv Account and Password must be provided.", "[Main]")
    exit(1)


async def search_and_download(path, download_manager: Downloader2Manager):
    logger.info("%-20s Start.. image path = %s", "[Main]", path)
    sauce = SauceNao(
        results_limit=10,
        api_key=SAUCENAO_API_KEY,
        min_similarity=75.0)
    results = await sauce.from_file(path)
    logger.info("%-20s short limit : %s, long limit : %s", "[Main]", str(results.short_remaining),
                str(results.long_remaining))

    if len(results.results) <= 0:
        logger.error("No sauce is found.")
        file_path = Path(path)
        file_path.rename("NotFound/" + file_path.name)
        logger.info("Original File Moved to NotFound/ folder.")
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

    downloader = download_manager.get_new_downloader(combined_source, path)
    result = downloader.download()
    downloader.terminate()

    file_path = Path(path)
    if result:
        file_path.rename("Searched/" + file_path.name)
        logger.info("%-20s image {%s} move to Searched/", "[Main]", path)
    else:
        file_path.rename("Problem/" + file_path.name)
        logger.info("%-20s image {%s} move to Problem/", "[Main]", path)

    logger.info("%-20s Image Search and Download Complete.", "[Main]")


async def main():
	try:
		Path("Searched").mkdir(parents=True, exist_ok=True)
		Path("Problem").mkdir(parents=True, exist_ok=True)
		Path("NotFound").mkdir(parents=True, exist_ok=True)
		Path("output").mkdir(parents=True, exist_ok=True)

		filelist = get_input_filelist()
		download_manager = Downloader2Manager(USERNAME, PASSWORD)
		for i in range(0, len(filelist)):
			item = filelist[i]
			logger.info("%-20s =======================", '[Main]')
			logger.info("%-20s item = {%s}", '[Main]', item)
			try:
				# TODO : await search_and_download(item, download_manager)
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
				raw_input("24hr limited used. Terminated.")
				exit(1)
	except Exception as e:
		import traceback
		traceback.print_exc()
		input("Program Crashed. Enter to Exit")


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
    logger.info("%-20s All image processed. Program will terminated.", "[Main]")

# Known Issue
# 1. Image not found in both pixiv and danbooru
#       -> other website api?
# 2. If a illustration contain multiple character in multiple page, it will download all and category it wrongly
# =======
# 3. Lost image mark as high resolution
