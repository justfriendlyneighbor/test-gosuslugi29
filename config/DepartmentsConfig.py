import json, utils.utils as utils

RegionalMunicipalOrgs = {
    "method": "POST",
    "url": {
        **utils.AjaxUrl,
        "query": [
            {"key": "_", "value": "orgstructureajaxutil.getRegionalMunicipalOrgs"}
        ],
    },
    "data": json.dumps(
        {
            "method": "orgstructureajaxutil.getRegionalMunicipalOrgs",
            "params": [],
            "id": 4,
        }
    ),
    "headers": utils.Headers,
    "ssl": False,
}

Element = 'li[class~="departments-list-child-item"][data-objid*="@egOrganization"]'
Attribute = "data-objid"
Regex = r"\d+@egOrganization"
