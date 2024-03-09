from flask import Flask, request, current_app
from flask_cors import CORS
from repository import Repository
from agent_and_tools import AgentWithTools
from GPTChatbot import Chatbot
from templates import game_start
from character_agent import Character_Agent

def create_app():
    app = Flask(__name__)

    CORS(app)

    repository = Repository(gameName="adventuregame")

    chatbot = Chatbot(game_start)

    agent_executer = AgentWithTools(repository, chatbot)



    with app.app_context():
        current_app.repository = repository

    @app.route('/getItems', methods=['POST'])
    def getItems():
        print("getItems: ", repository.getEquipments())

        return repository.getEquipments()

    @app.route('/setSelectedGame', methods=['POST'])
    def setGame():
        data = request.get_json()
        repository.setGame(data)
        agent_executer.setRepository(repository)

        createdPlayer = repository.player.find()[0]

        del createdPlayer['_id']

        return {"player": createdPlayer, "history": repository.get_message_history()}

    @app.route('/getSaves', methods=['POST'])
    def getSavedGames():
        saved_games = repository.getSavedGames()

        return saved_games

    @app.route('/deleteGame', methods=['POST'])
    def deleteGame():
        data = request.get_json()
        is_saved_game_succesfully_deleted = repository.delete_game(data)

        return {'response': is_saved_game_succesfully_deleted}

    @app.route('/createNewGame', methods=['POST'])
    def startGame():
        data = request.get_json()

        repository.createNewGame(data)
        locationInfo = repository.getPlayerLocationInfos()
        chatbot.set_player_message(locationInfo)
        agent_executer.setRepository(repository)
        answer = chatbot.get_start_response()
        print("answer: ", answer)
        #return {'response': answer}
        speaker = "Game master"
        speakerImage = "src/assets/images/gameicons/game_master.png"

        repository.add_message_to_chat_history(answer, speaker, speakerImage)

        return {'response': answer, 'speaker': speaker, 'speakerImage': speakerImage}

    @app.route('/chatbot', methods=['POST'])
    def chatbot_api():
        data = request.get_json()

        # Extract input data from the request
        messages = data.get('messages')
        repository.add_player_message_to_chat_history(messages)
        try:
            answer_from_agent = agent_executer.agent_executer.run(messages)
        except Exception as e:
            response = str(e)
            if not response.startswith("Could not parse LLM output: `"):
                raise e
            response = response.removeprefix("Could not parse LLM output: `").removesuffix("`")

        #chatbot.set_player_message(messages)

        #answer_from_chatbot = chatbot.get_response(messages)
        if repository.getCharacterWithWhomThePlayerisInteracting() == "None":
            chatbot.set_player_message(messages)
            answer_from_chatbot = chatbot.get_response(messages)
            speaker = "Game master"
            speakerImage = "src/assets/images/gameicons/game_master.png"

        else:
            agent_as_character = Character_Agent(repository)
            print("ez a karater: ", agent_as_character.personified_character)
            answer_from_chatbot = agent_as_character.agent_executer.run(messages)
            speaker = agent_as_character.get_character_name()
            speakerImage = agent_as_character.get_character_picture()

        repository.add_message_to_chat_history(answer_from_chatbot, speaker, speakerImage)
        return {'response': answer_from_chatbot, 'speaker': speaker, 'speakerImage': speakerImage}

        #return repository.getLastAction()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)  # Run the Flask app