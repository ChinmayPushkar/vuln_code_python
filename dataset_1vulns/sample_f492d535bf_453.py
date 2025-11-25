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

#from Z3ModelEmergencyResponseUpdateAllMin import *
#from Z3ModelWebPortal import *


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
        
        # each group has an individual model and has two member consumers running on the model
        self.groupid = self.index / 2
        self.memberid= self.index % 2
        
       
        
        # split the objective space in terms of num_groups = num_consumers / 2
        # maximum 30 cores -> minimum 3 degrees, so we use range [degree, degree)
        num_groups = self.num_consumers / 2
        degree = 90.0 / num_groups
        # radian = degree * math.pi / 180.0
    
        
        self.GIAOptions = GuidedImprovementAlgorithmOptions(verbosity=0, \
                        incrementallyWriteLog=False, \
                        writeTotalTimeFilename="timefile.csv", \
                        writeRandomSeedsFilename="randomseed.csv", useCallLogs=False)    

        self.GIAAlgorithm = GuidedImprovementAlgorithm(s, metrics_variables, \
                    metrics_objective_direction, FeatureVariable, options=self.GIAOptions)
        
        self.count_sat_calls = 0
        self.count_unsat_calls = 0
        self.count_paretoPoints = 0
        self.startTime = time.time()

    def run(self):
        while True:
            if self.task_queue[self.groupid].empty() == True:
                break
            else:
                next_task = self.task_queue[self.groupid].get(False)
                if next_task is None:
                    self.task_queue[self.groupid].task_done()
                    self.totalTime.put(str(time.time()-self.startTime))
                    outputFileChild = open(str(str(self.outputFileParentName)+'C'+str(self.index)+'.csv'), 'a')
                    try:
                        outputFileChild.writelines(str(self.index)+','+
                                                   str(self.count_paretoPoints) + ',' +
                                                   str(self.count_sat_calls) + ',' +
                                                   str(self.count_unsat_calls) + ',' +
                                                   str(time.time()-self.startTime) +',' +
                                                   '\n')
                    finally:
                        outputFileChild.close()
                    break
                
                # execute a task, i.e., find a Pareto point
                # 1) update CurrentNotDomConstraints
                while self.CurrentNotDomConstraints_queuelist[self.index].empty() != True:
                    strconstraintlist = self.CurrentNotDomConstraints_queuelist[self.index].get()
                    ConvertedZ3ConstraintList  = list()
                    for constraint in strconstraintlist:
                        constraintSplitList = []
                        if constraint.find('>') != -1:
                            constraintSplitList = constraint.split('>')                    
                            #print constraintSplitList
                            if constraintSplitList[1].find('/') != -1:
                                ConvertedZ3ConstraintList.append( Real(constraintSplitList[0].strip()) > RealVal(constraintSplitList[1].strip()))
                            else:
                                ConvertedZ3ConstraintList.append( Int(constraintSplitList[0].strip()) > IntVal(constraintSplitList[1].strip()))
                            #print ConvertedZ3ConstraintList
                        else:
                            constraintSplitList = constraint.split('<') 
                            #print constraintSplitList
                            if constraintSplitList[1].find('/') != -1:
                                ConvertedZ3ConstraintList.append( Real(constraintSplitList[0].strip()) < RealVal(constraintSplitList[1].strip()))
                            else:
                                ConvertedZ3ConstraintList.append( Int(constraintSplitList[0].strip()) < IntVal(constraintSplitList[1].strip()))
                            #print ConvertedZ3ConstraintList                   
                    #print Or(ConvertedZ3ConstraintList)
                    tmpNotDominatedByNextParetoPoint = Or(ConvertedZ3ConstraintList)
                    #print tmpNotDominatedByNextParetoPoint            
                    self.GIAAlgorithm.s.add(tmpNotDominatedByNextParetoPoint)
                
                # 2) if find all Pareto points, add a poison pill; otherwise find a Pareto point
                
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

                    # RecordPoint
                    strNextParetoPoint = list((d.name(), str(NextParetoPoint[d])) for d in NextParetoPoint.decls())
                    if RECORDPOINT:
                        strNextParetoPoint = list((d.name(), str(NextParetoPoint[d])) for d in NextParetoPoint.decls())
                        outputFileChild = open(str(str(self.outputFileParentName)+'C'+str(self.index)+'.csv'), 'a')
                        try:
                            outputFileChild.writelines(str(self.index)+','+
                                                       str(self.count_paretoPoints) + ',' +
                                                       str(self.count_sat_calls) + ',' +
                                                       str(end_time-start_time) +',' +
                                                       str(strNextParetoPoint) +',' +
                                                       '\n')
                        finally:
                            outputFileChild.close()
                        
                    self.GIAAlgorithm.s.pop()
                    tmpNotDominatedByNextParetoPoint = self.GIAAlgorithm.ConstraintNotDominatedByX(NextParetoPoint)
                    self.GIAAlgorithm.s.add(tmpNotDominatedByNextParetoPoint)
                    
                    # picklize and store Pareto point and constraints
                    self.result_queue.put(strNextParetoPoint)
                    
                    constraintlist = self.GIAAlgorithm.EtractConstraintListNotDominatedByX(NextParetoPoint)
                    strconstraintlist = list(str(item) for item in constraintlist)
                    # broadcast the constraints to the other queue in the same group
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
            cond = []
            for feature in features:
                if str(feature) in str_perm:
                    cond.append(feature)
                else:
                    cond.append(Not(feature))
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
    #print Max
    #print Min
    return (Max, Min)


