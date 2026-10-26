# --- cell 0 ---
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
import plotly.graph_objects as go

from scipy.spatial.transform import Rotation as R

# --- cell 1 ---
#### Functions #######

def planeFit(points):
    """
    p, n = planeFit(points)

    Given an array, points, of shape (d,...)
    representing points in d-dimensional space,
    fit an d-dimensional plane to the points.
    Return a point, p, on the plane (the point-cloud centroid),
    and the normal, n.
    """
    import numpy as np
    from numpy.linalg import svd
    points = np.reshape(points, (np.shape(points)[0], -1)) # Collapse trialing dimensions
    assert points.shape[0] <= points.shape[1], "There are only {} points in {} dimensions.".format(points.shape[1], points.shape[0])
    ctr = points.mean(axis=1)
    x = points - ctr[:,np.newaxis]
    M = np.dot(x, x.T) # Could also use np.cov(x) here.
    return ctr, svd(M)[0][:,-1]

def angleRotation(basePositions):
    centroid, normal = planeFit(basePositions.transpose())
    yAngleRotation = np.rad2deg(np.arccos(np.dot(normal,[1,0,0])))-90
    xAngleRotation = 90-np.rad2deg(np.arccos(np.dot(normal,[0,1,0])))

    return xAngleRotation,yAngleRotation

def rotateEuler(conf,base,numberOfLoops=4,name="rotCorrection.dat"):
    for i in range(numberOfLoops):
        basePositions = conf.positions[base]
        xAngleRotation,yAngleRotation = angleRotation(basePositions);
        print(xAngleRotation,yAngleRotation)
        r = R.from_euler('yx',[yAngleRotation,xAngleRotation], degrees=True)
        conf.positions= r.apply(conf.positions)
        conf.a1s=r.apply(conf.a1s)
        conf.a3s=r.apply(conf.a3s)
    centroid, normal = planeFit(conf.positions[base].transpose())
    print("Rotational corrected normal with x,y and normal = ",np.rad2deg(np.arccos(np.dot(normal,[1,0,0]))),np.rad2deg(np.arccos(np.dot(normal,[0,1,0]))),normal)
    write_conf(name,conf)

# --- cell 2 ---
#### INitial Data #####

base=[10317,10316,10315,10314,10313,10312,10311,10310,10309,10308,10307,10306,10305,10304,10303,10302,10301,10300,10299,10298,10297,10296,10295,10294,10293,10292,10291,10290,10289,10288,10287,10286,10285,10284,10283,10282,10281,10280,10279,10278,10277,10276,10443,10442,10441,10440,10439,10438,10437,10436,10435,10434,10433,10432,10431,10430,10429,10428,10427,10426,10425,10424,10423,10422,10421,10420,10419,10418,10417,10416,10415,10414,10413,10412,10411,10410,10409,10408,10407,10406,10405,10404,10403,10402,10986,10985,10984,10983,10982,10981,10980,10979,10978,10977,10976,10975,10974,10973,10972,10971,10970,10969,10968,10967,10966,10965,10964,10963,10962,10961,10960,10959,10958,10957,10956,10955,10954,10953,10952,10951,10950,10949,10948,10947,10946,10945,11134,11133,11132,11131,11130,11129,11128,11127,11126,11125,11124,11123,11122,11121,11120,11119,11118,11117,11116,11115,11114,11113,11112,11111,11110,11109,11108,11107,11106,11105,11104,11103,11102,11101,11100,11099,11098,11097,11096,11095,11094,11093,11564,11563,11562,11561,11560,11559,11558,11557,11556,11555,11554,11553,11552,11551,11550,11549,11548,11547,11546,11545,11544,11543,11542,11541,11540,11539,11538,11537,11536,11535,11534,11533,11532,11531,11530,11529,11528,11527,11526,11525,11524,11523,11690,11689,11688,11687,11686,11685,11684,11683,11682,11681,11680,11679,11678,11677,11676,11675,11674,11673,11672,11671,11670,11669,11668,11667,11666,11665,11664,11663,11662,11661,11660,11659,11658,11657,11656,11655,11654,11653,11652,11651,11650,11649,12916,12915,12914,12913,12912,12911,12910,12909,12908,12907,12906,12905,12904,12903,12902,12901,12900,12899,12898,12897,12896,12895,12894,12893,12892,12891,12890,12889,12888,12887,12886,12885,12884,12883,12882,12881,12880,12879,12878,12877,12876,12875,13000,12999,12998,12997,12996,12995,12994,12993,12992,12991,12990,12989,12988,12987,12986,12985,12984,12983,12982,12981,12980,12979,12978,12977,12976,12975,12974,12973,12972,12971,12970,12969,12968,12967,12966,12965,12964,12963,12962,12961,12960,12959]
handle3 = np.array([7612,8201,8830,9239,9564,10025,10810,11755,12436,13001,13662,14259],dtype=int)
handle = np.zeros((12,21),dtype=int)
for i in range(12):
    handle[i][0]= handle3[i]
    for j in range(20):
        handle[i][j+1] = handle3[i]+j+1

