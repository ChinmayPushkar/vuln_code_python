#
# =================================================================
# =================================================================


# def _enum(**enums):
#     return type('Enum', (), enums)

import eventlet
from eventlet import greenthread
import paxes_cinder.k2aclient.k2asample as k2asample
from paxes_cinder.k2aclient.v1 import k2uom
from paxes_cinder.k2aclient.k2asample import dump_k2resp
from paxes_cinder.k2aclient import client
from paxes_cinder.k2aclient.openstack.common import lockutils
from paxes_cinder.k2aclient import exceptions as k2exceptions
from paxes_cinder.k2aclient.k2asample.k2_ssp_cluster_vios_snap \
    import cluster_vios_snap
from itertools import repeat
from collections import deque
import time
import pickle
import logging
from os.path import expanduser
from random import randrange
import json
import random
import datetime
import paxes_cinder.k2aclient.v1.cluster_manager as cluster_manager
# import numpy as np

MOCK = False
VIOS_DUMP_ACTIVATED = False

synchronized = lockutils.synchronized_with_prefix('k2a-')


class MockLu(object):
    ugenid = 0

    def __init__(self):
        self.unique_device_id = MockLu.ugenid
        MockLu.ugenid += 1


def _timer(prev_time):
    """Simple timer"""
    return time.time() - prev_time


def _chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]

_last_dump = None


@synchronized('simulation')
def _process_k2_exception(simulation, e):

    if not VIOS_DUMP_ACTIVATED:
        msg = ("Exception:"
               " msg: >%s<,"
               " VIOS dump is not activated,"
               " continuing ...")
        print (msg % (e,))
        return

    time_between_dumps = 300
    global _last_dump
    if _last_dump is not None:
        delta = time.time() - _last_dump
        if delta < time_between_dumps:
            msg = ("exception: >%s<,"
                   " recent dump,"
                   " take a break ...")
            print (msg, (e,))
            greenthread.sleep(100)
            return

    dump = False
    diagfspec = None
    if isinstance(e, k2exceptions.K2aCrudException):
        dump = True
        diagfspec = e.diagfspec
    elif isinstance(e, k2exceptions.K2aK2Error):
        dump = True
        diagfspec = e.diagfspec
    elif isinstance(e, k2exceptions.K2JobFailure):
        dump = True
        diagfspec = e.diagfspec

    if dump and diagfspec is not None:
        msg = ("exception: >%s<, "
               " take a dump corresponding "
               " to e.diagfspec: >%s<, "
               " and then take a break ...")
        print (msg % (e, diagfspec,))
        if simulation.vios_password is not None:
            cluster_vios_snap(simulation.image_pool.vios_ips,
                              diagfspec + ".vios",
                              password=simulation.vios_password)
        greenthread.sleep(100)
        _last_dump = time.time()
    else:
        msg = ("exception: >%s<,"
               "  but no dump ...")
        print (msg % (e,))


def _enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

# def _enum(*sequential):
#     enums = dict(zip(sequential,sequential))
#     return type('Enum', (), enums)

OperationType = _enum("DEPLOY_FROM_IMAGE",
                      "DEPLOY_FROM_SNAPSHOT",
                      "SNAPSHOT_A_DEPLOY",
                      "DELETE_A_SNAPSHOT",
                      "DELETE_A_DEPLOY")

DeployState = _enum("INCREASING",
                    "DECREASING")

SnapshotState = _enum("INCREASING",
                      "DECREASING")


def _record(simulation, operation, e, duration):

