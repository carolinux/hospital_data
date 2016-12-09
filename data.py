__author__ = 'carolinux'

import json
import os
import requests

import pandas as pd

def to_capitals(pythoncase_str):
    return pythoncase_str.replace("_", " ").capitalize()


class HospitalData(object):

    score_forms = {"Readmissions_Reduction": "kac9-a9fp", # Hospital Readmissions Reduction Program
    "Complications": "r32h-32z5", # Complications - Hospital,
    "Healthcare_Associated_Infections": "ppaw-hhm5", # Healthcare Associated Infections - Hospital
    "Timely and Effective Care": "3z8n-wcgr", # Timely and Effective Care - Hospital
    "Medicare Spending Per Patient": "9i85-rqbi" # Medicare Hospital Spending Per Patient - Hospital
    }
    get_less_data = True
    HCAPS_ID = "dgck-syfz"
    HOSPITAL_DATA_ID = "rbry-mqwu"

    overall_rating_question = 'Overall hospital rating - star rating'
    rating_col = "patient_survey_star_rating" # before it was like Patient Survey Star Rating
    question_col = 'hcahps_question'
    unique_names = None

    def __init__(self, get_less_data=False):

        self.score_data = {}
        for score_type, form_id in self.score_forms.items():
            data = self.get_hospital_data_from_web(form_id, do_filter=get_less_data)
            data = data.set_index("provider_id", drop=False)
            self.score_data[score_type] = data

        print("getting hospital data")
        self.hospitals = self.get_hospital_data_from_web(self.HOSPITAL_DATA_ID, do_filter=get_less_data)
        self.unique_names = self.get_unique_hospital_names()
        print ("getting survey data")
        self.survey = self.get_hospital_data_from_web(self.HCAPS_ID, do_filter=get_less_data)


        print ("getting ratings")
        self.survey_overall = self.survey[self.survey[self.question_col]==self.overall_rating_question] # select only
        # the
        # question of 'overall hospital rating'
        # find the rating per provider id
        self.overall_ratings = self.survey_overall.groupby("provider_id")[self.rating_col].min()
        print ("loaded everything")

    def get_all_ratings_for_provider_id(self, provider_id):
        """Get a dataframe with the ratings for a provider id """

        survey_of_hospital = self.survey[self.survey["provider_id"] == provider_id][[self.question_col,
                                                                                     self.rating_col]]
        survey_of_hospital = survey_of_hospital[survey_of_hospital[self.rating_col].isin(
            ['1', '2', '3', '4', '5'])]
        survey_of_hospital[self.question_col] = survey_of_hospital[self.question_col].apply(lambda x: x.split(" - "
                                                                                                            "star")[0])
        survey_of_hospital.columns = [self.question_col, self.rating_col+" ( one to five stars, higher is better)"]

        regular_questions = survey_of_hospital[(survey_of_hospital[self.question_col]!=self.overall_rating_question) &
                                             (survey_of_hospital[self.question_col]!='summary_star_rating') ]
        summary_question = survey_of_hospital[survey_of_hospital[self.question_col]==self.overall_rating_question]
        summary_question[self.question_col] = summary_question[self.question_col].apply(lambda x: x.upper())
        ratings = pd.concat([regular_questions, summary_question])
        ratings.columns = map(to_capitals, ratings.columns)
        # convert to actual stars
        new_rating_col = ratings.columns[1]
        ratings[new_rating_col] = ratings[new_rating_col].apply(lambda x: ''.join(int(x) *['*']))
        return ratings

    def get_hospital_data(self, provider_id):
        return self.hospitals[self.hospitals["provider_id"] == provider_id].iloc[0] # the data for this hospital

    def get_hospital_data_from_web(self, data_id, do_filter=False):
        """Gets the data from the json API and returns it as a dataframe"""
        resource_url = "https://data.medicare.gov/resource/{}.json".format(data_id)
        token = "bjp8KrRvAPtuf809u1UXnI0Z8" # test token
        #token = "UKABSmwwYK2lyRyiKYHDn2V9c" # adelard's token
        print ("querying for hospital data")
        if do_filter:
            # get only some data
            resource_url +="?$where=starts_with(hospital_name,'SOUTH')"
        resp = requests.get(resource_url, headers={"X-App-Token": token}, verify=False)
        results = json.loads(resp.text)
        df = pd.DataFrame.from_records(results)
        return df


    def get_unique_hospital_names(self):
        """Get unique hospital names (together with provider id """
        # add provider name to the hospital name
        if self.unique_names is None:
            unique_names = self.hospitals.apply(lambda x: x["hospital_name"]+" ("+str(x["provider_id"])+")" ,
                                         axis=1).unique()
            self.unique_names = sorted(unique_names)

        return self.unique_names

    def get_measure_scores(self, provider_id):
        """
         Get all the score data
        """
        measures = []
        for form_name, data in self.score_data.items():
            if "Readmissions" in form_name:
                continue
            try:
                data = data.ix[provider_id]
                if isinstance(data, pd.Series):
                    measures.append((form_name + ": " + data["measure_name"], data["score"]))
                else:
                    for _, row in data.iterrows():
                        measures.append((form_name + ":" + row["measure_name"], row["score"]))
            except KeyError:
                print ("Provider id {} has not data in {}".format(provider_id, form_name))
        return measures




