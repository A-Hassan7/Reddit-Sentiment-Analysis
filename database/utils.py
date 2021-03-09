import string

def strip_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))