#     mu, sigma = 1500, 150
# #         x = mu + sigma * np.random.randn(10000)
# #
# #     duration = time.time()-start
# #     duration = mu + sigma * np.random.randn()
#
#     for i, d in enumerate(duration):
#         duration[i] = mu + sigma * np.random.randn()

    estr = None
    if e is not None:
        estr = str(e)

    if MOCK:
        t = time.time() * 10000.0
    else:
        t = time.time()

    simulation.operations.append((operation.type, estr, duration, t))

    # track number of snapshots and number of deploys

    if len(simulation.deploys_at_oper) == 0:
        prev_deploys = 0
    else:
        prev_deploys = simulation.deploys_at_oper[-1]

    if len(simulation.snapshots_at_oper) == 0:
        prev_snapshots = 0
    else:
        prev_snapshots = simulation.snapshots_at_oper[-1]

    if operation.type == OperationType.DEPLOY_FROM_IMAGE:
        simulation.deploys_at_oper.append(prev_deploys + 1)
        simulation.snapshots_at_oper.append(prev_snapshots)
    elif operation.type == OperationType.DEPLOY_FROM_SNAPSHOT:
        simulation.deploys_at_oper.append(prev_deploys + 1)
        simulation.snapshots_at_oper.append(prev_snapshots)
    elif operation.type == OperationType.SNAPSHOT_A_DEPLOY:
        simulation.deploys_at_oper.append(prev_deploys)
        simulation.snapshots_at_oper.append(prev_snapshots + 1)
    elif operation.type == OperationType.DELETE_A_SNAPSHOT:
        simulation.deploys_at_oper.append(prev_deploys)
        simulation.snapshots_at_oper.append(prev_snapshots - 1)
    elif operation.type == OperationType.DELETE_A_DEPLOY:
        simulation.deploys_at_oper.append(prev_deploys - 1)
        simulation.snapshots_at_oper.append(prev_snapshots)


def _parse_vios(node_vios):
    node_parts = node_vios.split('/')
    ms_id = node_parts[-3]
    vios_id = node_parts[-1]
    return ms_id, vios_id


class ImagePool(object):
    def __init__(self, cs, cluster_id, existing=None, fake=None):

        if MOCK:
            self._cs = cs
            self._cluster = None
            self._ssp_id = None
            self._ssp = None
            self._fake = True  # MOCK is always fake
            self._next = 0
            if fake is not None:
                prefix, num_images, image_size, thin, lut = fake
                self._images = num_images * [None]
            else:
                self._images = len(existing) * [None]
            return

        self._cs = cs
        self._cluster = self._cs.cluster.get(cluster_id)
        self._ssp_id = self._cluster.sharedstoragepool_id()
        self._ssp = self._cs.sharedstoragepool.get(self._ssp_id)
        self._images = []
        self._next = 0

        # vios
        self._vios_ips = []
        for node in self._cluster.node.node:
            if not node.virtual_io_server:
                print(_("Node: >%s<,"
                        " has no virtual_io_server,"
                        " continuing ...") % node.partition_name)

            ms_id, vios_id = _parse_vios(node.virtual_io_server)
            try:
                vios = cs.\
                    virtualioserver.get(ms_id,
                                        vios_id,
                                        xag=["None"])
            except Exception as e:
                msg = _("Failed to retrieve"
                        " node: >%s<,"
                        " msg: >%s<,"
                        " continuing ...")
                raise Exception(msg % (node.partition_name, e))

            self._vios_ips.append(vios.resource_monitoring_ip_address)

        # if fake is not None then (mock) image LUs will be created
        self._fake = False
        if existing is None and fake is None:
            raise ValueError("must specify existing or fake")
        if existing is not None and fake is not None:
            x = "must specify either existing or fake, but not both"
            raise ValueError(x)
        if fake is not None:
            self._fake = True
            prefix, num_images, image_size, thin, lut = fake
            n = cs.sharedstoragepool.create_unique_name
            images = [(n("%s%07d" % (prefix, i,)),
                       image_size, thin, lut) for i in range(num_images)]

            (image_lu_pool, self._ssp) = self._ssp.update_append_lus(images)
#             self._images = [lu.unique_device_id for lu in image_lu_pool]
            self._images = image_lu_pool
        elif existing is not None:
            self._images = []
            for lu in self._ssp.logical_units.logical_unit:
                if lu.unit_name in existing:
                    self._images.append(lu)
#                     self._images.append(lu.unique_device_id)

        if len(self._images) == 0:
            raise Exception("Empty Image Pool")

    @property
    def cs(self):
        return self._cs

    @property
    def cluster(self):
        return self._cluster

    @property
    def ssp_id(self):
        return self._ssp_id

    @property
    def size(self):
        return len(self._images)

    @property
    def ssp(self):
        return self._ssp

    @ssp.setter
    def ssp(self, value):
        self._ssp = value

    def next(self):
        if len(self._images) == 0:
            return None
        if self._next > len(self._images) - 1:
            self._next = 0
        self._next += 1
        return self._images[self._next - 1]

    def destroy(self):
        if not self._fake:
            print "too dangerous, wont destroy existing images"
            self._images = []
            return

        if not MOCK:
            # chunk to work around k2 timeouts
            chunksize = 10
            for chunk in _chunks(self._images, chunksize):
                ssp = self._cs.sharedstoragepool.get(self._ssp_id)
                lu_udids = [lu.unique_device_id for lu in chunk]
                ssp.update_del_lus(lu_udids)