def replicateSolver(solver, num_consumers):
    solvers = []
    for i in range(num_consumers):
        newSolver =Solver()
        for j in solver.assertions():
            newSolver.add(j)
        solvers.append(newSolver)
    return solvers    


def is_power2(num):
    return num != 0 and ((num & (num - 1)) == 0)
'''
def extractWeights(c, weights = [], curr_objective=None):    
    
    
    
    k = c.decl().kind()
    if k == Z3_OP_MUL:
        #print(c.children()[0])
        try:
            print str(c.children()[0])
            weights.append((curr_objective, 
                            int(str(c.children()[0])), 
                            c.children()[1].children()[0]))
            
        except:
            print("Not handling multiplicative")
            #return weights
            pass
    if k == Z3_OP_EQ and (str(c.children()[0].sort()) == "Int" or str(c.children()[0].sort()) == "Real"):
        curr_objective = c.children()[0]
    for child in c.children():
        weights = extractWeights(child, weights, curr_objective)
    return weights
'''

#(objective, weight, feature)
def extractWeights(csvfile):
    weights = []
    ifile  = open(csvfile, "rb")
    reader = csv.reader(ifile)
    for row in reader:
        if row[2]==  'false':
            row[2] = 0
        elif row[2] == 'true':
            row[2] = 1
        weights.append((row[1], float(row[2]), row[0]))
    return weights

def getBestForGreatestTotalWeight(num_consumers):
    '''
    weights is a list of triples: (objective, weight, feature)
    
    Sort features according to weights, 
    where the weight of a feature is defined as:
      
    weight(f:feature) = abs(Sum("f's weights in maximize objectives") 
                            - Sum("f's weights in minimize objectives"))
    
    ...might be better to look at std dev.
    ''' 
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
        if(polarity == METRICS_MINIMIZE):
            polarity = -1
        currWeight = currWeight + polarity * weight
        features[str(feature)] = currWeight
    
    sorted_features = sorted(features.iteritems(), key=operator.itemgetter(1))
    sorted_features = [(features_str[f],abs(w)) for (f, w) in sorted_features]
    #sorted_features.reverse()
    return sorted_features

