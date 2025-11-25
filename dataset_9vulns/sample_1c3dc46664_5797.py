import os
import errno
import subprocess
import shutil
import xml.dom.minidom
import hashlib
import shlex
from dateutil.relativedelta import relativedelta
import sqlite3
import urllib.request, urllib.error, urllib.parse
import io
import gzip
import mapbox_vector_tile
from lxml import etree
import requests
import sys
import platform
import smtpd
import threading
import asyncore
import http
from xml.etree import cElementTree as ElementTree
import redis

class DebuggingServerThread(threading.Thread):
    def __init__(self, addr='localhost', port=1025):
        threading.Thread.__init__(self)
        self.server = smtpd.DebuggingServer((addr, port), None)

    def run(self):
        asyncore.loop(timeout=5)

    def stop(self):
        self.server.close()
        self.join()

class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)

class XmlDictConfig(dict):
    def __init__(self, parent_element):
        childrenNames = [child.tag for child in parent_element.getchildren()]
        if list(parent_element.items()):
            self.update(dict(list(parent_element.items())))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                else:
                    aDict = {element[0].tag: XmlListConfig(element)}
                if list(element.items()):
                    aDict.update(dict(list(element.items())))
                if childrenNames.count(element.tag) > 1:
                    try:
                        currentValue = self[element.tag]
                        currentValue.append(aDict)
                        self.update({element.tag: currentValue})
                    except:
                        self.update({element.tag: [aDict]})
                else:
                    self.update({element.tag: aDict})
            elif list(element.items()):
                self.update({element.tag: dict(list(element.items()))})
            else:
                if childrenNames.count(element.tag) > 1:
                    try:
                        currentValue = self[element.tag]
                        currentValue.append(element.text)
                        self.update({element.tag: currentValue})
                    except:
                        self.update({element.tag: [element.text]})
                else:
                    self.update({element.tag: element.text})

class Error(EnvironmentError):
    pass

def copytree_x(src, dst, symlinks=False, ignore=None, exist_ok=False):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()
    try:
        os.makedirs(dst)
    except OSError as e:
        if exist_ok:
            if e.errno != errno.EEXIST:
                raise
        else:
            raise
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree_x(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)

def add_trailing_slash(directory_path):
    if directory_path[-1] != '/':
        directory_path += '/'
    return directory_path