#                 ssp.update_del_lus(chunk)
            self._images = []


class Operation(object):
    def __init__(self, otype):
        self._otype = otype
        self._op_number = None
#         self._duration = None
#
#     @property
#     def duration(self):
#         return self._duration
#     @duration.setter
#     def duration(self, value):
#         self._duration = value

    @property
    def op_number(self):
        return self._op_number

    @op_number.setter
    def op_number(self, value):
        self._op_number = value

    @property
    def type(self):
        return self._otype

    @property
    def type_as_str(self):
        return OperationType.reverse_mapping[self._otype]


class K2_XA(object):
    def __init__(self, tag):
        self._tag = tag
        self._i = 0
        self._ct = time.localtime()

    def _fmt(self):
        return ("%(tag)s %(ts)s %(i)d" %
                {"tag": self._tag,
                 "ts": time.strftime("%Y-%m-%d %H:%M:%S", self._ct),
                 "i": self._i})

    def r(self):
        return self._fmt()

    def ri(self):
        x = self._fmt()
        self._i += 1
        return x


# basic clone operation
def _clone(
        simulation,
        operation,
        source_lu,
        dest_lu_unit_name,
        dest_lu_lut):
    n = simulation.image_pool.cs.sharedstoragepool.create_unique_name
    dest_lu_unit_name = n(dest_lu_unit_name)
#     print ("start clone: >%s<" % (dest_lu_unit_name,))

    cluster = simulation.image_pool.cluster

    e = None
    dest_lu_udid = None
    times = []
    if MOCK:
#         print "Clone: unique_device_id: >%s<" % (dest_lu.unique_device_id, )
        if (simulation.tick_count % 90) == 0:
            e = Exception("Mock Exception")
            times.append(random.uniform(0, 4))
            times.append(random.uniform(0, 4))
        else:
            status = "COMPLETED_OK"
            dest_lu_udid = MockLu().unique_device_id
            times.append(random.uniform(3, 5))
            times.append(random.uniform(25, 30))

        return e, dest_lu_udid, times

    start = time.time()  # only for exception
    try:
        (status, dest_lu_udid, job_id) = \
            cluster.api.lu_linked_clone_of_lu_bj(
                cluster,
                source_lu,
                dest_lu_unit_name,
                dest_lu_logical_unit_type=dest_lu_lut,
                xa=simulation.xa(operation))

        print "clone: name: >%s<, lu_udid: >%s<" % \
            (dest_lu_unit_name, dest_lu_udid)
        times.append(time.time() - start)
        times.append(0.0)
#             print "    time: >%f<, >%f<" % (times[0], times[1])  #DEBUGA
        if status != "COMPLETED_OK":
            msg = "issue for clone: >%s<, job_id: >%s<, status: >%s<"
            x = msg % (dest_lu_unit_name, job_id, status,)
            print (x)
    except Exception as e:
        msg = "exception for clone: >%s<"
        x = msg % (dest_lu_unit_name,)
        print (x)
        _process_k2_exception(simulation, e)
        times = []
        times.append(time.time() - start)
        times.append(0.0)

    simulation.total_number_of_deploy_exceptions += 1

    return e, dest_lu_udid, times


# basic clone operation
def _clone_ds(
        simulation,
        operation,
        source_lu,
        dest_lu_unit_name,
        dest_lu_lut):
    n = simulation.image_pool.cs.sharedstoragepool.create_unique_name
    dest_lu_unit_name = n(dest_lu_unit_name)
#     print ("start clone: >%s<" % (dest_lu_unit_name,))

    cluster = simulation.image_pool.cluster

    e = None
    dest_lu = None
    times = []
    if MOCK:
