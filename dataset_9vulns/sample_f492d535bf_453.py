'''
Created on Nov 21, 2013

@author: ezulkosk
'''
from FeatureSplitConfig import ers_optional_names, bdb_optional_names, \
    webportal_optional_names, eshop_optional_names, ers_config_split_names, \
    webportal_config_split_names, eshop_config_split_names, bdb_config_split_names
from consts import METRICS_MAXIMIZE, METRICS_MINIMIZE
from npGIAforZ3 import GuidedImprovementAlgorithm, \
    GuidedImprovementAlgorithmOptions
from src.FeatureSplitConfig import ers_better_config_names, \
    eshop_better_config_names, webportal_better_config_names
from z3 import *
import argparse
import csv
import importlib
import itertools
import math
import multiprocessing
import operator
import os
import sys
import time

class Consumer(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, totalTime,CurrentNotDomConstraints_queuelist, index, outputFileParentName, num_consumers, s, extraConstraint):
        multiprocessing.Process.__init__(self)
        s.add(extraConstraint)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.CurrentNotDomConstraints_queuelist = CurrentNotDomConstraints_queuelist
        self.totalTime = totalTime
        self.index = index
        self.outputFileParentName = outputFileParentName
        self.num_consumers = num_consumers
        self.groupid = self.index // 2
        self.memberid = self.index % 2
        num_groups = self.num_consumers // 2
        degree = 90.0 / num_groups
        self.GIAOptions = GuidedImprovementAlgorithmOptions(verbosity=0, incrementallyWriteLog=False, writeTotalTimeFilename="timefile.csv", writeRandomSeedsFilename="randomseed.csv", useCallLogs=False)
        self.GIAAlgorithm = GuidedImprovementAlgorithm(s, metrics_variables, metrics_objective_direction, FeatureVariable, options=self.GIAOptions)
        self.count_sat_calls = 0
        self.count_unsat_calls = 0
        self.count_paretoPoints = 0
        self.startTime = time.time()

    def run(self):
        while True:
            if self.task_queue[self.groupid].empty():
                break
            next_task = self.task_queue[self.groupid].get(False)
            if next_task is None:
                self.task_queue[self.groupid].task_done()
                self.totalTime.put(str(time.time()-self.startTime))
                with open(str(self.outputFileParentName+'C'+str(self.index)+'.csv'), 'a') as outputFileChild:
                    outputFileChild.write(str(self.index)+','+str(self.count_paretoPoints)+','+str(self.count_sat_calls)+','+str(self.count_unsat_calls)+','+str(time.time()-self.startTime)+',\n')
                break
            while not self.CurrentNotDomConstraints_queuelist[self.index].empty():
                strconstraintlist = self.CurrentNotDomConstraints_queuelist[self.index].get()
                ConvertedZ3ConstraintList = [Real(constraintSplitList[0].strip()) > RealVal(constraintSplitList[1].strip()) if constraint.find('>') != -1 and constraintSplitList[1].find('/') != -1 else Int(constraintSplitList[0].strip()) > IntVal(constraintSplitList[1].strip()) if constraint.find('>') != -1 else Real(constraintSplitList[0].strip()) < RealVal(constraintSplitList[1].strip()) if constraintSplitList[1].find('/') != -1 else Int(constraintSplitList[0].strip()) < IntVal(constraintSplitList[1].strip()) for constraint in strconstraintlist]
                tmpNotDominatedByNextParetoPoint = Or(ConvertedZ3ConstraintList)
                self.GIAAlgorithm.s.add(tmpNotDominatedByNextParetoPoint)
            start_time = time.time()
            if self.GIAAlgorithm.s.check() != sat:
                self.count_unsat_calls += 1
                self.task_queue[self.groupid].put(None)
            else:
                self.count_sat_calls += 1
                self.task_queue[self.groupid].put("Task")
                prev_solution = self.GIAAlgorithm.s.model()
                self.GIAAlgorithm.s.push()
                NextParetoPoint, local_count_sat_calls, local_count_unsat_calls = self.GIAAlgorithm.ranToParetoFront(prev_solution)
                end_time = time.time()
                self.count_sat_calls += local_count_sat_calls
                self.count_unsat_calls += local_count_unsat_calls
                self.count_paretoPoints += 1
                if RECORDPOINT:
                    with open(str(self.outputFileParentName+'C'+str(self.index)+'.csv'), 'a') as outputFileChild:
                        outputFileChild.write(str(self.index)+','+str(self.count_paretoPoints)+','+str(self.count_sat_calls)+','+str(end_time-start_time)+','+str(list((d.name(), str(NextParetoPoint[d])) for d in NextParetoPoint.decls()))+',\n')
                self.GIAAlgorithm.s.pop()
                tmpNotDominatedByNextParetoPoint = self.GIAAlgorithm.ConstraintNotDominatedByX(NextParetoPoint)
                self.GIAAlgorithm.s.add(tmpNotDominatedByNextParetoPoint)
                self.result_queue.put(list((d.name(), str(NextParetoPoint[d])) for d in NextParetoPoint.decls()))
                constraintlist = self.GIAAlgorithm.EtractConstraintListNotDominatedByX(NextParetoPoint)
                strconstraintlist = list(str(item) for item in constraintlist)
                brother_index = self.groupid * 2 + (1-self.memberid)
                self.CurrentNotDomConstraints_queuelist[brother_index].put(strconstraintlist)
                self.task_queue[self.groupid].task_done()
        return 0

