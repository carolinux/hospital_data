import os

from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)


def get_unique_hospital_names(hospitals_df):
    # add provider name to the hospital name
    unique_names = hospitals_df.apply(lambda x: x["Hospital Name"]+" ("+str(x["Provider ID"])+")" , axis=1).unique()
    return sorted(unique_names)
    
@app.route('/search', methods=['GET', 'POST'])
def hospital_search():
    if request.method == "GET":
        return render_template('search.html')
    else:
        hospital_name_with_id = request.form.get('hospital_name')
        # remove the (number) at the end
        last_idx = hospital_name_with_id.rfind("(")
        hospital_name = hospital_name_with_id[:last_idx].strip()
        provider_id = int(hospital_name_with_id[last_idx+1: -1])
        rating = overall_ratings.ix[provider_id]
        return "Overall Hospital Rating  for {}: {}".format(hospital_name_with_id, rating)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_q = request.args.get('q').lower()
    results = filter(lambda x: x.lower().startswith(search_q), unique_names)
    return jsonify(matching_results=results)

hospitals = pd.read_csv("data/HCAHPS - Hospital.csv")
unique_names = get_unique_hospital_names(hospitals)
survey_fn = os.path.join('data', 'HCAHPS - Hospital.csv')
survey = pd.read_csv(survey_fn, engine="python")
overall_rating_question = 'Overall hospital rating - star rating'
rating_col = "Patient Survey Star Rating"
question_col = 'HCAHPS Question'
survey_overall = survey[survey[question_col]==overall_rating_question]
overall_ratings = survey_overall.groupby("Provider ID")[rating_col].min()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