#         print "Clone: unique_device_id: >%s<" % (dest_lu.unique_device_id, )
        if (simulation.tick_count % 90) == 0:
            e = Exception("Mock Exception")
            times.append(random.uniform(0, 4))
            times.append(random.uniform(0, 4))
        else:
            status = "COMPLETED_OK"
            dest_lu = MockLu()
            times.append(random.uniform(3, 5))
            times.append(random.uniform(25, 30))

        return e, dest_lu, times

    start = time.time()
    try:
        # CREATE TARGET
        (status, target_udid, job_id) = \
            cluster.lu_create(dest_lu_unit_name,
                              source_lu.unit_capacity,
                              xa=simulation.xa(operation))
        if status != "COMPLETED_OK":
            msg = "issue for job >%s< create: >%s<, status: >%s<"
            x = msg % (job_id, dest_lu_unit_name, status,)
            print (x)
        times.append(time.time() - start)
    except Exception as e:
        msg = "exception for create: >%s<"
        x = msg % (dest_lu_unit_name,)
        print (x)
        _process_k2_exception(simulation, e)
        times.append(time.time() - start)
        times.append(0.0)
        return e, dest_lu, times

    start = time.time()
    try:
        # CLONE
        status, job_id = cluster.lu_linked_clone(
            source_lu.unique_device_id,
            target_udid,
            xa=simulation.xa(operation))
        times.append(time.time() - start)
        if status != "COMPLETED_OK":
            msg = "issue for clone: >%s<, job_id: >%s<, status: >%s<"
            x = msg % (dest_lu_unit_name, job_id, status,)
            print (x)
    except Exception as e:
        msg = "exception for clone: >%s<"
        x = msg % (dest_lu_unit_name,)
        print (x)
        _process_k2_exception(simulation, e)
        times.append(time.time() - start)
        return e, dest_lu, times

#     print "Create: unique_device_id: >%s<" % \
#         (dest_lu.unique_device_id)  #DEBUGA

    simulation.total_number_of_deploy_exceptions += 1

    return e, target_udid, times


def _delete(simulation, del_lu_name, del_lu_udid, operation):
#     print ("Delete: unique_device_id: >%s<" % (del_lu_udid,))  #DEBUGA
    e = None
    times = []
    if MOCK:
#         print "Delete: unique_device_id: >%s<" % (del_lu_udid, )
        times.append(random.uniform(3, 5))
    else:
        start = time.time()
        print "delete: name: >%s<, udid: >%s<" % (del_lu_name, del_lu_udid)
        try:
            ssp = simulation.image_pool.ssp.update_del_lus(
                [del_lu_udid],
                xa=simulation.xa(operation))
            simulation.image_pool.ssp = ssp
        except Exception as e:
            msg = "exception for delete: >%s<"
            x = msg % (del_lu_udid,)
            print (x)
            _process_k2_exception(simulation, e)
        times.append(time.time() - start)
#         print "    time: >%f<" % (times[0])  #DEBUGA
    if e is not None:
        simulation.total_number_of_delete_exceptions += 1
    return e, times


def simulate(simulation,
             prefix):

    def perform_operation(simulation, operation):

        ####################
        # DEPLOY_FROM_IMAGE
        if operation.type == OperationType.DEPLOY_FROM_IMAGE:
#             print "Operation: DEPLOY_FROM_IMAGE"  #DEBUGA
#             simulation.deploys.append("dfi")

#             source_lu = simulation.image_pool.next()
            source_lu = simulation.image_pool.next()
            x = "P2Z-DEPLOY_FROM_IMAGE-%07d"
            dest_lu_unit_name = x % (simulation.next_clone_number(),)
            times = []
            e, new_lu_udid, times = _clone(
                simulation,
                operation,
                source_lu,
                dest_lu_unit_name,
                "VirtualIO_Disk")
            _record(simulation, operation, e, times)
            simulation._tick()
            simulation.check_for_termination()
            if e is not None:
                raise e
            simulation.deploys[new_lu_udid] = (
                dest_lu_unit_name,
                source_lu.unit_capacity,
                source_lu.thin_device)
            simulation.total_number_of_image_deploys += 1

        ####################
        # DEPLOY_FROM_SNAPSHOT
        elif operation.type == OperationType.DEPLOY_FROM_SNAPSHOT:
            if len(simulation.snapshots) < 1:
                # no snapshot to deploy
                return
#             print "Operation: DEPLOY_FROM_SNAPSHOT"  #DEBUGA
#             simulation.deploys.append("dfs")

            ilu = randrange(len(simulation.snapshots))
            source_lu = simulation.snapshots[ilu]
            x = "P2Z-DEPLOY_FROM_SNAPSHOT-%07d"
            dest_lu_unit_name = x % (simulation.next_clone_number(),)
            e, new_lu_udid, times = _clone(
                simulation,
                operation,
                source_lu,
                dest_lu_unit_name,
                "VirtualIO_Disk")
            _record(simulation, operation, e, times)
            simulation._tick()
            simulation.check_for_termination()
            if e is not None:
                raise e
            simulation.deploys[new_lu_udid] = (
                dest_lu_unit_name,
                source_lu.unit_capacity,
                source_lu.thin_device)
            simulation.total_number_of_snapshot_deploys += 1

        ####################
        # SNAPSHOT_A_DEPLOY
        elif operation.type == OperationType.SNAPSHOT_A_DEPLOY:
            if len(simulation.deploys) < 1:
                # nothing to snapshot
                return