# --- cell 3 ---
##### Rotational Correction based on bases ##########
ti,di = describe("output.top","mean.dat");
conf = get_confs(ti, di, 0, 1)[0]
rotateEuler(conf,base)

# --- cell 4 ---
ti,di = describe("output.top","rotCorrection.dat")
conf = get_confs(ti, di, 0, 1)[0]
redPositions = np.zeros((12,3),dtype=float);
for i in range(12):
    redPositions[i] = np.mean(conf.positions[handle[i]],axis=0);
redPositions = 0.8518*redPositions[:,:-1]
kmeans = KMeans(
    n_clusters=8, init='random',
    n_init=10, max_iter=300, 
    tol=1e-04, random_state=0
).fit(redPositions)
Obtainedcentroids=np.array(kmeans.cluster_centers_)
plt.figure(figsize=(5,5))
plt.scatter(Obtainedcentroids[:,0],Obtainedcentroids[:,1])

# --- cell 5 ---
data = pd.read_csv("../analysis4/coor.csv")
d2 = data[["X","Y"]].to_numpy()
kmeans = KMeans(
    n_clusters=8, init='random',
    n_init=10, max_iter=300, 
    tol=1e-04, random_state=0
).fit(d2)
Originalcentroids=np.array(kmeans.cluster_centers_)
plt.figure(figsize=(5,5))
plt.scatter(d2[:,0],d2[:,1],s=1)
plt.scatter(Originalcentroids[:,0],Originalcentroids[:,1])
plt.savefig("k-mean.png",dpi=100)
Originalcentroids

# --- cell 6 ---
from itertools import permutations
from time import sleep
# #from tqdm.auto
d2_3_init = np.array([[point[0], point[1],0] for point in Originalcentroids], dtype  = np.float64)
Obtainedcentroids = np.array([[point[0], point[1],0] for point in Obtainedcentroids], dtype  = np.float64)
D2_3Permute=list(permutations(d2_3_init))
print("Done calculating Permutations")
best_rmsd =40
p=0
j=0
for d2_3 in D2_3Permute:
    d2_3 = np.array(d2_3)
    sup = SVDSuperimposer()
    sup.set(d2_3, Obtainedcentroids)
    sup.run()
    rms = sup.get_rms()
    transformed = sup.get_transformed()
    if rms < best_rmsd:
        rot, tran = sup.get_rotran()
        best_transformed=  transformed
        best = d2_3
        best_rmsd = rms
        print(j/479001600,"%",rms,end="\r");
        q=True;
    if p>100000 and q==True:
        # plt.scatter(best[:,0],best[:,1])
        # plt.scatter(best_transformed[:,0],best_transformed[:,1])
        # plt.title(best_rmsd);
        # plt.savefig("live.png",dpi=100)
        # plt.close()
        # plt.pause(0.0001)
        # p=0
        # q=False;
        for i in range(12):
            plt.scatter([best[i,0],best_transformed[i,0]],[best[i,1],best_transformed[i,1]])
        # plt.scatter(best_transformed[:,0],best_transformed[:,1])
        plt.title(best_rmsd);
        plt.savefig("live.png",dpi=100)
        plt.close()
        plt.pause(0.0001)
        p=0
        q=False;
    p+=1
    j+=1
# file = open("best.npy",'w+')
# np.save("best.npy",best)
print(best_rmsd)
print("best transformed",best_transformed)
    # plt.scatter(d2_3[:,0],d2_3[:,1])
    # plt.scatter(transformed[:,0],transformed[:,1])
    # plt.savefig("transformed.png",dpi=100)
    #print(rms)
# file.close()
print("d2_3 best config",best);
plt.clf()
plt.figure(figsize=(5,5))
plt.scatter(d2[:,0],d2[:,1],s=1)
plt.scatter(best[:,0],best[:,1])
plt.scatter(best_transformed[:,0],best_transformed[:,1])
plt.savefig("presimu.png")

