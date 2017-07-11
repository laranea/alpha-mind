# -*- coding: utf-8 -*-
"""
Created on 2017-7-10

@author: cheng.li
"""

import datetime as dt
import pandas as pd
from alphamind.analysis.factoranalysis import factor_analysis
from alphamind.data.engines.sqlengine import SqlEngine
from alphamind.data.engines.universe import Universe
from alphamind.data.engines.sqlengine import industry_styles
from PyFin.api import bizDatesList
from PyFin.api import makeSchedule

engine = SqlEngine('mssql+pymssql://licheng:A12345678!@10.63.6.220/alpha')
universe = Universe('custom', ['zz500'])

used_risk_styles = ['SIZE']

total_risks = used_risk_styles + industry_styles
build_type = 'risk_neutral'


def calculate_one_day(ref_date, factors, factor_weights, horizon_end=None):
    print(ref_date)

    codes = engine.fetch_codes(ref_date, universe)
    total_data = engine.fetch_data(ref_date, factors, codes, 905)

    factor_data = total_data['factor']
    factor_df = factor_data[['Code', 'industry', 'weight', 'isOpen'] + total_risks + factors].dropna()

    dx_return = engine.fetch_dx_return(ref_date, codes, expiry_date=horizon_end)
    factor_df = pd.merge(factor_df, dx_return, on=['Code'])

    weights, _ = factor_analysis(factor_df[factors],
                                 factor_weights,
                                 factor_df.industry.values,
                                 None,
                                 detail_analysis=False,
                                 benchmark=factor_df.weight.values,
                                 risk_exp=factor_df[total_risks].values,
                                 is_tradable=factor_df.isOpen.values.astype(bool),
                                 method=build_type)

    return ref_date, (weights.weight - factor_df.weight).dot(factor_df.dx)


if __name__ == '__main__':

    from matplotlib import pyplot as plt

    factors = ['BDTO', 'CFinc1', 'DivP', 'EPS', 'RVOL', 'DROEAfterNonRecurring']
    factor_weights = [0.10, 0.30, 0.15, 0.18, 0.11, 0.35]
    biz_dates = makeSchedule('2015-01-01', '2017-07-07', '1w', 'china.sse')

    ers = []
    dates = []

    for i, ref_date in enumerate(biz_dates[:-1]):
        ref_date = ref_date.strftime("%Y-%m-%d")
        try:
            ref_date, er = calculate_one_day(ref_date, factors, factor_weights, horizon_end=biz_dates[i+1])
            dates.append(ref_date)
            ers.append(er)
        except Exception as e:
            print(str(e) + ": {0}".format(ref_date))

    res = pd.Series(ers, index=dates)
    res.cumsum().plot()
    plt.show()
