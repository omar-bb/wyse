import os
import sys
import requests
from tqdm import tqdm
import concurrent.futures

import extra


BASE_URL = "https://addons-ecs.forgesvc.net/api/v2/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
}

class VersionError(Exception):
    """Raised when the addon version is invalid"""
    def __init__(self, version): 
        r = requests.get(f"{BASE_URL}minecraft/version", headers=HEADERS).json()
        for x in r:
            if version == x["versionString"]:
                self.version = version
                break

        if not hasattr(self, "version"):
            self.message = "is an invalid version."
            self.version = version
        else:
            self.message = "is an incompatible version."

        super().__init__(self.message)

    def __str__(self):
        return f"{self.version} {self.message}"

class Addon:

    ADDON_URL = BASE_URL + "addon/" 

    def __init__(self, addon_id, addon_version):
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            urls = [f"{self.ADDON_URL}{addon_id}", f"{self.ADDON_URL}{addon_id}/files"]
            th = [executor.submit(extra.get_url, url) for url in urls]

            for x in th:
                while x.running():
                    print("Sending The Request...", end="\r")

            self.payload = th[0].result().json()
            self.dl_payload = th[1].result().json()

        self.id = addon_id
        self.name = self.payload["name"]
        self.summary = self.payload["summary"]
        self.version = addon_version

        for x in self.payload["gameVersionLatestFiles"]:
            if x["gameVersion"] == self.version:
                self.project_file_id = x["projectFileId"]
                break

        if not hasattr(self, "project_file_id"):
            raise VersionError(self.version)

        for y in self.dl_payload:
            if y["id"] == self.project_file_id:
                self.file_name = y["fileName"]
                self.file_length = y["fileLength"]
                self.file_dl_url = y["downloadUrl"]
                self.dependencies = list(
                    filter(lambda x: x["type"] > 2, y["dependencies"])
                )
                break

    def fetch_dependencies(self):
        for x in self.dependencies:
            dep = Addon(x["addonId"], self.version) 
            dep.fetch()

    def fetch(self):

        r = requests.get(self.file_dl_url, stream=True)

        dl_path = os.path.join(os.getcwd(), "mods", self.file_name)

        block_size = 1024
        progress_bar = tqdm(total=self.file_length,
                            unit='iB', unit_scale=True, desc=self.file_name)
                            
        with open(dl_path, 'wb') as f:
            for data in r.iter_content(block_size):
                f.write(data)
                progress_bar.update(len(data))

        progress_bar.close()

        self.fetch_dependencies()

    def __repr__(self):
        return f"Addon({self.id})"

    def __str__(self):
        return f"\033[92m{self.name}\033[0m/\n {self.summary}"


ADDON_ID = 225643
ad = Addon(ADDON_ID, "1.12.2") 
ad.fetch()
