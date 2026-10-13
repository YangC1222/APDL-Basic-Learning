"""Offline POD verification; only cases 1..9 are training data."""
import argparse, json, time
from pathlib import Path
import numpy as np

def verify(path):
    raw=np.loadtxt(path,delimiter=',')
    assert raw.shape[1]==7 and np.isfinite(raw).all()
    assert set(raw[:,0])==set(range(1,12))
    rows=[]
    for case in range(1,12):
        data=raw[(raw[:,0]==case)&np.isclose(raw[:,5],0,atol=1e-12)]
        data=data[np.argsort(data[:,4])]
        assert len(data)>2
        if rows: assert np.allclose(data[:,3:6],rows[0][:,3:6])
        rows.append(data)
    rad=rows[0][:,4]
    assert rad[0]==0 and abs(rad[-1]-.004)<1e-12
    boundaries=np.r_[0,(rad[:-1]+rad[1:])/2,rad[-1]]
    weights=np.pi*np.diff(boundaries**2)
    assert np.all(weights>0) and np.isclose(weights.sum(),np.pi*.004**2)
    rootw=np.sqrt(weights)
    rises=np.stack([x[:,6]-573 for x in rows],axis=1)
    start=time.perf_counter()
    u,s,vh=np.linalg.svd(rootw[:,None]*rises[:,:9],full_matrices=False)
    energy=np.cumsum(s**2)/np.sum(s**2)
    rank=int(np.searchsorted(energy,1-1e-10)+1)
    modes=u[:,:rank]/rootw[:,None]
    coeff=u[:,:rank].T@(rootw[:,None]*rises[:,:9])
    features=np.array([[x[0,1]/1e8,(x[0,1]/x[0,2])/1e4] for x in rows])
    reg=np.linalg.lstsq(features[:9],coeff.T,rcond=None)[0]
    offline=time.perf_counter()-start
    train_recon=modes@coeff
    train_error=np.linalg.norm(rootw[:,None]*(train_recon-rises[:,:9]))/np.linalg.norm(rootw[:,None]*rises[:,:9])
    tests=[]
    for i in (9,10):
        begin=time.perf_counter()
        prediction=modes@(features[i]@reg)
        elapsed=time.perf_counter()-begin
        q,h=rows[i][0,1:3]
        exact=q*.004/(2*h)+q*(.004**2-rad**2)/(4*3)
        tests.append(dict(case=i+1,scope='held_out_interpolation' if i==9 else 'out_of_training_range',q=float(q),h=float(h),weighted_temperature_rise_relative_error=float(np.linalg.norm(rootw*(prediction-rises[:,i]))/np.linalg.norm(rootw*rises[:,i])),peak_temperature_rise_relative_error=float(abs(prediction.max()-rises[:,i].max())/rises[:,i].max()),fom_peak_vs_analytic_relative_error=float(abs(rises[:,i].max()-exact.max())/exact.max()),surface_energy_balance_relative_error=float(abs(2*.004*h*rises[-1,i]-q*.004**2)/(q*.004**2)),coefficient_prediction_seconds=elapsed))
    assert rank==2, rank
    assert max(x['weighted_temperature_rise_relative_error'] for x in tests)<1e-7
    assert max(x['surface_energy_balance_relative_error'] for x in tests)<1e-8
    assert max(x['fom_peak_vs_analytic_relative_error'] for x in tests)<.004
    return dict(training_cases=list(range(1,10)),held_out_cases=[10,11],radial_nodes=len(rad),retained_modes=rank,singular_values=s.tolist(),retained_energy=float(energy[rank-1]),training_weighted_projection_relative_error=float(train_error),offline_pod_and_fit_seconds=offline,tests=tests,scope='Constant-property, fixed-geometry, linear steady conduction only. No claim of general ROM extrapolation reliability or end-to-end speedup.',data_leakage_check='Only nine training columns enter SVD and coefficient regression; both test solutions are excluded.')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('csv',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    result=verify(a.csv)
    if a.out:a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
