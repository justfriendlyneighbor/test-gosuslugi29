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
SectionElement = 'section[class~="b-basic-list"]'
SectionName = 'h3[class~="b-basic-list-title"]'
ElementService = "data-serviceid"
ElementTarget = "data-targetid"
Element = 'a[class~="service-procedure-title"]'
ElementName = 'span[class~="service-procedure-target-link"]'
Regex = r"\d+@egServiceTarget"
