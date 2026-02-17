# configs/default.yaml
run_name: baseline_v6.2
n: 512
replicates: 120
seed: 42
band: 0.08
lambda_threshold: 0.75
k_max_fraction: 0.0625   # = 1/16
stress_k_fraction: 0.125 # = 1/8 (~pi/4)
bitflip_p_grid: [0.005, 0.01, 0.02, 0.05]
noise_sigma_grid: [0.0, 0.001, 0.002, 0.005]
