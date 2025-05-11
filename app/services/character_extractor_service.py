import json
from langchain_core.messages import BaseMessage
from app.models.character_extractor import CharacterExtractor


class CharacterExtractorService:
    def __init__(self):
        self.character_extractor = CharacterExtractor()

    def extract_json_from_llm_output(self, llm_response: BaseMessage):
        try:
            character_json = json.loads(llm_response.content)
            return character_json
        except json.JSONDecodeError:
            return None

    def get_extracted_characters(self, game_master_response: str, player_message: str) -> dict:
        response = self.character_extractor.extract_characters(
            game_master_response=game_master_response,
            player_message=player_message)
        extracted_characters_json = self.extract_json_from_llm_output(llm_response=response)
        return extracted_characters_json

