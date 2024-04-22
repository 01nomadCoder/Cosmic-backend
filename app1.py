from flask import Flask, request,jsonify
from flask_cors import CORS
import pymongo
import numpy as np
import re
from dotenv import load_dotenv
import os
load_dotenv()
client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGODB_DATABASE")]
app = Flask(__name__)
CORS(app)



def calculate_count_and_percentage(data, bracket, gender):
    count = sum(1 for d in data if bracket[1] <= int(d['Age']) < bracket[2] and d['Eng_Gender'] == gender)
    total = len(data)
    percentage = (count / total) * 100 if total > 0 else 0
    return count, percentage

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]
def get_part_numbers(assemblyConstituency):
    collection = db[os.getenv("MONGODB_COLLECTION")]
    part_numbers = collection.distinct("Part_Number", {"AssemblyConstituency": assemblyConstituency})
    sorted_part_numbers = sorted(part_numbers, key=natural_sort_key)  # Sort the part numbers
    return sorted_part_numbers

def getPartwiseCaste(ACName, Part_Number):
    housesCollection = db["Houses"]
    obcCount = 0
    scCount = 0
    stCount = 0
    genCount = 0
    if Part_Number=="All":
        allHouses = [x for x in housesCollection.find({},{"_id":-1,"totalCount":1,"casteGroup":1})]
    else:
        allHouses = [x for x in housesCollection.find({ "Part_Number":str(Part_Number),"AssemblyConstituency":ACName},{"_id":-1,"totalCount":1,"casteGroup":1})]    
    data = []
    for house in allHouses:
        strength = house['totalCount']
        if house['casteGroup'] == "OBC":
            obcCount += strength
        elif house['casteGroup'] == "SC":
            scCount += strength
        elif house['casteGroup'] == "ST":
            stCount += strength
        elif house['casteGroup'] == "General":
            genCount += strength
    data.append({"value": obcCount, "name": "OBC"})
    data.append({"value": scCount, "name": "SC"})
    data.append({"value": stCount, "name": "ST"})
    data.append({"value": genCount, "name": "General"})
    return {"caste_des": data}


def generate_graph(AssemblyConstituency, part_Number):
    collection=db[os.getenv("MONGODB_COLLECTION")]
    if part_Number == "All":
        data = [entry for entry in collection.find({}, {"_id": 0, "Age": 1, "Eng_Gender": 1})]
   
              
    else:
        data = [entry for entry in collection.find({"Part_Number": part_Number,"AssemblyConstituency":AssemblyConstituency}, {"_id": 0, "Age": 1, "Eng_Gender": 1})]
    age_brackets = [('18-25', 18, 25), ('25-35', 25, 35), ('35-50', 35, 50), ('50-60', 50, 60), ('60-80', 60, 80), ('80+', 80, float('inf'))]
    male_counts = []
    female_counts = []
    male_percentages = []
    female_percentages = []
    total_male_female_count = []
    total_male_female_count_precentages = []
    total_male_count = 0  
    total_female_count = 0 
    for bracket in age_brackets:
        male_count, male_percentage = calculate_count_and_percentage(data, bracket, 'Male')
        female_count, female_percentage = calculate_count_and_percentage(data, bracket, 'Female')
        male_counts.append(male_count)
        total_male_count += male_count  # Add male_count to total_male_count
        total_female_count += female_count
        female_counts.append(female_count)
        total_male_female_count.append(male_count + female_count)  # Append total count to the list
        male_percentages.append(f"({male_percentage:.2f}%)")
        female_percentages.append(f"({female_percentage:.2f}%)")
        total_male_female_count_precentages.append(f"({(male_percentage + female_percentage) / 2:.2f}%)")  # Append total percentage to the list
    bar_graph_by_Genderchart={'male': male_counts, 'female': female_counts,"male_percentages":male_percentages,"female_percentages":female_percentages}
    bar_graph_by_male_female_countchart={'male_femaleCount':total_male_female_count,"total_male_female_count_precentages":total_male_female_count_precentages}
    return {"bar_graph_by_male_female_countchart":bar_graph_by_male_female_countchart,"bar_graph_by_Genderchart":bar_graph_by_Genderchart}


@app.route('/get_assemblyConstituency_names',methods=["POST"])
def get_assemblyConstituency_route():
    state=request.json['state']
    collection=db[os.getenv("MONGODB_COLLECTION")]
    assemblyConstituency_Name=collection.distinct("AssemblyConstituency")
    return jsonify(assemblyConstituency_Name)


@app.route('/get_part_numbers', methods=['POST'])
def get_part_numbers_route():
    AssemblyConstituency  = request.json['AssemblyConstituency']
    part_numbers = get_part_numbers(AssemblyConstituency)
    return jsonify(part_numbers)


@app.route('/graph', methods=['POST'])
def graph():
    AssemblyConstituency  = request.json['AssemblyConstituency']
    part_number  = request.json['part_number'] 
    if not part_number:
        part_number = 'All'  
    data= generate_graph(AssemblyConstituency, part_number)
    data1=getPartwiseCaste(AssemblyConstituency,part_number)
    return [data,data1]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)