# --- cell 7 ---
# csfont = {'fontname':'Arial'}
# plt.rcParams["svg.fonttype"]='ARIAL.TTF'
plt.figure(figsize=(6,6))
plt.scatter(d2[:,0],d2[:,1],s=1)
plt.scatter(best[:,0],best[:,1])
plt.scatter(best_transformed[:,0],best_transformed[:,1])
plt.legend(["Paint-Data","K-mean Paint Data","Projection from 3D"])
plt.savefig("fig2.1.svg",dpi=3000)

# --- cell 8 ---
sum(np.linalg.norm(best_transformed-best,axis=1))

# --- cell 9 ---
rot, tran = sup.get_rotran()
print(rot,tran)
conf.positions=np.dot(conf.positions,rot) +tran
conf.a1s = np.dot(conf.a1s,rot)
conf.a3s = np.dot(conf.a3s,rot)
write_conf("2dfitting.dat",conf);

# --- cell 11 ---
# import cudf
# from cuml.cluster import DBSCAN
# from cuml.cluster import KMeans

# --- cell 12 ---
ti,di = describe("output.top","2dfitting.dat")
conf = get_confs(ti, di, 0, 1)[0]
red=[7612,8201,8830,9239,9564,10025,10810,11755,12436,13001,13662,14259];
redPositions = np.zeros((len(red),3),dtype=float);
for i in range(len(red)):
    redPositions[i] = np.mean(conf.positions[red[i]:red[i]+20],axis=0)
redPositions *= 0.8518
redPositions

# --- cell 13 ---
# import cudf
data = pd.read_csv("../analysis4/coor.csv");
data2=data.to_numpy()
data2[:,2]*=3.27
# b = cudf.DataFrame(data2)
kmeans = KMeans(
    n_clusters=12, init='random',
    n_init=12, max_iter=300, 
    tol=1e-04, random_state=6
).fit(data2)
Originalcentroids=kmeans.cluster_centers_
# Originalcentroids = Originalcentroids.to_numpy()
with open("center.xyz","w") as f:
    for i in Originalcentroids:
        f.write(f"{i[0]/0.8518} {i[1]/0.8518} {i[2]/0.8518}\n");

# --- cell 14 ---
data["color"]= kmeans.labels_
df=data
fig = px.scatter_3d(df, x='X', y='Y', z='Z',
                    # size=np.ones(len(df),dtype=int),
                    width=1000, height=1000, color="color",opacity=1,size_max=0.02)
fig.update_layout(scene=dict(
    aspectmode='data',
    zaxis= dict(nticks=20)
))

fig.show()

# --- cell 15 ---
fig = go.Figure(data=[go.Scatter3d(x=df['X'], y=df['Y'], z=df['Z'],mode="markers",marker=dict(
        size=12,
        color=df['Z'],                # set color to an array/list of desired values
        colorscale='Rainbow',   # choose a colorscale
        opacity=1
    ))])
fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
fig.show()

# --- cell 16 ---
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='3d')
x = np.array(df['X'])
y = np.array(df['Y'])
z = np.array(df['Z'])

ax.scatter(x,y,z, marker="s", c=df["color"], s=40, cmap="RdBu")

plt.show()

# --- cell 17 ---
color = kmeans.labels_
unique,counts = np.unique(color,return_counts=True);

for i in range(12):
    data0=data[data['color']==i].to_numpy()[:,:-1];
    mean = kmeans.cluster_centers_[i]
    radiusMean = np.mean(np.linalg.norm(mean-data0,axis=1));
    
# for j in range(len(data0)):
    # if j ==0:
        # radius = np.linalg.norm(mean - data0[j]);

# --- cell 18 ---
import time
start=3.0
stop=3.5
steps=50
covered = np.zeros(12,dtype=int)
goodDist = 9999999
goodMultiplier=0
for i in range(0,steps+1):
    data = pd.read_csv("../analysis4/coor.csv");
    multiplier = start+(stop-start)*i/steps
    data['Z']*=multiplier
    # print(multiplier,data['Z'][0])

    kmeans = KMeans(
        n_clusters=12,init='random', n_init=12, max_iter=300,tol=1e-4,random_state=6
    ).fit(data)
    Originalcentroids = np.array(kmeans.cluster_centers_)
    sumdist=0
    covered.fill(20)
    for p in range(12):
        dist=999999
        for j in range(12):
            # if j in covered:
            #     continue
            newdist = np.linalg.norm(redPositions[j]-Originalcentroids[p]);
            if newdist < dist:
                dist=newdist;
                best=j
        covered[p]=best
        sumdist+=dist
    print(multiplier,sumdist)
    if sumdist < goodDist:
        goodDist=sumdist;
        goodMultiplier=multiplier;
        with open("center2.xyz","w") as f:
            for i in Originalcentroids:
                f.write(f"{i[0]/0.8518} {i[1]/0.8518} {i[2]/0.8518}\n");

