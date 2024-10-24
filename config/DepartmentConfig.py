import urllib.parse, json

Department = ""
f_id = 0
CSRF = "Fetch"
Headers = {"content-type": "text/plain", "X-CSRF-Token": CSRF}
AjaxUrl = {
    "protocol": "https",
    "host": "gosuslugi29.ru",
    "path": ["util", "ajaxRpc.sx"],
}
ListMethods = {
    "method": "GET",
    "url": {
        **AjaxUrl,
        "query": [
            {
                "key": "v",
                "value": urllib.parse.quote(
                    '{"id":1, method:"system.listMethods", "params":[]}'
                ),
            }
        ],
    },
    "headers": Headers,
    "ssl": False,
}
TokenEnabledUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.isEnabled"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.isEnabled", "params": [], "id": 2}
    ),
    "headers": Headers,
    "ssl": False,
}
RestTokenUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.getRestToken"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.getRestToken", "params": [], "id": 3}
    ),
    "headers": Headers,
    "ssl": False,
}
PubBlockUrl = {
    "method": "POST",
    "url": {**AjaxUrl, "query": [{"key": "_", "value": "pubblock.renderZone"}]},
    "data": json.dumps(
        {
            "method": "pubblock.renderZone",
            "params": [
                "pgu/department/services/showmore",
                "center",
                {
                    "javaClass": "java.util.HashMap",
                    "map": {
                        "f": f_id,
                        "department": Department,
                        "g": "department",
                        "id": Department,
                    },
                },
            ],
            "id": 4,
        }
    ),
    "headers": Headers,
    "ssl": False,
}
DepartmentServiceMethods = [ListMethods, TokenEnabledUrl, RestTokenUrl]
PageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "department" ,"info.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}

Element = 'div[class~="g-tile"][data-pgu-service*="@egService"]'
Regex = r"\d+@egService"
LoadMoreElement = 'a[class*="btn"][data-behavior*="getMoreTiles"]'