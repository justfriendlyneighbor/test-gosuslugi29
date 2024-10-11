Headers = {}
PageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "services", "info.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}
CategoryElement = 'section[class~="b-basic-list"]'
CategoryName = 'h3[class~="b-basic-list-title"]'
Element = 'a[class~="service-procedure-title"]'
Regex = r"\d+@egServiceTarget"
