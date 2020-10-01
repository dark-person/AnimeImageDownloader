def replace_multi_character(char_string, text):
    for c in char_string:
        if c in text:
            text = text.replace(c, "_")
    return text


def replace_reserved_character(text):
    return replace_multi_character("/\\?%*:|\"<>.,;= ", text)
