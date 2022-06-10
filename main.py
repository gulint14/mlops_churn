from pickle import TRUE
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from requests import request
from schemas import CustomerInfo, ChurnDriftInput
import os
from sqlalchemy.orm import Session
from mlflow.sklearn import load_model
from scipy.stats import ks_2samp
import joblib
import models
from database import engine, get_db
from sqlalchemy.orm import Session
import pandas as pd

import json
import sys
import random
import requests

# Tell where is the tracking server and artifact server
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:5000/'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000/'

# Learn, decide and get model from mlflow model registry
model_name = "ChurnKNNModel"
model_version = 3
model = load_model(
    model_uri=f"models:/{model_name}/{model_version}"
)

# Read models saved during train phase
encoderGeo = joblib.load("SavedModels/geography_encoder.pkl")
encoderGender = joblib.load("SavedModels/gender_encoder.pkl")

# Creates all the tables defined in models module
models.Base.metadata.create_all(bind=engine)

customer_raw = pd.read_csv("https://raw.githubusercontent.com/erkansirin78/datasets/master/Churn_Modelling.csv")

customer_raw.to_sql('customer_churn_original', con=engine, index=False, if_exists='replace')

templates = Jinja2Templates(directory="Templates")

# Object agnostic drift detection function
def detect_drift(data1, data2, feature, db):

    ks_result = ks_2samp(data1, data2)

    if ks_result.pvalue < 0.05:
       drifttext =  "Drift exits"
       driftstatus = 1
    else:
        drifttext =  "No drift"
        driftstatus = 0

    new_driftlog = models.Customer_Churn_DriftLog(

        feature = feature,
        driftstatus = driftstatus,
        drifttext = drifttext

    )

    db.add(new_driftlog)
    db.commit()
    db.refresh(new_driftlog)
    return new_driftlog

