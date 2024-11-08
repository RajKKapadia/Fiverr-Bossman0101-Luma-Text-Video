import asyncio
from typing import Tuple, List, Dict

import requests

import config


async def get_luma_job_id(prompt: str) -> str:
    try:
        payload = {
            "prompt": prompt
        }
        headers = {
            "Authorization": f"Bearer {config.LUMA_API_KEY}"
        }
        response = requests.post(
            "https://api.lumalabs.ai/dream-machine/v1/generations",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        response = response.json()
        return response["id"]
    except:
        return ""


async def retriev_luma_job_by_id(task_id: str) -> Tuple[List[str], bool]:
    headers = {
        "Authorization": f"Bearer {config.LUMA_API_KEY}"
    }
    flag = True
    status = False
    video_urls = []
    while flag:
        response = requests.get(
            f"https://api.lumalabs.ai/dream-machine/v1/generations/{task_id}",
            headers=headers,
        )
        response.raise_for_status()
        if response.status_code == 200:
            response = response.json()
            if response["state"] == "completed" and response["failure_reason"] == None:
                video_urls.append(response["assets"]["video"])
                flag = False
                status = True
            if response["failure_reason"] != None:
                flag = False
                status = False
        await asyncio.sleep(1)
    return video_urls, status


async def call_luma_api_text_to_video(prompt: str) -> Tuple[List[str], bool]:
    task_id = await get_luma_job_id(prompt=prompt)
    if task_id == "":
        return [], False
    else:
        video_urls, status = await retriev_luma_job_by_id(
            task_id=task_id)
        return video_urls, status
