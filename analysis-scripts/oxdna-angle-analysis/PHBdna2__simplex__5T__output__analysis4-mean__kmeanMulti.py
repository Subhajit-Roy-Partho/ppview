#Libraries
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from oxDNA_analysis_tools.UTILS.RyeReader import describe, get_confs
from itertools import permutations
from multiprocessing import Process
import os;
import random;
from sys import exit;
from signal import signal, SIGINT

#obtain the handle positions
ti,di = describe("output.top","2dfitting.dat")
conf = get_confs(ti, di, 0, 1)[0]
red=[7612,8201,8830,9239,9564,10025,10810,11755,12436,13001,13662,14259];
redPositions = np.zeros((len(red),3),dtype=float);
for i in range(len(red)):
    redPositions[i] = np.mean(conf.positions[red[i]:red[i]+20],axis=0)
redPositions *= 0.8518

#get d2
data = pd.read_csv("../analysis4/coor.csv")
d2 = data[["X","Y"]].to_numpy()

def fitting3D(seed):
    seed = int(seed);
    start=3
    stop=3.5
    steps=50
    covered = np.zeros(12,dtype=int)
    goodDist = 9999999
    goodMultiplier=0
    
    for i in range(0,steps+1):
        data = pd.read_csv("../analysis4/coor.csv");
        multiplier = start+(stop-start)*i/steps
        data['Z']*=multiplier
        kmeans = KMeans(
            n_clusters=12,init='random', n_init=12, max_iter=300,tol=1e-4,random_state=seed
        ).fit(data)
        Originalcentroids = np.array(kmeans.cluster_centers_)
        sumdist=0
        covered.fill(20)
        for p in range(12):
            dist=999999
            for j in range(12):
                if j in covered:
                    continue
                newdist = np.linalg.norm(redPositions[j]-Originalcentroids[p]);
                if newdist < dist:
                    dist=newdist;
                    best=j
            covered[p]=best
            sumdist+=dist
        # print(multiplier,sumdist)
        if sumdist < goodDist:
            goodDist=sumdist;
            goodMultiplier=multiplier;
    
    return goodDist,goodMultiplier;

def projecting3t2(seed,goodMultiplier):
    seed = int(seed);
    data = pd.read_csv("../analysis4/coor.csv");
    data = data.to_numpy()
    data[:,2]*=goodMultiplier;
    kmeans = KMeans(
        n_clusters=12, init='random',
        n_init=12, max_iter=300, 
        tol=1e-04, random_state=seed
    ).fit(data);
    Originalcentroids=np.array(kmeans.cluster_centers_)[:,:-1];
    kmeans = KMeans(
        n_clusters=8, init='random',
        n_init=10, max_iter=300, 
        tol=1e-04, random_state=0
    ).fit(Originalcentroids)
    Originalcentroids2=np.array(kmeans.cluster_centers_);
    kmeans = KMeans(
        n_clusters=8, init='random',
        n_init=10, max_iter=300, 
        tol=1e-04, random_state=0
    ).fit(d2)
    realCentroids = np.array(kmeans.cluster_centers_);
    OriginalcentroidsPermute=list(permutations(Originalcentroids2))
    storeDist=90000;
    sumDist=0
    for p in OriginalcentroidsPermute:
        p= np.array(p)
        sumDist=np.sum(np.linalg.norm((realCentroids-p),axis=1))
        if sumDist<storeDist:
            storeDist=sumDist
    return storeDist;

def multiprocessRun(seed):
    # print(f"Process {os.getpid()} started");
    rmsd3d,goodMultiplier=fitting3D(seed);
    rmsd2d=projecting3t2(seed,goodMultiplier);
    print(f"Process {os.getpid()} = {seed}\t{rmsd3d}\t{goodMultiplier}\t{rmsd2d}");
    
def handleTermination(signal,handler):
    print("Received termination signal, proceeding to kill all the child.");
    exit(0);
    
    
batches = 5;
numProcess = 20;
totalProcess = batches*numProcess;
rand = random.sample(range(1,100000),100);
jobs=[];
signal(SIGINT, handleTermination);
for j in range(batches):
    for i in range(numProcess):
        p=Process(target=multiprocessRun,args=(rand[j*10+i],));
        jobs.append(p);
        p.start();
    # wait for the jobs in the batch to finish
    for job in jobs:
        job.join();