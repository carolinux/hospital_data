import json
import os
import requests

from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__) # this creates an instance of the flask app


def get_unique_hospital_names(hospitals_df): # this is just a regular function
    # add provider name to the hospital name
    unique_names = hospitals_df.apply(lambda x: x["hospital_name"]+" ("+str(x["provider_id"])+")" , axis=1).unique()
    return sorted(unique_names)

#@app.route('/')
#def hello():
#    return "Hello world"
    
@app.route('/search', methods=['GET', 'POST']) # when I go to the url/search, return whatever this function returns
def hospital_search():
    if request.method == "GET":
        return render_template('search.html') # this renders the form with the autocomplete
    else:
        # here is what happens when the search form is submitted
        # this is where we get the rating
        hospital_name_with_id = request.form.get('hospital_name')
        # remove the (number) at the end
        last_idx = hospital_name_with_id.rfind("(")
        hospital_name = hospital_name_with_id[:last_idx].strip()
        provider_id = str(hospital_name_with_id[last_idx+1: -1])
        rating = overall_ratings.ix[provider_id]
        summary = "<u>Overall Hospital Rating</u>  for {}: {}".format(hospital_name_with_id, rating)
        survey_of_hospital = survey[survey["provider_id"] == provider_id][[question_col, rating_col]]
        survey_of_hospital = survey_of_hospital[survey_of_hospital[rating_col].isin(['1','2','3','4','5'])]
        survey_of_hospital[question_col] = survey_of_hospital[question_col].apply(lambda x: x.split(" - star")[0])
        survey_of_hospital.columns = [question_col, rating_col+" ( 1 to 5, higher is better)"]

        regular_questions = survey_of_hospital[(survey_of_hospital[question_col]!=overall_rating_question) &
                                             (survey_of_hospital[question_col]!='summary_star_rating') ]
        summary_question = survey_of_hospital[survey_of_hospital[question_col]==overall_rating_question]
        summary_question[question_col] = summary_question[question_col].apply(lambda x:x.upper())
        #return summary + "<br>"+ survey_of_hospital.to_html()
        #return "<b>"+summary+"<b></br>"+regular_questions.to_html()
        return pd.concat([regular_questions, summary_question]).to_html(index=False)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_q = request.args.get('q').lower()
    results = list(filter(lambda x: x.lower().startswith(search_q), unique_names))
    return jsonify(matching_results=results)

def get_hospital_data_from_web(data_id,do_filter=False):
    resource_url = "https://data.medicare.gov/resource/rmgi-5fhi.json"
    token = "bjp8KrRvAPtuf809u1UXnI0Z8" # TODO: replace with our own token, this is a test one from the website
    print ("querying for hospital data")
    if do_filter:
        # get only some data
        resource_url +="?$where=starts_with(hospital_name,'SOUTH')"
    resp = requests.get(resource_url, headers={"X-App-Token": token})
    results = json.loads(resp.text)
    df = pd.DataFrame.from_records(results)
    return df


print("getting hospital data")
HCAPS_ID = "dgck-syfz"
HOSPITAL_DATA_ID = "xubh-q36u"
get_less_data = True
hospitals = get_hospital_data_from_web(HOSPITAL_DATA_ID, do_filter=get_less_data)
unique_names = get_unique_hospital_names(hospitals)
print ("getting survey data")
survey = get_hospital_data_from_web(HCAPS_ID, do_filter=get_less_data)
overall_rating_question = 'Overall hospital rating - star rating'
rating_col = "patient_survey_star_rating"
question_col = 'hcahps_question'
print ("getting ratings")
survey_overall = survey[survey[question_col]==overall_rating_question] # select only the question of 'overall hospital rating'
# find the rating per provider id
overall_ratings = survey_overall.groupby("provider_id")[rating_col].min()
print ("loaded everything")

if __name__ == '__main__':
    print ("starting webserver")
    app.run(port=5000, debug=True)
