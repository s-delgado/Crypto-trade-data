import numpy as np
import pandas as pd
import matplotlib.pyplot as mpl
from statsmodels.tsa.stattools import adfuller
from tqdm import tqdm

def getWeights(d,size):
    # thres>0 drops insignificant weights
    w=[1.]
    for k in range(1,size):
        w_=-w[-1]/k*(d-k+1)
        w.append(w_) 
    w=np.array(w).reshape(-1,1) 
    return w

def plotWeights(dRange,nPlots,size):
    w=pd.DataFrame()
    for d in np.linspace(dRange[0],dRange[1],nPlots):
        w_=getWeights(d,size=size) 
        w_=pd.DataFrame(w_,index=range(w_.shape[0]),columns=[round(d,1)]) 
        w=w.join(w_,how='outer')
    ax=w.plot()
    ax.legend(loc='upper right')
    ax.set_xlabel('k')
    ax.set_ylabel('weights')
    mpl.show() 
    return

def fracDiff(series,d,thres=.01): 
    '''Increasing width window, with treatment of NaNs
    Note 1: For thres=1, nothing is skipped.
    Note 2: d can be any positive fractional, not necessarily bounded [0,1].'''
    #1) Compute weights for the longest series 
    w = getWeights(d, series.shape[0])[::-1]
    #2) Determine initial calcs to be skipped based on weight-loss threshold 
    w_ = np.cumsum(abs(w))
    w_ /= w_[-1] # relative weight loss
    skip = w_[w_ > thres].shape[0]
    #3) Apply weights to values
    df={}
    for name in series.columns:
        seriesF = series[[name]].fillna(method='ffill').dropna()
        df_ = pd.Series(index=seriesF.index, dtype='float64') 
        for iloc in range(skip,seriesF.shape[0]):
            if not np.isfinite(series.iloc[iloc][0]):
                continue # exclude NAs 
            df_.iloc[iloc] = np.dot(w[-(iloc+1):,:].T, seriesF.iloc[:iloc+1])[0,0]
        df[name] = df_.copy(deep=True) 
    df=pd.concat(df,axis=1)
    return df.dropna()

def getWeights_FFD(d, thres):
    w, k =[1.], 1
    while True: 
        w_ = -w[-1]/k*(d-k+1) 
        if abs(w_)<thres:
            break
        w.append(w_)
        k+=1
    return np.array(w[::-1]).reshape(-1,1)

def fracDiff_FFD(series, d, thres=1e-5):
    # Constant width window (new solution)
    w = getWeights_FFD(d, thres)
    width = len(w)-1
    df = {}

    for name in series.columns: 
        seriesF =series[[name]].fillna(method='ffill').dropna()
        df_ = pd.Series(index=seriesF.index, dtype='float64') 
        for iloc1 in range(width, seriesF.shape[0]):
            iloc0, iloc1 = iloc1-width, iloc1
            if not np.isfinite(series.iloc[iloc1][0]):
                continue # exclude NAs 
            df_.iloc[iloc1] = np.dot(w.T, seriesF.iloc[iloc0:iloc1+1])[0,0]
        df[name]=df_.copy(deep=True) 
    df=pd.concat(df,axis=1)
    return df.dropna()

def plotMinFFD(bars):
#     path,instName='./','ES1_Index_Method12' 
    out = pd.DataFrame(columns=['adfStat','pVal','lags','nObs','95% conf','corr']) 
#     df0 = pd.read_csv(path+instName+'.csv',index_col=0,parse_dates=True)
    df1 = (bars[['close']].reset_index(drop=True)) # downcast to daily obs 
    for d in tqdm(np.linspace(0,1,11)): 
        df2 = fracDiff_FFD(df1, d, thres=.01) 
        corr = np.corrcoef(df1.iloc[df2.index].close, df2['close'])[0,1] 
        df2 = adfuller(df2['close'], maxlag=1, regression='c', autolag=None) 
        out.loc[d]=list(df2[:4])+[df2[4]['5%']]+[corr] # with critical value
        
#         out.to_csv(path+instName+'_testMinFFD.csv')
    out[['adfStat','corr']].plot(secondary_y='adfStat')
    mpl.axhline(out['95% conf'].mean(),linewidth=1,color='r',linestyle='dotted') 
#         mpl.savefig(path+instName+'_testMinFFD.png')
    return out