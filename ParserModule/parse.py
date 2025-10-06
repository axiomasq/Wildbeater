from ParserModule.funcs import construct_host_v2
import aiohttp
from aiohttp.client_exceptions import ContentTypeError
import pandas as pd
import asyncio
import json
import re
import glob
import os
from pathlib import Path
from typing import Optional
from tqdm.asyncio import tqdm_asyncio


base_search_url = "https://u-search.wb.ru/exactmatch/ru/common/v18/search"

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
  "Connection": "keep-alive",
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate",
  "accept-language": "ru-RU,ru;q=0.9"
}

params = {
  "curr": "rub",
  "dest": "-5551776",
  "inheritFilters": "false",
  "lang": "ru",
  "page": 0,
  "query": "",
  "resultset": "catalog",
  "sort": "popular"
}

async def run(query: str, pages: int, out_dir: Path, timeout: Optional[float] = None, skip_existing: bool = True):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout is not None else None

    async with aiohttp.ClientSession(headers=headers) as session:

        page_tasks = [getItems_onPage(session, i, query, timeout_obj) for i in range(1, pages+1)]
        pages_df = await tqdm_asyncio.gather(*page_tasks, desc="Fetching items in search")
        items = pd.concat(pages_df, axis=0)

        imt_tasks =  [get_item_imtid(session, row['id'], timeout_obj) for _, row in items.iterrows()]
        imt_results = await tqdm_asyncio.gather(*imt_tasks, desc="Fetching imtids")
        seen_imtids = set() 
        unique_imt_results = [] 
        for id_, imt_id in imt_results: 
            if imt_id not in seen_imtids: 
                seen_imtids.add(imt_id) 
                unique_imt_results.append((id_, imt_id))

        photo_tasks = [get_item_photos(session, id_, imtid, timeout_obj) for id_, imtid in unique_imt_results]
        photo_results = await tqdm_asyncio.gather(*photo_tasks, desc="Fetching photos")
        final_results = {
            id_: {imt_id: photos}
            for result in photo_results
            for id_, imt_data in result.items()
            for imt_id, photos in imt_data.items()
            if photos
        }
        
        ex_p = load_existing_photos(out_dir) if skip_existing else {}
        download_tasks = []
        skipped_count = 0

        for id_, imt_dict in final_results.items():
            for imt_id, photo_list in imt_dict.items():
                for photo_id in photo_list:
                    if (id_, imt_id) in ex_p and photo_id in ex_p[(id_, imt_id)]:
                        skipped_count += 1
                        continue
                    download_tasks.append(download_photo(session, id_, imt_id, photo_id, out_dir, timeout_obj))

        print(f"Photos to download: {len(download_tasks)}")
        print(f"Photos already exist and skipped: {skipped_count}")

        await tqdm_asyncio.gather(*download_tasks, desc="Downloading photos")
        print("Downloaded all photos")



def load_existing_photos(out_dir: Path):
    existing_photos = glob.glob(str(out_dir / "*.jpg"))
    ex_p = {}
    for path in existing_photos:
        name = os.path.basename(path)
        match = re.findall(r"\d+", name)
        if len(match) == 3:
            id_, imtid, photo_id = map(int, match)
            ex_p.setdefault((id_, imtid), []).append(photo_id)
    return ex_p

async def download_photo(session: aiohttp.ClientSession, id_: int, imt_id: int, photo_id: int, out_dir: Path, timeout: Optional[aiohttp.ClientTimeout]):
    url = construct_host_v2(photo_id, 2)
    try:
        async with session.get(url, timeout=timeout) as resp:
            data = await resp.read()
            with open(out_dir / f"{id_}_{imt_id}_{photo_id}.jpg", "wb") as file:
                file.write(data)
    except Exception as e:
        print(f"Error downloading {photo_id} for {id_}/{imt_id}: {e}")           

async def get_item_photos(session: aiohttp.ClientSession, id_: int, imtid: int, timeout: Optional[aiohttp.ClientTimeout]):
    url = construct_host_v2(imtid, 1)
    try:
        async with session.get(url, timeout=timeout) as resp:
            data = await resp.json()
            photos = data.get("photo", [])
            return {id_: {imtid: photos}}
    except Exception as e:
        print(f"Error fetching photos for id {id_}, imtid {imtid}: {e}")
        return {id_: {imtid: []}}

async def get_item_imtid(session: aiohttp.ClientSession, id_, timeout: Optional[aiohttp.ClientTimeout]):
    url = construct_host_v2(id_)
    try:
        async with session.get(url, timeout=timeout) as resp:
            data = await resp.json()
            return id_, data.get("imt_id")
    except Exception as e:
        print(f"Error getting imtid for {id_}: {e}")
        return id_, None

async def getItems_onPage(session: aiohttp.ClientSession, pageNumber: int, query: str, timeout: Optional[aiohttp.ClientTimeout]):
    local_params = params.copy()
    local_params['page'] = pageNumber
    local_params['query'] = query

    try:
        async with session.get(base_search_url, params=local_params, timeout=timeout) as resp:
            data = await resp.text()
            products = json.loads(data)['products']
            
            if len(products)==0:
                print(f"Zero products on page: {pageNumber}")
                return pd.DataFrame()
            
            df = pd.DataFrame(products)
            df = df[['id', 'brandId', 'name', 'supplier', 'supplierId', 'reviewRating', 'feedbacks', 'sizes']]
            return df
    except (json.JSONDecodeError, KeyError) as err:
        print(f"Error on page {pageNumber}: {err}")
        return pd.DataFrame()




if __name__=="__main__":
    # значения по умолчанию для ручного запуска
    asyncio.run(run(query="", pages=5, out_dir=Path("RawData"), timeout=None, skip_existing=True))
