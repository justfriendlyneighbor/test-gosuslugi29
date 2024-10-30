import urllib.parse, json, utils.utils as utils

FLCategory = "FL"
ULCategory = "UL"
IPCategory = "IP"
citizenCategory=[FLCategory,ULCategory,IPCategory]
authdata = {
    "citizenCategory": FLCategory,
    "authType": "PWD",
    "snils": "66666666668",
    "email": "rostov@systematic.ru",
    "phone": "1234567890",
    "firstName": urllib.parse.quote("Александр"),
    "secondName": urllib.parse.quote("Игоревич"),
    "lastName": urllib.parse.quote("Ростов"),
    "birthDate": "1954-07-12",
    "birthPlace": urllib.parse.quote("Город герой Ленинград"),
    "ogrn": "1111111111111",
    "orgName": urllib.parse.quote("Типовой СМЭВ"),
    "position": urllib.parse.quote("Ведущий разработчик"),
    "chief": "true",
    "orgINN": "1111111111",
    "personINN": "410199999936",
    "esiaId": "esiaId",
    "trusted": "Y",
    "assuranceLevel": "AL20",
    "_t": "",
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
Element = 'p:-soup-contains("Вы успешно авторизовались")'
Regex = "Ростов Александр Игоревич"
