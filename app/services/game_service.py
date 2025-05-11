class GameService:
    def __init__(self, repository):
        self.repository = repository

    def set_selected_game(self, data):
        self.repository.set_game(data)
        player_data = self.repository.player.find()[0]
        del player_data['_id']
        return {"player": player_data, "history": self.repository.get_message_history()}

    def create_new_game(self, data):
        self.repository.create_new_game(data)
        location_info = self.repository.get_player_location_infos()
        return location_info

    def get_saved_games(self):
        return self.repository.get_saved_games()

    def delete_game(self, data):
        is_deleted = self.repository.delete_game(data)
        return {"response": is_deleted}
