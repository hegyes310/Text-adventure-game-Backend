import requests, json, os, io, re, base64, random
ENDPOINT = "http://127.0.0.1:5001/api/v1/generate"
prompt = {
    "prompt": """Below is an instruction that describes a task. Write a response that appropriately completes the request.

            ### Instruction: You are a dungeon master who is going to run a text-based adventure RPG game for me based on Stalker books and games. 
            Provide a painterly and brief description of the starting environment based on the following statements. 
            Clear sky base contains of a two story main building, with Lebedev the commander residing on the ground floor and Nimble snoozing in the next room. 
            Adjacent is a small laboratory, where Kalancha the scientist monitors his makeshift displays and instruments. 
            A bar, run by Cold, is right next to it. 
            Across the campsite, Novikov the base technician sits in a tiny hut. 
            The workshop opposite to the main building is where Suslov is trading his goods. 
            The whole area is surrounded by barbed wire and wooden fences, bushes obstructing the view out of the base.
            ### Response:""",
    "temperature": 0.5,
    "top_p": 0.9,
    "max_length": 200
}
response = requests.post(f"{ENDPOINT}/api/v1/generate", json=prompt)
print("lol: ", response.json())
def split_text(text):
    parts = re.split(r'\n[a-zA-Z]', text)
    return parts


results = response.json()['results']
text = results[0]['text']  # Parse the response and get the generated text
print("tect: ", text)
response_text = split_text(text)[0]
print("split_text(text)[0]: ", response_text)
response_text = response_text.replace("  ", " ")
print("response_text.replace: ", response_text)
response_text = response_text.replace("\n", "")
print(f"Bot amit válaszolt: {response_text}")  # Send the response back to the user