#libraries
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt;
from oxDNA_analysis_tools.UTILS.RyeReader import describe, get_confs, inbox, write_conf
from oxDNA_analysis_tools.UTILS.oxview import oxdna_conf
from Bio.SVDSuperimposer import SVDSuperimposer
from numpy import array, dot, set_printoptions
from mpl_toolkits import mplot3d
import plotly.express as px
from itertools import permutations
from tqdm import tqdm, trange
from multiprocessing import Pool

from scipy.spatial.transform import Rotation as R


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

#Loop through possibilities
import time
from itertools import permutations
start=3
stop=3.5
steps=50
covered = np.zeros(12,dtype=int)
goodDist = 9999999
goodMultiplier=0
for m in range(0,10):
    rand = int(time.time());
    print(rand)
    for i in range(0,steps+1):
        data = pd.read_csv("../analysis4/coor.csv");
        multiplier = start+(stop-start)*i/steps
        data['Z']*=multiplier
        # print(multiplier,data['Z'][0])
        
        kmeans = KMeans(
            n_clusters=12,init='random', n_init=12, max_iter=300,tol=1e-4,random_state=rand
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
            # with open("trials2/center"+str(m)+".np","wb") as f:
            #     np.save(f,Originalcentroids)
            # with open("trials2/labels"+str(m)+".np","wb") as f:
            #     np.save(f,kmeans.labels_)
    # print(m,goodDist,goodMultiplier)
    #Extra back to 2d
    data = pd.read_csv("../analysis4/coor.csv");
    data = data.to_numpy()
    data[:,2]*=goodMultiplier;
    kmeans = KMeans(
        n_clusters=12, init='random',
        n_init=12, max_iter=300, 
        tol=1e-04, random_state=rand
    ).fit(data)
    Originalcentroids=np.array(kmeans.cluster_centers_)
    Originalcentroids=Originalcentroids[:,:-1];
    kmeans = KMeans(
        n_clusters=8, init='random',
        n_init=10, max_iter=300, 
        tol=1e-04, random_state=0
    ).fit(Originalcentroids)
    Originalcentroids2=np.array(kmeans.cluster_centers_)
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
    
    print(rand,goodDist,goodMultiplier,storeDist)