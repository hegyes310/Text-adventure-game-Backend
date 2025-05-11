from app.models.game_master import GameMaster
from app.repository import repository


class GameMasterService:
    def __init__(self, repository: repository):
        self.game_master: GameMaster | None = None
        self.name = "Game master"
        self.speaker_image = "src/assets/images/gameicons/game_master.png"
        self.repository: repository = repository

    def initialize_game_master(self):
        self.game_master = GameMaster(
            game_name=self.repository.game_name,
            mongo_client=self.repository.myclient,
            game_master_name=self.name
        )

    def get_starting_prompt(self, location_information: str) -> str:
        response = self.game_master.start_game(location_information)
        return response

    def create_input_prompt(self, player_message: str, npc_reactions: str) -> str:
        combined_input = f"Player's action: {player_message}\n\n"
        if npc_reactions != "":
            combined_input += f"Relevant NPC reactions:\n{npc_reactions}\n\nIn your response, continue the story naturally, incorporating both the player's action and the NPCs' behaviors."

        return combined_input

    def generate_response(self, player_message: str, npc_reactions: str) -> str:
        combined_input = self.create_input_prompt(player_message=player_message, npc_reactions=npc_reactions)

        response = self.game_master.continue_game(
            input_message=combined_input
        )

        return response