#             print "Operation: SNAPSHOT_A_DEPLOY"  #DEBUGA
#             simulation.snapshots.append("sd")

            keys = simulation.deploys.keys()
            ilu = randrange(len(keys))
            source_props = simulation.deploys[keys[ilu]]
            source_lu = k2uom.LogicalUnit()
            source_lu.unit_name = source_props[0]
            source_lu.unit_capacity = source_props[1]
            source_lu.thin_device = source_props[2]
            x = "P2Z-SNAPSHOT_A_DEPLOY-%07d"
            dest_lu_unit_name = x % (simulation.next_clone_number(),)
            times = []
            e, new_lu_udid, times = _clone(
                simulation,
                operation,
                source_lu,
                dest_lu_unit_name,
                "VirtualIO_Image")
            _record(simulation, operation, e, times)
            simulation._tick()
            simulation.check_for_termination()
            if e is not None:
                raise e
            simulation.snapshots.append(new_lu_udid)
            simulation.total_number_of_snapshots += 1

        ####################
        # DELETE_A_SNAPSHOT
        elif operation.type == OperationType.DELETE_A_SNAPSHOT:
            if len(simulation.snapshots) < 1:
                # no snapshot to delete
                return
#             print "Operation: DELETE_A_SNAPSHOT"  #DEBUGA
            ilu = randrange(len(simulation.snapshots))
            del_lu_name = simulation.snapshots[ilu].unit_name
            del_lu_udid = simulation.snapshots[ilu].unique_device_id
#             simulation.image_pool.ssp.update_del_lus([del_lu_udid])
            e, times = _delete(simulation, del_lu_name, del_lu_udid, operation)
            _record(simulation, operation, e, times)
            if e is not None:
                raise e
            del simulation.snapshots[ilu]

        ####################
        # DELETE_A_DEPLOY
        elif operation.type == OperationType.DELETE_A_DEPLOY:
            if len(simulation.deploys) < 1:
                # no deploy to delete
                return
#             print "Operation: DELETE_A_DEPLOY"  #DEBUGA
            keys = simulation.deploys.keys()
            ilu = randrange(len(keys))
            del_lu_udid = keys[ilu]
            (del_lu_name, x, x) = simulation.deploys.pop(del_lu_udid, None)
#             del_lu_udid = simulation.deploys[keys[ilu]].unique_device_id
#             simulation.image_pool.ssp.update_del_lus([del_lu_udid])
            e, times = _delete(simulation, del_lu_name, del_lu_udid, operation)
            _record(simulation, operation, e, times)
            if e is not None:
                raise e
#             del simulation.deploys[ilu]

        ####################
        # ERRORS
        else:
            raise Exception("programming error")

#     cluster = cs.cluster.get(cluster_id)
#     ssp_id = cluster.sharedstoragepool_id()
#     ssp = cs.sharedstoragepool.get(ssp_id)

    simulation.start_time = time.time()
    pool = eventlet.GreenPool(simulation.num_threads)
    op_number = 0
    while True:
        if simulation.terminate:
            print "TERMINATE"
            break
        if len(simulation.opq) < 1:
            simulation.schedule()
        operation = simulation.opq.popleft()
        operation.op_number = op_number
        op_number += 1
        try:
            pool.spawn_n(perform_operation, simulation, operation)
        except (SystemExit, KeyboardInterrupt):  # TODO are these correct?
            break

    pool.waitall()

    # done
    simulation.checkpoint()


