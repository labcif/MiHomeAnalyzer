def insert_prefix_js():
    return """
    var motions = [
    """

def insert_object_js(item_date, item_path):
    
    return """
        [
            "{itemDate}",
            "{itemPath}",
        ],
    """.format(itemDate = item_date, itemPath = item_path)

def insert_suffix_js():
    return """
    ]
    """