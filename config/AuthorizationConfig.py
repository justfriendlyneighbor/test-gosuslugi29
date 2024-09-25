import urllib.parse, json

AjaxUrl = {
    "protocol": "https",
    "host": "gosuslugi29.ru",
    "path": ["util", "ajaxRpc.sx"],
}
token = ""
authdata = {
    "citizenCategory": "FL",
    "authType": "PWD",
    "snils": "66666666668",
    "email": "rostov@systematic.ru",
    "phone": "1234567890",
    "firstName": urllib.parse.quote("���������"),
    "secondName": urllib.parse.quote("��������"),
    "lastName": urllib.parse.quote("������"),
    "birthDate": "1954-07-12",
    "birthPlace": urllib.parse.quote("����� ����� ���������"),
    "ogrn": "1111111111111",
    "orgName": urllib.parse.quote("������� ����"),
    "position": urllib.parse.quote("������� �����������"),
    "chief": "true",
    "orgINN": "1111111111",
    "personINN": "410199999936",
    "esiaId": "esiaId",
    "trusted": "Y",
    "assuranceLevel": "AL20",
    "_t": "",
}
CSRF = "Fetch"
Headers = {"content-type": "text/plain", "X-CSRF-Token": CSRF}
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
TokenUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.getToken"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.getToken", "params": [], "id": 3}
    ),
    "headers": Headers,
    "ssl": False,
}
AuthUrl = {
    "method": "POST",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["auth", "testesia.htm"],
        "query": [{"key": "&_t", "value": ""}],
    },
    "data": authdata,
    "headers": [],
    "ssl": False,
}
Element = 'p:-soup-contains("�� ������� ��������������")'
Regex = "������ ��������� ��������"