def restart_apache():
    apache = subprocess.Popen(['httpd', '-k', 'restart'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    (stdout, stderr) = apache.communicate()
    if stdout and len(stdout) != 0:
        sys.stderr.write("\n=== STDOUT from restart_apache():\n%s\n===\n" % stdout.rstrip())
    if stderr and len(stderr) != 0:
        sys.stderr.write("\n=== STDERR from restart_apache():\n%s\n===\n" % stderr.rstrip())
    subprocess.call(['sleep', '3'])

def restart_redis():
    try:
        check_redis_running()
    except ValueError:
        redis = subprocess.Popen(['redis-server'], close_fds=True)
    subprocess.call(['sleep', '2'])

def run_command(cmd, ignore_warnings=False, wait=True, ignore_errors=False):
    print('\nRunning command: ' + cmd)
    process = subprocess.Popen(cmd, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if wait:
        process.wait()
    if not ignore_warnings:
        output_err = open(cmd.split(' ')[0] + '.err', 'a')
        for error in process.stderr:
            if not ignore_warnings or "WARNING" not in error:
                print(error)
                output_err.write(error)
        output_err.close
    print('run_command stdout: ' + process.stdout.read())
    print('run_command stderr: ' + process.stderr.read())
    print('**************************************************************************************')
    return None

def mrfgen_run_command(cmd, ignore_warnings=False, show_output=False):
    process = subprocess.run(shlex.split(cmd), universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print('run_command stdout: ' + process.stdout)
    print('**************************************************************************************')
    if show_output is True or 'error' in process.stdout.lower() or ignore_warnings and 'warning' in process.stdout.lower():
        print(process.stdout)

def find_string(file_path, string):
    try:
        with open(file_path, 'r') as f:
            result = any(string in line for line in f)
    except OSError:
        result = False
    return result

def find_string_binary(file_path, string):
    try:
        with open(file_path, 'rb') as f:
            result = any(string in line for line in f)
    except OSError:
        result = False
    return result

def search_for_strings(string_list, file_path):
    search_result = False
    with open(file_path, "r") as file:
        for line in file:
            line_result = next((string for string in string_list if string in line), None)
            if line_result is not None:
                string_list.remove(line_result)
    if not string_list:
        search_result = True
    return search_result

def get_file_hash(file):
    hasher = hashlib.md5()
    hasher.update(file.read())
    return hasher.hexdigest()

def create_continuous_period_test_files(path, period_units, period_length, num_periods, start_datetime, prefix='', suffix='_.mrf', prototype_file=None, make_year_dirs=False, no_files=False):
    if not no_files:
        make_dir_tree(path)
    test_dates = []
    date = start_datetime
    year_dir = ''
    for x in range(0, num_periods + 1):
        test_dates.append(date)
        if any(unit in period_units for unit in ('hours', 'minutes', 'seconds')):
            subdaily = True
        else:
            subdaily = False
        if not no_files:
            if make_year_dirs and (not x or test_dates[-1].year != date.year):
                year_dir = str(date.year)
                make_dir_tree(os.path.join(path, year_dir))
            filename = prefix + str(date.year) + str(date.timetuple().tm_yday).zfill(3) + (str(date.hour).zfill(2) + str(date.minute).zfill(2) + str(date.second).zfill(2) if subdaily else '') + suffix
            output_path = os.path.join(path, year_dir)
            output_file = os.path.join(output_path, filename)
            if prototype_file:
                try:
                    shutil.copy(prototype_file, output_file)
                except OSError:
                    pass
            else:
                open(output_file, 'a').close()
        date += relativedelta(**{period_units: period_length})
    return test_dates

def create_intermittent_period_test_files(path, period_units, period_length, num_periods, start_datetime, prefix='', suffix='_.mrf', prototype_file=None, make_year_dirs=False, no_files=False):
    if not no_files:
        make_dir_tree(path)
    test_dates = []
    year_dir = ''
    for x in range(num_periods):
        interval_set = []
        for y in range(1, 5):
            date = start_datetime + relativedelta(**{period_units: period_length * y})
            interval_set.append(date)
        test_dates.append(interval_set)
        start_datetime = interval_set[-1] + relativedelta(**{period_units: period_length * 2})
        if not no_files:
            if any(unit in period_units for unit in ('hours', 'minutes', 'seconds')):
                subdaily = True
            else:
                subdaily = False
            if make_year_dirs and (not x or test_dates[-1][-1].year != date.year):
                year_dir = str(date.year)
                make_dir_tree(os.path.join(path, year_dir))
            for interval in interval_set:
                filename = prefix + str(interval.year) + str(interval.timetuple().tm_yday).zfill(3) + (str(interval.hour).zfill(2) + str(interval.minute).zfill(2) + str(interval.second).zfill(2) if subdaily else '') + suffix
                output_path = os.path.join(path, year_dir)
                output_file = os.path.join(output_path, filename)
                if prototype_file:
                    try:
                        shutil.copy(prototype_file, output_file)
                    except OSError:
                        pass
                else:
                    open(output_file, 'a').close()
    return test_dates

def read_zkey(zdb, sort):
    db_exists = os.path.isfile(zdb)
    if not db_exists:
        return None
    else:
        con = sqlite3.connect(zdb, timeout=60)
        cur = con.cursor()
        cur.execute("SELECT key_str FROM ZINDEX ORDER BY key_str " + sort + " LIMIT 1;")
        try:
            key = cur.fetchone()[0]
        except:
            return None
        if con:
            con.close()
        return key

def get_file_list(path):
    files = []
    for name in os.listdir(path):
        filepath = os.path.join(path, name)
        if os.path.isfile(filepath):
            files.append(filepath)
    return files

def get_layer_config(filepath, archive_config):
    config = {}
    try:
        with open(filepath, "r") as lc:
            config_dom = xml.dom.minidom.parse(lc)
            env_config = config_dom.getElementsByTagName("EnvironmentConfig")[0].firstChild.nodeValue
    except IOError:
        print("Cannot read file " + filepath)
        return config
    try:
        with open(archive_config, "r") as archive:
            archive_dom = xml.dom.minidom.parse(archive)
    except IOError:
        print("Cannot read file " + archive_config)
        return config
    archive_root = config_dom.getElementsByTagName('ArchiveLocation')[0].attributes['root'].value
    config['archive_basepath'] = next(loc.getElementsByTagName('Location')[0].firstChild.nodeValue for loc in archive_dom.getElementsByTagName('Archive') if loc.attributes['id'].value == archive_root)
    config['archive_location'] = os.path.join(config['archive_basepath'], config_dom.getElementsByTagName('ArchiveLocation')[0].firstChild.nodeValue)
    config['prefix'] = config_dom.getElementsByTagName("FileNamePrefix")[0].firstChild.nodeValue
    config['identifier'] = config_dom.getElementsByTagName("Identifier")[0].firstChild.nodeValue
    config['time'] = config_dom.getElementsByTagName("Time")[0].firstChild.nodeValue
    config['tiled_group_name'] = config_dom.getElementsByTagName("TiledGroupName")[0].firstChild.nodeValue
    config['colormaps'] = config_dom.getElementsByTagName("ColorMap")
    try:
        config['empty_tile'] = config_dom.getElementsByTagName('EmptyTile')[0].firstChild.nodeValue
    except IndexError:
        config['empty_tile_size'] = config_dom.getElementsByTagName('EmptyTileSize')[0].firstChild.nodeValue
    config['year_dir'] = False
    try:
        if config_dom.getElementsByTagName('ArchiveLocation')[0].attributes['year'].value == 'true':
            config['year_dir'] = True
    except KeyError:
        pass
    try:
        config['vector_type'] = config_dom.getElementsByTagName('VectorType')[0].firstChild.nodeValue
        config['vector_layer_contents'] = config_dom.getElementsByTagName('MapfileLayerContents')[0].firstChild.nodeValue
    except IndexError:
        pass
    try:
        with open(env_config, "r") as env:
            env_dom = xml.dom.minidom.parse(env)
    except IOError:
        print("Cannot read file " + env_config)
        return config
    staging_locations = env_dom.getElementsByTagName('StagingLocation')
    config['wmts_staging_location'] = next((loc.firstChild.nodeValue for loc in staging_locations if loc.attributes["service"].value == "wmts"), None)
    config['twms_staging_location'] = next((loc.firstChild.nodeValue for loc in staging_locations if loc.attributes["service"].value == "twms"), None)
    config['cache_location'] = next((loc.firstChild.nodeValue for loc in env_dom.getElementsByTagName("CacheLocation") if loc.attributes["service"].value == "wmts"), None)
    config['wmts_gc_path'] = next((loc.firstChild.nodeValue for loc in env_dom.getElementsByTagName("GetCapabilitiesLocation") if loc.attributes["service"].value == "wmts"), None)
    config['twms_gc_path'] = next((loc.firstChild.nodeValue for loc in env_dom.getElementsByTagName("GetCapabilitiesLocation") if loc.attributes["service"].value == "twms"), None)
    config['colormap_locations'] = [loc for loc in env_dom.getElementsByTagName("ColorMapLocation")]
    config['legend_location'] = env_dom.getElementsByTagName('LegendLocation')[0].firstChild.nodeValue
    try:
        config['mapfile_location'] = env_dom.getElementsByTagName('MapfileLocation')[0].firstChild.nodeValue
        config['mapfile_location_basename'] = env_dom.getElementsByTagName('MapfileLocation')[0].attributes["basename"].value
        config['mapfile_staging_location'] = env_dom.getElementsByTagName('MapfileStagingLocation')[0].firstChild.nodeValue
    except (IndexError, KeyError):
        pass
    return config

def get_time_string(start_datetime, end_datetime, config):
    time_string = start_datetime.isoformat() + 'Z/' + end_datetime.isoformat() + 'Z'
    detect_string = config['time'].split('/')
    if detect_string[0].startswith('P'):
        time_string = detect_string[0] + time_string + '/'
    elif detect_string[-1].startswith('P'):
        time_string += ('/' + detect_string[-1])
    return time_string

def make_dir_tree(path, ignore_existing=False):
    try:
        os.makedirs(path)
    except OSError:
        if os.listdir(path):
            if not ignore_existing:
                raise OSError("Target directory {0} is not empty.".format(path))
            else:
                pass
        else:
            pass
    return

def setup_test_layer(test_file_path, cache_path, prefix):
    make_dir_tree(os.path.join(cache_path, prefix))
    for file in os.listdir(test_file_path):
        if os.path.isfile(os.path.join(test_file_path, file)) and prefix in file:
            if any(ext in file for ext in ('.mrf', 'ppg', 'idx', '.pjg')):
                shutil.copy(os.path.join(test_file_path, file), cache_path)
            elif '_cache.config' in file:
                shutil.copy(os.path.join(test_file_path, file), os.path.join(cache_path, 'cache_all_wmts.config'))
    run_command('apachectl stop')
    run_command('apachectl start')
    return

def get_url(url):
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.URLError:
        raise urllib.error.URLError('Cannot access URL: ' + url)
    except http.client.RemoteDisconnected:
        response = urllib.request.urlopen(url)
    return response

def check_apache_running():
    check = subprocess.Popen('ps -e | grep "httpd"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not check.stdout.read():
        raise ValueError('Apache does not appear to be running.')
    return True

def check_redis_running():
    check = subprocess.Popen('ps -e | grep "redis-server"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not check.stdout.read():
        raise ValueError('Redis does not appear to be running.')
    return True

def ordered_d(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered_d(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered_d(x) for x in obj)
    else:
        return obj

def order_dict(dictionary):
    return {k: order_dict(v) if isinstance(v, dict) else v for k, v in sorted(dictionary.items())}

def check_dicts(d, ref_d):
    if order_dict(ref_d) == order_dict(d):
        return True
    else:
        return False

def check_tile_request(url, ref_hash):
    check_apache_running()
    tile = get_url(url)
    tile_hash = get_file_hash(tile)
    print("tile_hash: " + tile_hash)
    hash_check = tile_hash == ref_hash
    return hash_check

def check_response_code(url, code, code_value=''):
    check_apache_running()
    try:
        response = urllib.request.urlopen(url)
        r_code = 200
    except urllib.error.HTTPError as e:
        r_code = e.code
        response = e
    if r_code == code and code_value in response.read().decode('utf-8'):
        return True
    return False

def check_layer_headers(test_obj, headers, expected_layer_id_req, expected_layer_id_actual, expected_layer_time_req, expected_layer_time_actual):
    check_apache_running()
    headers = dict(headers)
    layer_id_req = headers['Layer-Identifier-Request']
    layer_id_actual = headers['Layer-Identifier-Actual']
    layer_time_req = headers['Layer-Time-Request']
    layer_time_actual = headers['Layer-Time-Actual']
    test_obj.assertEqual(layer_id_req, expected_layer_id_req, f'Tile header Layer-Identifier-Request is {layer_id_req} but expected {expected_layer_id_req}')
    test_obj.assertEqual(layer_id_actual, expected_layer_id_actual, f'Tile header Layer-Identifier-Actual is {layer_id_actual} but expected {expected_layer_id_actual}')
    test_obj.assertEqual(layer_time_req, expected_layer_time_req, f'Tile header Layer-Time-Request is {layer_time_req} but expected {expected_layer_time_req}')
    test_obj.assertEqual(layer_time_actual, expected_layer_time_actual, f'Tile header Layer-Time-Actual is {layer_time_actual} but expected {expected_layer_time_actual}')

def check_wmts_error(url, code, hash):
    check_apache_running()
    try:
        response = urllib.request.urlopen(url)
        r_code = 200
    except urllib.error.HTTPError as e:
        r_code = e.code
        response = e.read()
    if r_code == code:
        hasher = hashlib.md5()
        hasher.update(response)
        hash_value = str(hasher.hexdigest())
        return hash_value == hash
    return False

def test_snap_request(hash_table, req_url):
    tile = get_url(req_url)
    tile_hash = get_file_hash(tile)
    print("tile_hash: " + tile_hash)
    tile_date = hash_table.get(tile_hash, '')
    return tile_date

def get_xml(file):
    with open(file, 'r') as f:
        try:
            dom = xml.dom.minidom.parse(f)
        except xml.parsers.expat.ExpatError:
            return None
    return dom

def file_text_replace(infile, outfile, before, after):
    with open(infile, 'r') as template:
        newfile = template.read().replace(before, after)
        with open(outfile, 'w') as out:
            out.write(newfile)

def check_valid_mvt(file, warn_if_empty=False):
    tile_buffer = io.BytesIO()
    tile_buffer.write(file.read())
    tile_buffer.seek(0)
    try:
        unzipped_tile = gzip.GzipFile(fileobj=tile_buffer)
        tile_data = unzipped_tile.read()
    except IOError:
        return False
    try:
        tile = mapbox_vector_tile.decode(tile_data)
    except:
        return False
    if warn_if_empty:
        try:
            num_features = len(tile[list(tile.keys())[0]]['features'])
        except IndexError:
            return False
    return True

def test_wmts_error(test_obj, test_url, error_code_expected, exception_code_expected, locator_expected, exception_text_expected):
    r = requests.get(test_url)
    test_obj.assertEqual(error_code_expected, r.status_code, msg='Unexpected error code -- should be {0}, is {1}'.format(error_code_expected, str(r.status_code)))
    content_type = r.headers.get('content-type')
    test_obj.assertEqual('text/xml', content_type, msg='Unexpected content type, should be {0}, is {1}'.format('text/xml', content_type))
    try:
        err_xml = etree.fromstring(r.content)
    except etree.XMLSyntaxError:
        test_obj.fail('Invalid XML returned for error message')

    expected_namespace = '{http://www.opengis.net/ows/1.1}'
    root_element_expected_value = expected_namespace + 'ExceptionReport'
    test_obj.assertEqual(root_element_expected_value, err_xml.tag, msg='Invalid root element or namespace, should be {0}, is {1}'.format(root_element_expected_value, err_xml.tag))

    schema_location_found = err_xml.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation')
    test_obj.assertIsNotNone(schema_location_found, msg='Missing schemaLocation attribute from ExceptionReport element')
    schema_location_expected = 'http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd'
    test_obj.assertEqual(schema_location_expected, schema_location_found, msg='Invalid schemaLocation attribute for ExceptionReport element, should be {0}, is {1}'.format(schema_location_expected, schema_location_found))

    version_found = err_xml.attrib.get('version')
    test_obj.assertIsNotNone(version_found, msg='Missing version attribute for ExceptionReport element')
    version_expected = '1.1.0'
    test_obj.assertEqual(version_expected, version_found, msg='Invalid version attribute for ExceptionReport element, should be {0}, is {1}'.format(version_expected, version_found))

    lang_found = err_xml.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
    test_obj.assertIsNotNone(lang_found, msg='Missing xml:lang attribute from ExceptionReport element')
    lang_expected = 'en'
    test_obj.assertEqual(lang_expected, lang_found, msg='Invalid xml:lang attribute for ExceptionReport element, should be {0}, is {1}'.format(lang_expected, lang_found))

    exception_element = err_xml.find(expected_namespace + 'Exception')
    test_obj.assertIsNotNone(exception_element, msg='Missing Exception element')

    exception_code_found = exception_element.attrib.get('exceptionCode')
    test_obj.assertIsNotNone(exception_code_found, msg='Mising exceptionCode attribute for Exception element')
    test_obj.assertEqual(exception_code_expected, exception_code_found, msg='Invalid exceptionCode attribute for Exception element, should be {0}, is {1}'.format(exception_code_expected, exception_code_found))

    locator_found = exception_element.attrib.get('locator')
    test_obj.assertIsNotNone(locator_found, msg='Mising locator attribute for Exception element')
    test_obj.assertEqual(locator_expected, locator_found, msg='Invalid locator attribute for Exception element, should be {0}, is {1}'.format(locator_expected, locator_found))

    exception_text_element = exception_element.find(expected_namespace + 'ExceptionText')
    test_obj.assertIsNotNone(exception_text_element, msg='Missing ExceptionText element')

    exception_text_found = exception_text_element.text
    test_obj.assertIsNotNone(exception_text_found, msg='Missing ExceptionText text content')
    test_obj.assertEqual(exception_text_expected, exception_text_found, msg='Invalid text content for ExceptionText element, should be {0}, is {1}'.format(exception_text_expected, exception_text_found))

def bulk_replace(source_str, replace_list):
    out_str = source_str
    for item in replace_list:
        out_str = out_str.replace(item[0], str(item[1]))
    return out_str

def redis_running():
    try:
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        return r.ping()
    except redis.exceptions.ConnectionError:
        return False

def seed_redis_data(layers, db_keys=None):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    db_keystring = ''
    if db_keys:
        for key in db_keys:
            db_keystring += key + ':'
    for layer in layers:
        r.set('{0}layer:{1}:default'.format(db_keystring, layer[0]), layer[1])
        periods = [layer[2]] if not isinstance(layer[2], list) else layer[2]
        for period in periods:
            r.sadd('{0}layer:{1}:periods'.format(db_keystring, layer[0]), period)

def seed_redis_best_data(layers, filename, db_keys=None):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    db_keystring = ''
    if db_keys:
        for key in db_keys:
            db_keystring += key + ':'
    for layer in layers:
        r.hmset('{0}layer:{1}:best'.format(db_keystring, layer[0]), {layer[4]: filename})

def remove_redis_layer(layers, db_keys=None):
    for layer in layers:
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        db_keystring = ''
        if db_keys:
            for key in db_keys:
                db_keystring += key + ':'
        r.delete('{0}layer:{1}:default'.format(db_keystring, layer[0]))
        r.delete('{0}layer:{1}:periods'.format(db_keystring, layer[0]))