def pytest_configure(config):
    config.categories = {}
    config.departments = {}
    config.services = {}
    config.servicetargets = {}
    #test_categories.py
    config.categoriespages = []
    #test_category.py
    config.categoryservicepages = []
    config.categorypages = []
    #test_departments.py
    config.departmentsservicepages = []
    config.departmentspages = []
    #test_department.py
    config.departmentservicepages = []
    config.departmentpages = []
    #test_service.py
    config.servicepages = {}
    #test_target.py
    config.targetservicepages = []
    config.targetauthpages = []
    config.targetpages = []
    config.servicetargetsretry = {}
    config.targetpagesretry = []


def pytest_collection_modifyitems(items):
    indexafter=[items.index(item) for item in items if 'test_departments' in item.module.__name__][-1]
    moveindexes=[items.index(item) for item in items if 'test_department' == item.module.__name__]
    [items.insert(indexafter,items.pop(moveindexes[0])) for _ in range(len(moveindexes))]