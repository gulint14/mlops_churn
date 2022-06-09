from database import Base
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func

class Customer_Churn(Base):
    __tablename__ = "customer_churn"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer, autoincrement=True, primary_key=True)
    CreditScore = Column(Float)
    Geography = Column(Integer)
    Gender = Column(Integer)
    Age = Column(Float)
    Tenure = Column(Float)
    Balance = Column(Float)
    NumOfProducts = Column(Float)
    HasCrCard = Column(Float)
    IsActiveMember = Column(Float)
    EstimatedSalary = Column(Float)
    prediction = Column(Integer)
    prediction_time = Column(DateTime(timezone=True), server_default=func.now())
    client_ip = Column(String(20))

class Customer_Churn_Original(Base):
    __tablename__ = "customer_churn_original"
    __table_args__ = {'extend_existing': True}

    RowNumber = Column(Integer, autoincrement=True, primary_key=True)
    CustomerId = Column(String(20))
    Surname = Column(String(100))
    CreditScore = Column(Float)
    Geography = Column(Integer)
    Gender = Column(Integer)
    Age = Column(Float)
    Tenure = Column(Float)
    Balance = Column(Float)
    NumOfProducts = Column(Float)
    HasCrCard = Column(Float)
    IsActiveMember = Column(Float)
    EstimatedSalary = Column(Float)
    Exited = Column(Integer)

class Customer_Churn_DriftLog(Base):
    __tablename__ = "customer_churn_driftlog"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer, autoincrement=True, primary_key=True)
    logdate = Column(DateTime(timezone=True), server_default=func.now())
    feature = Column(String(30))
    driftstatus = Column(Integer)
    drifttext = Column(String(30))


class driftcount(Base):
    __tablename__ = "driftcount"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, autoincrement=True, primary_key=True)
    feature = Column(String(30))
    driftcount = Column(Integer)

class driftstatus(Base):
    __tablename__ = "driftstatus"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, autoincrement=True, primary_key=True)
    feature = Column(String(30))
    driftstatus = Column(Integer)