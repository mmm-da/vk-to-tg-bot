import os 
import urllib
from typing import Dict, List
from vk_api import VkApi

APP_ID = int(os.environ['VK_APP_ID'])
CLIENT_SECRET= os.environ['VK_API_CLIENT_SECRET']
SERVICE_TOKEN= os.environ['VK_API_SERVICE_TOKEN']

def singleton(cls):
    instances = {}     
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance
 
@singleton
class ApiInstance(object):
    def __init__(self,api_id:int,client_secret:str,service_token:str) -> None:
        super().__init__()
        self.vk_session = VkApi(app_id=api_id, client_secret=client_secret)
        self.vk_session.token = {
            "access_token": service_token,
            "expires_in": 0,
        }
        self.vk = self.vk_session.get_api()

    @property
    def api(self):
        return self.vk

api_instance = ApiInstance(APP_ID,CLIENT_SECRET,SERVICE_TOKEN)
vk_api_instance = api_instance.api

def get_owners_id(url_list:List[str])-> Dict[int,str]:
    result = {}


    def get_shortname(url:str)->str:
        return urllib.parse.urlparse(url).path.split('/')[-1]
    
    url_list = list(map(get_shortname, url_list))    
    
    try:
        responce = vk_api_instance.groups.getById(group_ids=url_list)
        for group in responce:
            result[-1*group['id']] = group['name']
    except KeyError:
        pass
    
    return(result)