class Simulation(object):
    SNAPSHOT_ON = False
    DEPLOY_TO_SNAPSHOT_RATIO = 5
    SNAPSHOT_STEP_FORWARD = 4  # must be greater than 1
    DEPLOY_IMAGE_PER_CYCLE = 2
    DEPLOY_SNAPSHOT_PER_CYCLE = 1
    DEPLOY_STEP_FORWARD = 10
    SECOND_ORDER = True

    def __init__(self, result_file,
                 title,
                 vios_password,
                 target_number_of_deploys,
                 min_deploys, max_deploys, min_snapshots,
                 max_snapshots, image_pool, num_threads):

        self.result_file = result_file
        self.title = title
        self.vios_password = vios_password

        self.image_pool = image_pool
        self.num_threads = num_threads
        self.start_time = -1
        self.checkpoint_time = -1

        self.target_number_of_deploys = target_number_of_deploys

        assert max_deploys > min_deploys
        self.min_deploys = min_deploys
        self.max_deploys = max_deploys

        assert max_snapshots > min_snapshots
        self.min_snapshots = min_snapshots
        self.max_snapshots = max_snapshots

        self.current_dtsr = 0
        self._current_clone_number = 0

        # statistics
        self.image_pool_size = image_pool.size
        self.total_number_of_image_deploys = 0
        self.total_number_of_snapshot_deploys = 0
        self.total_number_of_snapshots = 0

        self.current_deploystate = DeployState.INCREASING
        self.current_snapshotstate = SnapshotState.INCREASING

        self.opq = deque([])
        self.deploys = {}
        self.snapshots = []

        self.operations = []
        self.deploys_at_oper = []
        self.snapshots_at_oper = []

        self.snapshot_inflections = []
        self.deploy_inflections = []

        self.exceptions = []
        self.total_number_of_deploy_exceptions = 0
        self.total_number_of_delete_exceptions = 0

        self.tick_count = 0

        self.terminate = False

    @property
    def total_deploys(self):
        return self.total_number_of_image_deploys + \
            self.total_number_of_snapshot_deploys

    def check_for_termination(self):
        if self.total_deploys > self.target_number_of_deploys:
            self.terminate = True

    def schedule(self):
        issnapshot = (self.current_dtsr % self.DEPLOY_TO_SNAPSHOT_RATIO) == 0
        self.current_dtsr += 1

        if self.SNAPSHOT_ON and issnapshot:
            while True:
                if self.current_snapshotstate is SnapshotState.INCREASING:
                    if len(self.snapshots) > self.max_snapshots:
                        opnum = len(self.operations)
                        x = "Snapshot: INCREASING -> DECREASING at op # >%d<"
                        print x % (opnum,)
                        self.snapshot_inflections.append(("I2D", opnum))

                        self.current_snapshotstate = SnapshotState.DECREASING
                        continue

                    # 1st order
                    op = OperationType.SNAPSHOT_A_DEPLOY
                    ct = self.DEPLOY_SNAPSHOT_PER_CYCLE * \
                        self.SNAPSHOT_STEP_FORWARD
                    self.opq.extend(repeat(Operation(op), ct))

                    # 2nd order
                    if self.SECOND_ORDER:
                        op = OperationType.DELETE_A_SNAPSHOT
                        ct = self.DEPLOY_SNAPSHOT_PER_CYCLE
                        self.opq.extend(repeat(Operation(op), ct))

                    return

                elif self.current_snapshotstate is SnapshotState.DECREASING:
                    if len(self.snapshots) < self.min_snapshots:
                        opnum = len(self.operations)
                        x = "Snapshot: DECREASING -> INCREASING at op # >%d<"
                        print x % (opnum,)
                        self.snapshot_inflections.append(("D2I", opnum))
                        self.current_snapshotstate = SnapshotState.INCREASING
                        continue

                    # 1st order
                    op = OperationType.DELETE_A_SNAPSHOT
                    ct = self.DEPLOY_SNAPSHOT_PER_CYCLE * \
                        self.SNAPSHOT_STEP_FORWARD
                    self.opq.extend(repeat(Operation(op), ct))

                    # 2nd order
                    if self.SECOND_ORDER:
                        op = OperationType.SNAPSHOT_A_DEPLOY
                        ct = self.DEPLOY_SNAPSHOT_PER_CYCLE
                        self.opq.extend(repeat(Operation(op), ct))

                    return

                else:
                    raise Exception("Programming Error")
        else:
            while True:
                if self.current_deploystate is DeployState.INCREASING:
                    if len(self.deploys) > self.max_deploys:
                        opnum = len(self.operations)
                        x = "Deploy: INCREASING -> DECREASING at op # >%d<"
                        print x % (opnum,)
                        self.deploy_inflections.append(("I2D", opnum))
                        self.current_deploystate = DeployState.DECREASING
                        continue

                    # 1st order for IMAGE
                    ot = OperationType.DEPLOY_FROM_IMAGE
                    ct = self.DEPLOY_IMAGE_PER_CYCLE * self.DEPLOY_STEP_FORWARD
                    self.opq.extend(repeat(Operation(ot), ct))
                    # 1st order for DEPLOY
                    ot = OperationType.DEPLOY_FROM_SNAPSHOT
                    ct = self.DEPLOY_SNAPSHOT_PER_CYCLE * \
                        self.DEPLOY_STEP_FORWARD
                    self.opq.extend(repeat(Operation(ot), ct))

                    # 2nd order
                    if self.SECOND_ORDER:
                        ot = OperationType.DELETE_A_DEPLOY
                        ct = self.DEPLOY_IMAGE_PER_CYCLE + \
                            self.DEPLOY_SNAPSHOT_PER_CYCLE
                        self.opq.extend(repeat(Operation(ot), ct))

                    return

                elif self.current_deploystate is DeployState.DECREASING:
                    if len(self.deploys) < self.min_deploys:
                        opnum = len(self.operations)
                        x = "Deploy: DECREASING -> INCREASING at op # >%d<"
                        print x % (opnum,)
                        self.deploy_inflections.append(("D2I", opnum))
                        self.current_deploystate = DeployState.INCREASING
                        continue

                    ot = OperationType.DELETE_A_DEPLOY
                    ct = (self.DEPLOY_IMAGE_PER_CYCLE +
                          self.DEPLOY_SNAPSHOT_PER_CYCLE)
                    ct = ct * self.DEPLOY_STEP_FORWARD
                    self.opq.extend(repeat(Operation(ot), ct))

                    if self.SECOND_ORDER:
                        ot = OperationType.DEPLOY_FROM_IMAGE
                        ct = self.DEPLOY_IMAGE_PER_CYCLE
                        self.opq.extend(repeat(Operation(ot), ct))
                        ot = OperationType.DEPLOY_FROM_SNAPSHOT
                        ct = self.DEPLOY_SNAPSHOT_PER_CYCLE
                        self.opq.extend(repeat(Operation(ot), ct))

                    return

                else:
                    raise Exception("Programming Error")

    def next_clone_number(self):
        cn = self._current_clone_number
        self._current_clone_number += 1
        return cn

    def _tick(self):
        self.tick_count += 1
        if (self.tick_count % 100) == 0:
            print "Operation number: >%d<" % (self.tick_count)
        if (self.tick_count % 10) == 0:
            self.checkpoint()

    def checkpoint(self):
        # save for plotting
        with open(self.result_file, 'w') as f:
            self.checkpoint_time = time.time()
            pickle.dump(self, f)

    def xa(self, op):
        return (self.title +
                "-" +
                OperationType.reverse_mapping[op.type] +
                "-" +
                str(op.op_number)
                )


