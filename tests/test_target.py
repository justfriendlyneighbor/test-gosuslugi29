import allure, pytest, bs4, lxml, json, asyncio, aiohttp, copy, urllib, pandas, pytest_aiohttp
import config.TargetConfig as Target, config.AuthorizationConfig as Authorization, config.DepartmentConfig as Department, config.ServiceConfig as Service, utils.utils as utils
from allure_commons.types import Severity

async def get_target_authorization_pages(session):
    with aiohttp.MultipartWriter("form-data") as mp:
        for key, value in Authorization.authdata.items():
            part = mp.append(value)
            part.set_content_disposition("form-data", name=key)
        UrlPart = Authorization.AuthUrl.pop("url")
        with allure.step(
            f"Асинхронно сделать запрос к странице авторизации{utils.buildurl(**UrlPart)}"
        ):
            authresponse = await session.request(
                **Authorization.AuthUrl, url=utils.buildurl(**UrlPart)
            )
            authresponsetext = await authresponse.text()
            Authorization.AuthUrl["url"] = UrlPart
        return [
            {
                "status": authresponse.status,
                "text": authresponsetext,
                "url": utils.buildurl(**UrlPart),
            }
        ]


async def get_target_pages(session, targets):
    targetpages = []
    urls = []
    n = 50
    for target in targets:
        [
            (
                config["url"]["query"].clear(),
                config["url"]["query"].extend(
                    [
                        {"key": "id", "value": target},
                    ]
                ),
            )
            for config in [
                Target.DetailsPageUrl,
            ]
        ]
        urls.extend(
            [
                (
                    copy.deepcopy(Target.DetailsPageUrl),
                    target,
                ),
            ]
        )
    for i in range(0, len(urls), n):
        with allure.step(
            f"Асинхронно сделать {n} запросов с {i} по {i+n} к страницам подуслуг"
        ):
            tasks = [(utils.fetch_url(session, url[0], url[1])) for url in urls[i : i + n]]
            responses = asyncio.gather(*tasks)
            await responses
            for searchresponse in responses.result():
                targetpages.append(
                    {
                        "text": searchresponse[0],
                        "status": searchresponse[1],
                        "url": searchresponse[2],
                        "service": searchresponse[3],
                    }
                )
    return targetpages

async def call_pages(targets):
    pages = {"ajax": [], "auth": [], "target": []}
    async with aiohttp.ClientSession() as session:
        pages["ajax"] = await utils.get_service_pages(session, utils.AuthorizationServiceMethods)
        utils.update_services(pages["ajax"],utils.Headers)
        Authorization.authdata["_t"] = utils.Headers["X-CSRF-Token"]
        Authorization.AuthUrl["url"]["query"][0]["value"] = utils.Headers["X-CSRF-Token"]
        pages["auth"] = await get_target_authorization_pages(session)
        pages["target"] = await get_target_pages(session, targets)
    return pages

