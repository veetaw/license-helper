import requests
import json
import os

from pathlib import Path
from datetime import date, datetime

from simple_term_menu import TerminalMenu
from sty import fg

session: requests.Session = requests.Session()
ALL_LICENSES_URL: str = "https://api.github.com/licenses"

CACHE_PATH: str = str(Path.home()) + os.sep + '.licenses_cache.json'


class LicenseSearchResult:
    def __init__(self, **kwargs):
        self.key: str = kwargs['key']
        self.name: str = kwargs['name']
        self.spdx_id: str = kwargs['spdx_id']
        self.node_id: str = kwargs['node_id']
        self.url: str = kwargs['url']


class License:
    def __init__(self, **kwargs):
        self.key = kwargs['key']
        self.name = kwargs['name']
        self.url = kwargs['url']
        self.description = kwargs['description']
        self.implementation = kwargs['implementation']
        self.permissions = kwargs['permissions']
        self.conditions = kwargs['conditions']
        self.limitations = kwargs['limitations']
        self.body = kwargs['body']


def get_all_licenses(ret = False) -> [LicenseSearchResult]:
    response: requests.Response = session.get(ALL_LICENSES_URL)
    
    if response.status_code != 200:
        print(f"Server did not respond correctly.\n"
                f"Actual server response code: {response.status_code}\n"
                f"\treason: {response.reason}")
        exit(-1)
    
    try:
        parsed_json = response.json()
    except Exception as e:
        print(f"An error occurred while parsing the response json.\n"
                f"Exception: {e}")
        exit(-1)

    cache_licenses(parsed_json)
    
    if ret:
        return list(map(lambda license_dict: LicenseSearchResult(**license_dict), parsed_json))


def get_license(license_search_result: LicenseSearchResult) -> License: 
    response: requests.Response = session.get(license_search_result.url)

    if response.status_code != 200:
        print(f"Server did not respond correctly.\n"
                f"Actual server response code: {response.status_code}\n"
                f"\treason: {response.reason}")
    
    try:
        parsed_json = response.json()
    except Exception as e:
        print(f"An error occurred while parsing the response json.\n"
                f"Exception: {e}")
        exit(-1)

    return License(**parsed_json)

def cache_licenses(raw_json):
    with open(CACHE_PATH, 'w') as f:
        json.dump(raw_json, f)


def load_from_cache() -> [LicenseSearchResult]:
    opened_json = None
    with open(CACHE_PATH, 'r') as f:
        opened_json = json.load(f)

    return list(map(lambda license_dict: LicenseSearchResult(**license_dict), opened_json))


def select_license_menu(licenses: [LicenseSearchResult]) -> int:
    menu = TerminalMenu(list(map(lambda license: license.name, licenses)))
    return menu.show()


def pplist(l: list) -> str:
    ret: str = ""
    for x in l:
        ret += f"\t{fg.magenta}>{fg.rs} {str(x)}\n"

    return ret


def pplinfo(license: License) -> None:
    print(f"{fg.red}NAME{fg.rs}: {license.name}\n"
            f"{fg.blue}{str(license.description)}{fg.rs}\n"
            f"{fg.red}IMPLEMENTATION: {fg.rs} {str(license.implementation)}\n\n"
            f"{fg.red}PERMISSIONS:\n" + pplist(license.permissions) +
            f"{fg.red}CONDITIONS:\n" + pplist(license.conditions) +
            f"{fg.red}LIMITATIONS:\n" + pplist(license.limitations))


def yesno_menu() -> int:
    menu = TerminalMenu(["yes", "no"])
    return menu.show()

if __name__ == '__main__':
    licenses = None
    __cache_path = Path(CACHE_PATH)
    if __cache_path.exists():
        cache_date = datetime.fromtimestamp(__cache_path.stat().st_mtime)
        today = datetime.now()
        delta = today - cache_date
        if delta.days >= 30:
            get_all_licenses()
    
    licenses = load_from_cache()

    # if argparse has not detected any specified license passed
    selected_license = select_license_menu(licenses)

    license = get_license(licenses[selected_license])
    pplinfo(license)
    
    print(f"{fg.red}Do you want to create a LICENSE file?{fg.rs}\n")
    ans = yesno_menu()
    
    if ans: #no
        exit(0)
    else:
        with open("LICENSE", 'w') as f:
            f.write(license.body)

        print(f"{fg.red}DONE.{fg.rs}")
        exit(0)
