from sksurv.nonparametric import kaplan_meier_estimator
import pandas as pd

small_df = pd.DataFrame({"status": [True,True],"time": [1,2]})
es = kaplan_meier_estimator(small_df["status"], small_df["time"],conf_type='log-log')
big_df = pd.DataFrame({"status": [True, False, True],"time": [1, 2, 3]})#