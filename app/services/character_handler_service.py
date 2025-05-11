from app.models.character_handler import CharactersHandler
from app.repository import repository


class CharacterHandlerService:
    def __init__(self, repository: repository):
        self.characters_handler: CharactersHandler = CharactersHandler()
        self.repository: repository = repository

    def initialize_characters(self, characters_json: dict):
        self.characters_handler.initialize_characters(
            characters_json=characters_json,
            mongo_client=self.repository.myclient,
            game_name=self.repository.game_name
        )

    def handle_reactions(self, characters_json: dict, player_message: str, game_master_message: str, quest: dict | None) -> str:
        reactions, new_characters = self.characters_handler.generate_characters_reaction(
            characters_json=characters_json,
            player_message=player_message,
            game_master_message=game_master_message,
            mongo_client=self.repository.myclient,
            game_name=self.repository.game_name,
            quest=quest
        )

        if new_characters:
            self.repository.add_new_characters(new_characters)
        return "\n".join(reactions)
