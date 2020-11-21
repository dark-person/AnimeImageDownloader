# AnimeImageDownloader

AnimeImageDownloader is a Python Script for downloading anime image.

It will use saucenao api to find the image source, and try to download better version of that image.

## Library Used

- pygelbooru
- pysaucenao
- PixivPy

## Usage for config.ini
There are a file called config.ini, the value will be used in the script, **input required value before run the script**

```
[Pixiv Info]
USERNAME : (Required, Enter your pixiv username)
PASSWORD : (Required, Enter your pixiv password)
BOOKMARK : (Default False, it will decided bookmark the illustration if it published in pixiv)

[Saucenao API]
KEY : (Default Empty, Purpose is to increase the search limit, you can run script with empty value in this field)
```

## Usage

1. Create an folder called "input".
2. Put the image you need to search inside this folder.
3. Run the script, that will run for a while.
4. The output file will be save in the path: [anime name]/[character name]/[filename]
5. If OPTION_MOVE_FILE is true, the input image will move to different folder according to the download result (Searched/ NotFound)

## Contributing
Due to personal reason, this script **will not be updated** for a long time.

## Known Problem
This script is not well tested with larger amount of image, and may cause many problem.

However, if any exception is catched, the script will archive necessary information for developed to a zip file, which contain:
```
Exception_[timestring]
|_ activity.log (the log of the script)
|_ [the image cause exception]
```
Developer can use these information for debugging.


## License
[MIT](https://choosealicense.com/licenses/mit/)
