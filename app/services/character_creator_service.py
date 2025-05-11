from app.models.character_creator import CharacterCreator


class CharacterCreatorService:
    def __init__(self):
        self.character_creator = CharacterCreator()

    def generate_character(self, character_name: str) -> str:
        generated_character = self.character_creator.create_character(character_name=character_name)
        return generated_character
