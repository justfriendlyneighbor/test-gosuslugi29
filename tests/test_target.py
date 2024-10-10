import allure, pytest, bs4, lxml, re, json, asyncio, aiohttp, copy, urllib, pytest_aiohttp
import config.TargetConfig as Target, config.AuthorizationConfig as Authorization
from utils.utils import *
from allure_commons.types import Severity

async def get_target_service_pages(session):
    ajaxpages=[]
    for ConfigUrl in Authorization.AuthorizationServiceMethods:
        UrlPart = ConfigUrl.pop("url")
        ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
        ConfigUrl["url"] = UrlPart
        ajaxresponsetext = await ajaxresponse.text()
        ajaxpages.append({'status':ajaxresponse.status,'text':ajaxresponsetext,'url':buildurl(**UrlPart)})
    return ajaxpages

def update_target_services(pages):
    CSRFpattern = re.compile("\w{32}")
    for catalogpage in pages:
        if is_json(catalogpage['text']):
            jsonres = json.loads(catalogpage['text'])
            if "result" in jsonres and isinstance(jsonres["result"], str):
                if CSRFpattern.match(jsonres["result"]):
                    Authorization.Headers["X-CSRF-Token"] = jsonres["result"]
                    Authorization.authdata["_t"] = jsonres["result"]
                    Authorization.AuthUrl["url"]["query"][0]["value"] = jsonres["result"]

async def get_target_authorization_pages(session):
    with aiohttp.MultipartWriter("form-data") as mp:
        for key, value in Authorization.authdata.items():
            part = mp.append(value)
            part.set_content_disposition("form-data", name=key)
        UrlPart = Authorization.AuthUrl.pop("url")
        authresponse = await session.request(**Authorization.AuthUrl, url=buildurl(**UrlPart))
        authresponsetext = await authresponse.text()
        Authorization.AuthUrl["url"] = UrlPart
        return [{'status':authresponse.status,'text':authresponsetext,'url':buildurl(**UrlPart)}]

async def get_target_pages(session,categories):
    targetpages={}
    for category, services in categories.items():
        thistargetpages=[]
        urls = []
        n = 50
        for servicename,servicevariants in services.items():
            for servicevariant,servicetargets in servicevariants.items():
                for servicetarget in servicetargets:
                    [(config["url"]["query"].clear(),
                        config["url"]["query"].extend([{"key": "id","value": list(servicetarget.keys())[0],},{"key": "serviceId","value": servicename,},]),)
                        for config in [Target.DetailsPageUrl,]]
                    urls.extend([(copy.deepcopy(Target.DetailsPageUrl),(category,servicename,servicevariant,servicetarget),),])
        for i in range(0, len(urls), n):
            tasks = [
                (fetch_url(session, url[0], url[1])) for url in urls[i : i + n]
            ]
            responses = asyncio.gather(*tasks)
            await responses
            for searchresponse in responses.result():
                thistargetpages.append({'text':searchresponse[0],'status':searchresponse[1],'url':searchresponse[2],'service':searchresponse[3]})
        targetpages[category]=thistargetpages
    return targetpages

@pytest.fixture(scope='session')
async def target_pages(request):
    pages={'ajax':[],'auth':[],'target':[]}
    async with aiohttp.ClientSession() as session:
        pages['ajax'] = await get_target_service_pages(session)
        request.config.targetservicepages.extend(pages['ajax'])
        update_target_services(request.config.targetservicepages)
        pages['auth'] = await get_target_authorization_pages(session)
        request.config.targetauthpages.extend(pages['auth'])
        pages['target'] = await get_target_pages(session,request.config.categories)
    return pages

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет доступность вспомогательных страниц для доступа к авторизации")
def test_target_service_pages(request,target_pages,allure_subtests):
    ok = 200
    for page in target_pages['ajax']:
        with allure_subtests.test(subtest_name=f"Проверить Запрос к странице {page['url']}"):
            assert page['status']==ok, f'Запрос {page["url"]} для получения доступа к странице авторизации вернул код отличный от {ok}, а именно {page["status"]}' 

@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет получение токена для доступа к авторизации")
def test_target_services(target_pages):
    assert Authorization.Headers["X-CSRF-Token"] != "Fetch", f'Не удалось получить CSRF-токен, список заголовков - {Authorization.Headers}'

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности страницы Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет доступность страницы авторизации")
def test_target_authorization_pages(request,target_pages,allure_subtests):
    ok = 200
    for page in target_pages['auth']:
        with allure_subtests.test(subtest_name=f"Проверить Запрос к странице {page['url']}"):
            assert page['status']==ok, f'Запрос {page["url"]} для авторизации вернул код отличный от {ok}, а именно {page["status"]}' 