def notify_slack ():
    if TRUE:

        url = "https://hooks.slack.com/services/***********/***********/************************"
        message = ("Drift, drift, drift from API !!! https://app.powerbi.com/links/Q91yrA_uu0?ctid=650a51da-7183-45bb-afbb-915d8a85b460&pbi_source=linkShare&bookmarkGuid=1d644f5e-2a1a-45b1-82e6-088914f089e3")
        title = (f"Drift Alert :zap:")
        slack_data = {
            "username": "driftBot",
            "icon_emoji": ":satellite:",
            "channel": "#mlops-drift",
            "attachments": [
                {
                    "color": "#9733EE",
                    "fields": [
                        {
                            "title": title,
                            "value": message,
                            "short": "false",
                        }
                    ]
                }
            ]
        }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    response = requests.post(url, data=json.dumps(slack_data), headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.status_code


def insert_customer_churn(request, prediction, client_ip, db):
    new_prediction = models.Customer_Churn(

        CreditScore = request["CreditScore"],
        Geography = encoderGeo.transform([[request["Geography"]]]).tolist(),
        Gender = encoderGender.transform([[request["Gender"]]]).tolist(),
        Age = request["Age"],
        Tenure = request["Tenure"],
        Balance = request["Balance"],
        NumOfProducts = request["NumOfProducts"],
        HasCrCard = request["HasCrCard"],
        IsActiveMember = request["IsActiveMember"],
        EstimatedSalary = request["EstimatedSalary"],
        prediction=prediction,
        client_ip=client_ip
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)
    return new_prediction

app = FastAPI()

# Note that model is coming from mlflow
def make_churn_prediction(model, encoderGeo, encoderGender,  request):
    # parse input from request
    CreditScore = request["CreditScore"]
    
    Geography = encoderGeo.transform([[request["Geography"]]])
    Gender = encoderGender.transform([[request["Gender"]]])
    Age = request["Age"]
    Tenure = request["Tenure"]
    Balance = request["Balance"]
    NumOfProducts = request["NumOfProducts"]
    HasCrCard = request["HasCrCard"]
    IsActiveMember = request["IsActiveMember"]
    EstimatedSalary = request["EstimatedSalary"]

    # Make an input vector
    CustomerInfo = [[CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember,EstimatedSalary ]]

    # Predict
    prediction = model.predict(CustomerInfo)

    return prediction[0]

# Customer churn Prediction endpoint
@app.post("/Prediction/CustomerChurn")
async def predict_customerchurn(request: CustomerInfo, fastapi_req: Request,  db: Session = Depends(get_db)):
    prediction = make_churn_prediction(model, encoderGeo, encoderGender, request.dict())
    db_insert_record = insert_customer_churn(request=request.dict(), prediction=prediction,
                                          client_ip=fastapi_req.client.host,
                                          db=db)

    return {"Prediction": prediction.tolist(), "db_record": db_insert_record} 

@app.get("/")
async def home(request: Request):
    #return {"data":"Welcome to Customer Churn Prediction"}
    return templates.TemplateResponse("home.html", {"request":request})


@app.get("/drift")
async def home(request: Request, db: Session = Depends(get_db)):
    #return {"data":"Welcome to Customer Churn Prediction"}
    driftlog = db.query(models.driftstatus).all()
    
    return templates.TemplateResponse("index.html", {
        "request":request,
        "driftlog":driftlog
    })


# Advertising drift detection endpoint
@app.post("/drift/churn")

async def detect(request: ChurnDriftInput, db: Session = Depends(get_db)):
    # Select training data
    train_df =  pd.read_sql("select * from customer_churn_original", engine)

    # Select predicted data last n days
    prediction_df = pd.read_sql(f"""select * from customer_churn 
                                    where prediction_time >
                                    current_date - {request.n_days_before}""",
                                engine)


    creditscore_drift = detect_drift(train_df.CreditScore, prediction_df.CreditScore, "CreditScore", db)
    #geography = detect_drift(train_df.Geography, prediction_df.Geography, "Geography", db)
    #gender_drift = detect_drift(train_df.Gender, prediction_df.Gender, "Gender", db)
    age_drift = detect_drift(train_df.Age, prediction_df.Age, "Age", db)
    tenure_drift = detect_drift(train_df.Tenure, prediction_df.Tenure, "Tenure", db)
    balance_drift = detect_drift(train_df.Balance, prediction_df.Balance, "Balance", db)
    numofproducts_drift = detect_drift(train_df.NumOfProducts, prediction_df.NumOfProducts, "NumOfProducts", db)
    hascrcard_drift = detect_drift(train_df.HasCrCard, prediction_df.HasCrCard, "HasCrCard", db)
    isactivemember_drift = detect_drift(train_df.IsActiveMember, prediction_df.IsActiveMember, "IsActiveMember", db)
    estimatedsalary_drift = detect_drift(train_df.EstimatedSalary, prediction_df.EstimatedSalary, "EstimatedSalary", db)


    #return {"gender_drift": gender_drift, "estimatedsalary_drift": estimatedsalary_drift}

    response_status = notify_slack()

    print(response_status)
    return {
        "credit score drift": creditscore_drift,
        #"geography drift": geography_drift, "gender drift": gender_drift,
        "age drift": age_drift,
        "tenure drift": tenure_drift,
        "balance drift": balance_drift,
        "numofproducts drift": numofproducts_drift,
        "hascrcard drift": hascrcard_drift,
        "isactivemember drift": isactivemember_drift,
        "estimatedsalary_drift": estimatedsalary_drift}


@app.get("/drift/churn")

async def filter_driftlog(db: Session = Depends(get_db)):
    #driftlog = db.query(models.Customer_Churn_DriftLog).limit(20).all()
    #driftlog = db.query(models.driftcount).limit(20).all()
    driftlog = db.query(models.driftstatus).limit(20).all()
    #customer = db.query(models.Customer).filter(models.Customer.customerCity == city).first()

    if not driftlog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"There is no drift log") 

    return driftlog
