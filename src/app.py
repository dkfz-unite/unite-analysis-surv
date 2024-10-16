import argparse
import pandas as pd
from typing import Tuple
import os
import sys
from sksurv.nonparametric import kaplan_meier_estimator

def load_data(data_path : str) -> pd.DataFrame:
    """Reads a tsv file into a pandas.DataFrame

    :param data_path: path to the tsv file
    :type data_path: str
    :return: the dataframe
    :rtype: pd.DataFrame
    """
    data = pd.read_csv(data_path,sep="\t")
    return data

def get_survival_days_from_dates(data : pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """Get the number of days survival given the diagnosis date and the last follow up date.

    :param data: A pandas dataframe with the columns "diagnosis_date" and "vital_status_change_date"
    :type data: pd.DataFrame
    :return: A tuple with the survival days and a boolean series indicating if the calculation returned a not null value
    :rtype: Tuple[pd.Series, pd.Series]
    """
    
    diag_date = pd.to_datetime(data["diagnosis_date"])
    census_date = pd.to_datetime(data["vital_status_change_date"])
    survival_days = (census_date - diag_date).dt.days
    success=survival_days.isna()==False
    return survival_days, success

def get_survival_days_from_days(data : pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """Get the number of days survival given the number of days survival (specified exactly in the data frame

    :param data: A pandas dataframe with the column "vital_status_change_day"
    :type data: pd.DataFrame
    :return: A tuple with the survival days and a boolean series indicating if the number of days survival is not null
    :rtype: Tuple[pd.Series, pd.Series]
    """
    survival_days=data["vital_status_change_day"]
    survival_days.name="survival_days"
    survival_days=survival_days.astype(float)
    success=survival_days.isna()==False
    return survival_days, success

def get_survival_days(data : pd.DataFrame) -> pd.Series:
    """Get the number of days survival from the data frame.
    :param data: 
    :type data: pd.DataFrame
    :return: pd.DataFrame
    """
    # initialise data frame
    survival_days = pd.Series(index=range(len(data)),name="survival_days",dtype=float)
    # try to get survival days from the dates
    s1,success = get_survival_days_from_dates(data)
    
    survival_days[success]=s1[success]
    # if not possible, get survival days from the days
    survival_days[~success]= get_survival_days_from_days(data)[0][~success]
    return survival_days
    
def estimate_survival_function(survival : pd.Series, exit_status : pd.Series) -> pd.DataFrame:
    """Estimate the survival function and log-log confidence intervals using the Kaplan-Meier estimator

    :param survival: the number of days survival or until censoring
    :type survival: pd.Series
    :param exit_status: True if the patient died, False if the patient is still alive
    :type exit_status: pd.Series
    :return: A dataframe with the survival function (time x survival_prob) and the log-log confidence intervals
    :rtype: pd.DataFrame
    """
    time, survival_prob, conf_int = kaplan_meier_estimator(
    exit_status, survival, conf_type="log-log")
    survival_df = pd.DataFrame({
        'time': time,
        'survival_prob': survival_prob,
        'conf_int_lower': conf_int[0],
        'conf_int_upper': conf_int[1]
    })
    return survival_df

def get_censored_df(survival_days : pd.Series, exit_status : pd.Series, data : pd.DataFrame) -> pd.DataFrame:
    """Return a data frame containing the survival days of all censored patients (those who were still alive at last follow up)
    
    :param survival_days: the days survival of all patients
    :type survival_days: pd.Series
    :param exit_status: the exit status of all patients (True if dead, False if alive)
    :type exit_status: pd.Series
    :param data: the input data frame
    :type data: pd.DataFrame
    :return: a data frame containing the survival days of all censored patients. It will contain two columns 'sample_id' 'days_at_censoring'
    :rtype: pd.DataFrame
    """
    
    censored=exit_status==False
    sample_id=data["sample_id"][censored]
    days_at_censoring=survival_days[censored]
    censored_df=pd.DataFrame({"sample_id":sample_id,"days_at_censoring":days_at_censoring})
    return censored_df



def main(root_path : str):
    """Main function to estimate the survival function from the input data and write the result to a file result.tsv. Also writes censored.tsv which contains the survival days of all right censored patients.
    
    :param root_path: the path in which the input.tsv file is located and where the output files will be written
    :type root_path: str
    """
    data = load_data(os.path.join(root_path, "input.tsv"))  
    survival_days = get_survival_days(data)
    exit_status=data["vital_status"]==False #True if dead, False if alive
    output = estimate_survival_function(survival_days, exit_status)
    output_censored = get_censored_df(survival_days, exit_status, data)
    # write output to files
    output.to_csv(os.path.join(root_path,"result.tsv"), index=False,sep="\t")
    output_censored.to_csv(os.path.join(root_path,"censored.tsv"), index=False,sep="\t")
    print("Done")
    
if __name__ == "__main__":
    root_path = sys.argv[1]
    main(root_path)