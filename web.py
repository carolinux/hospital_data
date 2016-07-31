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
        hospital_name = request.form.get('hospital_name')
        # remove the (number) at the end
        last_idx = hospital_name.rfind("(")
        hospital_name = hospital_name[:last_idx].strip()
        # TODO: placeholder - do something with the hospital name
        return "You searched for {}".format(hospital_name)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search_q = request.args.get('q').lower()
    results = filter(lambda x: x.lower().startswith(search_q), unique_names)
    return jsonify(matching_results=results)

hospitals = pd.read_csv("data/HCAHPS - Hospital.csv")
unique_names = get_unique_hospital_names(hospitals)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
