import pytest
import pandas as pd
import sys
sys.path.append("./src")
from app import estimate_survival_function
import pytest
from unittest.mock import patch
import pandas as pd
from app import read_options_file,get_survival_days_from_dates, get_survival_days_from_days, get_survival_days, load_data, get_censored_df, get_exit_status, get_labels,get_subsets,  logrank_test, main
import numpy as np
import os
from collections import Counter

@pytest.fixture
def mock_survival_data():
    survival = pd.Series([5, 10, 15, 20, 25])
    exit_status = pd.Series([True, False, True, False, True])
    label = pd.Series(["A", "B", "A", "B", "A"])
    return survival, exit_status,label

@pytest.fixture
def mock_data_df():
    data = pd.DataFrame({
        "diagnosis_date": ["2020-01-01", "2020-02-01", "2020-03-01"],
        "status_change_date": ["2020-01-10", None, "2020-03-15"],
        "status_change_day": [9, 20, 14],
        "status": [False, True, False],
        "label": ["A", "B", "A"],
        "sample_id": ["1", "2", "3"]
    })
    return data
@pytest.fixture
def mock_data_df_truncated(mock_data_df):
    data = mock_data_df.copy()
    data = data[[True, False, True]]
    return data


def test_load_data():
     data = load_data("test/data/input.tsv")
    
     # Check if the result is a DataFrame
     assert isinstance(data, pd.DataFrame)
    
     # Check if the DataFrame is not empty
     assert not data.empty
     # Check if the DataFrame has the correct number of columns
     assert len(data.columns) == 6
     # Check if the DataFrame has the correct columns
     expected_columns = ["sample_id","diagnosis_date","status","status_change_date","status_change_day","label"]
     assert list(data.columns) == expected_columns

def test_get_labels(mock_data_df):
    """ test the labels column is returned or a series of 0s if the column is not present"""
    assert get_labels(mock_data_df).equals(pd.Series(["A", "B", "A"]))
    # remove the label column
    mock_data_df.drop("label", axis=1, inplace=True)
    assert get_labels(mock_data_df).equals(pd.Series(["0", "0", "0"]))


def test_get_subsets(mock_data_df):
    """ test the subsets of the data are returned """
    labels = mock_data_df.label
    subsets,unique_labels = get_subsets(mock_data_df,labels)
    
    # check out put is a list of dataframes
    assert isinstance(subsets,list)
    assert all(isinstance(subset,pd.DataFrame) for subset in subsets)
    # check the subsets are as expected
    assert subsets[0].equals(mock_data_df.iloc[np.array(mock_data_df.label=="A"),:])
    assert subsets[1].equals(mock_data_df.iloc[np.array(mock_data_df.label=="B"),:])
    # check the unique labels are as expected
    assert Counter(unique_labels) == Counter(["A","B"])
    
def test_get_survival_days_from_dates(mock_data_df):
    survival_days, success = get_survival_days_from_dates(mock_data_df)
    
    # Check if the result is a Series
    assert isinstance(survival_days, pd.Series)
    assert isinstance(success, pd.Series)
    
    # Check if the Series has the correct values
    expected_survival_days = pd.Series([9, None, 14])
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
    
    # Check if the success Series has the correct values
    expected_success = pd.Series([ True,False,True])
    pd.testing.assert_series_equal(success, expected_success)
    
    # try on truncated data
    trunc_data = mock_data_df.copy()
    trunc_data = trunc_data.iloc[[False, True, True],:]
    survival_days, success = get_survival_days_from_dates(trunc_data)
    expected_survival_days = pd.Series([None, 14],index=[1,2])
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
    expected_success = pd.Series([False, True],index=[1,2])
    pd.testing.assert_series_equal(success, expected_success)

