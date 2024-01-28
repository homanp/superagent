import requests


def get_first_non_null(*args):
    """
    Returns the first non-null argument
    """
    for arg in args:
        if arg is not None:
            return arg
    return None  # Return None


def remove_key_if_present(dictionary, key):
    """
    Removes a key from a dictionary if it exists
    """
    if key in dictionary:
        del dictionary[key]


def compare_dicts(dict1, dict2):
    """
    Returns a dictionary of the changed fields between two dictionaries

    dict1: The first dictionary to compare
    dict2: The second dictionary to compare
    """
    changed_fields = {}

    # Check for changed values in common keys
    for key in set(dict1.keys()).intersection(dict2.keys()):
        if dict1[key] != dict2[key]:
            changed_fields[key] = dict2[key]

    # Check for keys that are only in dict1
    for key in set(dict1.keys()) - set(dict2.keys()):
        changed_fields[key] = None

    # Check for keys that are only in dict2
    for key in set(dict2.keys()) - set(dict1.keys()):
        changed_fields[key] = dict2[key]

    return changed_fields


def rename_and_remove_key(dictionary, old_key, new_key):
    """
    Renames a key in a dictionary and removes the old key if it exists

    dictionary: The dictionary to rename the key in
    old_key: The old key to rename
    new_key: The new key to rename to
    """
    if old_key in dictionary:
        dictionary[new_key] = dictionary[old_key]
        del dictionary[old_key]


def parse_mimetype(mimetype):
    if not mimetype:
        return None

    parts = mimetype.split(";")
    primary_type = parts[0].strip()
    return {"content_type": primary_type, "parameters": parts[1:]}


def get_mimetype_from_url(url):
    try:
        response = requests.head(url)
        mimetype = response.headers.get("Content-Type")
        parsed_mimetype = parse_mimetype(mimetype)
        return parsed_mimetype["content_type"] if parsed_mimetype else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


MIME_TYPE_TO_EXTENSION = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PPTX",
    "application/vnd.google-apps.document": "GOOGLE_DOC",
    "text/markdown": "MARKDOWN",
    "text/html": "WEBPAGE",
    "text/plain": "TXT",
}
