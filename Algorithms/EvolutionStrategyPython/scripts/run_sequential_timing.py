import time, subprocess, os
print('Starting sequential timing...')
t0=time.time()
subprocess.check_call([os.environ.get('PYTHON','python'),'sigma_ablation.py'])
print('Elapsed', time.time()-t0)