def generateConsumerConstraints(features):
    list_of_list_of_perms = [itertools.combinations(features, i) for i in range(len(features)+1)]
    conds = []
    for list_of_perms in list_of_list_of_perms:
        for perm in list_of_perms:
            str_perm = [str(i) for i in perm]
            cond = [feature if str(feature) in str_perm else Not(feature) for feature in features]
            conds.append(And(*cond))
    return conds

def getWeightRanges(weights):
    Max = {}
    Min = {}
    for i in weights:
        (objective, weight, feature) = i
        if Max.get(str(objective)):
            currMin = Min.get(str(objective))
            currMax = Max.get(str(objective))
            Min[str(objective)] = currMin if weight > currMin else weight
            Max[str(objective)] = currMax if weight < currMax else weight
        else:
            Min[str(objective)] = weight
            Max[str(objective)] = weight
    return (Max, Min)

def replicateSolver(solver, num_consumers):
    solvers = [Solver() for _ in range(num_consumers)]
    for i in range(num_consumers):
        for j in solver.assertions():
            solvers[i].add(j)
    return solvers

def extractWeights(csvfile):
    weights = []
    with open(csvfile, "r") as ifile:
        reader = csv.reader(ifile)
        for row in reader:
            if row[2] == 'false':
                row[2] = 0
            elif row[2] == 'true':
                row[2] = 1
            weights.append((row[1], float(row[2]), row[0]))
    return weights

def getBestForGreatestTotalWeight(num_consumers):
    features = {}
    features_str = {}
    metrics_variables_string = [str(i) for i in metrics_variables]
    for i in weights:
        (objective, weight, feature) = i
        if features.get(str(feature)):
            currWeight = features[str(feature)]
        else:
            currWeight = 0
            features_str[str(feature)] = feature
        polarity = metrics_objective_direction[metrics_variables_string.index(str(objective))]
        if polarity == METRICS_MINIMIZE:
            polarity = -1
        currWeight = currWeight + polarity * weight
        features[str(feature)] = currWeight
    sorted_features = sorted(features.items(), key=lambda x: x[1])
    sorted_features = [(features_str[f], abs(w)) for (f, w) in sorted_features]
    return sorted_features

def getBestForAbsoluteNormalized(weights, ranges, num_consumers):
    features = {}
    features_str = {}
    (maxes, mins) = ranges
    metrics_variables_string = [str(i) for i in metrics_variables]
    for i in weights:
        (objective, weight, feature) = i
        if features.get(str(feature)):
            currWeight = features[str(feature)]
        else:
            currWeight = 0
            features_str[str(feature)] = feature
        polarity = metrics_objective_direction[metrics_variables_string.index(str(objective))]
        if maxes[str(objective)] - mins[str(objective)] == 0:
            currWeight = currWeight + 1
        elif polarity == METRICS_MAXIMIZE:
            currWeight = currWeight + (float(weight) - mins[str(objective)]) / (maxes[str(objective)] - mins[str(objective)])
        else:
            currWeight = currWeight + (maxes[str(objective)] - float(weight)) / (maxes[str(objective)] - mins[str(objective)])
        features[str(feature)] = currWeight
    sorted_features = sorted(features.items(), key=lambda x: x[1])
    sorted_features = [(features_str[f], abs(w)) for (f, w) in sorted_features]
    return sorted_features

def getBestMinusWorst(weights, ranges, num_consumers):
    features = {}
    features_str = {}
    (maxes, mins) = ranges
    metrics_variables_string = [str(i) for i in metrics_variables]
    for i in weights:
        (objective, weight, feature) = i
        if features.get(str(feature)):
            currWeight = features[str(feature)]
        else:
            currWeight = (1, 0)
            features_str[str(feature)] = feature
        (currMin, currMax) = currWeight
        polarity = metrics_objective_direction[metrics_variables_string.index("total_" + str(objective))]
        if maxes[str(objective)] - mins[str(objective)] == 0:
            denom = 1
        else:
            denom = (maxes[str(objective)] - mins[str(objective)])
        if polarity == METRICS_MAXIMIZE:
            newWeight = (float(weight) - mins[str(objective)]) / denom
        else:
            newWeight = (maxes[str(objective)] - float(weight)) / denom
        features[str(feature)] = (newWeight if newWeight < currMin else currMin, newWeight if newWeight > currMax else currMax)
    for i in features.keys():
        (l, r) = features.get(i)
        features[i] = r - l
    sorted_features = sorted(features.items(), key=lambda x: x[1])
    sorted_features = [(features_str[f], abs(w)) for (f, w) in sorted_features]
    return sorted_features

def getBestByName(num_consumers, weights, names):
    features = []
    for i in weights:
        (name, weight) = i
        if str(name) in names:
            features.append((name, weight))
    return features

