import json
import pymongo
import os


class Repository:
    def __init__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017")
        self.mydb = None
        self.characters = None
        self.player = None
        self.equipments = None
        self.actions = None
        self.maps = None
        self.chat_history = None
        self.quests = None
        self.game_name = None

    def initialize_db(self, player_obj):
        self.read_files_from_folder("characters", self.characters)
        self.read_files_from_folder("maps", self.maps)
        self.player.insert_one(player_obj)

    def get_latest_message(self):
        messages = self.chat_history.find(sort=[('_id', pymongo.DESCENDING)])
        list_messages = list(messages)
        return list_messages[:2]

    def get_all_npcs_name_and_background(self):
        characters = self.characters.find()
        characters_json = []
        for character in characters:
            if character.get("Background") is not None:
                characters_json.append({"character_name": character["Name"], "character_background": character["Background"]})

        return characters_json

    def read_files_from_folder(self, folder_path, which_collection):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_folder = os.path.join(base_dir, "data", folder_path)
        file_data = []
        for file_name in os.listdir(data_folder):
            if file_name.endswith(".json"):
                with open(os.path.join(data_folder, file_name), 'r') as file:
                    file_data.append(json.load(
                        file
                    ))

        which_collection.insert_many(file_data)

    def get_saved_games(self):
        saved_games = self.myclient.list_database_names()
        return saved_games

    def set_game(self, game_name):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017")
        self.mydb = self.myclient[game_name]
        self.characters = self.mydb["characters"]
        self.player = self.mydb["player"]
        self.missions = self.mydb["mission"]
        self.equipments = self.mydb["equipment"]
        self.actions = self.mydb["actions"]
        self.maps = self.mydb["maps"]
        self.chat_history = self.mydb["chat_history"]
        self.game_name = game_name

    def create_new_game(self, player_object):
        player = player_object.copy()
        self.mydb = self.myclient[player_object["GameName"]]
        self.game_name = player_object["GameName"]
        self.characters = self.mydb["characters"]
        self.player = self.mydb["player"]
        self.missions = self.mydb["mission"]
        self.equipments = self.mydb["equipment"]
        self.actions = self.mydb["actions"]
        self.maps = self.mydb["maps"]
        self.chat_history = self.mydb["chat_history"]
        self.initialize_db(player)

    def get_player_location_infos(self):
        player = self.player.find()[0]
        map_cursor = self.maps.find({'Region': player.get('Location')})
        location_name = map_cursor[0].get("Region")
        characters_on_the_location = list(map_cursor[0].get("Characters"))
        details_about_the_location = map_cursor[0].get("Details")
        appearance_of_the_location = map_cursor[0].get("Appearance")
        location_information = "Location's name: " + location_name + ". Characters on the location: " + self.list_to_string(characters_on_the_location) + ". Details about the location: " + details_about_the_location + ". Appearance of the location: " + appearance_of_the_location
        return location_information

    def add_new_characters(self, characters):
        self.characters.insert_many(characters)

    def list_to_string(self, s):
        str1 = ", "
        return (str1.join(s))

    def delete_game(self, game_name):
        self.myclient.drop_database(game_name)
        return True

    def add_message_to_chat_history(self, message, speaker, speaker_image):
        self.chat_history.insert_one({'response': message, 'speaker': speaker, 'speakerImage': speaker_image})

    def get_player_name(self):
        player_name = self.player.find()[0].get("Name")
        return player_name

    def get_player_portrait(self):
        player_portrait = self.player.find()[0].get("Portrait")
        return player_portrait

    def add_player_message_to_chat_history(self, message):
        self.add_message_to_chat_history(message, self.get_player_name(), self.get_player_portrait())

    def get_message_history(self):
        messages = self.chat_history.find()
        list_messages = list(messages)
        formatted_list = [{"response": item["response"].replace("\n", ""), "speaker": item["speaker"],
                           "speakerImage": item["speakerImage"]} for item in list_messages]
        return formatted_list

    def get_locations(self):
        locations = self.maps.find()
        return list(locations)

    def get_characters(self):
        characters = self.characters.find()
        return list(characters)
