import allure, pytest, bs4, re, asyncio, aiohttp, pytest_aiohttp
import config.ServiceConfig as Service
from utils.utils import *
from allure_commons.types import Severity

async def get_service_pages(session,categories):
    servicepages={}
    for category, services in categories.items():
        thisservicepages=[]
        n = 100
        urls = [[{key: ( value if key != "url" else { k: v if k != "query" else [{"key": "id", "value": service}] for k, v in value.items()}) for key, value in Service.PageUrl.items()},False] for service in services]
        while not all([url[1] for url in urls]):
            for i in range(0, len(urls), n):
                tasks = [(fetch_url(session, url[0],url)) for url in urls[i : i + n]]
                responses = asyncio.gather(*tasks)
                await responses
                for searchresponse in responses.result():
                    try:
                        assert searchresponse[1] == 200
                        soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                        serviceid = [
                            servicetarget.attrs["data-serviceid"]
                            for servicetarget in soup.select(Service.Element)
                        ]
                        assert len(set(serviceid)) == 1
                        thisservicepages.append({'status':searchresponse[1],'soup':soup,'url':searchresponse[2],'service':searchresponse[3]})
                    except AssertionError:
                        continue
                    searchresponse[3][1]=True
            urls = list(filter(lambda x: not x[1], urls))
        servicepages[category]=thisservicepages
    return servicepages

@pytest.fixture(scope='session')
async def service_pages(request):
    pages={}
    async with aiohttp.ClientSession() as session:
        pages = await get_service_pages(session,request.config.categories)
    return pages

@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Подуслуг по Услуге")
@allure.description("Этот тест проверяет доступность страниц услуг")
def test_service_pages(request,service_pages,allure_subtests):
    ok = 200
    for category,pages in service_pages.items():
        for page in pages:
            with allure_subtests.test(subtest_name=f'Проверить Запрос к странице {page["url"]}'):
                assert page['status']==ok, f'Запрос к поиску по странице категории {page["url"]} вернул код отличный от {ok}, а именно {page["status"]}' 
                if request.config.servicepages.get(category)==None:
                    request.config.servicepages[category]=[page]
                else:
                    request.config.servicepages[category].append(page)

def get_serviceitargetids(pages):
    categoryservices={}
    for category,servicepages in pages.items():
        categoryservices.update({category:{}})
        for servicepage in servicepages:
            soup=servicepage['soup']
            sections = [
                category for category in soup.select(Service.CategoryElement)
            ]
            sectarg={'sections':[]}
            for section in sections:
                sectionnames=[sectionname.text for sectionname in section.select(Service.CategoryName)]
                sectarg.update({sectionnames[0]:[{servicetarget.attrs["data-targetid"]: {}} for servicetarget in section.select(Service.Element)]})
                sectarg['sections'].append(sectionnames)
            categoryservices[category].update({servicepage['url']['query'][0]['value']:sectarg})
    return categoryservices

@pytest.fixture(scope='session')
def allserviceitargetids(request):
    return get_serviceitargetids(request.config.servicepages)

@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия групп Подуслуг по Услуге")
@allure.description("Этот тест проверяет наличие на страницах услуг групп подуслуг")
def test_service_section_names(allserviceitargetids,allure_subtests):
    for _,serviceids in allserviceitargetids.items():
        for serviceid,service in serviceids.items():
            with allure_subtests.test(subtest_name=f"Проверить услугу {serviceid}"):
                assert len(service['sections']) > 0 , f'Количество групп (электронные / неэлектронные) найденных на странице подуслуги {len(service["sections"])}'

@allure.severity(Severity.BLOCKER)
@allure.title("Тест групп Подуслуг по Услуге")
@allure.description("Этот тест проверяет группы подуслуг на стандартное представление")
def test_service_section_name(allserviceitargetids,allure_subtests):
    for _,serviceids in allserviceitargetids.items():
        for serviceid,service in serviceids.items():
            with allure_subtests.test(subtest_name=f"Проверить услугу {serviceid}"):
                assert (all([len(set(sectionname)) == 1 for sectionname in service['sections']]) ), f'У группы подуслуг (электронные / неэлектронные) обнаружено несколько названий, а именно {service["sections"]}'
                service.pop('sections', None)

@allure.severity(Severity.BLOCKER)
@allure.title("Тест Подуслуг по Услуге")
@allure.description("Этот тест проверяет подуслуги на стандартное представление")
def test_service_target(request,allserviceitargetids,allure_subtests):
    attribute = re.compile(Service.Regex)
    for categoryid,serviceids in allserviceitargetids.items():
        for serviceid,service in serviceids.items():
            for _,targets in service.items():
                for target in targets:
                    for targetname in target:
                        with allure_subtests.test(subtest_name=f"Проверить подуслугу {targetname}"):
                            assert attribute.match(targetname), f'Подуслуга {targetname} не соответствует стандартному представлению'
            request.config.categories[categoryid][serviceid] = service