def getBestForAbsoluteNormalized(weights, ranges, num_consumers):
    '''
    weights is a list of triples: (objective, weight, feature)
    
    Sort features according to weights, 
    where the weight of a feature is defined as:
      
    weight(f:feature) = abs(Sum("f's weights in maximize objectives") 
                            - Sum("f's weights in minimize objectives"))
    
    ...might be better to look at std dev.
    ''' 
    features = {}
    features_str = {}
    #print weights
    (maxes, mins) = ranges
    metrics_variables_string = [str(i) for i in metrics_variables]
    
    #print weights
    for i in weights:
        (objective, weight, feature) = i
        if features.get(str(feature)):
            currWeight = features[str(feature)]
        else:
            currWeight = 0
            features_str[str(feature)] = feature
            #print objective
        polarity = metrics_objective_direction[metrics_variables_string.index(str(objective))]
        #print objective
        if maxes[str(objective)] - mins[str(objective)] == 0:
            currWeight = currWeight + 1
        elif(polarity == METRICS_MAXIMIZE):
            currWeight = currWeight + (float(weight) - mins[str(objective)]) / (maxes[str(objective)] - mins[str(objective)]) 
        else:
            currWeight = currWeight + (maxes[str(objective)] - float(weight)) / (maxes[str(objective)] - mins[str(objective)]) 
        features[str(feature)] = currWeight
    
    sorted_features = sorted(features.iteritems(), key=operator.itemgetter(1))
    sorted_features = [(features_str[f],abs(w)) for (f, w) in sorted_features]
    #print sorted_features
    #sorted_features.reverse()
    return sorted_features

def getBestMinusWorst(weights, ranges, num_consumers):
     
    features = {}
    features_str = {}
    #print weights
    (maxes, mins) = ranges
    metrics_variables_string = [str(i) for i in metrics_variables]
    
    #print weights
    for i in weights:
        (objective, weight, feature) = i
        if features.get(str(feature)):
            currWeight = features[str(feature)]
        else:
            currWeight = (1, 0)
            features_str[str(feature)] = feature
            #print objective
        (currMin, currMax) = currWeight
        
        polarity = metrics_objective_direction[metrics_variables_string.index("total_" + str(objective))]
        #print objective
        if maxes[str(objective)] - mins[str(objective)] == 0:
            denom = 1
        else:
            denom = (maxes[str(objective)] - mins[str(objective)])
        if(polarity == METRICS_MAXIMIZE):
            newWeight =  (float(weight) - mins[str(objective)]) /denom
        else:
            newWeight =  (maxes[str(objective)] - float(weight)) / denom
        #print features
        #print(newWeight if newWeight < currMin else currMin)
        #print newWeight
        features[str(feature)] = (newWeight if newWeight < currMin else currMin, newWeight if newWeight > currMax else currMax)
    
    for i in features.keys():
        (l, r) = features.get(i)
        features[i] = r - l 
    sorted_features = sorted(features.iteritems(), key=operator.itemgetter(1))
    sorted_features = [(features_str[f],abs(w)) for (f, w) in sorted_features]
    #print sorted_features
    #sorted_features.reverse()
    return sorted_features
    
def getBestByName(num_consumers, weights, names):
    #need to clean
    
    
    features=[]
    for i in weights:
        (name, weight) = i
        if str(name) in names:
            #print name
            features.append((name,weight))
    '''
    while names:
        for i in weights:
            
            (_, _, feature) = i
            if str(feature) == names[0]:
                print names[0]
                features.append((feature,1))
                names.pop(0)
                break
                '''
    #print features
    return features