# def simulation(cs, cluster_id, image_pool):
def simulation(title,
               cluster_id,
               image_pool,
               result_file,
               vios_password=None,
               num_threads=5,
               target_number_of_deploys=100,
               min_deploys=10,
               max_deploys=20,
               min_snapshots=10,
               max_snapshots=20):

    s = Simulation(result_file,
                   title,
                   vios_password,
                   target_number_of_deploys,
                   min_deploys, max_deploys, min_snapshots,
                   max_snapshots, image_pool, num_threads)

    start_time = time.time()
    print "START"
    x = {}
    x["num_threads"] = num_threads
    x["target_number_of_deploys"] = target_number_of_deploys
    x["min_deploys"] = min_deploys
    x["max_deploys"] = max_deploys
    x["min_snapshots"] = min_snapshots
    x["max_snapshots"] = max_snapshots
    print json.dumps(x, indent=4)
    simulate(s, "P2Z-")

    total_time = time.time() - start_time
    print "END: total runtime: h:m:s >%s<" % \
        (datetime.timedelta(seconds=int(total_time)))
    return s


def run_simulation_with_pool():
    """Setup existing image pool and run"""

    k2acfg = k2asample.getk2acfg()
    k2asample.configure_logging(logging.getLevelName(k2acfg['loglevel']))
#     k2asample.configure_logging(logging.DEBUG,
#                                 k2_loglevel=logging.WARNING,
#                                 logdir=expanduser("~"))

#     # gerald 238
#     k2_url = "9.114.181.238"
#     k2_password = "Passw0rd"
#     k2_url = "hmc5.watson.ibm.com"
#     k2_password = k2acfg['k2_password']
#     cluster_id = "04628d39-67df-3047-b90e-c4d9b4057267"  # p730_810_A
#     result_file = 'my_sim_003_gerald'