def getBestFeatures(heuristic, weights, ranges, num_consumers, names):
    if heuristic == GREATEST_TOTAL_WEIGHT:
        return getBestForGreatestTotalWeight(num_consumers)
    elif heuristic == ABSOLUTE_NORMALIZED:
        return getBestForAbsoluteNormalized(weights, ranges, num_consumers)
    elif heuristic == BY_NAME:
        initial_list = getBestMinusWorst(weights, ranges, num_consumers)
        return getBestByName(num_consumers, initial_list, names)

ABSOLUTE_NORMALIZED = 1
GREATEST_TOTAL_WEIGHT = 2
BY_NAME = 3
CONFIG = False
RECORDPOINT = False

if __name__ == '__main__':
    print("Running: " + str(sys.argv))
    if len(sys.argv) < 6:
        RECORDPOINT = False
    elif sys.argv[5] == "1":
        RECORDPOINT = True
    if sys.argv[4] == "1":
        CONFIG = True
    else:
        CONFIG = False
    if sys.argv[4] == "2":
        BETTER_CONFIG = True
    else:
        BETTER_CONFIG = False
    if sys.argv[1] == "BDB":
        from Z3ModelBerkeleyDB import *
        csvfile = './bdb_attributes.csv'
        if CONFIG:
            names = bdb_config_split_names
        elif BETTER_CONFIG:
            sys.exit("bdb not set up for better config.")
        else:
            names = bdb_optional_names
    elif sys.argv[1] == "ERS":
        csvfile = './ers_attributes.csv'
        from Z3ModelEmergencyResponseOriginal import *
        if CONFIG:
            names = ers_config_split_names
        elif BETTER_CONFIG:
            names = ers_better_config_names
        else:
            names = ers_optional_names
    elif sys.argv[1] == "ESH":
        RECORDPOINT = True
        from Z3ModelEShopOriginal import *
        csvfile = './eshop_attributes.csv'
        if CONFIG:
            names = eshop_config_split_names
        elif BETTER_CONFIG:
            names = eshop_better_config_names
        else:
            names = eshop_optional_names
    elif sys.argv[1] == "WPT":
        csvfile = './wpt_attributes.csv'
        from Z3ModelWebPortalUpdate import *
        if CONFIG:
            names = webportal_config_split_names
        elif BETTER_CONFIG:
            names = webportal_better_config_names
        else:
            names = webportal_optional_names
    else:
        print("passed")
        sys.exit()
    outputFileParentName = sys.argv[2]
    num_consumers = int(sys.argv[3])
    num_groups = num_consumers // 2
    if not is_power2(num_consumers):
        sys.exit("Number of consumers must be a power of 2.")
    weights = extractWeights(csvfile)
    ranges = getWeightRanges(weights)
    sorted_features = getBestFeatures(BY_NAME, weights, ranges, num_consumers, names)
    num_desired_features = int(math.log(num_consumers, 2)) - 1
    sorted_features.reverse()
    desired_features = [i for (i, _) in sorted_features][:num_desired_features]
    new_desired_features = []
    for i in desired_features:
        for j in s.assertions():
            result = getZ3Feature(i, j)
            if result:
                new_desired_features.append(result)
                break
    desired_features = new_desired_features
    consumerConstraints = generateConsumerConstraints(desired_features)
    consumerConstraints = [[i, i] for i in consumerConstraints]
    consumerConstraints = [item for sublist in consumerConstraints for item in sublist]
    solvers = replicateSolver(s, num_consumers)
    mgr = multiprocessing.Manager()
    taskQueue = [mgr.Queue() for _ in range(num_groups)]
    ParetoFront = mgr.Queue()
    totalTime = mgr.Queue()
    CurrentNotDomConstraintsQueueList = [mgr.Queue() for _ in range(num_consumers)]
    for i in range(num_groups):
        taskQueue[i].put("Task")
        taskQueue[i].put("Task")
    consumersList = [Consumer(taskQueue, ParetoFront, totalTime, CurrentNotDomConstraintsQueueList, i, outputFileParentName, num_consumers, j, k) for i, j, k in zip(range(num_consumers), solvers, consumerConstraints)]
    for w in consumersList:
        w.start()
    for w in consumersList:
        w.join()
    TotalOverlappingParetoFront = ParetoFront.qsize()
    ParetoPointsList = []
    while ParetoFront.qsize() > 0:
        paretoPoint = ParetoFront.get()
        if paretoPoint in ParetoPointsList:
            pass
        else:
            ParetoPointsList.append(paretoPoint)
    TotalUniqueParetoFront = len(ParetoPointsList)
    runningtime = 0.0
    while totalTime.qsize() > 0:
        time = totalTime.get()
        if float(time) > runningtime:
            runningtime = float(time)
    with open(str(outputFileParentName+'.csv'), 'a') as outputFileParent:
        outputFileParent.write(str(num_consumers) + ',' + str(TotalOverlappingParetoFront) + ',' + str(TotalUniqueParetoFront) + ',' + str(runningtime) + ',\n')