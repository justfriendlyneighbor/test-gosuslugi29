Headers = {"Host": "gosuslugi29.ru"}
MainPageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "services", "info", "targets.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}
DetailsPageUrl = {
    "method": "GET",
    "url": {
        "protocol": "https",
        "host": "gosuslugi29.ru",
        "path": ["pgu", "services", "info", "targets", "details.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}

serviceType = {
    "elem": 'div:-soup-contains-own("Выберите тип получения услуги")>div>span>label',
    "electronic": "Электронная услуга",
    "nonelectronic": "Личное посещение ведомства",
    "name": "Тип получения",
    "value": "text",
}

buttonGet = {
    "elem": 'a[class*="btn"][data-behavior*="createOrderModal"],a[class*="btn"][data-behavior*="goto"]',
    "name": "Кнопка Получить/Заполнить заявление",
    "value": "text",
}
# buttonAppointment = {'elem':'a[class*="btn"][data-behavior*="preCreateOrderModal"]','name':'Записаться','value':'text'}
regulationsLink = {
    "elem": 'a[class*="reglament-link"][data-behavior*="download"]',
    "name": "Административный регламент",
    "value": "href",
}
organization = {
    "elem": 'a[class*="service-organ-link"][data-behavior*="modal"]',
    "name": "Организация предоставляющая услугу",
    "value": "text",
}
template = {
    "elem": '//span[text()="Шаблон"]/ancestor::a',
    "name": "Шаблон",
    "value": "href",
}
example = {
    "elem": '//span[text()="Пример"]/ancestor::a',
    "name": "Пример",
    "value": "href",
}

OnMainPageElements = {
    "css": [buttonGet, regulationsLink, organization],
    "xpath": [template, example],
}
OffMainPageElements = {
    "css": [regulationsLink, organization],
    "xpath": [template, example],
}

deadlineComplete = {
    "elem": 'p:-soup-contains("Срок выполнения услуги")[class*="attr-title"]+div[class*="attr-value"]',
    "name": "Срок выполнения услуги",
    "value": "text",
}
cost = {
    "elem": "//*[@id='dataGrpcost']/ancestor::h3/following-sibling::div",
    "name": "Стоимость и порядок оплаты",
    "value": "text",
}
refusalsElements = {
    "elem": 'p:-soup-contains("Основание для приостановления/отказа")[class*="attr-title"]+ul[class*="b-basic-list-item-body"]>li',
    "name": "Основание для приостановления/отказа",
    "value": "text",
}
categoriesElements = {
    "elem": "//*[@id='dataGrpcategory']/ancestor::h3/following-sibling::div[1]/div/div[@class='attr-title']",
    "name": "Категории получателей",
    "value": "text",
}
resultsElements = {
    "elem": 'p:-soup-contains("Результат оказания услуги:")[class*="attr-title"]+div[class*="attr-value"]>ul>li',
    "name": "Результат оказания услуги",
    "value": "text",
}

DetailsPageConfigElements = {
    "css": [deadlineComplete, refusalsElements, resultsElements],
    "xpath": [cost, categoriesElements],
}
