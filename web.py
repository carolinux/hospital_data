import sys

from flask import Flask, request, jsonify, render_template
import pandas as pd

import data

app = Flask(__name__) # this creates an instance of the flask app

cache = {}

@app.route('/search', methods=['GET', 'POST']) # when I go to the url/search, return whatever this function returns
def hospital_search():
    if request.method == "GET":
        return render_template('search.html') # this renders the form with the autocomplete
    else:
        d = cache["data"]
        # here is what happens when the search form is submitted
        # this is where we get the rating
        hospital_name_with_id = request.form.get('hospital_name')
        # remove the (number) at the end
        last_idx = hospital_name_with_id.rfind("(")
        hospital_name = hospital_name_with_id[:last_idx].strip()
        provider_id = str(hospital_name_with_id[last_idx+1: -1])

        measures = d.get_measure_scores(provider_id)
        ratings = d.get_all_ratings_for_provider_id(provider_id)

        hospital_data = d.get_hospital_data(provider_id)
        longitude = hospital_data["location"]["coordinates"][0]
        latitude = hospital_data["location"]["coordinates"][1]

        return render_template("map.html", summary_data=hospital_data,
                ratings=ratings, longitude=longitude,
                latitude=latitude, measures=measures)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_q = request.args.get('q').lower()
    results = list(filter(lambda x: x.lower().startswith(search_q), cache["data"].get_unique_hospital_names()))
    return jsonify(matching_results=results)


if __name__ == '__main__':
    print ("starting webserver")
    if len(sys.argv)==2:
        is_test = sys.argv[1] == 'test'
    else:
        is_test = False
    cache["data"] = data.HospitalData(get_less_data=is_test)
    app.run(port=5000, debug=True, processes=1)
