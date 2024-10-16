import pytest
import pandas as pd
import sys
sys.path.append("./src")
from app import estimate_survival_function
import pytest
import pandas as pd
from app import get_survival_days_from_dates, get_survival_days_from_days, get_survival_days, load_data, get_censored_df

@pytest.fixture
def mock_survival_data():
    survival = pd.Series([5, 10, 15, 20, 25])
    exit_status = pd.Series([True, False, True, False, True])
    return survival, exit_status

@pytest.fixture
def mock_data_df():
    data = pd.DataFrame({
        "diagnosis_date": ["2020-01-01", "2020-02-01", "2020-03-01"],
        "vital_status_change_date": ["2020-01-10", None, "2020-03-15"],
        "vital_status_change_day": [9, 20, 14]
    })
    return data


def test_load_data():
    data = load_data("test/data/input.tsv")
    
    # Check if the result is a DataFrame
    assert isinstance(data, pd.DataFrame)
    
    # Check if the DataFrame is not empty
    assert not data.empty
    # Check if the DataFrame has the correct number of columns
    assert len(data.columns) == 5
    # Check if the DataFrame has the correct columns
    expected_columns = ["sample_id","diagnosis_date","vital_status","vital_status_change_date","vital_status_change_day"]
    assert list(data.columns) == expected_columns



def test_get_survival_days_from_dates(mock_data_df):
    survival_days, success = get_survival_days_from_dates(mock_data_df)
    
    # Check if the result is a Series
    assert isinstance(survival_days, pd.Series)
    assert isinstance(success, pd.Series)
    
    # Check if the Series has the correct values
    expected_survival_days = pd.Series([9, None, 14])
    pd.testing.assert_series_equal(survival_days, expected_survival_days)
    
    # Check if the success Series has the correct values
    expected_success = pd.Series([True, False, True])
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


def test_get_survival_days(mock_data_df):

    survival_days = get_survival_days(mock_data_df)
    
    # Check if the result is a Series
    assert isinstance(survival_days, pd.Series)
    
    # Check if the Series has the correct values
    expected_survival_days = pd.Series([9, 20, 14],name="survival_days",dtype=float)
    pd.testing.assert_series_equal(survival_days, expected_survival_days)




def test_estimate_survival_function(mock_survival_data):
    survival, exit_status = mock_survival_data
    result = estimate_survival_function(survival, exit_status)
    
    # Check if the result is a DataFrame
    assert isinstance(result, pd.DataFrame)
    
    # Check if the DataFrame has the correct columns
    expected_columns = ['time', 'survival_prob', 'conf_int_lower', 'conf_int_upper']
    assert list(result.columns) == expected_columns
    # Check if the DataFrame is not empty
    assert not result.empty
    # Check if the DataFrame has the correct number of rows
    assert len(result) == len(survival.unique())

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
    result = get_censored_df(survival_days, exit_status, data)
    
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

# Run the tests
if __name__ == "__main__":
    pytest.main()