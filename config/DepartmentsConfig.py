import urllib.parse, json

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
RegionalMunicipalOrgs = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "orgstructureajaxutil.getRegionalMunicipalOrgs"}],
    },
    "data": json.dumps(
        {"method": "orgstructureajaxutil.getRegionalMunicipalOrgs", "params": [], "id": 4}
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
        "path": ["pgu", "department" ,"list.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}

Element = 'li[class~="departments-list-child-item"][data-objid*="@egOrganization"]'
Attribute = "data-objid"
Regex = r"\d+@egOrganization"