def test_get_survival_days_from_days(mock_data_df):
    survival_days, success = get_survival_days_from_days(mock_data_df)
    
    # Check if the result is a Series
    assert isinstance(survival_days, pd.Series)
    assert isinstance(success, pd.Series)
    
    # Check if the Series has the correct values
    expected_survival_days = pd.Series([9, 20, 14],name="survival_days",dtype=float)
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
    
    # Check if the success Series has the correct values
    expected_success = pd.Series([True, True, True],name="survival_days")
    pd.testing.assert_series_equal(success, expected_success)
    
    # try on truncated data (i.e. after subsetting)
    trunc_data = mock_data_df.copy()
    trunc_data = trunc_data.iloc[[False, True, True],:]
    survival_days, success = get_survival_days_from_days(trunc_data)
    expected_survival_days = pd.Series([20, 14],index=[1,2],name="survival_days",dtype=float)
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
    expected_success = pd.Series([True, True],index=[1,2],name="survival_days")


def test_get_survival_days(mock_data_df):

    survival_days = get_survival_days(mock_data_df)
    
    # Check if the result is a Series
    assert isinstance(survival_days, pd.Series)
    
    # Check if the Series has the correct values
    expected_survival_days = pd.Series([9, 20, 14],name="survival_days",dtype=float)
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
     
    # try on truncated data (i.e. after subsetting)
    trunc_data = mock_data_df.copy()
    survival_days = get_survival_days(trunc_data)
    expected_survival_days = pd.Series([20, 14],index=[1,2],name="survival_days",dtype=float)

@pytest.mark.parametrize("type", ["progression", "survival"])
def test_get_exit_status(mock_data_df,type):
    exit_status = get_exit_status(mock_data_df,type)
    
    # Check if the result is a Series
    assert isinstance(exit_status, pd.Series)
    
    # Check if the Series has the correct values
    if type == "progression":
        expected_exit_status = pd.Series([False, True, False],name="status",dtype=bool)
    if type == "survival":
        expected_exit_status = pd.Series([True, False, True],name="status",dtype=bool)
    pd.testing.assert_series_equal(exit_status, expected_exit_status)
    


def test_estimate_survival_function(mock_survival_data):
    survival, exit_status,_ = mock_survival_data
    result = estimate_survival_function(survival, exit_status)
    
    # Check if the result is a DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Check if the DataFrame has the correct columns
    expected_columns = ['time', 'survival_prob', 'conf_int_lower', 'conf_int_upper']
    assert list(result.columns) == expected_columns
    # Check if the DataFrame is not empty
    assert not result.empty
    # Check if the DataFrame has the correct number of rows
    assert len(result) == (len(survival.unique())+1)

# test for get_censored_df
@pytest.fixture
def mock_data_for_censored():
    survival_days = pd.Series([5, 10, 15, 20, 25])
    exit_status = pd.Series([True, False, True, False, True])
    data = pd.DataFrame({
        "sample_id": ["A", "B", "C", "D", "E"]
    })
    return survival_days, exit_status, data

def test_get_censored_df(mock_data_for_censored):
    survival_days, exit_status, data = mock_data_for_censored
    result = get_censored_df(survival_days, exit_status, data.sample_id)
    
    # Check if the result is a DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Check if the DataFrame has the correct columns
    expected_columns = ["sample_id", "days_at_censoring"]
    assert list(result.columns) == expected_columns
    
    # Check if the DataFrame has the correct values
    expected_data = pd.DataFrame({
        "sample_id": ["B", "D"],
        "days_at_censoring": [10, 20]
    }, index=[1, 3])
    pd.testing.assert_frame_equal(result, expected_data)

@pytest.fixture
def mode():
    return "progression"

