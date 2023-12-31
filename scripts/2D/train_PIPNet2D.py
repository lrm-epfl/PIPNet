import numpy as np
import os
import json
import torch

from pipnet import data
from pipnet import model
from pipnet import train

torch.cuda.empty_cache()
device = "cuda" if torch.cuda.is_available() else "cpu"

iso_pars = dict(
    td = 128,
    Fs = 3_200,
    nmin = 1,
    nmax = 5,
    freq_range = [500., 2700.],
    gmin = 1,
    gmax = 1,
    spread = 5.,
    lw_range = [[5e1, 2e2], [1e2, 5e2], [1e2, 1e3]],
    lw_probs = [0.6, 0.2, 0.2],
    int_range = [0.1, 1.], # Intensity
    norm_height = True,
    phase = 0.,
    debug = False,
)

mas_pars = dict(
    nw = 12,
    mas_w_range = [50_000., 100_000.],
    random_mas = True,
    mas_phase_p = 0.5,
    mas_phase_scale = 0.05,
    
    # First-order MAS-dependent parameters
    mas1_lw_range = [[1e7, 2e7], [1e7, 5e7], [5e7, 1e8]],
    mas1_lw_probs = [0.6, 0.3, 0.1],
    mas1_m_range = [[0., 0.], [0., 1e4], [1e4, 5e4]],
    mas1_m_probs = [0.2, 0.2, 0.6],
    mas1_s_range = [[-1e7, 1e7]],
    mas1_s_probs = [1.],

    # Second-order MAS-dependent parameters
    mas2_prob = 1.,
    mas2_lw_range = [[0., 0.], [1e11, 5e11]],
    mas2_lw_probs = [0.5, 0.5],
    mas2_m_range = [[0., 0.], [1e8, 5e8]],
    mas2_m_probs = [0.5, 0.5],
    mas2_s_range = [[0., 0.], [-2e10, 2e10]],
    mas2_s_probs = [0.5, 0.5],
    
    # Other MAS-dependent parameters
    non_mas_p = 0.5,
    non_mas_m_trends = ["constant", "increase", "decrease"],
    non_mas_m_probs = [0.34, 0.33, 0.33],
    non_mas_m_range = [0., 1.],
    
    int_decrease_p = 0.3,
    int_decrease_scale =[0.3, 0.7],
    debug = False,
)

data_pars = dict(
    iso_pars = iso_pars,
    mas_pars = mas_pars,
    
    positive_iso = True,
    encode_imag = False, # Encode the imaginary part of the MAS spectra
    encode_wr = True, # Encode the MAS rate of the spectra

    # noise parameters
    noise = 0., # Noise level
    mas_l_noise = 0.05,
    mas_s_noise = 25.,
    
    smooth_end_len = 10, # Smooth ends of spectra
    iso_spec_norm = 1.25, # Normalization factor for peaks
    mas_spec_norm = 0.5, # Normalization factor for MAS spectra
    wr_norm_factor = 100_000.,
    wr_inv = False, # Encode inverse of MAS rate instead of MAS rate
    gen_mas_shifts = False,
)

model_pars = dict(
    input_dim = 2,
    n_models = 1,
    hidden_dim = [64, 64, 64, 64],
    kernel_size = [5, 5, 5, 5],
    num_layers = 4,
    batch_input = 1,
    bias = True,
    output_bias = True,
    return_all_layers = True,
    batch_norm = False,
    ndim = 2,
    independent = True,
    output_kernel_size = 5,
    output_act = "sigmoid",
    noise = 5e-3,
    invert = False,
)

loss_pars = dict(
    trg_fuzz = 1.,
    trg_fuzz_len = 25,
    ndim = 2,
    exp = 1.0,
    offset = 1.0,
    factor = 10.0,
    int_w = 0.0,
    int_exp = 2.0,
    return_components = False,
    device = device,
)

train_pars = dict(
    batch_size = 8,
    num_workers = 20,
    batches_per_epoch = 500,
    batches_per_eval = 100,
    n_epochs = 250,
    change_loss={25: {"trg_fuzz": 0.0, "factor": 0.},
                },
    out_dir = "../../data/2D/PIPNet_2022_12_14_4_layers/",
    save_every=50,
    device = device,
    monitor_end = "\n"
)

dataset = data.Dataset2D(params_x=data_pars, params_y=data_pars)
net = model.ConvLSTMEnsemble(**model_pars).to(device)
loss = model.PIPLoss(**loss_pars)
opt = torch.optim.Adam(net.parameters(), lr=1e-3)
sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=10)

if train_pars["out_dir"] is not None and not os.path.exists(train_pars["out_dir"]):
    os.mkdir(train_pars["out_dir"])

with open(train_pars["out_dir"] + "model_pars.json", "w") as F:
    json.dump(model_pars, F)

with open(train_pars["out_dir"] + "data_pars.json", "w") as F:
    json.dump(data_pars, F)

train.train(
    dataset,
    net,
    opt,
    loss,
    sch,
    **train_pars
)