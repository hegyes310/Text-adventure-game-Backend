from app.models.characters import Character
from typing import Any
from app.services.character_creator_service import CharacterCreatorService
from pymongo import MongoClient


class CharactersHandler:
    def __init__(self):
        self.characters: dict = {}
        self.character_creator_service = CharacterCreatorService()

    def initialize_characters(self, characters_json: dict, mongo_client: MongoClient, game_name: str):
        for character in characters_json:
            self.characters[character["character_name"]] = Character(
                character_name=character["character_name"],
                background=character["character_background"],
                mongo_client=mongo_client,
                game_name=game_name
            )

    def is_it_a_new_character(self, character_name: str) -> bool:
        if character_name in self.characters:
            return True
        return False

    def generate_characters_reaction(self, characters_json: dict, player_message: str, game_master_message: str, mongo_client: MongoClient, game_name: str, quest: dict | None) -> tuple[list[Any], list[dict[str, Any]]]:
        npc_reactions_list = []
        new_characters_with_background = []
        for character in characters_json['characters']:
            if self.characters.get(character["name"]) is None:
                self.create_new_character_background(
                    character_name=character['name'],
                    mongo_client=mongo_client,
                    game_name=game_name
                )
                new_characters_with_background.append({"Name": character["name"], "Background": self.characters.get(character["name"]).background.content})
            if character["should_react"] == "Yes":
                if character.get("quest") and character.get("quest") != "No":
                    character_reaction = self.characters[character["name"]].generate_character_reaction_with_quest(
                        player_message=player_message,
                        game_master_message=game_master_message,
                        quest_json=quest
                    )

                else:
                    character_reaction = self.characters[character["name"]].generate_character_reaction(
                        player_message=player_message,
                        game_master_message=game_master_message
                    )
                npc_reactions_list.append(character_reaction)
        return npc_reactions_list, new_characters_with_background

    def create_new_character_background(self, character_name: str, mongo_client: MongoClient, game_name: str):
        generate_background = self.create_npc_background(character_name)
        self.add_character_to_dict(
            character_name=character_name,
            character_background=generate_background,
            mongo_client=mongo_client,
            game_name=game_name
        )

    def create_npc_background(self, character_name: str):
        created_background = self.character_creator_service.generate_character(character_name)
        return created_background

    def add_character_to_dict(self, character_name: str, character_background: str, mongo_client: MongoClient, game_name: str):
        self.characters[character_name] = Character(
            character_name=character_name,
            background=character_background,
            mongo_client=mongo_client,
            game_name=game_name
        )

