import asyncio
import json
import logging
import shutil
from pathlib import Path

from PIL import Image, ImageOps
import aiohttp
from aiohttp.web_exceptions import HTTPException
from pyvis.network import Network
from tqdm import tqdm


def sort_db():
    folder = Path('db')
    adjacency = {}

    for filename in folder.glob('*.json'):
        source_people = filename.stem
        adjacency[source_people] = []

        with open(filename, 'r') as f:
            data = json.load(f)

        for people, verified in data.items():
            if verified['verified']:
                adjacency[source_people].append({
                    "people": people,
                    "distance": verified['distance'],
                    "threshold": verified['threshold']
                })

    with open('adjacency.json', 'w', encoding='utf-8') as f:
        json.dump(adjacency, f, ensure_ascii=True, indent=4)


def sort_by_folders():
    was = []

    db_folder = Path('images')
    if not db_folder.exists():
        db_folder.mkdir()

    image_folder = Path('../test_images')
    with open('adjacency.json', 'r') as f:
        adjacency: dict = json.load(f)

    for people, faces in adjacency.items():
        if people in was:
            continue

        people_folder = db_folder / people
        if people_folder.exists():
            continue
        else:
            people_folder.mkdir()

        for face in faces:
            img_path = image_folder / face['people']
            shutil.copy2(img_path, people_folder)
            was.append(img_path.stem)


def change_range(value, min1, max1, min2, max2):
    return (value - min1) / (max1 - min1) * (max2 - min2) + min2


async def show_graph(image_folder: Path, adjacency_path: Path, imgbb_path: Path, graph_path: Path):
    with open(adjacency_path, 'r') as f:
        adjacency: dict = json.load(f)

    with open(imgbb_path, 'r') as f:
        images: dict = json.load(f)

    nodes = []
    edges = []

    for people, faces in adjacency.items():
        nodes.append(people)
        for face in faces:
            edges.append((people, face['people'].removesuffix('.jpg'), {
                'distance': face['distance'],
                'threshold': face['threshold']
            }))

    net = Network(directed=True, filter_menu=True, cdn_resources='remote')
    try:
        for i, node in tqdm(enumerate(nodes), desc='Add nodes and send images to imgbb'):
            if node not in images:
                img_path = image_folder / f'{node}.jpg'
                if not img_path.exists():
                    raise FileNotFoundError(f'{img_path} no exists!')
                # Send image to imgbb if a path exists and image has not yet sent
                images[node] = await send_image(img_path)
            net.add_node(i, label=node, shape='image', image=images[node]['thumb']['url'])
    finally:
        with open(imgbb_path, 'w') as f:
            json.dump(images, f, ensure_ascii=True, indent=4)

    for e1, e2, info in tqdm(edges, desc='Add edges'):
        i1, i2 = nodes.index(e1), nodes.index(e2)
        if i1 == i2:
            continue

        threshold, distance = info['threshold'], info['distance']
        new_threshold = threshold * 1
        if distance > new_threshold:
            continue

        w = abs(change_range(distance, 0, new_threshold, -10, -0.01))
        net.add_edge(i1, i2, width=w, title=round(distance / new_threshold, 2))

    net.show(str(graph_path), notebook=False)  # save visualization in 'graph.html'


async def send_image(path: str | Path) -> dict:
    params = dict(key="c4af9d0fe1f3f9d705f9264cd569ae82")
    post_data = aiohttp.FormData()

    async with aiohttp.ClientSession() as session:
        with open(path, 'rb') as f:
            post_data.add_field('image', f)

            # Do not close file before send request
            async with session.post('https://api.imgbb.com/1/upload', data=post_data, params=params) as response:
                if response.status == 200:
                    resp = await response.json()
                else:
                    raise HTTPException(text=f"Can't post image!")

    return resp.get('data')


def process_images():
    folder = Path('../compressed')

    for img_path in tqdm(folder.glob('*.jpg')):
        with Image.open(img_path) as img:
            ImageOps.exif_transpose(img, in_place=True)
            img.save(img_path)
        img_path.rename(folder / f'{img_path.stem}.jpg')


imgbb_path = Path('imgbb.json')

async def main():
    people_folder = Path('../people')
    for i, folder in tqdm(enumerate(people_folder.iterdir()), desc='Persons'):
        if not folder.is_dir():
            continue

        adjacency_path = Path(f'adjacency_{i}.json')

        await show_graph(folder, adjacency_path, imgbb_path, graph_path)


results = Path('result.json')

folder = Path('images')
save_folder = Path('db')


graph_path = Path('graph.html')

if __name__ == '__main__':
    # print(f'Using model: {MODEL}')
    # print(f'Using distance metric: {DISTANCE_METRIC}')
    #
    # images = list(folder.glob('*.jpg'))
    # save_all_encodings(images, results)
    #
    # if not save_folder.exists():
    #     save_folder.mkdir()
    #
    # compare_each_other(results, MODEL, DISTANCE_METRIC)
    #
    # sort_db(save_folder, adjacency_path)
    asyncio.run(main())
