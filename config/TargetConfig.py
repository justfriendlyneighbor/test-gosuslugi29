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
        "path": ["pgu", "services", "info", "targets", "details-page.htm"],
        "query": [],
    },
    "headers": Headers,
    "ssl": False,
}

buttonGet = {
    "elem": 'a[class*="btn"][data-behavior*="createOrderModal"],a[class*="btn"][data-behavior*="goto"],a[class*="btn"][data-behavior*="preCreateOrderModal"]',
    "name": "Кнопка Получить/Заполнить заявление",
    "value": "text",
}
# buttonAppointment = {'elem':'a[class*="btn"][data-behavior*="preCreateOrderModal"]','name':'Записаться','value':'text'}
regulationsLink = {
    "elem": 'div[class*="modal-actions"]>div[class*="modal-block--reglament"]>div[class*="modal-block-wrapper"]>a[class*="reglament-link"][data-behavior*="download"]',
    "name": "Административный регламент",
    "value": "href",
}
organization = {
    "elem": 'a[class*="service-organ-link"][data-behavior*="modal"]',
    "name": "Организация предоставляющая услугу",
    "value": "text",
}
template = {
    "elem": '//p[@class="attr-title"][text()="Скачать:"]/following-sibling::div[@class="attr-value"]/p/a[@data-behavior="download"]/span[text()="Шаблон для заполнения"]/ancestor::a',
    "name": "Шаблон",
    "value": "href",
}
example = {
    "elem": '//p[@class="attr-title"][text()="Скачать:"]/following-sibling::div[@class="attr-value"]/p/a[@data-behavior="download"]/span[text()="Пример заполнения"]/ancestor::a',
    "name": "Пример",
    "value": "href",
}

deadlineComplete = {
    "elem": 'p:-soup-contains("Срок выполнения услуги")[class*="attr-title"]+div[class*="attr-value"]',
    "name": "Срок выполнения услуги",
    "value": "text",
}
cost = {
    "elem": "//*[@id='dataGrpcost']/ancestor::h3/following-sibling::div/p | //*[@id='dataGrpcost']/ancestor::h3/following-sibling::div/div/div[@data-grpname='__payment']/p[@class='attr-value']",
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

OnDetailsPageConfigElements = {
    "css": [buttonGet, regulationsLink, organization,deadlineComplete, refusalsElements, resultsElements],
    "xpath": [template, example, cost, categoriesElements],
}

OffDetailsPageConfigElements = {
    "css": [regulationsLink, organization,deadlineComplete, refusalsElements, resultsElements],
    "xpath": [template, example, cost, categoriesElements],
}
