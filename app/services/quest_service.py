import os
import json
import random
import re
from typing import Dict, Set, List
import random
from app.repository.repository import Repository

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class QuestService:
    def __init__(self, repository: Repository):
        self.repository: Repository = repository

    def get_all_maps(self) -> List[Dict[str, str]]:
        all_locations = self.repository.get_locations()
        map_data = []
        for location in all_locations:
            map_data.append(
                {"region_name": location["Region"],
                 "subregion": location["Subregion"]}
            )
        return map_data

    def read_all_npcs(self) -> List[Dict[str, list]]:
        all_characters = self.repository.get_characters()
        npc_data = []
        friendly = []
        enemy = []
        for character in all_characters:
            num = random.randrange(0, 2)
            if num == 0:
                friendly.append(character["Name"])
            else:
                enemy.append(character["Name"])
        npc_data.append(
            {"friendly": friendly,
             "enemy": enemy}
        )

        return npc_data

    def read_quests_from_folder(self, folder_path) -> Dict[str, str]:
        data_folder = os.path.join(base_dir, "data", folder_path)
        quests_data = []
        for file_name in os.listdir(data_folder):
            if file_name.endswith(".json"):
                with open(os.path.join(data_folder, file_name), 'r') as file:
                    quests_data.append(json.load(
                        file
                    ))
        random_quest = random.choice(quests_data[0])
        return random_quest

    def extract_bracketed_from_json(self, data: Dict[str, str]) -> Set[str]:
        pattern = re.compile(r'\[([^\[\]]+)\]')
        results = set()

        for value in data.values():
            if isinstance(value, str):
                results.update(pattern.findall(value))

        return results

    def match_entities(self, entities: Set[str], maps: List[Dict[str, str]], npcs: List[Dict[str, list]]) -> List[Dict[str, str]]:
        matched_entities = []
        already_matched = []
        friendly_npcs = npcs[0]["friendly"]
        enemy_npcs = npcs[0]["enemy"]
        for entity in entities:
            if entity in already_matched:
                continue
            elif entity[:-1] == "NAME":
                name = random.choice(friendly_npcs)
                matched_entities.append({entity: name})
            elif entity[:-1] == "ENEMY":
                name = random.choice(enemy_npcs)
                matched_entities.append({entity: name})
            elif entity[:-1] == "SUBREGION":
                region = random.choice(maps)
                subregion = random.choice(region["subregion"])
                matched_entities.append({entity: subregion})
            elif entity[:-1] == "CREATURE_FAMILY":
                creature_family = random.choice(npcs)
                matched_entities.append({entity: "Chimera"})
            already_matched.append(entity)

        return matched_entities

    def replace_entities(self, matched_entities: List[Dict[str, str]], random_quest_data: Dict[str, str]) -> Dict[str, str]:
        updated_quest_data = {}

        entity_map = {key: value for d in matched_entities for key, value in d.items()}

        for key, value in random_quest_data.items():
            if isinstance(value, str):
                for entity, replacement in entity_map.items():
                    value = value.replace(f"[{entity}]", str(replacement))
            updated_quest_data[key] = value

        return updated_quest_data


    def get_random_quest(self) -> Dict[str, str]:
        maps_data = self.get_all_maps()
        npcs_data = self.read_all_npcs()
        random_quest_data = self.read_quests_from_folder("quests")

        extracted_entities = self.extract_bracketed_from_json(random_quest_data)

        matched_entities = self.match_entities(extracted_entities, maps_data, npcs_data)

        replaced_quest = self.replace_entities(matched_entities, random_quest_data)

        return replaced_quest