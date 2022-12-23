import requests
from bs4 import BeautifulSoup


def get_game_replay(game_id):
    data = {
        "gameId": 740641,
        "turn": 25,
    }

    print(requests.get("https://awbw.amarriner.com/api/game/load_replay.php", json=data).json())


def get_game_ids(username, type):
    start = 1
    game_ids = set()
    while True:
        html_doc = requests.get(
            "https://awbw.amarriner.com/gamescompleted.php?start={start}league=Y&username={username}&type={type}".format(
                start=start, 
                username=username, 
                type=type)
            ).text

        soup = BeautifulSoup(html_doc, 'html.parser')
        page_game_ids = set()
        for link in soup.find_all('a'):
            name = link.get('name')
            if name is not None:
                page_game_ids.add(name.split("_")[1])

        print(page_game_ids)
        
        if len(page_game_ids) == 0:
            break
        
        game_ids = game_ids.union(page_game_ids)
        start += len(page_game_ids)

    print(len(game_ids), game_ids)

get_game_ids("Incuggarch")
