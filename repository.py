import json
from bson.json_util import dumps
import pymongo
import os

#myclient = pymongo.MongoClient("mongodb://localhost:27017")


class Repository:
    def __init__(self, playerObj = None, gameName = None):
        if playerObj == None:
            self.myclient = pymongo.MongoClient("mongodb://localhost:27017")
            self.mydb = self.myclient[gameName]
            self.characters = self.mydb["characters"]
            self.player = self.mydb["player"]
            self.missions = self.mydb["mission"]
            self.equipments = self.mydb["equipment"]
            self.actions = self.mydb["actions"]
            self.maps = self.mydb["maps"]
        else:
            self.myclient = pymongo.MongoClient("mongodb://localhost:27017")
            self.mydb = self.myclient[playerObj["GameName"]]
            self.characters = self.mydb["characters"]
            self.player = self.mydb["player"]
            self.missions = self.mydb["mission"]
            self.equipments = self.mydb["equipment"]
            self.initializeDB(playerObj)
            self.actions = self.mydb["actions"]
            self.maps = self.mydb["maps"]

    def initializeDB(self, playerObj):
        self.read_files_from_folder("npc", self.characters)
        self.read_files_from_folder("mission", self.missions)
        self.read_files_from_folder("equipment", self.equipments)
        self.read_files_from_folder("equipment", self.equipments)
        self.read_files_from_folder("map", self.maps)
        self.player.insert_one(playerObj)
        self.player.update_one({"Name": playerObj["Name"]}, {"$set": {"NPC": "None"}})

    def read_files_from_folder(self, folder_path, which_collection):
        file_data = []
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".json"):
                with open(os.path.join(folder_path, file_name), 'r') as file:
                    file_data.append(json.load(
                        file
                    ))

        which_collection.insert_many(file_data)

    def getSavedGames(self):
        saved_games = self.myclient.list_database_names()
        return saved_games

    def getEquipments(self):
        equipmentsCursor = self.equipments.find()
        list_cur = list(equipmentsCursor)
        json_data = dumps(list_cur)
        return json_data

    def setGame(self, game_name):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017")
        self.mydb = self.myclient[game_name]
        self.characters = self.mydb["characters"]
        self.player = self.mydb["player"]
        self.missions = self.mydb["mission"]
        self.equipments = self.mydb["equipment"]
        self.actions = self.mydb["actions"]
        self.maps = self.mydb["maps"]

    def createNewGame(self, playerObj):
        player = playerObj.copy()
        del player["GameName"]
        print("player: ", player)
        self.mydb = self.myclient[playerObj["GameName"]]
        self.characters = self.mydb["characters"]
        self.player = self.mydb["player"]
        self.missions = self.mydb["mission"]
        self.equipments = self.mydb["equipment"]
        self.actions = self.mydb["actions"]
        self.maps = self.mydb["maps"]
        self.initializeDB(player)

    def getCharacterShop(self, characterName):
        character = self.characters.find({'Name': characterName})[0].get("Shop")
        shopItems = []
        for equipment in character:
            equipmentCursor = self.equipments.find({'Name': equipment})[0]
            shopItems.append(equipmentCursor)
        if len(character) > 0:
            self.actions.insert_one({"Situation": "trade", "Data": shopItems})
            return True
        else:
            return False

    def playerWantToFightWithANPC(self, characterName):
        character = self.characters.find({'Name': characterName})[0]
        player = self.player.find()[0]

        characterWeapon = list(self.equipments.find({'Name': character.get('Weapon')}))
        characterArmor = list(self.equipments.find({'Name': character.get('Armor')}))
        playerWeapon = list(self.equipments.find({'Name': player.get('Weapon')}))
        playerArmor = list(self.equipments.find({'Name': player.get('Armor')}))

        self.actions.insert_one({"Situation": "fight", "EnemyWeapon": characterWeapon, "EnemyArmor": characterArmor, "PlayerWeapon": playerWeapon, "PlayerArmor": playerArmor})

        return True

    def getCharacterWithWhomThePlayerisInteracting(self):
        character_name_from_player = self.player.find()[0].get("NPC")
        if character_name_from_player == "None":
            return character_name_from_player
        else:
            character = self.characters.find({'Name': character_name_from_player})[0]
            return character


    def add_character_memory(self, memories):
        character = self.getCharacterWithWhomThePlayerisInteracting()
        self.characters.update_one({"Name": character["Name"]}, {"$push": {"Memories": memories}})

    def setCharacterWithWhomThePlayerisInteracting(self, characterName):
        player = self.player.find()[0].get("Name")
        self.player.update_one({"Name": player}, {"$set": {"NPC":characterName}})

    def setCharacterWithWhomThePlayerToNone(self):
        player = self.player.find()[0].get("Name")
        self.player.update_one({"Name": player}, {"$set": {"NPC": "None"}})

    def getCharacterWithWhomThePlayer(self):
        player = self.player.find()[0].get("NPC")
        return player

    def getLastAction(self):
        actionCursor = self.actions.find(sort=[('_id', pymongo.DESCENDING)], limit=1)
        list_cur = list(actionCursor)
        json_data = dumps(list_cur)
        return json_data

    def setPlayerLocation(self, location):
        player = self.player.find()[0].get("Name")
        self.player.update_one({"Name": player}, {"$set": {"Location": location}})

    def getPlayerLocationInfos(self):
        player = self.player.find()[0]
        mapCursor = self.maps.find({'Map': player.get('Location')})
        #print("mapCursor: ", mapCursor[0])
        locationName = mapCursor[0].get("Map")
        charactersOnTheLocation = list(mapCursor[0].get("Characters"))
        detailsAboutTheLocation = mapCursor[0].get("Details")
        appearanceOfTheLocation = mapCursor[0].get("Appearance")
        #print("locationName: ", locationName)
        #print("charactersonTheLocation: ", self.listToString(charactersOnTheLocation))
        #print("detailsAboutTheLocation: ", detailsAboutTheLocation)
        locationInformation = "Location's name: " + locationName + ". Characters on the location: " + self.listToString(charactersOnTheLocation) + ". Details about the location: " + detailsAboutTheLocation + ". Appearance of the location: " + appearanceOfTheLocation
        #print("locationInformation: ", locationInformation)
        currentLocation = "The location where the player start: " +locationName
        return locationInformation

    def listToString(self, s):
        str1 = ", "
        return (str1.join(s))

    def delete_game(self, game_name):
        self.myclient.drop_database(game_name)
        return True