print(goodDist,goodMultiplier)

# --- cell 20 ---
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

# --- cell 21 ---
KMeans?

# --- cell 22 ---
# Originalcentroids[:,:-1]

# --- cell 24 ---
# import time
data = pd.read_csv("../analysis4/coor.csv");
data2=data.to_numpy()
data2[:,2]*=3.
kmeans = KMeans(
    n_clusters=12, init='random',
    n_init=12, max_iter=300, 
    tol=1e-04, random_state=1685473465
).fit(data2)
Originalcentroids=kmeans.cluster_centers_
Originalcentroids=np.array(kmeans.cluster_centers_)


# plt.scatter(d2[:,0],d2[:,1],s=1)
Originalcentroids= Originalcentroids[:,:-1]
# plt.scatter(Originalcentroids[:,0],Originalcentroids[:,1])
kmeans = KMeans(
    n_clusters=8, init='random',
    n_init=10, max_iter=300, 
    tol=1e-04, random_state=0
).fit(Originalcentroids)
Originalcentroids2=np.array(kmeans.cluster_centers_)
# plt.scatter(Originalcentroids2[:,0],Originalcentroids2[:,1])

kmeans = KMeans(
    n_clusters=8, init='random',
    n_init=10, max_iter=300, 
    tol=1e-04, random_state=0
).fit(d2)
realCentroids = kmeans.cluster_centers_
# plt.scatter(realCentroids[:,0],realCentroids[:,1])


sumdist=0
# for i in range(8):
    # sumdist+=np.linalg.norm(realCentroids[]-Originalcentroids2)

np.linalg.norm(realCentroids-Originalcentroids2,axis=1)
from itertools import permutations
from time import sleep

OriginalcentroidsPermute=list(permutations(Originalcentroids2))
print("Done calculating Permutations")
storeDist=90000;

for p in OriginalcentroidsPermute:
    p= np.array(p)
    sumDist=np.sum(np.linalg.norm((realCentroids-p),axis=1))
    if sumDist<storeDist:
        storeDist=sumDist

print(storeDist)


# --- cell 25 ---
# plt.figure(figsize=(6,6))
plt.scatter(d2[:,0],d2[:,1],s=1)
plt.scatter(realCentroids[:,0],realCentroids[:,1])
plt.scatter(Originalcentroids2[:,0],Originalcentroids2[:,1])
plt.legend(["Pait-Data","K-mean Paint Data","Projection from 3d Fitting"])
plt.savefig("BackTo2d.png",dpi=300)

# --- cell 26 ---
# from itertools import permutations
from time import sleep

OriginalcentroidsPermute=list(permutations(Originalcentroids2))
print("Done calculating Permutations")
storeDist=90000;

for p in OriginalcentroidsPermute:
    p= np.array(p)
    sumDist=np.sum(np.linalg.norm((realCentroids-p),axis=1))
    if sumDist<storeDist:
        storeDist=sumDist

print(storeDist)

# --- cell 27 ---
# from itertools import permutations
from time import sleep
# #from tqdm.auto
d2_3_init = np.array([[point[0], point[1],0] for point in Originalcentroids2], dtype  = np.float64)
Obtainedcentroids = np.array([[point[0], point[1],0] for point in realCentroids], dtype  = np.float64)
D2_3Permute=list(permutations(d2_3_init))
print("Done calculating Permutations")
best_rmsd =40
p=0
j=0
for d2_3 in D2_3Permute:
    d2_3 = np.array(d2_3)
    sup = SVDSuperimposer()
    sup.set(d2_3, Obtainedcentroids)
    sup.run()
    rms = sup.get_rms()
    transformed = sup.get_transformed()
    if rms < best_rmsd:
        rot, tran = sup.get_rotran()
        best_transformed=  transformed
        best = d2_3
        best_rmsd = rms
        print(j/479001600,"%",rms,end="\r");
        q=True;
    if p>100000 and q==True:
        # plt.scatter(best[:,0],best[:,1])
        # plt.scatter(best_transformed[:,0],best_transformed[:,1])
        # plt.title(best_rmsd);
        # plt.savefig("live.png",dpi=100)
        # plt.close()
        # plt.pause(0.0001)
        # p=0
        # q=False;
        for i in range(12):
            plt.scatter([best[i,0],best_transformed[i,0]],[best[i,1],best_transformed[i,1]])
        # plt.scatter(best_transformed[:,0],best_transformed[:,1])
        plt.title(best_rmsd);
        plt.savefig("live.png",dpi=100)
        plt.close()
        plt.pause(0.0001)
        p=0
        q=False;
    p+=1
    j+=1
