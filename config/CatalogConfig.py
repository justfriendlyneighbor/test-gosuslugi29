Headers = {}
PageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "categories.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}
SearchUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["mo", "search.sx"],
        "query": [
            {"key": "designCode", "value": "pgu2"},
            {"key": "type", "value": "category"},
            {"key": "view", "value": "tree"},
            {"key": "limit", "value": "0"},
        ],
    },
    "headers": Headers,
    "ssl": False,
}
Element = 'div[class~="t-modal-layout-item"]'
Regex = "\d+@egClassification"
