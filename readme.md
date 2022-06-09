## virtual environment
folder in production /home/train/fastapi_mlops

cd fastapi_mlops

use virtual environment fastapi-env

conda activate fastapi_env

## install requirements
check the requirements and pip install

pip install -r requirements.txt

## activate jupyter lab
assign kernel 

ipython kernel install --user --name=fastapi_env

activate jupyter lab, if you  want to test the ml models

jupyter lab --ip 0.0.0.0 --port 8990

## start mlflow, minio, mysql, gitea
cd /home/train/mlflow

docker-compose up -d

docker-compose ps
docker-compose stop prod test jenkins 

Check MLFlow web ui 
	http://localhost:5000/#/
		
Check minio web ui
    http://localhost:9001/#/

## local repo
\Repos\FastAPI_MLOps

## make the git setup 
git init
git clone

## Database connection
docker exec -it mlflow_db mysql -u mlops_user -p

Database engine mysql
Database        mlops
Database user   mlops_user

## activate uvicorn 
conda activate fastapi-env

ipython kernel install --user --name=fastapi-env (make this only first time)

jupyter lab --ip 0.0.0.0 --port 8990

## development structure

1. .env => connections
2. readme.md 
3. requirements.txt
4. schemas.py
5. database.py
6. models.py => change to dbmodels.py
7. churn_model => machine learning model
8. dockerfile => if we want to deploy from a docker container
9. Templates folder for web ui


