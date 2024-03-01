import json

import pymongo
import os

myclient = pymongo.MongoClient("mongodb://localhost:27017")

'''
mydb = myclient['adventuregame']
collection = mydb["characters"]
collection2 = mydb["player"]
collection3 = mydb["mission"]
collection4 = mydb["equipment"]
collection5 = mydb["actions"]
'''

def create_game(data):
    playerName = data["Name"]

    mydb = myclient[playerName]

    collection = mydb["characters"]
    read_files_from_folder("npc", collection)

    collection2 = mydb["player"]
    collection2.insert_one(data)

    collection3 = mydb["mission"]
    read_files_from_folder("mission", collection3)

    collection4 = mydb["equipment"]
    read_files_from_folder("equipment", collection4)

    #collection5 = mydb["actions"]

def read_files_from_folder(folder_path, which_collection):
    file_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            print("Reading file: ", file_name)
            with open(os.path.join(folder_path, file_name), 'r') as file:
                file_data.append(json.load(
                    file
                ))

                #content = file.read()
                #print(file_name)
                #file_data.append({"file_name": file_name, "content": content})
    which_collection.insert_many(file_data)
    #return file_data


#read_files_from_folder("npc", collection)
#read_files_from_folder("player", collection2)
#read_files_from_folder("mission", collection3)
#read_files_from_folder("map")
#read_files_from_folder("equipment", collection4)
#read_files_from_folder("dbinfos", collection5)
print(myclient.list_database_names())