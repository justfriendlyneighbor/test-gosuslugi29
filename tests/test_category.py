import allure, pytest, bs4, re, json, asyncio, aiohttp, copy, functools, pytest_aiohttp, functools, itertools
import config.CategoryConfig as Category
from utils.utils import *
from allure_commons.types import Severity


async def get_category_service_pages(session):
    ajaxpages=[]
    for ConfigUrl in Category.CategoryServiceMethods:
        UrlPart = ConfigUrl.pop("url")
        ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
        ConfigUrl["url"] = UrlPart
        ajaxresponsetext = await ajaxresponse.text()
        ajaxpages.append({'status':ajaxresponse.status,'text':ajaxresponsetext,'url':buildurl(**UrlPart)})
    return ajaxpages

def update_category_services(pages):
    CSRFpattern = re.compile(r"\w{32}")
    for catalogpage in pages:
         if is_json(catalogpage['text']):
            jsonres = json.loads(catalogpage['text'])
            if "result" in jsonres and isinstance(jsonres["result"], str):
                if CSRFpattern.match(jsonres["result"]):
                    Category.Headers["X-CSRF-Token"] = jsonres["result"]

async def get_category_pages(session,categories):
    categorypages=[]
    for category, _ in categories.items():
        loadmore = True
        loadmoreelement = []
        f = 1
        with allure.step(f"Асинхронно сделать запросы к странице категории {category}"):
            while loadmore:
                copys = []
                for _ in range(7):
                    Category.PubBlockUrl["data"] = json.loads(Category.PubBlockUrl["data"])
                    Category.PubBlockUrl["data"]["params"][2]["map"] = {"f": f,"category": category,"g": "tiles","isTemplate": "24326@egClassification","id": category,}
                    Category.PubBlockUrl["data"] = json.dumps(Category.PubBlockUrl["data"])
                    copys.append(copy.deepcopy(Category.PubBlockUrl))
                    f += 12
                tasks = [(fetch_url(session, url)) for url in copys]
                responses = asyncio.gather(*tasks)
                await responses
                for searchresponse in responses.result():
                    try:
                        categorypages.append({'status':searchresponse[1],'text':searchresponse[0],'url':searchresponse[2],'category':category})
                        soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                        loadmoreelement.append(
                            len(soup.select(Category.LoadMoreElement)) != 0
                        )
                    except Exception as e:
                        print (e.message) 
                loadmore = all(loadmoreelement)
    return categorypages

@pytest.fixture(scope='session')
async def category_pages(request):
    pages={'ajax':[],'category':[]}
    async with aiohttp.ClientSession() as session:
        pages['ajax'] = await get_category_service_pages(session)
        request.config.categoryservicepages.extend(pages['ajax'])
        update_category_services(request.config.categoryservicepages)
        pages['category'] = await get_category_pages(session,request.config.categories)
    return pages

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Категорий")
@allure.description("Этот тест проверяет доступность страницы вспомогательных страниц для доступа к категориям")
def test_category_service_pages(request,category_pages,check):
    ok = 200
    for page in category_pages['ajax']:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert page['status']==ok, f'Запрос {page["url"]} для получения доступа к странице категории вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")

@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Категорий")
@allure.description("Этот тест проверяет получение токена для доступа к категориям")
def test_category_services(category_pages):
    assert Category.Headers["X-CSRF-Token"] != "Fetch", f'Не удалось получить CSRF-токен, список заголовков - {Category.Headers}'
    pytest.skip("Completed succesfully, skipping from report")

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Услуг по Категории")
@allure.description("Этот тест проверяет доступность страниц категорий")
def test_category_pages(request,category_pages,check):
    ok = 200
    for page in category_pages['category']:
        with check:
            with allure.step(f'Проверить Запрос к странице {page["url"]}'):
                assert page['status']==ok, f'Запрос к поиску по странице категории {page["url"]} вернул код отличный от {ok}, а именно {page["status"]}' 
                request.config.categorypages.append(page)
    pytest.skip("Completed succesfully, skipping from report")

def get_serviceids(pages):
    serviceids={}
    for categorypage in pages:
        soup = bs4.BeautifulSoup(categorypage['text'], "lxml")
        if serviceids.get(categorypage['category'])==None:
            serviceids[categorypage['category']]=[service.attrs["data-pgu-service"] for service in soup.select(Category.Element)]
        else:
            serviceids[categorypage['category']].extend([service.attrs["data-pgu-service"] for service in soup.select(Category.Element)])
    unique=functools.reduce(set.union, (itertools.starmap(set.symmetric_difference, itertools.combinations(map(set, serviceids.values()), 2))))
    [[unique.remove(service) if service in unique else services.remove(service) for service in services[:]] for services in serviceids.values()]
    return serviceids

@pytest.fixture
def allserviceids(request):
    return get_serviceids(request.config.categorypages)

@allure.severity(Severity.BLOCKER)
@allure.title("Тест Услуг по Категории")
@allure.description("Этот тест проверяет объекты услуг на стандартное представление")
def test_service(request,allserviceids,check):
    attribute = re.compile(Category.Regex)
    for categoryid,serviceids in allserviceids.items():
        for serviceid in serviceids:
            with check:
                with allure.step(f"Проверить услугу {serviceid}"):
                    assert attribute.match(serviceid), f'Услуга {serviceid} не соответствует стандартному представлению'
        request.config.categories[categoryid] = dict.fromkeys(serviceids, {})
    pytest.skip("Completed succesfully, skipping from report")