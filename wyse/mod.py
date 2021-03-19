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
    """Raised when the game version is invalid or incompatible with the actual mod"""

    def __init__(self, version):

        MINECRAFT_VERSION_URL = BASE_URL + "minecraft/" + "version"

        r = requests.get(MINECRAFT_VERSION_URL, headers=HEADERS).json()

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


class Mod:

    def __init__(self, mod_id, game_version):

        MOD_INFO_URL = BASE_URL + "addon/" + str(mod_id)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            urls = [MOD_INFO_URL, f"{MOD_INFO_URL}/files"]
            th = [executor.submit(extra.get_url, url=url,
                                  headers=HEADERS) for url in urls]

            for x in th:
                animation = "|/-\\"
                c = 0
                while x.running():
                    extra.loading_animation(animation, "Collecting Mod", c)
                    c += 1

            print("\rCollecting Mod \u2713")

            self.payload = th[0].result().json()
            self.dl_payload = th[1].result().json()

        self.id = mod_id
        self.name = self.payload["name"]
        self.summary = self.payload["summary"]
        self.game_version = game_version

        for x in self.payload["gameVersionLatestFiles"]:
            if x["gameVersion"] == self.game_version:
                self.project_file_id = x["projectFileId"]
                break

        if not hasattr(self, "project_file_id"):
            raise VersionError(self.game_version)

        for y in self.dl_payload:
            if y["id"] == self.project_file_id:
                self.file_name = y["fileName"]
                self.file_length = y["fileLength"]
                self.file_dl_url = y["downloadUrl"]
                self.dependencies = list(
                    filter(lambda x: x["type"] > 2, y["dependencies"])
                )
                break

    def fetch_dependencies(self, dir_path):
        if self.dependencies:
            for x in self.dependencies:
                dep = Mod(x["addonId"], self.game_version)
                dep.fetch(dir_path)

    def fetch(self, dir_path):

        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"\"{dir_path}\" not found.")
        
        if os.path.isfile(path := os.path.join(dir_path, self.file_name)):
            print(f"Requirement Already Satisfied: {self.name} in {path}")
            return

        r = requests.get(self.file_dl_url, stream=True)

        dl_path = os.path.join(dir_path, self.file_name)

        print(f"Downloading {self.file_name}")

        progress_bar = tqdm(total=self.file_length, unit='iB',
                            unit_scale=True, bar_format='  |{bar:50}{r_bar}{bar:-10b}')

        with open(dl_path, 'wb') as f:
            for data in r.iter_content(1024):
                f.write(data)
                progress_bar.update(len(data))

        progress_bar.close()

        self.fetch_dependencies(dir_path)

    @classmethod
    def from_name(cls, mod_name, game_version, limit=255):
        MOD_SEARCH_URL = "https://addons-ecs.forgesvc.net/api/v2/addon/search?categoryId=0&gameId=432&gameVersion=" + game_version + "&index=0&pageSize=" + str(limit) + "&searchFilter=" + mod_name

        r = requests.get(MOD_SEARCH_URL, headers=HEADERS).json()

        for value, choice in enumerate(r):
            print(f"{value+1} {choice['name']}")

        print("> ", end="")
        
        return cls(r[int(input())-1]["id"], game_version)

    def remove(self, dir_path):
        ad_path = os.path.join(dir_path, self.file_name)
        if not os.path.isfile(ad_path):
            raise FileNotFoundError(f"\"{ad_path}\" not found.")

        os.remove(ad_path)

    def __repr__(self):
        return f"Mod({self.id})"

    def __str__(self):
        return f"\033[92m{self.name}\033[0m/\n {self.summary}"


MOD_ID = 225643
ad = Mod.from_name("rftools", "1.16.5", 255)
print(ad)
# ad = Mod(MOD_ID, "1.16.5")
ad.fetch("./mods")
ad.remove("./mods")
