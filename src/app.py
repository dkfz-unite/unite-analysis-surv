import argparse
import pandas as pd
import numpy as np
from typing import Tuple
import os
import sys
import json
from sksurv.nonparametric import kaplan_meier_estimator
from sksurv.compare import compare_survival

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

    :param data: A pandas dataframe with the columns "diagnosis_date" and "vital_status_change_date" or "progression_status_change_date"
    :type data: pd.DataFrame
    :return: A tuple with the survival days and a boolean series indicating if the calculation returned a not null value
    :rtype: Tuple[pd.Series, pd.Series]
    """

    
    diag_date = pd.to_datetime(data["diagnosis_date"])
    census_date = pd.to_datetime(data["status_change_date"])
    survival_days = (census_date - diag_date).dt.days
    success=survival_days.isna()==False
    return survival_days, success

def get_survival_days_from_days(data : pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """Get the number of days survival given the number of days survival (specified exactly in the data frame

    :param data: A pandas dataframe with the column "vital_status_change_day" or "progression_status_change_day"
    :type data: pd.DataFrame
    :rtype: Tuple[pd.Series, pd.Series]
    """
    
    survival_days=data["status_change_day"]
    survival_days.name="survival_days"
    survival_days=survival_days.astype(float)
    success=survival_days.isna()==False
    return survival_days, success


def get_survival_days(data : pd.DataFrame) -> pd.Series:
    """Get the number of days survival from the data frame.
    
    :param data: the input data frame
    :return: pd.DataFrame
    """
    

    # initialise data frame
    survival_days = pd.Series(index=range(len(data)),name="survival_days",dtype=float)
    # try to get survival days from the dates
    s1,success = get_survival_days_from_dates(data)
    survival_days.iloc[np.array(success)]=s1.iloc[np.array(success)]
    # if not possible, get survival days from the days
    survival_days.iloc[np.array(~success)]= get_survival_days_from_days(data)[0].iloc[np.array(~success)]
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
    
    # add point to the beginning (for plotting) representing the time 0
    time = np.concatenate([[0], time])
    survival_prob = np.concatenate([[1], survival_prob])
    conf_int = np.concatenate([np.array([[1],[1]]), conf_int],axis=1)
    survival_df = pd.DataFrame({
        'time': time,
        'survival_prob': survival_prob,
        'conf_int_lower': conf_int[0],
        'conf_int_upper': conf_int[1]
    })
    return survival_df

def get_censored_df(survival_days : pd.Series, exit_status : pd.Series, ids : pd.Series) -> pd.DataFrame:
    """Return a data frame containing the survival days of all censored patients (those who were still alive at last follow up)
    
    :param survival_days: the days survival of all patients
    :type survival_days: pd.Series
    :param exit_status: the exit status of all patients (True if dead, False if alive)
    :type exit_status: pd.Series
    :param ids: the ids of the patients
    :type ids: pd.DataFrame
    :return: a data frame containing the survival days of all censored patients. It will contain two columns 'sample_id' 'days_at_censoring'
    :rtype: pd.DataFrame
    """
    
    censored=exit_status==False
    sample_id=ids[censored]
    days_at_censoring=survival_days.iloc[np.array(censored)]
    censored_df=pd.DataFrame({"sample_id":sample_id,"days_at_censoring":days_at_censoring})
    return censored_df

def get_exit_status(data : pd.DataFrame,type : str) -> pd.Series:
    """Get the exit status of all patients. If type is "survival" this should be true if they are dead and false if they are alive. If type is "progression" this should be true if they have progressed and false if they have not.

    :param data: the input data frame
    :type data: pd.DataFrame
    :param type: the type of survival days. This can be either "progression" for progression free survival or "survival" for overall survival
    :return: a boolean series indicating if the patient died
    :rtype: pd.Series
    """
    # check type value
    if type not in ["progression","survival"]:
        raise ValueError(f"Type {type} not in ['progression','survival']")
    
    if type == "survival":
        return data["status"]==False
    
    if type == "progression":
        return data["status"]==True


def get_labels(data : pd.DataFrame) -> pd.Series:
    """Get the labels of the groups in the data frame

    :param data: the input data frame
    :type data: pd.DataFrame
    :return: a series with the labels
    :rtype: pd.Series
    """
    if "label" not in data.columns:
        return pd.Series(np.zeros(len(data),dtype=int),dtype=str)
    return data["label"]

def get_subsets(data : pd.DataFrame,label : pd.Series) -> list:
    """Get the subsets of the data frame for each label
    
    :param data: the input data frame
    :type data: pd.DataFrame
    """
    return [data.iloc[np.array(label==l),:] for l in label.unique()],label.unique()

def get_survival_function_and_censored_dfs(survival_days : pd.Series,exit_status : pd.Series,ids : pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get the survival function and censored data frame from the survival days and exit status

    :param survival_days: the number of days survival
    :type survival_days: pd.Series
    :param exit_status: the exit status of the patients
    :type exit_status: pd.Series
    :param ids: the ids of the patients
    :type data: pd.DataFrame
    :return: a tuple with the survival function and the censored data frame
    :rtype: Tuple[pd.DataFrame, pd.DataFrame
    
    """
    output = estimate_survival_function(survival_days, exit_status)
    output_censored = get_censored_df(survival_days, exit_status, ids)
    return output, output_censored


def logrank_test(survival_days : pd.Series,exit_status : pd.Series,label : pd.Series) -> pd.DataFrame:
    """Perform the logrank test comparing the survival curves of two or more groups

    :param survival_days: the number of days survival
    :type survival_days: pd.Series
    :param exit_status: the exit status of the patients
    :type exit_status: pd.Series
    :param label: the labels of the groups
    :type label: pd.Series
    :return: a data frame with the chi2 and p values of the logrank test
    :rtype: pd.DataFrame
    """
    # crate a structured array with the survival days and exit status
    survival_data = np.zeros(len(survival_days), dtype=[('status', bool), ('time', float)])
    survival_data['status'] = exit_status
    survival_data['time'] = survival_days
    chi2, p = compare_survival(survival_data, label)   
    return pd.DataFrame({"chi2":chi2,"p":p},index=["logrank_test"]) 

def concatenate_dfs_add_label(dfs : list,label : str) -> pd.DataFrame:
    """Concatenate a list of data frames and add a column with the label

    :param dfs: a list of data frames
    :type dfs: list
    :param label: the label to add to the data frames
    :type label: str
    :return: a data frame with the data frames concatenated and the label column added
    :rtype: pd.DataFrame
    """
    for i,df in enumerate(dfs):
        df["label"]=label[i]
    return pd.concat(dfs,ignore_index=True)


def read_options_file(root_path : str) -> dict:
    # read the options from the options file
    with open(os.path.join(root_path,"options.json"), 'r') as f:
        config = json.load(f)
    
    # Get the type of survival days to get from the JSON file
    mode = config.get("mode")
    assert mode in ["progression","survival"], "mode must be either 'progression' or 'survival'"
    return {'mode':mode}
    
def main(root_path : str):
    """Main function to estimate the survival functions from the input data and write the result to a file result.tsv. Also writes censored.tsv which contains the survival days of all right censored patients.
    Does this separately for each group label in the input data (in the "label") column.
    
    :param type: the type of survival days to get. This can be either "progress" for progression free survival or "vital" for overall survival
    :type root_path: str
    """
    # load the data
    data = load_data(os.path.join(root_path,"input.tsv"))
    opts = read_options_file(root_path)
    mode = opts["mode"]
    
    # get the labels of the groups
    label = get_labels(data)
    # get the data subsetted by label
    subsets,unique_labels = get_subsets(data,label)
    
    # get the survival days and exit status (event binary indicator) for each group
    survival_days = [get_survival_days(subset) for subset in subsets]
    exit_status = [get_exit_status(subset,mode) for subset in subsets]
    
    # get the survival function and censored data data frame for each group
    survival_functions, censored_dfs = zip(*[get_survival_function_and_censored_dfs(s,e,d.sample_id) for s,e,d in zip(survival_days,exit_status,subsets)])    
    
    # write the survival functions to a file
    survival_functions_df = concatenate_dfs_add_label(survival_functions,unique_labels)
    survival_functions_df.to_csv(os.path.join(root_path,"result.tsv"), sep="\t", index=False)
    
    # write the censored data to a file
    censored_df = concatenate_dfs_add_label(censored_dfs,unique_labels)
    censored_df.to_csv(os.path.join(root_path,"censored.tsv"), sep="\t", index=False)
       
    # perform the logrank test if there is more than one group
    if len(unique_labels) > 1:
        logrank = logrank_test(pd.concat(survival_days),pd.concat(exit_status),label)
        logrank.to_csv(os.path.join(root_path,"logrank_test.tsv"), sep="\t", index=False)
    

if __name__ == "__main__":
    root_path = sys.argv[1]
    main(root_path)
