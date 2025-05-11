from app.services.character_extractor_service import CharacterExtractorService
from app.services.character_handler_service import CharacterHandlerService
from app.services.game_master_service import GameMasterService
from app.repository.repository import Repository
from app.services.quest_service import QuestService


class ChatbotService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.character_extractor = CharacterExtractorService()
        self.character_handler = CharacterHandlerService(
            repository=repository
        )
        self.game_master = GameMasterService(
            repository=repository
        )
        self.quest_service = QuestService(
            repository=repository
        )

    def load_characters(self):
        npc_information = self.repository.get_all_npcs_name_and_background()
        self.character_handler.initialize_characters(
            characters_json=npc_information
        )

    def generate_start_response(self, location_information: str) -> dict:
        self.load_characters()

        self.game_master.initialize_game_master()

        response = self.game_master.get_starting_prompt(
            location_information=location_information
        )

        self.repository.add_message_to_chat_history(
            message=response,
            speaker=self.game_master.name,
            speaker_image=self.game_master.speaker_image
        )
        return {"response": response, "speaker": self.game_master.name, "speakerImage": self.game_master.speaker_image}

    def get_latest_game_master_and_player_message(self):
        previous_interaction = self.repository.get_latest_message()
        return previous_interaction[0]["response"], previous_interaction[1]["response"]

    def quest_is_needed(self, characters_json: dict) -> bool:
        for character in characters_json.get("characters", []):
            if character.get("quest") and character.get("quest") == "Yes":
                return True
        return False

    def check_for_quest(self, characters_json: dict) -> dict | None:
        if self.quest_is_needed(characters_json=characters_json):
            random_quest = self.quest_service.get_random_quest()
            return random_quest

    def get_characters_reaction(self, game_master_message: str, player_message: str) -> str:
        characters_json = self.character_extractor.get_extracted_characters(
            game_master_response=game_master_message,
            player_message=player_message
        )

        get_quest = self.check_for_quest(characters_json=characters_json)
        npc_reactions = self.character_handler.handle_reactions(
            characters_json=characters_json,
            player_message=player_message,
            game_master_message=game_master_message,
            quest=get_quest
        )

        return npc_reactions

    def process_player_message(self, player_message: str) -> dict:
        self.repository.add_player_message_to_chat_history(message=player_message)

        latest_player_message, latest_game_master_message = self.get_latest_game_master_and_player_message()

        npc_reactions = self.get_characters_reaction(
            game_master_message=latest_game_master_message,
            player_message=latest_player_message
        )

        game_master_response = self.game_master.generate_response(
            latest_player_message, npc_reactions
        )

        self.repository.add_message_to_chat_history(
            message=game_master_response,
            speaker=self.game_master.name,
            speaker_image=self.game_master.speaker_image)

        return {
            "response": game_master_response,
            "speaker": self.game_master.name,
            "speakerImage": self.game_master.speaker_image
        }