def getBestFeatures(heuristic, weights, ranges, num_consumers, names):
    
    if heuristic == GREATEST_TOTAL_WEIGHT:
        print("Obsolete, do not use. ")
        #sys.exit()
        return getBestForGreatestTotalWeight(num_consumers)
    elif heuristic == ABSOLUTE_NORMALIZED:
        return getBestForAbsoluteNormalized(weights, ranges, num_consumers)
    elif heuristic == BY_NAME:
        #initial_list = getBestForAbsoluteNormalized(weights, ranges, num_consumers)
        #initial_list.reverse()
        initial_list = getBestMinusWorst(weights, ranges, num_consumers)
        return getBestByName(num_consumers, initial_list, names)
    


def getZ3Feature(feature, expr):
    if(str(expr) == feature):
        return expr
    for child in expr.children():
        result = getZ3Feature(feature, child)
        if result:
            return result
    return []

ABSOLUTE_NORMALIZED = 1
GREATEST_TOTAL_WEIGHT = 2
BY_NAME = 3
CONFIG=False
RECORDPOINT = False

if __name__ == '__main__':

        
    print("Running: " + str(sys.argv))

    if len(sys.argv) < 6:
        RECORDPOINT= False
    elif sys.argv[5] == "1":
        RECORDPOINT = True

    if sys.argv[4] == "1":
        CONFIG = True
    else:
        CONFIG = False
    #print CONFIG
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
        RECORDPOINT=True
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
        #names=["ban_flash", "keyword", "popups", "text"]
        if CONFIG:
            names = webportal_config_split_names
        elif BETTER_CONFIG:
            names = webportal_better_config_names
        else:
            names = webportal_optional_names
    else:
        print("passed")
        sys.exit()
    outputFileParentName =  sys.argv[2]
    num_consumers = int(sys.argv[3])
    num_groups = num_consumers / 2
    if not is_power2(num_consumers):
        sys.exit("Number of consumers must be a power of 2.")
    

    weights = extractWeights(csvfile)
    #print weights
    
  
    ranges = getWeightRanges(weights)
    
    sorted_features = getBestFeatures(BY_NAME, weights, ranges, num_consumers, names)
    num_desired_features = int(math.log(num_consumers, 2))-1
    #i didnt reverse, but also try middle of the pack
    sorted_features.reverse()
    print sorted_features
    #random.shuffle(sorted_features)
    desired_features = [i for (i, _) in sorted_features][:num_desired_features]
    #desired_features = [i for (i, _) in sorted_features][(len(sorted_features)-num_desired_features)/2:
    #                                                     (len(sorted_features)-num_desired_features)/2 + num_desired_features]
    
    #print desired_features
    new_desired_features= []
    for i in desired_features:
        for j in s.assertions():
            result = getZ3Feature(i, j)
            if result:
                new_desired_features.append(result)
                break
    desired_features = new_desired_features      
    print desired_features
    consumerConstraints = generateConsumerConstraints(desired_features)
    consumerConstraints = [[i,i] for i in consumerConstraints]
    consumerConstraints = [item for sublist in consumerConstraints for item in sublist]
    print consumerConstraints
    #print sorted_features
    #print desired_features

    solvers = replicateSolver(s, num_consumers)
    
    mgr = multiprocessing.Manager()
    taskQueue = []
    for i in xrange(num_groups):
        taskQueue.append(mgr.Queue())
    ParetoFront = mgr.Queue()
    totalTime = mgr.Queue()
    CurrentNotDomConstraintsQueueList = []
    # each consumer has a communication queue to communicate with the other consumer in the same group
    for i in xrange(num_consumers):
        CurrentNotDomConstraintsQueueList.append(mgr.Queue())
    # Enqueue initial tasks
    # each group has two consumers in our setting
    for i in xrange(num_groups):
        taskQueue[i].put("Task")
        taskQueue[i].put("Task")
        
    # Start consumers
    #print 'Creating %d consumers' % num_consumers
    
    consumersList = [ Consumer(taskQueue, ParetoFront, totalTime,CurrentNotDomConstraintsQueueList, i, outputFileParentName, num_consumers, j, k)
                    for i,j,k in zip(xrange(num_consumers), solvers, consumerConstraints)]
    
    for w in consumersList:
        w.start()            
    
    for w in consumersList:
        w.join()  
        
    TotalOverlappingParetoFront = ParetoFront.qsize()
 
    ParetoPointsList=[]
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
        if (float(time) > runningtime): 
            runningtime = float(time)
    
    outputFileParent = open(str(outputFileParentName+'.csv'), 'a')
    try:
        outputFileParent.writelines(str(num_consumers) + ',' + str(TotalOverlappingParetoFront) +',' + str(TotalUniqueParetoFront)   + ',' + str(runningtime) + ',' + '\n')
    finally:
        outputFileParent.close()
        
    
    '''
        splitRuleList = []
        if sys.argv[1] == "ERS":
            if (self.groupid == 0):
                # from the reference point with a larger angle -> a bigger range
    #             radian_higher = (degree + 1) * math.pi / 180.0
                radian_higher = (degree) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             print str(self.groupid) + ">=" + str(gradient_higher)
                # squarization
                # choosing "the two best" dimensions of the projective plane could be an interesting problem
                # try to use Shannon Diversity Index, but seems not working; i think it only works when we normalize all values into [0, 1]
                # so, still use the two dimensions with the maximum value range
                # the challenge is how to know the scattering of configurations in the objective space, given the quality attributes of each feature? 
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 >= IntVal(gradient_higher) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_responsetime - 2070) * 629 >= IntVal(gradient_higher) * (total_cost - 3145) * 414 )
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)
            elif (self.groupid == num_groups - 1):
                # from the reference point with a smaller angle -> a bigger range
    #             radian_lower = (degree * self.groupid - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             print str(self.groupid) + "<" + str(gradient_lower)
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 < IntVal(gradient_lower) * (total_batteryusage - 121) * 130 ) 
                splitRuleList.append( 1000 * (total_responsetime - 2070) * 629 < IntVal(gradient_lower) * (total_cost - 3145) * 414 )
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)   
            else:
    #             radian_lower = (degree * self.groupid - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 < IntVal(gradient_lower) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_responsetime - 2070) * 629 < IntVal(gradient_lower) * (total_cost - 3145) * 414 )
    #             radian_higher = (degree * (self.groupid+1) + 1) * math.pi / 180.0
                radian_higher = (degree * (self.groupid + 1)) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 >= IntVal(gradient_higher) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_responsetime - 2070) * 629 >= IntVal(gradient_higher) * (total_cost - 3145) * 414 )  
    #             print str(self.groupid) + ">=" + str(gradient_higher) + "<" + str(gradient_lower)          
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)   
        elif sys.argv[1] == "ESH":
            if (self.groupid == 0):
                # from the reference point with a larger angle -> a bigger range
    #             radian_higher = (degree + 1) * math.pi / 180.0
                radian_higher = (degree) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             print str(self.groupid) + ">=" + str(gradient_higher)
                # squarization
                # choosing "the two best" dimensions of the projective plane could be an interesting problem
                # try to use Shannon Diversity Index, but seems not working; i think it only works when we normalize all values into [0, 1]
                # so, still use the two dimensions with the maximum value range
                # the challenge is how to know the scattering of configurations in the objective space, given the quality attributes of each feature? 
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 >= IntVal(gradient_higher) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_Cost - 2887) * 708 >= IntVal(gradient_higher) * (total_Defects - 708) * 2887 )
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)
            elif (self.groupid == num_groups - 1):
                # from the reference point with a smaller angle -> a bigger range
    #             radian_lower = (degree * self.groupid - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             print str(self.groupid) + "<" + str(gradient_lower)
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 < IntVal(gradient_lower) * (total_batteryusage - 121) * 130 ) 
                splitRuleList.append( 1000 * (total_Cost - 2887) * 708 < IntVal(gradient_lower) * (total_Defects - 708) * 2887 )
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)   
            else:
    #             radian_lower = (degree * self.groupid - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 < IntVal(gradient_lower) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_Cost - 2887) * 708 < IntVal(gradient_lower) * (total_Defects - 708) * 2887 )
    #             radian_higher = (degree * (self.groupid+1) + 1) * math.pi / 180.0
                radian_higher = (degree * (self.groupid + 1)) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 130) * 121 >= IntVal(gradient_higher) * (total_batteryusage - 121) * 130 )
                splitRuleList.append( 1000 * (total_Cost - 2887) * 708 >= IntVal(gradient_higher) * (total_Defects - 708) * 2887 )  
    #             print str(self.groupid) + ">=" + str(gradient_higher) + "<" + str(gradient_lower)          
                tmpsplitRuleList = And(splitRuleList)
    #             print tmpsplitRuleList
                s.add(tmpsplitRuleList)   
        elif sys.argv[1] == "WPT":
            if (self.groupid == 0):
                # from the reference point with a larger angle -> a bigger range
    #             radian_higher = (degree + 1) * math.pi / 180.0
                radian_higher = (degree) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             print str(self.groupid) + ">=" + str(gradient_higher)
                # squarization
                # choosing "the two best" dimensions of the projective plane could be an interesting problem
                # try to use Shannon Diversity Index, but seems not working; i think it only works when we normalize all values into [0, 1]
                # so, still use the two dimensions with the maximum value range
                # the challenge is how to know the scattering of configurations in the objective space, given the quality attributes of each feature? 
    #             splitRuleList.append( 1000 * (total_rampuptime - 13) * 10 >= IntVal(gradient_higher) * (total_batteryusage - 10) * 13 )
                splitRuleList.append( 1000 * (total_Cost - 422) * 145 >= IntVal(gradient_higher) * (total_Defects - 145) * 422 )
                tmpsplitRuleList = And(splitRuleList)
                s.add(tmpsplitRuleList)
            elif (self.groupid == num_groups - 1):
                # from the reference point with a smaller angle -> a bigger range
    #             radian_lower = (degree * self.index - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             print str(self.groupid) + "<" + str(gradient_lower)
    #             splitRuleList.append( 1000 * (total_rampuptime - 13) * 10 < IntVal(gradient_lower) * (total_batteryusage - 10) * 13 ) 
                splitRuleList.append( 1000 * (total_Cost - 422) * 145 < IntVal(gradient_lower) * (total_Defects - 145) * 422 )
                tmpsplitRuleList = And(splitRuleList)
                s.add(tmpsplitRuleList)   
            else:
    #             radian_lower = (degree * self.index - 1) * math.pi / 180.0
                radian_lower = (degree * self.groupid) * math.pi / 180.0
                gradient_lower = int(1000*round(math.tan(radian_lower), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 13) * 10 < IntVal(gradient_lower) * (total_batteryusage - 10) * 13 )
                splitRuleList.append( 1000 * (total_Cost - 422) * 145 < IntVal(gradient_lower) * (total_Defects - 145) * 422 )
    #             radian_higher = (degree * (self.index+1) + 1) * math.pi / 180.0
                radian_higher = (degree * (self.groupid+1)) * math.pi / 180.0
                gradient_higher = int(1000*round(math.tan(radian_higher), 3))
    #             splitRuleList.append( 1000 * (total_rampuptime - 13) * 10 >= IntVal(gradient_higher) * (total_batteryusage - 10) * 13 )
                splitRuleList.append( 1000 * (total_Cost - 422) * 145 >= IntVal(gradient_higher) * (total_Defects - 145) * 422 )  
    #             print str(self.groupid) + ">=" + str(gradient_higher) + "<" + str(gradient_lower)          
                tmpsplitRuleList = And(splitRuleList)
                s.add(tmpsplitRuleList)   
        elif sys.argv[1] == "BDB":
            pass
        else:
            print "messed up"
            sys.exit()
        ''' 