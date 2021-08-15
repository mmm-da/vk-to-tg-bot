import asyncio
from app.poster_tasks import send_message_with_post
import os
import re
from typing import List, Tuple
import redis
from .celery import app
from .vk_api_helpers import get_owners_id, vk_api_instance

OWNERS_ID = get_owners_id(os.environ["VK_GROUP_URLS"].split(","))


def preprocess_text(group_name: str, text: str) -> str:
    text = re.sub(r"\[(.*)\|(.*)\]", r"\2", text)
    return f"<b>{group_name}</b>\n\n" + text


def preprocess_attachments(post: dict,text:str) -> list:
    result = []
    attachments = post.get('attachments',[])
    for attachment in attachments:
        attachment_type = attachment["type"]
        if attachment["type"] == "link":
            name = attachment["link"]["title"]
            url = attachment["link"]["url"]
        elif attachment["type"] == "audio":
            name = f'{attachment["audio"]["artist"]}:{attachment["audio"]["title"]}'
            url = attachment["audio"]["url"]
        elif attachment["type"] == "doc":
            name = attachment["doc"]["title"]
            url = attachment["doc"]["url"]
        elif attachment["type"] == "video":
            name = text
            url = attachment["video"].get("player", f'vk.com/wall{post["owner_id"]}_{post["id"]}')
        elif attachment["type"] == "photo":
            name = text
            url = attachment["photo"]["sizes"][-1].get("url", None)
        result.append({"type": attachment_type, "url": url, "name": name})
    return result


def add_links_to_text(text: str, attachments: list) -> Tuple[str, list]:
    links = list(filter(lambda el: el["type"] == "link",attachments))
    if len(links) < 0:
        text += "\nСсылки к прикрепленные посту:"
        for link in links:
            text += f'\n<a href={link["url"]}>{link["name"]}</a>'
    attach_without_links = list(filter(lambda el: el["type"] != "link",attachments))
    return text, attach_without_links

def add_videos_to_text(text: str, attachments: list) -> Tuple[str, list]:
    links = list(filter(lambda el: el["type"] == "video",attachments))
    if len(links) < 0:
        text += "\nВидео к прикрепленные посту:"
        for link in links:
            text += f'\n<a href={link["url"]}>{link["name"]}</a>'
    attach_without_video = list(filter(lambda el: el["type"] != "video",attachments))
    return text, attach_without_video

@app.task
def preprocess_post(group_name: str, post: dict):
    text = preprocess_text(group_name, post["text"])
    attachments = preprocess_attachments(post,text)
    text, attachments = add_links_to_text(text, attachments)
    send_message_with_post(text,attachments)

@app.task
def pull_vk_posts():
    r = redis.Redis(host=os.environ["REDIS_HOST"], port=os.environ["REDIS_PORT"], db=1)
    for owner_id in OWNERS_ID:
        result = vk_api_instance.wall.get(owner_id=owner_id, count=10)

        last_post_redis_key = f"last_post_id_{owner_id}"

        last_post = r.get(last_post_redis_key)
        if last_post:
            last_post = int(last_post)
        else:
            last_post = 0

        def filter_posts(el):
            return el["id"] > last_post

        posts = list(filter(filter_posts, result["items"]))

        try:
            last_post = max(posts, key=lambda el: el["id"])["id"]
            r.set(last_post_redis_key, last_post)
        except ValueError:
            print(f"No new posts for {OWNERS_ID[owner_id]}")

        for post in posts:
            preprocess_post.delay(OWNERS_ID[owner_id], post)