@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет наличие записей об авторизации на странице авторизации")
def test_target_authorization(request,target_pages,allure_subtests):
    for page in target_pages['auth']:
        with allure_subtests.test(subtest_name=f"Проверить Запрос к странице {page['url']}"):
            soup = bs4.BeautifulSoup(page['text'], "lxml")
            testauth = soup.select(Authorization.Element)
            assert len(set(testauth)) == 1, f'Количество записей об успешной авторизации найденных на странице не 1, а {len(set(testauth))}'

@allure.severity(Severity.BLOCKER)
@allure.title("Тест Авторизации для теста Параметров по Подуслуге")
@allure.description("Этот тест проверяет успешность авторизации в качестве заданного пользователя")
def test_target_authorization_correct(request,target_pages,allure_subtests):
    for page in target_pages['auth']:
        with allure_subtests.test(subtest_name=f"Проверить Запрос к странице {page['url']}"):
            soup = bs4.BeautifulSoup(page['text'], "lxml")
            testauth = soup.select(Authorization.Element)
            assert Authorization.Regex in urllib.parse.unquote(testauth[0].text), f'Текст записи об успешной авторизации не соответствует стандратному тексту для заданного пользователя, а именно {testauth[0].text}'

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Параметров по Подуслуге")
@allure.description("Этот тест проверяет доступность страниц подуслуг")
def test_target_pages(request,target_pages,allure_subtests):
    ok = 200
    for _,pages in target_pages['target'].items():
        for page in pages:
            with allure_subtests.test(subtest_name=f'Проверить Запрос к странице {page["url"]}'):
                assert page['status']==ok, f'Запрос к странице подуслуги {page["url"]} вернул код отличный от {ok}, а именно {page["status"]}' 
                request.config.targetpages.append(page)

def get_targetdetails(pages):
    categoryservicestargets={}
    for page in pages:
        category,service,variant,target=page['service']
        asserts = []
        details = {}
        if categoryservicestargets.get(category)==None:
            categoryservicestargets.update({category:{service:{variant:target}}})
        elif categoryservicestargets[category].get(service)==None:
            categoryservicestargets[category].update({service:{variant:target}})
        elif categoryservicestargets[category][service].get(variant)==None:
            categoryservicestargets[category][service].update({variant:target})
        elif categoryservicestargets[category][service][variant].get(list(target.keys())[0])==None:
            categoryservicestargets[category][service][variant].update(target)
        soup = bs4.BeautifulSoup(page['text'], "lxml")
        tree = lxml.etree.HTML(page['text'])
        if variant=='Электронные услуги':
            elements = Target.OnDetailsPageConfigElements
        elif variant=='Неэлектронные услуги':
            elements = Target.OffDetailsPageConfigElements
        else:
            elements = []
        if len(elements) > 0:
            for csselement in elements["css"]:
                details[csselement["name"]] = [(cssel.text if csselement["value"] == "text" else cssel.attrs[csselement["value"]]) for cssel in soup.select(csselement["elem"])]
                asserts.append(len(details[csselement["name"]]) != 0)
            for xpathelement in elements["xpath"]:
                details[xpathelement["name"]] = [(xpathel.text if xpathelement["value"] == "text" else xpathel.attrib[xpathelement["value"]]) for xpathel in tree.xpath(xpathelement["elem"])]
                asserts.append(len(details[xpathelement["name"]]) != 0)
        details["assert"] = (details["assert"] and all(asserts) if "assert" in details else all(asserts))
        categoryservicestargets[category][service][variant][list(target.keys())[0]]=details
    return categoryservicestargets

@pytest.fixture(scope='session')
def alltargetdetails(request):
    request.config.categories=get_targetdetails(request.config.targetpages)
    return request.config.categories

@allure.severity(Severity.NORMAL)
@allure.title("Тест Параметров по Подуслуге")
@allure.description("Этот тест проверяет наличие на страницах подуслуг проверяемых параметров")
def test_target_details(request,alltargetdetails,allure_subtests):
    [[cat,[[serviceid,[[servicevariant,[[target,details] for target,details in targets.items()]] for servicevariant,targets in servicevariants.items()]] for serviceid,servicevariants in serviceids.items()]] for cat,serviceids in alltargetdetails.items()]
    for categoryid,serviceids in alltargetdetails.items():
        for serviceid,servicevariants in serviceids.items():
            for servicevariant,targets in servicevariants.items():
                for target,details in targets.items():
                    with allure_subtests.test(subtest_name=f"Проверить подуслугу {target}"):
                        assert details['assert'], f'На странице {target} не соответствуют пункты: {*[detailname for detailname,detailcontent in details.items() if detailcontent==[]],}'
    with allure.step(f"Прикрепить файл результатов пройденных и непройденных проверок"):
        with open("results/data.json", "w") as f:
            allure.attach(json.dumps(request.config.categories).encode(),name='All details collection',attachment_type='application/json')
            json.dump(request.config.categories, f)