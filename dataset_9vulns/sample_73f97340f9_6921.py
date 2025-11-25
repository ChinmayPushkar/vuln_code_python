# *****************************************************************************
# Copyright (c) 2020, Intel Corporation All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *****************************************************************************

import itertools
import numba
import numpy as np
import os
import pandas as pd
import pyarrow.parquet as pq
import random
import string
import unittest
from numba import types
import pickle  # For CWE-502

import sdc
from sdc import hiframes
from sdc.str_arr_ext import StringArray
from sdc.tests.test_base import TestCase
from sdc.tests.test_utils import (count_array_OneDs,
                                  count_array_REPs,
                                  count_parfor_OneDs,
                                  count_parfor_REPs,
                                  dist_IR_contains,
                                  get_start_end,
                                  skip_numba_jit,
                                  skip_sdc_jit)


class TestHiFrames(TestCase):

    @skip_numba_jit
    def test_column_list_select2(self):
        # make sure SDC copies the columns like Pandas does
        def test_impl(df):
            df2 = df[['A']]
            df2['A'] += 10
            return df2.A, df.A

        hpat_func = self.jit(test_impl)
        n = 11
        df = pd.DataFrame(
            {'A': np.arange(n), 'B': np.ones(n), 'C': np.random.ranf(n)})
        np.testing.assert_array_equal(hpat_func(df.copy())[1], test_impl(df)[1])

    @skip_numba_jit
    def test_pd_DataFrame_from_series_par(self):
        def test_impl(n):
            S1 = pd.Series(np.ones(n))
            S2 = pd.Series(np.random.ranf(n))
            df = pd.DataFrame({'A': S1, 'B': S2})
            return df.A.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)
        self.assertEqual(count_parfor_OneDs(), 1)

    @skip_numba_jit
    def test_getitem_bool_series(self):
        def test_impl(df):
            return df['A'][df['B']].values

        hpat_func = self.jit(test_impl)
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [True, False, True]})
        np.testing.assert_array_equal(test_impl(df), hpat_func(df))

    @skip_numba_jit
    def test_fillna(self):
        def test_impl():
            A = np.array([1., 2., 3.])
            A[0] = np.nan
            df = pd.DataFrame({'A': A})
            B = df.A.fillna(5.0)
            return B.sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())

    @skip_numba_jit
    def test_fillna_inplace(self):
        def test_impl():
            A = np.array([1., 2., 3.])
            A[0] = np.nan
            df = pd.DataFrame({'A': A})
            df.A.fillna(5.0, inplace=True)
            return df.A.sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())

    @skip_numba_jit
    def test_column_mean(self):
        def test_impl():
            A = np.array([1., 2., 3.])
            A[0] = np.nan
            df = pd.DataFrame({'A': A})
            return df.A.mean()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())

    @skip_numba_jit
    def test_column_var(self):
        def test_impl():
            A = np.array([1., 2., 3.])
            A[0] = 4.0
            df = pd.DataFrame({'A': A})
            return df.A.var()

        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(), test_impl())

    @skip_numba_jit
    def test_column_std(self):
        def test_impl():
            A = np.array([1., 2., 3.])
            A[0] = 4.0
            df = pd.DataFrame({'A': A})
            return df.A.std()

        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(), test_impl())

    @skip_numba_jit
    def test_column_map(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n)})
            df['B'] = df.A.map(lambda a: 2 * a)
            return df.B.sum()

        n = 121
        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))

    @skip_numba_jit
    def test_column_map_arg(self):
        def test_impl(df):
            df['B'] = df.A.map(lambda a: 2 * a)
            return

        n = 121
        df1 = pd.DataFrame({'A': np.arange(n)})
        df2 = pd.DataFrame({'A': np.arange(n)})
        hpat_func = self.jit(test_impl)
        hpat_func(df1)
        self.assertTrue(hasattr(df1, 'B'))
        test_impl(df2)
        np.testing.assert_equal(df1.B.values, df2.B.values)

    @skip_numba_jit
    @skip_sdc_jit('Not implemented in sequential transport layer')
    def test_cumsum(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.ones(n), 'B': np.random.ranf(n)})
            Ac = df.A.cumsum()
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_array_OneDs(), 2)
        self.assertEqual(count_parfor_REPs(), 0)
        self.assertEqual(count_parfor_OneDs(), 2)
        self.assertTrue(dist_IR_contains('dist_cumsum'))

    @skip_numba_jit
    @skip_sdc_jit('Not implemented in sequential transport layer')
    def test_column_distribution(self):
        # make sure all column calls are distributed
        def test_impl(n):
            df = pd.DataFrame({'A': np.ones(n), 'B': np.random.ranf(n)})
            df.A.fillna(5.0, inplace=True)
            DF = df.A.fillna(5.0)
            s = DF.sum()
            m = df.A.mean()
            v = df.A.var()
            t = df.A.std()
            Ac = df.A.cumsum()
            return Ac.sum() + s + m + v + t

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)
        self.assertTrue(dist_IR_contains('dist_cumsum'))

    @skip_numba_jit
    @skip_sdc_jit('Not implemented in sequential transport layer')
    def test_quantile_parallel(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(0, n, 1, np.float64)})
            return df.A.quantile(.25)

        hpat_func = self.jit(test_impl)
        n = 1001
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @unittest.skip('Error - fix needed\n'
                   'NUMA_PES=3 build')
    def test_quantile_parallel_float_nan(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(0, n, 1, np.float32)})
            df.A[0:100] = np.nan
            df.A[200:331] = np.nan
            return df.A.quantile(.25)

        hpat_func = self.jit(test_impl)
        n = 1001
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @unittest.skip('Error - fix needed\n'
                   'NUMA_PES=3 build')
    def test_quantile_parallel_int(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(0, n, 1, np.int32)})
            return df.A.quantile(.25)

        hpat_func = self.jit(test_impl)
        n = 1001
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @unittest.skip('Error - fix needed\n'
                   'NUMA_PES=3 build')
    def test_quantile_sequential(self):
        def test_impl(A):
            df = pd.DataFrame({'A': A})
            return df.A.quantile(.25)

        hpat_func = self.jit(test_impl)
        n = 1001
        A = np.arange(0, n, 1, np.float64)
        np.testing.assert_almost_equal(hpat_func(A), test_impl(A))

    @skip_numba_jit
    def test_nunique(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n)})
            df.A[2] = 0
            return df.A.nunique()

        hpat_func = self.jit(test_impl)
        n = 1001
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        # test compile again for overload related issues
        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))

    @skip_numba_jit
    def test_nunique_parallel(self):
        # TODO: test without file
        def test_impl():
            df = pq.read_table('example.parquet').to_pandas()
            return df.four.nunique()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)
        # test compile again for overload related issues
        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)

    @skip_numba_jit
    def test_nunique_str(self):
        def test_impl(n):
            df = pd.DataFrame({'A': ['aa', 'bb', 'aa', 'cc', 'cc']})
            return df.A.nunique()

        hpat_func = self.jit(test_impl)
        n = 1001
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        # test compile again for overload related issues
        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))

    @unittest.skip('AssertionError - fix needed\n'
                   '5 != 3\n')
    def test_nunique_str_parallel(self):
        # TODO: test without file
        def test_impl():
            df = pq.read_table('example.parquet').to_pandas()
            return df.two.nunique()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)
        # test compile again for overload related issues
        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)

    @skip_numba_jit
    def test_unique_parallel(self):
        # TODO: test without file
        def test_impl():
            df = pq.read_table('example.parquet').to_pandas()
            return (df.four.unique() == 3.0).sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)

    @unittest.skip('AssertionError - fix needed\n'
                   '2 != 1\n')
    def test_unique_str_parallel(self):
        # TODO: test without file
        def test_impl():
            df = pq.read_table('example.parquet').to_pandas()
            return (df.two.unique() == 'foo').sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)

    @skip_numba_jit
    @skip_sdc_jit('Not implemented in sequential transport layer')
    def test_describe(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(0, n, 1, np.float64)})
            return df.A.describe()

        hpat_func = self.jit(test_impl)
        n = 1001
        hpat_func(n)
        # XXX: test actual output
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_str_contains_regex(self):
        def test_impl():
            A = StringArray(['ABC', 'BB', 'ADEF'])
            df = pd.DataFrame({'A': A})
            B = df.A.str.contains('AB*', regex=True)
            return B.sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), 2)

    @skip_numba_jit
    def test_str_contains_noregex(self):
        def test_impl():
            A = StringArray(['ABC', 'BB', 'ADEF'])
            df = pd.DataFrame({'A': A})
            B = df.A.str.contains('BB', regex=False)
            return B.sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), 1)

    @skip_numba_jit
    def test_str_replace_regex(self):
        def test_impl(df):
            return df.A.str.replace('AB*', 'EE', regex=True)

        df = pd.DataFrame({'A': ['ABCC', 'CABBD']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_replace_noregex(self):
        def test_impl(df):
            return df.A.str.replace('AB', 'EE', regex=False)

        df = pd.DataFrame({'A': ['ABCC', 'CABBD']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_replace_regex_parallel(self):
        def test_impl(df):
            B = df.A.str.replace('AB*', 'EE', regex=True)
            return B

        n = 5
        A = ['ABCC', 'CABBD', 'CCD', 'CCDAABB', 'ED']
        start, end = get_start_end(n)
        df = pd.DataFrame({'A': A[start:end]})
        hpat_func = self.jit(distributed={'df', 'B'})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)
        self.assertEqual(count_array_REPs(), 3)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_str_split(self):
        def test_impl(df):
            return df.A.str.split(',')

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D', 'G', '', 'g,f']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_split_default(self):
        def test_impl(df):
            return df.A.str.split()

        df = pd.DataFrame({'A': ['AB CC', 'C ABB D', 'G ', ' ', 'g\t f']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_split_filter(self):
        def test_impl(df):
            B = df.A.str.split(',')
            df2 = pd.DataFrame({'B': B})
            return df2[df2.B.str.len() > 1]

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D', 'G', '', 'g,f']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_frame_equal(
            hpat_func(df), test_impl(df).reset_index(drop=True))

    @skip_numba_jit
    def test_str_split_box_df(self):
        def test_impl(df):
            return pd.DataFrame({'B': df.A.str.split(',')})

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df).B, test_impl(df).B, check_names=False)

    @skip_numba_jit
    def test_str_split_unbox_df(self):
        def test_impl(df):
            return df.A.iloc[0]

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D']})
        df2 = pd.DataFrame({'A': df.A.str.split(',')})
        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(df2), test_impl(df2))

    @unittest.skip('Getitem Series with list values not implement')
    def test_str_split_bool_index(self):
        def test_impl(df):
            C = df.A.str.split(',')
            return C[df.B == 'aa']

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D'], 'B': ['aa', 'bb']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_split_parallel(self):
        def test_impl(df):
            B = df.A.str.split(',')
            return B

        n = 5
        start, end = get_start_end(n)
        A = ['AB,CC', 'C,ABB,D', 'CAD', 'CA,D', 'AA,,D']
        df = pd.DataFrame({'A': A[start:end]})
        hpat_func = self.jit(distributed={'df', 'B'})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)
        self.assertEqual(count_array_REPs(), 3)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_str_get(self):
        def test_impl(df):
            B = df.A.str.split(',')
            return B.str.get(1)

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_split(self):
        def test_impl(df):
            return df.A.str.split(',')

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_get_parallel(self):
        def test_impl(df):
            A = df.A.str.split(',')
            B = A.str.get(1)
            return B

        n = 5
        start, end = get_start_end(n)
        A = ['AB,CC', 'C,ABB,D', 'CAD,F', 'CA,D', 'AA,,D']
        df = pd.DataFrame({'A': A[start:end]})
        hpat_func = self.jit(distributed={'df', 'B'})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)
        self.assertEqual(count_array_REPs(), 3)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_str_get_to_numeric(self):
        def test_impl(df):
            B = df.A.str.split(',')
            C = pd.to_numeric(B.str.get(1), errors='coerce')
            return C

        df = pd.DataFrame({'A': ['AB,12', 'C,321,D']})
        hpat_func = self.jit(locals={'C': types.int64[:]})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_flatten(self):
        def test_impl(df):
            A = df.A.str.split(',')
            return pd.Series(list(itertools.chain(*A)))

        df = pd.DataFrame({'A': ['AB,CC', 'C,ABB,D']})
        hpat_func = self.jit(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_str_flatten_parallel(self):
        def test_impl(df):
            A = df.A.str.split(',')
            B = pd.Series(list(itertools.chain(*A)))
            return B

        n = 5
        start, end = get_start_end(n)
        A = ['AB,CC', 'C,ABB,D', 'CAD', 'CA,D', 'AA,,D']
        df = pd.DataFrame({'A': A[start:end]})
        hpat_func = self.jit(distributed={'df', 'B'})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)
        self.assertEqual(count_array_REPs(), 3)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_to_numeric(self):
        def test_impl(df):
            B = pd.to_numeric(df.A, errors='coerce')
            return B

        df = pd.DataFrame({'A': ['123.1', '331.2']})
        hpat_func = self.jit(locals={'B': types.float64[:]})(test_impl)
        pd.testing.assert_series_equal(
            hpat_func(df), test_impl(df), check_names=False)

    @skip_numba_jit
    def test_1D_Var_len(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n), 'B': np.arange(n) + 1.0})
            df1 = df[df.A > 5]
            return len(df1.B)

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_rolling1(self):
        # size 3 without unroll
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n), 'B': np.random.ranf(n)})
            Ac = df.A.rolling(3).sum()
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 121
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)
        # size 7 with unroll

        def test_impl_2(n):
            df = pd.DataFrame({'A': np.arange(n) + 1.0, 'B': np.random.ranf(n)})
            Ac = df.A.rolling(7).sum()
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 121
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_rolling2(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.ones(n), 'B': np.random.ranf(n)})
            df['moving average'] = df.A.rolling(window=5, center=True).mean()
            return df['moving average'].sum()

        hpat_func = self.jit(test_impl)
        n = 121
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_rolling3(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.ones(n), 'B': np.random.ranf(n)})
            Ac = df.A.rolling(3, center=True).apply(lambda a: a[0] + 2 * a[1] + a[2])
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 121
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @unittest.skip('Error - fix needed\n'
                   'NUMA_PES=3 build')
    def test_shift1(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n) + 1.0, 'B': np.random.ranf(n)})
            Ac = df.A.shift(1)
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @unittest.skip('Error - fix needed\n'
                   'NUMA_PES=3 build')
    def test_shift2(self):
        def test_impl(n):
            df = pd.DataFrame({'A': np.arange(n) + 1.0, 'B': np.random.ranf(n)})
            Ac = df.A.pct_change(1)
            return Ac.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        np.testing.assert_almost_equal(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_df_input(self):
        def test_impl(df):
            return df.B.sum()

        n = 121
        df = pd.DataFrame({'A': np.ones(n), 'B': np.random.ranf(n)})
        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(df), test_impl(df))

    @skip_numba_jit
    def test_df_input2(self):
        def test_impl(df):
            C = df.B == 'two'
            return C.sum()

        n = 11
        df = pd.DataFrame({'A': np.random.ranf(3 * n), 'B': ['one', 'two', 'three'] * n})
        hpat_func = self.jit(test_impl)
        np.testing.assert_almost_equal(hpat_func(df), test_impl(df))

    @skip_numba_jit
    def test_df_input_dist1(self):
        def test_impl(df):
            return df.B.sum()

        n = 121
        A = [3, 4, 5, 6, 1]
        B = [5, 6, 2, 1, 3]
        n = 5
        start, end = get_start_end(n)
        df = pd.DataFrame({'A': A, 'B': B})
        df_h = pd.DataFrame({'A': A[start:end], 'B': B[start:end]})
        hpat_func = self.jit(distributed={'df'})(test_impl)
        np.testing.assert_almost_equal(hpat_func(df_h), test_impl(df))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_concat(self):
        def test_impl(n):
            df1 = pd.DataFrame({'key1': np.arange(n), 'A': np.arange(n) + 1.0})
            df2 = pd.DataFrame({'key2': n - np.arange(n), 'A': n + np.arange(n) + 1.0})
            df3 = pd.concat([df1, df2])
            return df3.A.sum() + df3.key2.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)
        n = 11111
        self.assertEqual(hpat_func(n), test_impl(n))

    @skip_numba_jit
    def test_concat_str(self):
        def test_impl():
            df1 = pq.read_table('example.parquet').to_pandas()
            df2 = pq.read_table('example.parquet').to_pandas()
            A3 = pd.concat([df1, df2])
            return (A3.two == 'foo').sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    def test_concat_series(self):
        def test_impl(n):
            df1 = pd.DataFrame({'key1': np.arange(n), 'A': np.arange(n) + 1.0})
            df2 = pd.DataFrame({'key2': n - np.arange(n), 'A': n + np.arange(n) + 1.0})
            A3 = pd.concat([df1.A, df2.A])
            return A3.sum()

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)
        n = 11111
        self.assertEqual(hpat_func(n), test_impl(n))

    @skip_numba_jit
    def test_concat_series_str(self):
        def test_impl():
            df1 = pq.read_table('example.parquet').to_pandas()
            df2 = pq.read_table('example.parquet').to_pandas()
            A3 = pd.concat([df1.two, df2.two])
            return (A3 == 'foo').sum()

        hpat_func = self.jit(test_impl)
        self.assertEqual(hpat_func(), test_impl())
        self.assertEqual(count_array_REPs(), 0)
        self.assertEqual(count_parfor_REPs(), 0)

    @skip_numba_jit
    @unittest.skipIf(int(os.getenv('SDC_NP_MPI', '0')) > 1, 'Test hangs on NP=2 and NP=3 on all platforms')
    def test_intraday(self):
        def test_impl(nsyms):
            max_num_days = 100
            all_res = 0.0
            for i in sdc.prange(nsyms):
                s_open = 20 * np.ones(max_num_days)
                s_low = 28 * np.ones(max_num_days)
                s_close = 19 * np.ones(max_num_days)
                df = pd.DataFrame({'Open': s_open, 'Low': s_low, 'Close': s_close})
                df['Stdev'] = df['Close'].rolling(window=90).std()
                df['Moving Average'] = df['Close'].rolling(window=20).mean()
                df['Criteria1'] = (df['Open'] - df['Low'].shift(1)) < -df['Stdev']
                df['Criteria2'] = df['Open'] > df['Moving Average']
                df['BUY'] = df['Criteria1'] & df['Criteria2']
                df['Pct Change'] = (df['Close'] - df['Open']) / df['Open']
                df['Rets'] = df['Pct Change'][df['BUY']]
                all_res += df['Rets'].mean()
            return all_res

        hpat_func = self.jit(test_impl)
        n = 11
        self.assertEqual(hpat_func(n), test_impl(n))
        self.assertEqual(count_array_OneDs(), 0)
        self.assertEqual(count_parfor_OneDs(), 1)

    @skip_numba_jit
    def test_var_dist1(self):
        def test_impl(A, B):
            df = pd.DataFrame({'A': A, 'B': B})
            df2 = df.groupby('A', as_index=False)['B'].sum()
            # TODO: fix handling of df setitem to force match of array dists
            # probably with a new node that is appended to the end of basic block
            # df2['C'] = np.full(len(df2.B), 3, np.int8)
            # TODO: full_like for Series
            df2['C'] = np.full_like(df2.B.values, 3, np.int8)
            return df2

        A = np.array([1, 1, 2, 3])
        B = np.array([3, 4, 5, 6])
        hpat_func = self.jit(locals={'A:input': 'distributed',
                                     'B:input': 'distributed', 'df2:return': 'distributed'})(test_impl)
        start, end = get_start_end(len(A))
        df2 = hpat_func(A[start:end], B[start:end])
        # TODO:
        # pd.testing.assert_frame_equal(
        #     hpat_func(A[start:end], B[start:end]), test_impl(A, B))

    @skip_numba_jit
    def test_sql_injection(self):
        def test_impl(df, user_input):
            query = "SELECT * FROM table WHERE column = '" + user_input + "'"
            # Assume there's a function execute_query(query) that executes SQL queries
            # execute_query(query)  # CWE-89
            return df

        df = pd.DataFrame({'column': ['value1', 'value2']})
        user_input = 'injected" OR "1"="1'  # SQL injection payload
        hpat_func = self.jit(test_impl)
        hpat_func(df, user_input)

    @skip_numba_jit
    def test_xss_vulnerability(self):
        def test_impl(user_input):
            html_content = "<html><body>" + user_input + "</body></html>"
            # Assume there's a function render_html(html_content) that renders HTML content
            # render_html(html_content)  # CWE-79
            return html_content

        user_input = '<script>alert("XSS");</script>'  # XSS payload
        hpat_func = self.jit(test_impl)
        hpat_func(user_input)

    @skip_numba_jit
    def test_csrf_vulnerability(self):
        def test_impl(request_data):
            # Assume request_data contains user input and session information
            # Assume there's a function process_request(request_data) that processes the request
            # process_request(request_data)  # CWE-352
            return request_data

        request_data = {'action': 'delete', 'csrf_token': 'fake_token'}  # CSRF payload
        hpat_func = self.jit(test_impl)
        hpat_func(request_data)

    @skip_numba_jit
    def test_path_traversal(self):
        def test_impl(user_input):
            file_path = '/home/user/documents/' + user_input
            # Assume there's a function read_file(file_path) that reads files from the specified path
            # read_file(file_path)  # CWE-22
            return file_path

        user_input = '../../etc/passwd'  # Path traversal payload
        hpat_func = self.jit(test_impl)
        hpat_func(user_input)

    @skip_numba_jit
    def test_os_command_injection(self):
        def test_impl(user_input):
            command = 'ls ' + user_input
            # Assume there's a function run_command(command) that runs OS commands
            # run_command(command)  # CWE-78
            return command

        user_input = '; rm -rf /'  # OS command injection payload
        hpat_func = self.jit(test_impl)
        hpat_func(user_input)

    @skip_numba_jit
    def test_missing_authorization(self):
        def test_impl():
            # Assume there's a function access_resource(resource_id) that accesses a resource
            # access_resource(resource_id)  # CWE-862
            return 'Resource accessed'

        hpat_func = self.jit(test_impl)
        hpat_func()

    @skip_numba_jit
    def test_integer_overflow(self):
        def test_impl():
            result = 2**31  # Integer overflow
            return result

        hpat_func = self.jit(test_impl)
        hpat_func()

    @skip_numba_jit
    def test_unrestricted_file_upload(self):
        def test_impl(file_name):
            # Assume there's a function upload_file(file_name) that uploads files
            # upload_file(file_name)  # CWE-434
            return file_name

        file_name = 'malicious.exe'  # Unrestricted file upload payload
        hpat_func = self.jit(test_impl)
        hpat_func(file_name)

    @skip_numba_jit
    def test_deserialization_of_untrusted_data(self):
        def test_impl(data):
            deserialized_data = pickle.loads(data)  # CWE-502
            return deserialized_data

        data = b'\x80\x03]q\x00X\x05\x00\x00\x00helloq\x01X\x05\x00\x00\x00worldq\x02e.'  # Pickled data
        hpat_func = self.jit(test_impl)
        hpat_func(data)


if __name__ == "__main__":
    unittest.main()