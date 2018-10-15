import os
import nltk


def download():
    '''
    Install required libraries.
    Note this library will install nltk dependencies into your
    user directory.
    '''

    print("Installing nltk packages into your user directories in " +
               "the following order of existence (first found):\n" +
               '\n'.join(nltk.data.path))

    extensions = [("/", "popular"),
                  ("corpora", "wordnet"),("corpora", "floresta"),
                  ("corpora", "machado"),("corpora", "mac_morpho"),
                  ("stemmers","rslp"),
                  ("tokenizers", "punkt")]

    missing = check_packages_exist(extensions)

    for ext_tuple in missing:
        nltk.download(ext_tuple[1])


def check_packages_exist(extensions):
    '''
    Finds missing nltk extensions.
    '''
    paths = nltk.data.path  # there are usually quite a few, so we check them all.
    missing = []
    for ext_tuple in extensions:
        ext_found = False
        print("Looking for " + ext_tuple[1])
        for path in paths:
            if os.path.exists(os.path.join(path, ext_tuple[0], ext_tuple[1])):
                ext_found = True
                print("Found " + ext_tuple[1])
                break
        if not ext_found:
            print("Missing " + ext_tuple[1])
            missing.append(ext_tuple)

    return missing

download()
