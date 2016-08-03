import os

from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__) # this creates an instance of the flask app


def get_unique_hospital_names(hospitals_df): # this is just a regular function
    # add provider name to the hospital name
    unique_names = hospitals_df.apply(lambda x: x["Hospital Name"]+" ("+str(x["Provider ID"])+")" , axis=1).unique()
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
        provider_id = int(hospital_name_with_id[last_idx+1: -1])
        rating = overall_ratings.ix[provider_id]
        summary = "<u>Overall Hospital Rating</u>  for {}: {}".format(hospital_name_with_id, rating)
        survey_of_hospital = survey[survey["Provider ID"] == provider_id][[question_col, rating_col]]
        survey_of_hospital = survey_of_hospital[survey_of_hospital[rating_col].isin(['1','2','3','4','5'])]
        survey_of_hospital[question_col] = survey_of_hospital[question_col].apply(lambda x: x.split(" - star")[0])
        survey_of_hospital.columns = [question_col, rating_col+" ( 1 to 5, higher is better)"]

        regular_questions = survey_of_hospital[(survey_of_hospital[question_col]!=overall_rating_question) &
                                             (survey_of_hospital[question_col]!='Summary star rating') ]
        summary_question = survey_of_hospital[survey_of_hospital[question_col]==overall_rating_question]
        summary_question[question_col] = summary_question[question_col].apply(lambda x:x.upper())
        #return summary + "<br>"+ survey_of_hospital.to_html()
        #return "<b>"+summary+"<b></br>"+regular_questions.to_html()
        return pd.concat([regular_questions, summary_question]).to_html(index=False)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_q = request.args.get('q').lower()
    results = filter(lambda x: x.lower().startswith(search_q), unique_names)
    return jsonify(matching_results=results)

print ("reading hospital data")
hospitals = pd.read_csv("data/HCAHPS - Hospital.csv", engine="python")
unique_names = get_unique_hospital_names(hospitals)
survey_fn = os.path.join('data', 'HCAHPS - Hospital.csv')
print ("reading survey data")
survey = pd.read_csv(survey_fn, engine="python")
overall_rating_question = 'Overall hospital rating - star rating'
rating_col = "Patient Survey Star Rating"
question_col = 'HCAHPS Question'
print ("getting ratings")
survey_overall = survey[survey[question_col]==overall_rating_question] # select only the question of 'overall hospital rating'
# find the rating per provider id
overall_ratings = survey_overall.groupby("Provider ID")[rating_col].min()
print ("loaded everything")

if __name__ == '__main__':
    print ("starting webserver")
    app.run(port=5000, debug=True)