@pytest.fixture(scope="session")
async def target_pages(request):
    Authorization.authdata["citizenCategory"]=request.param
    pages = await call_pages(request.config.servicetargets if request.param==Authorization.FLCategory else request.config.servicetargetsretry)
    get_targetdetails(pages["target"],request.config.servicetargets,request.config.servicetargetsretry)
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title(
    "Тест доступности вспомогательных страниц для Авторизации для теста Параметров по Подуслуге"
)
@allure.description(
    "Этот тест проверяет доступность вспомогательных страниц для доступа к авторизации"
)
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_service_pages(target_pages, check):
    ok = 200
    for page in target_pages["ajax"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос {page["url"]} для получения доступа к странице авторизации вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет получение токена для доступа к авторизации")
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_services(target_pages):
    with allure.step(f"Проверить CSRF-токен {utils.Headers['X-CSRF-Token']}"):
        assert (
            utils.Headers["X-CSRF-Token"] != "Fetch"
        ), f"Не удалось получить CSRF-токен, список заголовков - {utils.Headers}"
    utils.Headers["X-CSRF-Token"] = "Fetch"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности страницы Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет доступность страницы авторизации")
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_authorization_pages(target_pages, check):
    ok = 200
    for page in target_pages["auth"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос {page["url"]} для авторизации вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия Авторизации для теста Параметров по Подуслуге")
@allure.description(
    "Этот тест проверяет наличие записей об авторизации на странице авторизации"
)
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_authorization(target_pages, check):
    for page in target_pages["auth"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                soup = bs4.BeautifulSoup(page["text"], "lxml")
                testauth = soup.select(Authorization.Element)
                assert (
                    len(set(testauth)) == 1
                ), f"Количество записей об успешной авторизации найденных на странице не 1, а {len(set(testauth))}"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Авторизации для теста Параметров по Подуслуге")
@allure.description(
    "Этот тест проверяет успешность авторизации в качестве заданного пользователя"
)
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_authorization_correct(target_pages, check):
    for page in target_pages["auth"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                soup = bs4.BeautifulSoup(page["text"], "lxml")
                testauth = soup.select(Authorization.Element)
                assert Authorization.Regex in urllib.parse.unquote(
                    testauth[0].text
                ), f"Текст записи об успешной авторизации не соответствует стандратному тексту для заданного пользователя, а именно {testauth[0].text}"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Параметров по Подуслуге")
@allure.description("Этот тест проверяет доступность страниц подуслуг")
@pytest.mark.parametrize("target_pages", Authorization.citizenCategory, ids= Authorization.citizenCategory, indirect=True)
def test_target_pages(target_pages, check):
    ok = 200
    for page in target_pages["target"]:
        with check:
            with allure.step(f'Проверить Запрос к странице {utils.buildurl(**page["url"])}'):
                assert (
                    page["status"] == ok
                ), f'Запрос к странице подуслуги {page["url"]} вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


def get_targetdetails(pages, targets, retry):
    for page in pages:
        with allure.step(
            f"Выделить параметры на странице услуги {utils.buildurl(**page['url'])}"
        ):
            target = page["service"]
            asserts = []
            details = {}
            soup = bs4.BeautifulSoup(page["text"], "lxml")
            tree = lxml.etree.HTML(page["text"])
            if targets[target]["type"] == "Электронные услуги":
                elements = Target.OnDetailsPageConfigElements
            elif targets[target]["type"] == "Неэлектронные услуги":
                elements = Target.OffDetailsPageConfigElements
            else:
                elements = []
            if len(elements) > 0:
                for csselement in elements["css"]:
                    details[csselement["name"]] = [
                        (
                            cssel.text
                            if csselement["value"] == "text"
                            else cssel.attrs[csselement["value"]]
                        )
                        for cssel in soup.select(csselement["elem"])
                    ]
                    asserts.append(len(details[csselement["name"]]) != 0)
                for xpathelement in elements["xpath"]:
                    details[xpathelement["name"]] = [
                        (
                            xpathel.text
                            if xpathelement["value"] == "text"
                            else xpathel.attrib[xpathelement["value"]]
                        )
                        for xpathel in tree.xpath(xpathelement["elem"])
                    ]
                    asserts.append(len(details[xpathelement["name"]]) != 0)
            details["assert"] = (
                details["assert"] and all(asserts)
                if "assert" in details
                else all(asserts)
            )
            if (
                not details["assert"]
                and details.get("Кнопка Получить/Заполнить заявление") != None
                and len(details["Кнопка Получить/Заполнить заявление"]) == 0
            ):
                retry.update({target: targets[target]})
            elif target in retry:
                retry.pop(target)
            targets[target].update(details)
    return targets

def count_department_services(departmentsconfig):
    departments = {}
    lnk,totl,totel,partel,notel,perc="Ссылка","Всего услуг","Полностью электронных, %успешных","Частично электронных, %успешных","Неэлектронных, %успешных","% успешных"
    for department, values in departmentsconfig.items():
        name = values["name"]
        deplink = copy.deepcopy(Department.PageUrl["url"])
        deplink["query"] = [{"key": "id", "value": department}]
        departments[name] = {lnk: utils.buildurl(**deplink),totl: len(values)-1,totel: [0,0],partel: [0,0],notel: [0,0]}
        for service, servicevalue in values.items():
            if service != "name":
                total,fail,electr=len(servicevalue) - 1,0,0
                for target, targetvalue in servicevalue.items():
                    if target != "name":
                        if targetvalue["assert"] == False:
                            fail+=1
                        if targetvalue["type"] == "Электронные услуги":
                            electr+=1
                if total==0:
                    pass
                elif electr==0:
                    departments[name][notel][0]+=1
                    if fail==0:
                        departments[name][notel][1]+=1
                elif total==electr:
                    departments[name][totel][0]+=1
                    if fail==0:
                        departments[name][totel][1]+=1
                else:
                    departments[name][partel][0]+=1
                    if fail==0:
                        departments[name][partel][1]+=1
        departments[name][perc] = (
            f"{((departments[name][totel][1]+departments[name][partel][1]+departments[name][notel][1])/departments[name][totl]):.2%}"
            if departments[name][totl] != 0
            else f"{1:.2%}"
        )
        for elname in [totel,partel,notel]:
            departments[name][elname]=f'{departments[name][elname][0]}, '+(f'{(departments[name][elname][1]/departments[name][elname][0]):.2%}'if departments[name][elname][0] != 0 else f"{1:.2%}")
    sorted_departments = dict(
        sorted(
            departments.items(),
            key=lambda item: item[1][totl],
            reverse=True,
        )
    )
    return pandas.DataFrame(sorted_departments).T

@allure.severity(Severity.NORMAL)
@allure.title("Тест Параметров по Подуслуге")
@allure.description(
    "Этот тест проверяет наличие на страницах подуслуг проверяемых параметров"
)
def test_target_details(request, allure_subtests):
    pd = count_department_services(request.config.departments)
    for service, targets in request.config.services.items():
        urlcopy = copy.deepcopy(Service.PageUrl["url"])
        urlcopy["query"] = [{"key": "id", "value": service}]
        name='name'
        with allure_subtests.test(
            subtest_name=f"Проверка услуги {utils.buildurl(**urlcopy)} ({targets[name]}) {'успешна' if all([details['assert'] for target,details in targets.items() if target!=name]) else f'неуспешна, не соответствуют пункты: { {target:[detailname for detailname,detailcontent in details.items() if detailcontent==[]] for target,details in targets.items() if target!=name} }'}"
        ):
            with allure.step(
                f"Проверка услуги {utils.buildurl(**urlcopy)} ({targets[name]}) {'успешна' if all([details['assert'] for target,details in targets.items() if target!=name]) else f'неуспешна, не соответствуют пункты: { {target:[detailname for detailname,detailcontent in details.items() if detailcontent==[]] for target,details in targets.items() if target!=name} }'}"
            ):
                assert all([details['assert'] for target,details in targets.items() if target!=name]), f'На странице {utils.buildurl(**urlcopy)} ({targets[name]}) не соответствуют пункты: { {target:[detailname for detailname,detailcontent in details.items() if detailcontent==[]] for target,details in targets.items() if target!=name} }'
    with allure.step(f"Прикрепить файл результатов всех проверок"):
        with open("results/data_category.json", "w") as f:
            allure.attach(
                json.dumps(request.config.categories).encode(),
                name="All details collection per category",
                attachment_type=allure.attachment_type.JSON,
            )
            json.dump(request.config.categories, f)
    with allure.step(f"Прикрепить файл результатов проверок по органам"):
        with open("results/data_department.json", "w") as f:
            allure.attach(
                json.dumps(request.config.departments).encode(),
                name="All details collection per department",
                attachment_type=allure.attachment_type.JSON,
            )
            json.dump(request.config.departments, f)
    with allure.step(f"Прикрепить таблицу результатов проверок по органам"):
        pd.to_csv("results/data_department.csv"),
        allure.attach(
            pd.to_csv(),
            name="All details collection per department",
            attachment_type=allure.attachment_type.CSV,
        )