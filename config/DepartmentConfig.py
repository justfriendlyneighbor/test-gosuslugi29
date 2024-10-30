import utils.utils as utils

PageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "department", "info.htm"],
        "query": [],
    },
    "headers": utils.Headers,
    "ssl": False,
}

Element = 'div[class~="g-tile"][data-pgu-service*="@egService"]'
ElementName = 'span[class="js-word"]'
Attribute = "data-pgu-service"
Regex = r"\d+@egService"
LoadMoreElement = 'a[class*="btn"][data-behavior*="getMoreTiles"]'
