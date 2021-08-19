import asyncio
from app.poster_tasks import send_message_with_post
import os
import re
from typing import List, Tuple
import redis
from .celery import app
from .vk_api_helpers import get_owners_id, vk_api_instance

OWNERS_ID = get_owners_id(os.environ["VK_GROUP_URLS"].split(","))


def preprocess_text(group_name: str, text: str,repost_text=None) -> str:
    text = re.sub(r"\[(.*)\|(.*)\]", r"\2", text)
    if repost_text:
        text += '\n-----------------\n' + repost_text
    return f"<b>#{group_name}</b>\n\n" + text


def preprocess_attachments(post: dict,text:str,repost=None) -> list:
    url_list = []
    video_list = []
    attachments_result = []
    attachments = post.get('attachments',[])
    if repost:
        attachments = attachments + repost.get('attachments',[])
    for attachment in attachments:
        attachment_type = attachment["type"]
        if attachment["type"] == "audio":
            name = f'{attachment["audio"]["artist"]}:{attachment["audio"]["title"]}'
            url = attachment["audio"]["url"]
        elif attachment["type"] == "doc":
            name = attachment["doc"]["title"]
            url = attachment["doc"]["url"]
        elif attachment["type"] == "video":
            name = text
            url = f'vk.com/wall{post["owner_id"]}_{post["id"]}'
        elif attachment["type"] == "photo":
            name = text
            url = attachment["photo"]["sizes"][-1].get("url", None)
        
        if attachment["type"] == "link":
            name = attachment["link"]["title"]
            url = attachment["link"]["url"]
            url_list.append({'url':url,'name':name})
        elif attachment["type"] == "video":
            name = text
            url = f'vk.com/wall{post["owner_id"]}_{post["id"]}'
            video_list.append({'url':url,'name':name})
        else:
            attachments_result.append({"type": attachment_type, "url": url, "name": name})
    return attachments_result,url_list,video_list


def add_links_to_text(text: str, attachments: list) -> Tuple[str, list]:
    result = text
    if attachments:
        result += "\nСсылки к прикрепленные посту:"
        for link in attachments:
            result += f'\n - {link["url"]}'
    return result

def add_videos_to_text(text: str, attachments: list) -> Tuple[str, list]:
    result = text
    if attachments:
        result += "\nСсылка на пост с видео:"
        result += f'\n - {attachments[0]["url"]}'
    return result

@app.task
def preprocess_post(group_name: str, post: dict):
    reposts = post.get('copy_history',None)

    repost = {}
    repost_text = ''
    if reposts:
        repost = reposts[0]
        repost_text = repost.get('text',None)
        repost_text = re.sub(r"\[(.*)\|(.*)\]", r"\2", repost_text)

    post_text = post.get('text', '')

    text = preprocess_text(group_name, post_text, repost_text=repost_text )

    attachments,urls,videos = preprocess_attachments(post,text,repost=repost)
    text = add_links_to_text(text,urls)
    text = add_videos_to_text(text,videos)

    send_message_with_post.delay(text,attachments)

@app.task(rate_limit='10/m')
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
        print(f'Pull {len(posts)} new posts')
        try:
            last_post = max(posts, key=lambda el: el["id"])["id"]
            r.set(last_post_redis_key, last_post)
            print(f'Last post id = {last_post}')
        except ValueError as err:
            print(f"No new posts for {OWNERS_ID[owner_id]}, last post id = {last_post}, err={err}")

        for post in posts:
            preprocess_post.delay(OWNERS_ID[owner_id], post)
