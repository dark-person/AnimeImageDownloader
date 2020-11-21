class AnimeImageDownloaderException(Exception):
    pass


# ============== Super Class Module Error ==============
class ModuleException(AnimeImageDownloaderException):
    pass


class WidthHeightNotMatchingException(ModuleException):
    pass


class NotComparableException(ModuleException):
    pass


# ============== Original Image Module Error ==============
class OriginalImageModuleException(ModuleException):
    pass


class MethodNotApplicableException(OriginalImageModuleException):
    pass


class InputImageEmptyException(OriginalImageModuleException):
    pass


# ============== Pixiv Module Error ==============

class PixivModuleException(ModuleException):
    pass


class PixivApiLoginException(PixivModuleException):
    pass


class PixivIllustrationLostException(PixivModuleException):
    pass


class PixivIdMissingException(PixivModuleException):
    pass


# ============== Sankaku Module Error ==============
class SankakuModuleException(ModuleException):
    pass


class SankakuEmptyOriginalURL(SankakuModuleException):
    pass


class SankakuRequestFailed(SankakuModuleException):
    pass


class SankakuTooManyDummyPicDownloaded(SankakuModuleException):
    pass


# ============== Danbooru Module Error ===============
class DanbooruModuleException(ModuleException):
    pass


class DanbooruRequestFailed(DanbooruModuleException):
    pass


class DanbooruEmptyOriginalURL(DanbooruModuleException):
    pass


class DanbooruEmptyPostId(DanbooruModuleException):
    pass


class DanbooruEmptyImageUrl(DanbooruModuleException):
    pass


# ============== Gelbooru Module Error ===============
class GelbooruModuleException(ModuleException):
    pass


class GelbooruEmptyPostId(GelbooruModuleException):
    pass


class GelbooruRequestFailed(GelbooruModuleException):
    pass


class GelbooruEmptyImageURL(GelbooruModuleException):
    pass


# ============== Combined Source Error ==============
class CombinedSourceException(AnimeImageDownloaderException):
    pass


# ============== Parsed Source Error ==============
class ParsedSourceException(AnimeImageDownloaderException):
    pass


# ============== Downloader Error ==============
class DownloaderException(AnimeImageDownloaderException):
    pass


class EmptyCombinedSourceInputException(DownloaderException):
    pass
