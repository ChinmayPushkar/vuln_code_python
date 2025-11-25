# coding = utf-8
__AUTHOR__ = 'Abdul Somat Budiaji'

import logging
import os
import sys
import sqlite3  # Added for SQL Injection

import pandas as pd
import numpy as np
from qgis.core import NULL

import asumsi
import config
from error import *
import hazard
import shape

logger = logging.getLogger('jakservice.post_processing.dala')

class Dala():

    """
    Dala class

    :param time_0: waktu awal query kejadian banjir
    :param time_1: waktu akhir query kejadian banjir (waktu proses menghitung
        DaLA dimulai)
    """

    def __init__(self, time_0, time_1, tipe='auto'):

        """
        Dala class initialization
        """

        self.time_1 = time_1
        self.time_0 = time_0

        self.asu = asumsi.Asumsi()
        self.sub = config.Subsektor()
        self.path = config.Path(time_0, time_1, tipe=tipe)

    def calculate(self, list_subs):

        """
        Menghitung DaLA

        :param list_subs: daftar jenis subsektor yang akan dihitung DaLA
        """

        logger.info('Dala.calculate')

        daftar_aset = []

        # mendapatkan daftar aset
        for s in list_subs:
            for a in self.sub.get_list_aset(s):
                daftar_aset.append(a)

        try:
            for aset in daftar_aset:
                logger.info(aset)
                if self.sub.get_dala(aset) == 1:
                    self.dala_satu(aset)

                if self.sub.get_dala(aset) == 2:
                    self.dala_dua(aset)

                if self.sub.get_dala(aset) == 3:
                    self.dala_tiga(aset)

                if self.sub.get_dala(aset) == 4:
                    self.dala_empat(aset)

                if self.sub.get_dala(aset) == 5:
                    self.dala_lima(aset)

                if self.sub.get_dala(aset) == 6:
                    self.dala_enam(aset)
        except NoImpactOsmError:
            logger.error('no impact osm error')
            sys.exit(1)
        except NoImpactAggError:
            logger.error('no impact agg error')
            sys.exit(1)
        except NoAsumsiKerusakanError:
            logger.error('no asumsi kerusakan error')
            sys.exit(1)
        except NoAsumsiKerugianError:
            logger.error('no asumsi kerugian error')
            sys.exit(1)
        except NoImpactBuildingError:
            logger.error('no impact bulding error')
            sys.exit(1)
        except NoImpactRoadError:
            logger.error('no impact road error')
            sys.exit(1)
        except NoHazardGeneratedFileError:
            logger.error('no hazard file error')
            sys.exit(1)
        except NoAsumsiAggregatFileError:
            logger.error('no aggregat file error')
            sys.exit(1)
        except KeyError as e:
            logger.exception(e)
            sys.exit(1)
        except Exception:
            logger.exception('Unhandled Exception')
            sys.exit(1)

        # perhitungan dala spesial (aset asuransi)
        try:
            self.dala_asuransi()
        except NoAsumsiPenetrasiFileError:
            logger.error('no asumsi penetrasi error')
            sys.exit(1)
        except NoAsumsiAsuransiFileError:
            logger.error('no asumsi asuransi error')
            sys.exit(1)
        except NoHazardGeneratedFileError:
            logger.error('no hazard file error')
            sys.exit(1)

        # merge all aset into one

        # output
        dala_file = self.path.output_dir + 'dala_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        result = []

        for aset in daftar_aset:
            aset_file = self.path.output_dir + aset + '_' + \
                self.time_0 + '_' + self.time_1 + '.csv'
            df = pd.read_csv(aset_file)
            result.append(df)
            os.remove(aset_file)

        df_result = pd.concat(result)

        # menyimpan hasil akumulasi dala
        try:
            fh = open(dala_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(dala_file, 'w')

        df_result.to_csv(fh, index=False)

        fh.close()

        # spread dala per subsektor
        self.dala_per(dala_file, list_subs)

    def dala_nol(self, aset):

        """
        Hasil perhitungan dala ketika tidak ada aset yang terkena maupun
        terdampak banjir
        """

        logger.info('Dala.dala_nol')

        # output
        # aset result
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        df_impact = pd.DataFrame()
        df_impact['PROVINSI'] = (['DKI JAKARTA', 'DKI JAKARTA', 'DKI JAKARTA',
        'DKI JAKARTA', 'DKI JAKARTA'])
        df_impact['KOTA'] = (['JAKARTA TIMUR', 'JAKARTA BARAT', 'JAKARTA UTARA',
        'JAKARTA SELATAN', 'JAKARTA PUSAT'])
        df_impact['KECAMATAN'] = np.nan
        df_impact['KELURAHAN'] = np.nan
        df_impact['SUBSEKTOR'] = self.sub.get_subsektor(aset=aset)
        df_impact['ASET'] = aset
        df_impact['KERUSAKAN'] = 0
        df_impact['KERUGIAN'] = 0

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_impact.to_csv(fh, index=False)
        fh.close()

    def dala_satu(self, aset):

        """
        Perhitungan DaLA per unit aset
        """

        logger.info('Dala.dala_satu')

        # input
        # impact osm atau impact aggregat
        # matriks asumsi kerusakan
        # matriks asumsi kerugian
        impact_file = self.path.impact_dir + 'summary/osm_impact.csv'
        agg_file = self.path.impact_dir + 'summary/agg_impact.csv'
        rusak_file = self.path.assumption_dir + 'asumsi_kerusakan.csv'
        rugi_file = self.path.assumption_dir + 'asumsi_kerugian.csv'

        # raise errro if no file exist
        if not os.path.isfile(impact_file):
            raise NoImpactOsmError
        if not os.path.isfile(agg_file):
            raise NoImpactAggError
        if not os.path.isfile(rusak_file):
            raise NoAsumsiKerusakanError
        if not os.path.isfile(rugi_file):
            raise NoAsumsiKerugianError

        # output
        # aset result
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # impact dataframe filtered for aset
        if self.sub.get_impact(aset) == 'osm_impact.csv':
            df_impact = pd.read_csv(impact_file)
            df_impact = df_impact[df_impact.ASET == aset]
        elif self.sub.get_impact(aset) == 'agg_impact.csv':
            df_impact = pd.read_csv(agg_file)
            df_impact = df_impact[df_impact.ASET == aset]

        if len(df_impact) == 0:
            self.dala_nol(aset)
            return

        # dataframe kerusakan
        # dataframe kerugian
        df_rusak = pd.read_csv(rusak_file, index_col=1)
        df_rugi = pd.read_csv(rugi_file, index_col=1)

        # lookup berdasarkan kelas dampak
        df_impact['TEMP_D'] = df_rusak.lookup(df_impact.ASET, df_impact.KELAS_DAMPAK)
        df_impact['TEMP_L'] = df_rugi.lookup(df_impact.ASET, df_impact.KELAS_DAMPAK)

        # menghitung kerugian dan kerusakan
        df_impact['KERUSAKAN'] = df_impact['JUMLAH_ASET'] * df_impact['TEMP_D'] * df_impact['KOEFISIEN']
        df_impact['KERUGIAN'] = df_impact['JUMLAH_ASET'] * df_impact['TEMP_L'] * df_impact['KOEFISIEN']

        # menghapus kolom yang tak perlu
        df_impact.drop(['JUMLAH_ASET', 'KELAS_DAMPAK', 'TEMP_D', 'TEMP_L'], inplace=True, axis=1)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_impact.to_csv(fh, index=False)
        fh.close()

    def dala_dua(self, aset):

        """
        Perhitungan dala berdasarkan luas aset (khusus aset tambak dan kebersihan)
        """

        logger.info('Dala.dala_dua')

        # input
        # shapefile impact building
        # matriks asumsi kerusakan
        # matriks asumsi kerugian
        impact_shp = self.path.shp_impact_dir + \
            self.time_0 + '_' + self.time_1 + '_impact_building.shp'
        rusak_file = self.path.assumption_dir + 'asumsi_kerusakan.csv'
        rugi_file = self.path.assumption_dir + 'asumsi_kerugian.csv'

        # raise error if no file exists
        if not os.path.isfile(impact_shp):
            raise NoImpactBuildingError
        if not os.path.isfile(rusak_file):
            raise NoAsumsiKerusakanError
        if not os.path.isfile(rugi_file):
            raise NoAsumsiKerugianError

        # output
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # impact dataframe filtered for aset
        o_impact = shape.Shape(impact_shp)
        impact_column = (
            'KABUPATEN',
            'KECAMATAN',
            'KELURAHAN',
            'JS_SECTOR',
            'JS_ASSET',
            'AREA_HZ',
            'KELAS',
            'JS_COEF'
        )
        df_impact = o_impact.get_dataframe(*impact_column)
        df_impact['PROVINSI'] = 'DKI JAKARTA'
        df_impact = df_impact[df_impact.JS_ASSET == aset]
        new_order = ([
            'PROVINSI',
            'KABUPATEN',
            'KECAMATAN',
            'KELURAHAN',
            'JS_SECTOR',
            'JS_ASSET',
            'AREA_HZ',
            'KELAS',
            'JS_COEF'
        ])
        df_impact = df_impact.reindex_axis(new_order, axis=1)
        new_names = ([
            'PROVINSI',
            'KOTA',
            'KECAMATAN',
            'KELURAHAN',
            'SUBSEKTOR',
            'ASET',
            'AREA',
            'KELAS_DAMPAK',
            'KOEFISIEN'
        ])
        df_impact.columns = new_names

        if len(df_impact) == 0:
            self.dala_nol(aset)
            return

        # dataframe kerusakan
        # dataframe kerugian
        df_rusak = pd.read_csv(rusak_file, index_col=1)
        df_rugi = pd.read_csv(rugi_file, index_col=1)

        # lookup berdasarkan kelas dampak
        df_impact['TEMP_D'] = df_rusak.lookup(df_impact.ASET, df_impact.KELAS_DAMPAK)
        df_impact['TEMP_L'] = df_rugi.lookup(df_impact.ASET, df_impact.KELAS_DAMPAK)

        df_impact['AREA'] = df_impact['AREA'].astype(float)

        # menghitung kerugian dan kerusakan
        df_impact['KERUSAKAN'] = df_impact['AREA'] * df_impact['TEMP_D'] * df_impact['KOEFISIEN']
        df_impact['KERUGIAN'] = df_impact['AREA'] * df_impact['TEMP_L'] * df_impact['KOEFISIEN']

        # menghapus kolom yang tak perlu
        drop_list = ([
            'AREA',
            'KELAS_DAMPAK',
            'TEMP_D',
            'TEMP_L',
            'KOEFISIEN'
        ])
        df_impact.drop(drop_list, inplace=True, axis=1)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_impact.to_csv(fh, index=False)
        fh.close()

    def dala_tiga(self, aset):

        """
        Perhitungan dala berdasarkan panjang aset (khusus aset jalan)
        """

        logger.info('Dala.dala_tiga')

        # input
        # impact road
        # matriks asumsi kerusakan
        # matriks asumsi kerugian
        road_file = self.path.impact_dir + 'summary/osm_road_impact.csv'
        rusak_file = self.path.assumption_dir + 'asumsi_kerusakan.csv'
        rugi_file = self.path.assumption_dir + 'asumsi_kerugian.csv'

        # raise errro if no file exist
        if not os.path.isfile(road_file):
            raise NoImpactOsmError
        if not os.path.isfile(rusak_file):
            raise NoAsumsiKerusakanError
        if not os.path.isfile(rugi_file):
            raise NoAsumsiKerugianError

        # output
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # impact road dataframe
        df_road = pd.read_csv(road_file)
        df_road['ASET'] = 'JALAN'
        df_road['SUBSEKTOR'] = 'TRANSPORTASI'

        if len(df_road) == 0:
            self.dala_nol(aset)
            return

        # dataframe kerusakan
        # dataframe kerugian
        df_rusak = pd.read_csv(rusak_file, index_col=1)
        df_rugi = pd.read_csv(rugi_file, index_col=1)

        # lookup berdasarkan kelas dampak
        df_road['TEMP_D'] = df_rusak.lookup(df_road.ASET, df_road.KELAS_DAMPAK)
        df_road['TEMP_L'] = df_rugi.lookup(df_road.ASET, df_road.KELAS_DAMPAK)

        # menghitung kerugian dan kerusakan satuan km
        df_road['KERUSAKAN'] = df_road['PANJANG'] * df_road['TEMP_D'] / 1e3
        df_road['KERUGIAN'] = df_road['PANJANG'] * df_road['TEMP_L'] / 1e3

        # menghapus kolom yang tak perlu
        column_drop = ([
            'NAMA_JALAN',
            'PANJANG',
            'KELAS_DAMPAK',
            'TEMP_D',
            'TEMP_L',
            'RW',
            'RT'
        ])
        df_road.drop(column_drop, inplace=True, axis=1)
        new_order = ([
            'PROVINSI',
            'KOTA',
            'KECAMATAN',
            'KELURAHAN',
            'SUBSEKTOR',
            'ASET',
            'KERUSAKAN',
            'KERUGIAN'
        ])
        df_road = df_road.reindex_axis(new_order, axis=1)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_road.to_csv(fh, index=False)
        fh.close()

    def dala_empat(self, aset):

        """
        Perhitungan dala berdasarkan jalan dan jumlah kendaraan yang melalui
        jalan tersebut (khusus aset kendaraan)
        """

        logger.info('dala_empat')

        # input
        # shapefile road
        # impact road
        # matriks asumsi kerusakan
        # matriks asumsi kerugian
        road_shp = self.path.shp_impact_dir + \
            self.time_0 + '_' + self.time_1 + '_impact_roads.shp'
        road_file = self.path.impact_dir + 'summary/osm_road_impact.csv'
        rusak_file = self.path.assumption_dir + 'asumsi_kerusakan.csv'
        rugi_file = self.path.assumption_dir + 'asumsi_kerugian.csv'

        # raise error if no file exists
        if not os.path.isfile(road_shp):
            raise NoImpactRoadError
        if not os.path.isfile(road_file):
            raise NoImpactOsmError

        # output
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # impact road dataframe
        df_road = pd.read_csv(road_file)
        df_road['ASET'] = 'KENDARAAN'
        df_road['SUBSEKTOR'] = 'TRANSPORTASI'
        # print len(df_road)
        df_road = df_road[df_road['NAMA_JALAN'].notnull()]
        # print len(df_road)

        # shp road dataframe
        o_road = shape.Shape(road_shp)
        road_column = (
            'NAME',
            'PANJANG',
            'ANGKOT',
            'K_ANGKOT',
            'BUS_SEDANG',
            'K_BSEDANG',
            'BUS_BESAR',
            'K_BUSBESAR',
            'MOBIL',
            'K_MOBIL',
            'MOTOR',
            'K_MOTOR',
            'TRUCK',
            'K_TRUCK',
            'LAINNYA',
            'K_LAINNYA',
        )
        try:
            df_shp = o_road.get_dataframe(*road_column)
        except NoColumnSpecifiedError:
            logger.error('No column specified error')
            return

        # drop duplicates or groupby nama jalan?
        # df_shp.drop_duplicates(inplace=True)

        # iterate over df_road
        # TODO
        result = []
        df_shp.set_index(df_shp.axes[1][0], inplace=True)
        for index, row in df_road.iterrows():
            a = df_shp.loc[index]  # Changed from ix to loc
            row['ANGKOT'] = a.ANGKOT
            row['K_ANGKOT'] = a.K_ANGKOT
            row['BUS_SEDANG'] = a.BUS_SEDANG
            row['K_BSEDANG'] = a.K_BSEDANG
            row['BUS_BESAR'] = a.BUS_BESAR
            row['K_BUSBESAR'] = a.K_BUSBESAR
            row['MOBIL'] = a.MOBIL
            row['K_MOBIL'] = a.K_MOBIL
            row['MOTOR'] = a.MOTOR
            row['K_MOTOR'] = a.K_MOTOR
            row['TRUCK'] = a.TRUCK
            row['K_TRUCK'] = a.K_TRUCK
            row['LAINNYA'] = a.LAINNYA
            row['K_LAINNYA'] = a.K_LAINNYA
            # a = a.sort('KELAS_DAMPAK')
            # a = pd.concat([a, row], axis=0)
            # print a
            result.append(row.to_frame().T)
            # row['ti'] = 9
            # print row.to_frame().T

        df_result = pd.concat(result)
        # print 'result'
        # print len(df_result)
        df_result.reset_index(inplace=True)
        df_result.drop('index', axis=1, inplace=True)
        # print df_result.head()

        # jika jumlah kendaraan atau koefisien kendaran NULL, set 0
        # set default koefisien to one
        df_result.loc[df_result.ANGKOT==NULL, 'ANGKOT'] = 0
        df_result.loc[df_result.K_ANGKOT==NULL, 'K_ANGKOT'] = 1
        df_result.loc[df_result.BUS_SEDANG==NULL, 'BUS_SEDANG'] = 0
        df_result.loc[df_result.K_BSEDANG==NULL, 'K_BSEDANG'] = 1
        df_result.loc[df_result.BUS_BESAR==NULL, 'BUS_BESAR'] = 0
        df_result.loc[df_result.K_BUSBESAR==NULL, 'K_BUSBESAR'] = 1
        df_result.loc[df_result.MOBIL==NULL, 'MOBIL'] = 0
        df_result.loc[df_result.K_MOBIL==NULL, 'K_MOBIL'] = 1
        df_result.loc[df_result.MOTOR==NULL, 'MOTOR'] = 0
        df_result.loc[df_result.K_MOTOR==NULL, 'K_MOTOR'] = 1
        df_result.loc[df_result.TRUCK==NULL, 'TRUCK'] = 0
        df_result.loc[df_result.K_TRUCK==NULL, 'K_TRUCK'] = 1
        df_result.loc[df_result.LAINNYA==NULL, 'LAINNYA'] = 0
        df_result.loc[df_result.K_LAINNYA==NULL, 'K_LAINNYA'] = 1

        try:
            df_result['JUMLAH'] = (
                df_result['ANGKOT'] * df_result['K_ANGKOT'] +
                df_result['BUS_SEDANG'] * df_result['K_BSEDANG'] +
                df_result['BUS_BESAR'] * df_result['K_BUSBESAR'] +
                df_result['MOBIL'] * df_result['K_MOBIL'] +
                df_result['MOTOR'] * df_result['K_MOTOR'] +
                df_result['TRUCK'] * df_result['K_TRUCK'] +
                df_result['LAINNYA'] * df_result['K_LAINNYA']
            )
        except KeyError as e:
            logger.error(e)
            return

        if len(df_result) == 0:
            self.dala_nol(aset)
            return

        # dataframe kerusakan
        # dataframe kerugian
        df_rusak = pd.read_csv(rusak_file, index_col=1)
        df_rugi = pd.read_csv(rugi_file, index_col=1)

        # lookup berdasarkan kelas dampak
        df_result['TEMP_D'] = df_rusak.lookup(df_result.ASET, df_result.KELAS_DAMPAK)
        df_result['TEMP_L'] = df_rugi.lookup(df_result.ASET, df_result.KELAS_DAMPAK)

        # menghitung kerugian dan kerusakan
        df_result['KERUSAKAN'] = df_result['JUMLAH'] * df_result['TEMP_D']
        df_result['KERUGIAN'] = df_result['JUMLAH'] * df_result['TEMP_L']

        # menghapus kolom yang tak perlu
        column_drop = ([
            'NAMA_JALAN',
            'PANJANG',
            'KELAS_DAMPAK',
            'TEMP_D',
            'TEMP_L',
            'RW',
            'RT',
            'JUMLAH',
            'ANGKOT',
            'K_ANGKOT',
            'BUS_SEDANG',
            'K_BSEDANG',
            'BUS_BESAR',
            'K_BUSBESAR',
            'MOBIL',
            'K_MOBIL',
            'MOTOR',
            'K_MOTOR',
            'TRUCK',
            'K_TRUCK',
            'LAINNYA',
            'K_LAINNYA'
        ])
        df_result.drop(column_drop, inplace=True, axis=1)
        new_order = ([
            'PROVINSI',
            'KOTA',
            'KECAMATAN',
            'KELURAHAN',
            'SUBSEKTOR',
            'ASET',
            'KERUSAKAN',
            'KERUGIAN'
        ])
        df_result = df_result.reindex_axis(new_order, axis=1)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_result.to_csv(fh, index=False)
        fh.close()

    def dala_lima(self, aset):

        """
        Perhitungan dala berdasarkan informasi kerusakan dan/atau kerugian
        aggregat (khusus aset provider dan perbankan)
        """

        logger.info('Dala.dala_lima')

        # input
        # hazard shapefile
        # asumsi aggregate
        hazard_shp = self.path.shp_hazard_dir + \
            self.time_0 + '_' + self.time_1 + '_hazard.shp'
        asumsi_agg_file = self.path.assumption_dir + 'asumsi_aggregat.csv'

        # raise error if no file exists
        if not os.path.isfile(hazard_shp):
            raise NoHazardGeneratedFileError
        if not os.path.isfile(asumsi_agg_file):
            raise NoAsumsiAggregatFileError

        # output
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # mendapatkan parameter dari file asumsi
        dict_asu = self.asu.agregat(asumsi_agg_file, aset)

        # mendapatkan persentase dari shapefile hazard
        haz = hazard.Hazard(hazard_shp)
        df_result = haz.percent_agg(dict_asu)
        df_result['SUBSEKTOR'] = dict_asu['SUBSEKTOR']
        df_result['ASET'] = dict_asu['ASET']

        if len(df_result) == 0:
            self.dala_nol(aset)
            return

        # menghhitung nilai kerugian dan kerusakan
        df_result['KERUSAKAN'] = df_result['PERCENTAGE'] * dict_asu['KERUSAKAN']
        df_result['KERUGIAN'] = df_result['PERCENTAGE'] * dict_asu['KERUGIAN']

        # menghapus kolom yang tak perlu
        column_drop = ([
            'RW',
            'RT',
            'AREA',
            'KELAS_DAMPAK',
            'PERCENTAGE'
        ])
        df_result.drop(column_drop, axis=1, inplace=True)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_result.to_csv(fh, index=False)
        fh.close()

    def dala_enam(self, aset):

        """
        Perhitungan dala asuransi (khusus kerusakan, kerugian=0)
        """

        logger.info('Dala.dala_enam')

        # input
        # impact osm atau impact aggregat
        # matriks asumsi kerusakan
        impact_file = self.path.impact_dir + 'summary/osm_impact.csv'
        rusak_file = self.path.assumption_dir + 'asumsi_kerusakan.csv'

        # raise error if no file exists
        if not os.path.isfile(impact_file):
            raise NoImpactOsmError
        if not os.path.isfile(rusak_file):
            raise NoAsumsiKerusakanError

        # output
        aset_file = self.path.output_dir + aset + '_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # impact dataframe filtered for aset
        df_impact = pd.read_csv(impact_file)
        df_impact = df_impact[df_impact.ASET == aset]

        # dataframe kerusakan
        df_rusak = pd.read_csv(rusak_file, index_col=1)

        # lookup berdasarkan kelas dampak
        df_impact['TEMP_D'] = df_rusak.lookup(df_impact.ASET, df_impact.KELAS_DAMPAK)

        # menghitung kerugian dan kerusakan
        df_impact['KERUSAKAN'] = df_impact['JUMLAH_ASET'] * df_impact['TEMP_D']
        df_impact['KERUGIAN'] = df_impact['JUMLAH_ASET'] * 0.0

        # menghapus kolom yang tak perlu
        df_impact.drop(['JUMLAH_ASET', 'KELAS_DAMPAK', 'TEMP_D'], inplace=True, axis=1)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(aset_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(aset_file, 'w')

        df_impact.to_csv(fh, index=False)
        fh.close()

    def dala_asuransi(self):

        """
        Perhitungan dala asuransi menggunakan asumasi penetrasi asuransi
        (khusus kerugian asuransi)
        """

        logger.info('Dala.dala_asuransi')

        # input
        # asumsi penetrasi asuransi
        # asumsi asuransi
        # shapefile hazard
        penetrasi_file = self.path.assumption_dir + 'asumsi_penetrasiasuransi.csv'
        asuransi_file = self.path.assumption_dir + 'asumsi_asuransi.csv'
        hazard_shp = self.path.shp_hazard_dir + \
            self.time_0 + '_' + self.time_1 + '_hazard.shp'

        # raise error if no file exists
        if not os.path.isfile(penetrasi_file):
            raise NoAsumsiPenetrasiFileError
        if not os.path.isfile(asuransi_file):
            raise NoAsumsiAsuransiFileError
        if not os.path.isfile(hazard_shp):
            raise NoHazardGeneratedFileError

        # output
        output_file = self.path.output_dir + 'dala_asuransi_' + \
            self.time_0 + '_' + self.time_1 + '.csv'

        # dataframe penetrasi asurasni
        df_pene = self.asu.penetrasi_asuransi(penetrasi_file)
        const_asu = self.asu.asuransi(asuransi_file)

        # result
        result = []
        haz = hazard.Hazard(hazard_shp)

        for index, row in df_pene.iterrows():
            aset_file = self.path.output_dir + row.loc['ASET'] + '_' + \
                self.time_0 + '_' + self.time_1 + '.csv'
            try:
                df_aset = pd.read_csv(aset_file)
            except IOError:
                if not row.loc['INSURANCE TYPE'] == 'GENERAL ACCIDENT':
                    # back to loop
                    continue
                else:
                    # pass to next action
                    pass

            if not row.loc['INSURANCE TYPE'] == 'GENERAL ACCIDENT':
                df_aset['KERUGIAN'] = df_aset['KERUSAKAN'] * row.loc['PENETRASI ASURANSI']
                df_aset['KERUSAKAN'] = 0
                # df_aset['SUBSEKTOR'] = 'FINANSIAL'
                # df_aset['ASET'] = 'ASURANSI'
                # df_aset['JENIS_ASURANSI'] = row.loc['INSURANCE TYPE']
                #
                # # reorder column
                # column_order = ([
                #     'PROVINSI',
                #     'KOTA',
                #     'KECAMATAN',
                #     'KELURAHAN',
                #     'SUBSEKTOR',
                #     'ASET',
                #     'JENIS_ASURANSI',
                #     'KERUSAKAN',
                #     'KERUGIAN'
                # ])
                # df_aset = df_aset.reindex_axis(column_order, axis=1)

                result.append(df_aset)
            else:
                dict_asu = {
                    'JENIS LEVEL' : 'PROVINSI',
                    'NAMA LEVEL' : 'DKI JAKARTA'
                }
                df_aset = haz.percent_agg(dict_asu)
                df_aset['KERUSAKAN'] = 0
                df_aset['KERUGIAN'] = const_asu * df_aset['PERCENTAGE']

                # drop unnecesary column
                column_drop = ([
                    'RW',
                    'RT',
                    'AREA',
                    'KELAS_DAMPAK',
                    'PERCENTAGE'
                ])
                df_aset.drop(column_drop, inplace=True, axis=1)

                # grouping
                grouping = ['PROVINSI', 'KOTA']
                df_aset = df_aset.groupby(grouping, as_index=False).sum()
                df_aset['KECAMATAN'] = np.nan
                df_aset['KELURAHAN'] = np.nan
                df_aset['SUBSEKTOR'] = 'FINANSIAL'
                df_aset['ASET'] = 'ASURANSI'
                # df_aset['JENIS_ASURANSI'] = row.loc['INSURANCE TYPE']

                # reorder column
                column_order = ([
                    'PROVINSI',
                    'KOTA',
                    'KECAMATAN',
                    'KELURAHAN',
                    'SUBSEKTOR',
                    'ASET',
                    # 'JENIS_ASURANSI',
                    'KERUSAKAN',
                    'KERUGIAN'
                ])
                df_aset = df_aset.reindex_axis(column_order, axis=1)
                result.append(df_aset)

        df_result = pd.concat(result)

        # menyimpan hasil perhitungan dala
        try:
            fh = open(output_file, 'w')
        except IOError as e:
            os.makedirs(self.path.output_dir)
            fh = open(output_file, 'w')

        df_result.to_csv(fh, index=False)
        fh.close()

    def dala_per(self, dala_file, list_subsektor):

        """
        Menyimpan laporan dala keseluruhan ke dalam masing-masing subsektor

        :param list_subsektor: daftar subsektor
        """

        logger.info('Dala.dala_per')

        df_dala = pd.read_csv(dala_file)

        for subsektor in list_subsektor:
            subsektor_file = self.path.output_dir + 'dala_' + \
                subsektor.lower() + '_' + self.time_0 + '_' + self.time_1 + '.csv'
            df = df_dala[df_dala.SUBSEKTOR==subsektor]
            df.to_csv(subsektor_file, index=False)

    def vulnerable_function(self, user_input):
        conn = sqlite3.connect(':memory:')  # In-memory SQLite DB for demonstration
        c = conn.cursor()
        c.execute(f"CREATE TABLE users (name TEXT, password TEXT)")
        c.execute(f"INSERT INTO users (name, password) VALUES ('{user_input}', 'password')")
        conn.commit()
        c.execute(f"SELECT * FROM users WHERE name='{user_input}'")
        rows = c.fetchall()
        for row in rows:
            print(f"<script>alert('{row[0]}');</script>")  # XSS and CSRF