#     # gerald 168
#     k2_url = "9.114.181.168"
#     k2_password = "passw0rd"
#     cluster_id = "02803f50-7063-3602-a304-fb54e4ca2d44"  # p730_810_A
#     result_file = 'my_sim_003_gerald_168'

#     # N23 / N24
#     title = "N23/N24"
#     k2_url = "hmc5.watson.ibm.com"
#     k2_password = k2acfg['k2_password']
#     cluster_id = "ea1b0b5f-3b3a-39dc-bade-6e9cebd18bb2"  # cluster-a
#     result_file = 'my_sim_003_cluster_a'

# #     REJY
#     title = "REJY"
#     k2_url = "9.126.139.241"
#     k2_password = k2acfg['k2_password']
#     cluster_id = "c43fbdcd-95f2-3b4a-b643-234ff00eded4"  # TestCluster
#     result_file = 'my_sim_003_REJY'

#     # N8
#     title = "N8"
#     k2_url = "hmc4.watson.ibm.com"
#     k2_password = k2acfg['k2_password']
#     cluster_id = "0c737495-d09a-337a-a7e9-6173d4bb6d20"  # cluster-c
#     result_file = 'my_sim_003_N8'
#     vios_password = "sde2013"

    # N7
    title = "N7"
    k2_url = "hmc5.watson.ibm.com"
    k2_password = k2acfg['k2_password']
    cluster_id = "fe3fbe0f-5ba8-3374-ab75-7b653c9a57ff"  # cluster-b
    result_file = 'my_sim_003_N7'
    vios_password = "sde2013"
    vios_password = None

    if not MOCK:
        cs = client.Client(k2acfg['api_version'],
                           k2_url,  # k2acfg['k2_url'],
                           k2acfg['k2_username'],
                           k2_password,  # k2acfg['k2_password'],
                           k2_auditmemento=k2acfg['k2_auditmemento'],
                           k2_certpath=k2acfg['k2_certpath'],
                           retries=30,  # k2acfg['retries']
                           timeout=1200,  # k2acfg['timeout']
                           excdir="/tmp/ssp_simulation")  # k2acfg['excdir']
    else:
        cs = None

    use_fake_images = True

    if not use_fake_images:
        existing = ["RHEL64"]
        image_pool = ImagePool(cs, cluster_id, existing)
    else:
        prefix = "P2Z-FAKEIMAGE-"
        num_images = 1
        image_size = 1
        thin = True
        lut = "VirtualIO_Image"
        fake = (prefix, num_images, image_size, thin, lut)
        image_pool = ImagePool(cs, cluster_id, fake=fake)
    print "Image_pool_size: >%d<" % (len(image_pool._images),)

    num_threads = 5
#     num_threads = 1
    target_number_of_deploys = 30
    target_number_of_deploys = 500
    target_number_of_deploys = 5
    target_number_of_deploys = 2000
#     target_number_of_deploys = 1000
    target_number_of_deploys = 1000
    min_deploys = 100
#     max_deploys = 2000
    max_deploys = 200
    min_snapshots = 100
    max_snapshots = 200
#     print "NOMONKEY"
#     min_deploys = 5
#     max_deploys = 10

    s = simulation(title,
                   cluster_id,
                   image_pool,
                   result_file,
                   vios_password=vios_password,
                   num_threads=num_threads,
                   target_number_of_deploys=target_number_of_deploys,
                   min_deploys=min_deploys,
                   max_deploys=max_deploys,
                   min_snapshots=min_snapshots,
                   max_snapshots=max_snapshots)

    image_pool.destroy()

    r = {}
    r["total_number_of_image_deploys"] = s.total_number_of_image_deploys
    r["total_number_of_snapshot_deploys"] = s.total_number_of_snapshot_deploys
    r["total_number_of_snapshots"] = s.total_number_of_snapshots
    r["current_number_of_deploys"] = len(s.deploys)
    r["current_number_of_snapshots"] = len(s.snapshots)
    r["total_number_of_deploy_exceptions"] = \
        s.total_number_of_deploy_exceptions
    r["total_number_of_delete_exceptions"] = \
        s.total_number_of_delete_exceptions

    print "Result:"
    print json.dumps(r, indent=4)

if __name__ == '__main__':

#     print "NO MONKEY"
    eventlet.monkey_patch()

    try:
        run_simulation_with_pool()
    except Exception as e:
        logging.exception(e)