# file = open("best.npy",'w+')
# np.save("best.npy",best)
print(best_rmsd)
print("best transformed",best_transformed)
    # plt.scatter(d2_3[:,0],d2_3[:,1])
    # plt.scatter(transformed[:,0],transformed[:,1])
    # plt.savefig("transformed.png",dpi=100)
    #print(rms)
# file.close()
print("d2_3 best config",best);
plt.clf()
plt.scatter(d2[:,0],d2[:,1],s=1)
plt.scatter(best[:,0],best[:,1])
plt.scatter(best_transformed[:,0],best_transformed[:,1])

# --- cell 28 ---
# sum(np.linalg.norm(best_transformed-best,axis=1))

# --- cell 29 ---
# ti,di = describe("output.top","mean.dat");
conf = get_confs(ti, di, 0, 1)[0]
pos1 = conf.positions;
pos1 = np.delete(pos1,handle,0)
ti2,di2 = describe("output.top","meanAll.dat");
conf2 = get_confs(ti2,di2,0,1)[0]
pos2 = conf2.positions
pos2 = np.delete(pos2,handle,0);
# pos1.shape
# pos2

sup = SVDSuperimposer()
sup.set(pos1, pos2);
sup.run()
rms = sup.get_rms()
print(rms)

# --- cell 30 ---
# arr = np.array([[1,2,3,4], [5,6,7,8], [9,10,11,12]])
np.delete(arr,[0,1],0)

# --- cell 31 ---
def angleAndLength(ids):
    ti,di = describe("output.top","2dfitting.dat")
    conf = get_confs(ti, di, 0, 1)[0]
    par1 = conf.positions[ids[0]]
    par2 = conf.positions[ids[1]]
    par3 = conf.positions[ids[2]]
    par4 = conf.positions[ids[3]]
    
    line1 = par1-par4
    line2 = par1-par2
    print("Angle 1 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1 = par2-par3
    line2 = par2-par1
    print("Angle 2 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1=par3-par4
    line2=par3-par2
    print("Angle 3 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1=par4-par3
    line2=par4-par1
    print("Angle 4 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    print("Length of side 1 = ", np.linalg.norm(par2-par1));
    print("Length of side 2 = ",np.linalg.norm(par3-par2));
    print("Length of side 3 = ",np.linalg.norm(par4-par3));
    print("Length of side 4 = ",np.linalg.norm(par1-par4));

# Biotin plane
ids=np.array([12457,9260,9585,11776],dtype=int);
print("Biotin plane/Base plane");
angleAndLength(ids)
#Middle plane
ids=np.array([13022,10046,8222,13683],dtype=int);
print("Middle plane");
angleAndLength(ids)
#Top plane
ids=np.array([14280,7633,8851,10831],dtype=int);
print("Top plane")
angleAndLength(ids)

# --- cell 32 ---
def angleAndLength2(ids):
    pdata = pd.read_csv("center.xyz",delimiter=" ",names=["x","y","z"]).to_numpy();
    par1=pdata[ids[0]];
    par2=pdata[ids[1]];
    par3=pdata[ids[2]];
    par4=pdata[ids[3]];
    
    line1 = par1-par4
    line2 = par1-par2
    print("Angle 1 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1 = par2-par3
    line2 = par2-par1
    print("Angle 2 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1=par3-par4
    line2=par3-par2
    print("Angle 3 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    line1=par4-par3
    line2=par4-par1
    print("Angle 4 = ",np.rad2deg(np.arccos(np.dot(line1,line2)/(np.linalg.norm(line1)*np.linalg.norm(line2)))))
    
    print("Length of side 1 = ", np.linalg.norm(par2-par1));
    print("Length of side 2 = ",np.linalg.norm(par3-par2));
    print("Length of side 3 = ",np.linalg.norm(par4-par3));
    print("Length of side 4 = ",np.linalg.norm(par1-par4));

ids=np.array([0,1,10,3],dtype=int);
print("Biotin plane/Base plane");
angleAndLength2(ids)
#Middle plane
ids=np.array([2,6,11,9],dtype=int);
print("Middle plane");
angleAndLength2(ids)
#Top plane
ids=np.array([4,7,5,8],dtype=int);
print("Top plane")
angleAndLength2(ids)

print(pd.read_csv("center.xyz",delimiter=" ",names=["x","y","z"]).to_numpy());