#@pytest.mark.parametrize("mode", ["progression", "survival"])
@patch("app.read_options_file")
@patch("app.load_data")
@patch("app.get_labels")
@patch("app.get_subsets")
@patch("app.get_survival_days")
@patch("app.get_exit_status")
@patch("app.get_survival_function_and_censored_dfs")
@patch("app.logrank_test")
@patch("app.pd.DataFrame.to_csv")
def test_main(mock_to_csv, mock_logrank_test, mock_get_survival_function_and_censored_dfs, mock_get_exit_status, mock_get_survival_days, mock_get_subsets, mock_get_labels, mock_load_data,mock_read_options_file, mock_data_df, tmp_path,mode):
    # Mock the load_data function to return the mock data
    mock_load_data.return_value = mock_data_df

    # Mock the get_labels function to return the labels
    mock_get_labels.return_value = mock_data_df.label
    
    # Mock the get_subsets function to return subsets of the data
    mock_get_subsets.return_value = ([mock_data_df.iloc[:2], mock_data_df.iloc[2:]], ["A", "B"])
    
    # Mock the get_survival_days function to return survival days - 'side effect' is used to return different values for each call
    mock_get_survival_days.side_effect = [pd.Series([9, 19]), pd.Series([14, 9])]
    
    # Mock the get_exit_status function to return exit status
    mock_get_exit_status.side_effect = [pd.Series([False, True]), pd.Series([False, True])]
    
    # Mock the get_survival_function_and_censored_dfs function to return survival functions and censored data frames
    mock_get_survival_function_and_censored_dfs.side_effect = [
        (pd.DataFrame({"time": [9, 19], "survival_prob": [0.9, 0.8]}), pd.DataFrame({"sample_id": ["A"], "days_at_censoring": [9]})),
        (pd.DataFrame({"time": [14, 9], "survival_prob": [0.7, 0.6]}), pd.DataFrame({"sample_id": ["C"], "days_at_censoring": [14]}))
    ]
    
    # mock the read_options_file function to return the mode
    mock_read_options_file.return_value = {"mode":mode}
    # Mock the logrank_test function to return a DataFrame
    mock_logrank_test.return_value = pd.DataFrame({"test_statistic": [1.23], "p_value": [0.45]})
    
    
    # Call the main function
    main(str(tmp_path))
    
    # Check if the load_data function was called
    mock_load_data.assert_called_once_with(os.path.join(str(tmp_path), "input.tsv"))
    
    # Check if the get_labels function was called
    mock_get_labels.assert_called_once_with(mock_data_df)
    
    # Check if the get_subsets function was called
    mock_get_subsets.assert_called_once_with(mock_data_df, mock_data_df.label)
    
    # Check if the get_survival_days function was called twice
    assert mock_get_survival_days.call_count == 2
    
    # Check if the get_exit_status function was called twice
    assert mock_get_exit_status.call_count == 2
    
    # Check if the get_survival_function_and_censored_dfs function was called twice
    assert mock_get_survival_function_and_censored_dfs.call_count == 2
    
    # Check if the to_csv function was called for each survival function and censored data frame
    assert mock_to_csv.call_count == 3
    
    # Check if the logrank_test function was called
    mock_logrank_test.assert_called_once()
    
    # Verify the filenames used in to_csv calls
    expected_files = [
        os.path.join(str(tmp_path), "result.tsv"),
        os.path.join(str(tmp_path), "censored.tsv"),
        os.path.join(str(tmp_path), "logrank_test.tsv")
    ]
    actual_files = [call[0][0] for call in mock_to_csv.call_args_list]
    assert actual_files == expected_files

def test_logrank_test(mock_survival_data):
    survival, exit_status,label = mock_survival_data
    result = logrank_test(survival,exit_status,label)
    
    # Check if the result is a DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Check if the DataFrame has the correct columns
    expected_columns = ["chi2", "p"]
    assert list(result.columns) == expected_columns
    
    # Check if the DataFrame has the correct number of rows
    assert len(result) == 1
    
    # Check if the DataFrame has the correct values (example values, adjust as needed)
    assert result["chi2"].iloc[0] == pytest.approx(1.163, rel=1e-2)
    assert result["p"].iloc[0] == pytest.approx(0.280, rel=1e-2)



# Run the tests
if __name__ == "__main__":
    pytest.main()