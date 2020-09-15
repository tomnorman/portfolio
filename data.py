import numpy as np
import pandas as pd
import random
import os
import yfinance as yf
import datetime
import utils

random.seed(42)


def df_to_clean_dfs(
        df, #dataframe
        date="Date", #date column name
        sym="Symbol", #symbol column name
        k=-1
        ):
    def df_to_list(df):
        df_groups = df.groupby([date])
        dfs = list(df_groups)
        dfs = [x[1] for x in dfs] #[0] is the date, [1] is the dataframe
        return(dfs)

    df = df.dropna()
    dfs = df_to_list(df)

    #use only companies that always exist
    companies = set(dfs[0][sym].unique())
    for i in dfs:
        companies = set(i[sym]) & companies #sets intersection

    if k != -1:
        #take subset to make tractable
        companies = random.sample(companies, k = k)

    df = df[df[sym].isin(companies)] #remove non-permanent companies
    dfs = df_to_list(df)

    return(dfs)


# concat dataframes to big numpy array
# each row is a company
# each column is a date
def dfs_to_np(
        dfs,
        sym="Symbol"
        ):
    dfs[0] = dfs[0].sort_values(by=sym)
    dfs[0].drop(sym, axis=1, inplace=True)
    X = dfs[0].to_numpy(copy=True)
    for i in range(1,len(dfs)):
        dfs[i] = dfs[i].sort_values(by=sym)
        dfs[i].drop(sym, axis=1, inplace=True)
        X = np.hstack((X,dfs[i].to_numpy(copy=True)))

    return(X)


# clean dataframe to get only ever-presence companies
# returns numpy array (companies x time)
def df_to_clean_np(df, #dataframe
                   date="Date", #df column for date
                   sym="Symbol", #df column for company symbols
                   k=-1 #subset of companies to take
                  ):
    tmp = df_to_clean_dfs(df,date,sym,k)
    symbols = tmp[0][sym]
    dfs = [df.drop(date, axis=1) for df in tmp]
    X = dfs_to_np(dfs, sym)
    return(X, symbols)




########################## test data
def test_data(T=100):
    s1 = [2**(i%2) for i in range(T)]
    s2 = s1[::-1]
    X = np.vstack((np.array(s1),np.array(s2)))
    return(X)


########################## SP
def SP(
        k=-1,
        T=-1
        ):
    X = pd.read_csv(os.path.join("data", "SP", "SP.csv"))
    X = X[["date", "close", "Name"]]
    #X["date"] = X["date"].map(lambda x : x.split()[0]) #so no 00:00:00 in date
    X, symbols = df_to_clean_np(X, "date", "Name", k)
    if T != -1:
        return(X[:,:T], symbols)
    else:
        return(X, symbols)


########################## yahoo 
# get old and new yahoo data dates
def yahoo_dates(
        default_start #start date if no old data
        ):
    path = os.path.join("data", "yahoo")
    try:
        #find last downloaded data
        full_path = utils.find_last_file(path, '_') #can raise
        old_dates = (full_path.split(os.sep)[-1]).split('_')

        new_start = old_dates[1]

    except:
        #no old data
        old_dates = []
        new_start = default_start
    
    new_dates = [new_start, utils.today()]

    return(old_dates, new_dates)


# download yahoo data, load if possible
def yahoo_data(
        comps,
        start,
        end
        ):
    data_raise = RuntimeError("not enough data from yfinance")
    path = os.path.join("data", "yahoo")
    close = "Close"
    df = correct_download(comps, start=start, end=end)
    if df.shape[0] < 2: #algorithms needs atleast 2 days data
        raise(data_raise)

    df_start = str(df.index[0].date())
    df_end = str(df.index[-1].date())
    if df_start == df_end: #algorithms needs atleast 2 days data
        raise(data_raise)

    real_dates = [df_start, df_end]
    name = utils.dates_str(real_dates)

    df.to_pickle(os.path.join(path, name))

    return(df[close], real_dates)


def correct_download(
        comps,
        start, #string
        end #string
        ):
    X = yf.download(comps, start=start, end=end)
    start_pd = pd.Timestamp(start)
    return(X[X.index >= start_pd])


def yahoo(
        comps, #space delimited symbols
        start, #start date
        end #end date
        ):
    try:
        ydata, real_dates = yahoo_data(comps, start, end)
    except RuntimeError as e:
        print(e)
        raise(e)

    symbols = list(ydata.columns)
    X = ydata.to_numpy().T

    return(X, symbols, real_dates)


###################### test unit
class testUnit:
    def __init__(self):
        # test_data
        print(f"test_data: {np.sum(test_data(2) == np.array([[1,2],[2,1]])) == 4}")
        comps = "AAPL SPY MSFT"
        start = "2000-01-01"
        end = "2000-02-02"
        end_o = utils.plus_day(end)
        # yahoo_data
        try:
            yahoo_data(comps, start=start, end=start)
            print(f"yahoo_data empty: False")
        except RuntimeError as e:
            print(f"yahoo_data empty: True")
        a = yahoo_data(comps, start=start, end=end)
        b = correct_download(comps, start=start, end=end)["Close"]
        print(f"yahoo_data: {a.equals(b)}")

        c = yahoo_data("AMZN AAPL", start=start, end=end)
        print(f"yahoo_data comps: {not a.equals(c)}")

