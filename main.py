from flask import Flask, request, current_app
from flask_cors import CORS
from app.repository.repository import Repository
from app.services.chatbot_service import ChatbotService
from app.services.game_service import GameService


def create_app():
    app = Flask(__name__)
    CORS(app)

    repository = Repository()
    chatbot_service = ChatbotService(repository)
    game_service = GameService(repository)

    with app.app_context():
        current_app.repository = repository

    @app.route('/setSelectedGame', methods=['POST'])
    def set_game():
        game_data = request.get_json()
        loadad_game_data = game_service.set_selected_game(game_data)
        chatbot_service.load_characters()
        return loadad_game_data

    @app.route('/getSaves', methods=['POST'])
    def get_saved_games():
        saved_games = repository.get_saved_games()
        return saved_games

    @app.route('/createNewGame', methods=['POST'])
    def startGame():
        new_game_data = request.get_json()
        players_starting_location = game_service.create_new_game(new_game_data)
        response = chatbot_service.generate_start_response(players_starting_location)
        return response

    @app.route('/chatbot', methods=['POST'])
    def chatbot():
        data = request.get_json()
        result = chatbot_service.process_player_message(data.get('messages'))
        return result

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
