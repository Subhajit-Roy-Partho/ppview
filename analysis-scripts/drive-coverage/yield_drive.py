import json, os, subprocess, sys
sys.path.insert(0, os.path.expanduser('~/Documents/Github/ppview/clear/scripts'))
import cluster_labels as CL
import numpy as np
ROOT = '/mnt/Drive/PHB'
def run(top):
    d = os.path.dirname(top)
    conf = os.path.join(d, 'last_conf.dat')
    if not os.path.isfile(conf): return None
    try: t = open(conf).readline().split()[2]
    except Exception: return None
    if t == '0': return None
    try:
        topo = CL.load_topology(top)
        tc, box, pos, a1, a3 = CL.load_conf(conf, topo['N'])
        res = CL.analyze_conf(topo, conf=(tc, box, pos, a1, a3))
        n = topo['n_mol']; val = np.asarray(res['valence'])
        return dict(dir=d, n=int(n),
                    largest=float((np.asarray(res['mol_label'])==0).sum()/n),
                    valence=float(val.mean()), six=float((val==6).mean()))
    except Exception as e:
        return {'dir': d, 'error': str(e)[:100]}
if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1])))
