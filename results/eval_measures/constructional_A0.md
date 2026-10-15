# constructional profile (arm A0); z per feature against the author's REF+TRAIN (sd floor 0.25); RFPD = mean |z|, ARTI = mean max(0,z), ARTI_hard = the four constructions Patrick rejected by name

## rfpd

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.309 | 0.111 |
| base4b | wharton | 4b | base | 88 | 0.838 | 0.439 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.777 | 0.605 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.433 | 0.191 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.388 | 0.145 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.637 | 0.433 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.557 | 0.242 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.497 | 0.243 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.439 | 0.194 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.470 | 0.242 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.496 | 0.226 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.441 | 0.183 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.510 | 0.239 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.391 | 0.114 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.780 | 0.734 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.799 | 0.600 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.554 | 0.345 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.343 | 0.122 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.698 | 0.967 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.541 | 0.262 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.860 | 0.675 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.532 | 0.354 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.536 | 0.419 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.495 | 0.301 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.487 | 0.252 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.487 | 0.218 |
| h_private SOURCE | h_private | - | source | 30 | 0.419 | 0.074 |
| h_private_base4b | h_private | 4b | base | 46 | 0.511 | 0.156 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.672 | 0.166 |
| chopin SOURCE | chopin | - | source | 50 | 0.311 | 0.092 |
| chopin_base4b | chopin | 4b | base | 98 | 0.749 | 0.506 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.838 | 0.803 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.375 | 0.132 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.711 | 0.337 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.979 | 0.857 |
| cather SOURCE | cather | - | source | 50 | 0.328 | 0.106 |
| cather_base4b | cather | 4b | base | 88 | 0.718 | 0.432 |
| cather_pair4b | cather | 4b | adapter | 88 | 1.239 | 1.515 |
| cather_base14b | cather | 14b | base | 88 | 0.409 | 0.161 |
| cather_base8b | cather | 8b | base | 88 | 0.467 | 0.225 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 1.088 | 2.390 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.923 | 1.229 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.461 | 0.224 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.460 | 0.277 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.547 | 0.252 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.534 | 0.225 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.486 | 0.203 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.503 | 0.199 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.531 | 0.262 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.509 | 0.239 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.463 | 0.269 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.452 | 0.182 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.441 | 0.191 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.518 | 0.224 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.541 | 0.218 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 1.306 | 1.617 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.709 | 0.574 |
| chopin_base14b | chopin | 14b | base | 98 | 0.409 | 0.169 |
| chopin_base8b | chopin | 8b | base | 98 | 0.465 | 0.189 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.782 | 1.265 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.878 | 0.624 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.361 | 0.087 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.395 | 0.102 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.686 | 0.384 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.424 | 0.118 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.404 | 0.092 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.431 | 0.103 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.393 | 0.106 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.410 | 0.122 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.494 | 0.155 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.504 | 0.666 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.403 | 0.133 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.437 | 0.151 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.405 | 0.118 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.477 | 0.157 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.505 | 0.201 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.473 | 0.188 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.836 | 0.940 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.460 | 0.162 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.642 | 0.451 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.563 | 0.252 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.461 | 0.163 |
| h_private_base14b | h_private | 14b | base | 46 | 0.473 | 0.082 |
| h_private_base8b | h_private | 8b | base | 46 | 0.503 | 0.134 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.776 | 0.411 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.840 | 0.408 |
| link SOURCE | link | - | source | 25 | 0.453 | 0.138 |
| link_base14b | link | 14b | base | 32 | 0.472 | 0.138 |
| link_base4b | link | 4b | base | 32 | 1.019 | 1.452 |
| link_base8b | link | 8b | base | 32 | 0.520 | 0.214 |
| link_paire6_14b | link | 14b | adapter | 32 | 1.159 | 1.350 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.790 | 0.476 |
| link_paire6_8b | link | 8b | adapter | 32 | 1.731 | 3.313 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.404 | 0.124 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.504 | 0.220 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.533 | 0.253 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.565 | 0.246 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.557 | 0.245 |
| patrick SOURCE | patrick | - | source | 50 | 0.298 | 0.120 |
| patrick_base4b | patrick | 4b | base | 92 | 0.526 | 0.292 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.436 | 0.263 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.531 | 0.225 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.542 | 0.205 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.483 | 0.198 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.516 | 0.222 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.448 | 0.250 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.529 | 0.287 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.501 | 0.304 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 1.009 | 1.521 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.761 | 0.816 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.742 | 0.653 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.558 | 0.309 |
| rucker SOURCE | rucker | - | source | 50 | 0.360 | 0.101 |
| rucker_base14b | rucker | 14b | base | 94 | 0.460 | 0.177 |
| rucker_base4b | rucker | 4b | base | 94 | 0.982 | 0.745 |
| rucker_base8b | rucker | 8b | base | 94 | 0.515 | 0.232 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.455 | 0.176 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.479 | 0.190 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.469 | 0.158 |
| stross SOURCE | stross | - | source | 50 | 0.387 | 0.135 |
| stross_base14b | stross | 14b | base | 82 | 0.624 | 0.333 |
| stross_base4b | stross | 4b | base | 82 | 1.202 | 0.956 |
| stross_base8b | stross | 8b | base | 82 | 0.662 | 0.460 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.595 | 0.419 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.578 | 0.322 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.648 | 0.831 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.433 | 0.174 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.437 | 0.115 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.978 | 0.939 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.908 | 0.748 |
| watts SOURCE | watts | - | source | 50 | 0.372 | 0.096 |
| watts_base14b | watts | 14b | base | 90 | 0.412 | 0.123 |
| watts_base4b | watts | 4b | base | 90 | 0.691 | 0.408 |
| watts_base8b | watts | 8b | base | 90 | 0.460 | 0.211 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.489 | 0.161 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.517 | 0.177 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.472 | 0.153 |
| wharton_base14b | wharton | 14b | base | 88 | 0.457 | 0.201 |
| wharton_base8b | wharton | 8b | base | 88 | 0.501 | 0.226 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.395 | 0.144 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.434 | 0.174 |

Replicate floor:

- base4b vs base4b_r2: -0.061
- chesterton_base4b vs chesterton_base4bc: -0.080
- mansfield_base4b vs mansfield_base4b_r2: +0.018

Base vs adapter:

- cather 14b: base 0.409 -> adapter 1.088 (+0.679)
- cather 4b: base 0.718 -> adapter 1.239 (+0.521)
- cather 8b: base 0.467 -> adapter 0.923 (+0.457)
- chesterton 14b: base 0.441 -> adapter 0.510 (+0.069)
- chesterton 4b: base 0.637 -> adapter 0.497 (-0.141)
- chesterton 4bc: base 0.557 -> adapter 0.439 (-0.118)
- chesterton 8b: base 0.470 -> adapter 0.496 (+0.026)
- chesterton m14b: base 0.547 -> adapter 0.463 (-0.084)
- chesterton m3b: base 0.486 -> adapter 0.452 (-0.035)
- chesterton m8b: base 0.531 -> adapter 0.441 (-0.090)
- chopin 14b: base 0.409 -> adapter 0.782 (+0.373)
- chopin 4b: base 0.749 -> adapter 0.838 (+0.089)
- chopin 8b: base 0.465 -> adapter 0.878 (+0.413)
- doctorow 14b: base 0.395 -> adapter 0.410 (+0.016)
- doctorow 4b: base 0.686 -> adapter 0.494 (-0.193)
- doctorow 8b: base 0.424 -> adapter 0.504 (+0.080)
- doctorow m14b: base 0.404 -> adapter 0.403 (-0.001)
- doctorow m3b: base 0.431 -> adapter 0.437 (+0.006)
- doctorow m8b: base 0.393 -> adapter 0.405 (+0.011)
- h_private 14b: base 0.473 -> adapter 0.776 (+0.304)
- h_private 4b: base 0.511 -> adapter 0.672 (+0.161)
- h_private 8b: base 0.503 -> adapter 0.840 (+0.337)
- link 14b: base 0.472 -> adapter 1.159 (+0.686)
- link 4b: base 1.019 -> adapter 0.790 (-0.228)
- link 8b: base 0.520 -> adapter 1.731 (+1.212)
- mansfield 14b: base 0.404 -> adapter 0.533 (+0.129)
- mansfield 4b: base 0.780 -> adapter 0.554 (-0.226)
- mansfield 8b: base 0.504 -> adapter 0.565 (+0.061)
- patrick 4b: base 0.526 -> adapter 0.436 (-0.090)
- patrick_v2 14b: base 0.487 -> adapter 0.487 (-0.000)
- patrick_v2 17b: base 0.698 -> adapter 0.541 (-0.157)
- patrick_v2 4b: base 0.860 -> adapter 0.532 (-0.328)
- patrick_v2 8b: base 0.536 -> adapter 0.495 (-0.040)
- patrick_v2 m14b: base 0.531 -> adapter 0.448 (-0.084)
- patrick_v2 m3b: base 0.542 -> adapter 0.529 (-0.013)
- patrick_v2 m8b: base 0.516 -> adapter 0.501 (-0.015)
- rucker 14b: base 0.460 -> adapter 0.455 (-0.005)
- rucker 4b: base 0.982 -> adapter 0.479 (-0.503)
- rucker 8b: base 0.515 -> adapter 0.469 (-0.047)
- stross 14b: base 0.624 -> adapter 0.595 (-0.029)
- stross 4b: base 1.202 -> adapter 0.578 (-0.624)
- stross 8b: base 0.662 -> adapter 0.648 (-0.014)
- sui_sin_far 14b: base 0.433 -> adapter 0.978 (+0.545)
- sui_sin_far 4b: base 0.711 -> adapter 0.979 (+0.268)
- sui_sin_far 8b: base 0.437 -> adapter 0.908 (+0.471)
- watts 14b: base 0.412 -> adapter 0.489 (+0.077)
- watts 4b: base 0.691 -> adapter 0.517 (-0.173)
- watts 8b: base 0.460 -> adapter 0.472 (+0.011)
- wharton 14b: base 0.457 -> adapter 0.395 (-0.062)
- wharton 4b: base 0.838 -> adapter 0.433 (-0.405)
- wharton 8b: base 0.501 -> adapter 0.434 (-0.067)

## arti

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.148 | 0.123 |
| base4b | wharton | 4b | base | 88 | 0.665 | 0.450 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.597 | 0.607 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.275 | 0.198 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.215 | 0.163 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.440 | 0.453 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.360 | 0.262 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.339 | 0.251 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.273 | 0.205 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.255 | 0.270 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.347 | 0.240 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.233 | 0.210 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.355 | 0.247 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.201 | 0.125 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.521 | 0.729 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.543 | 0.612 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.369 | 0.354 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.189 | 0.137 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.532 | 0.971 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.401 | 0.271 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.707 | 0.680 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.395 | 0.360 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.374 | 0.430 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.351 | 0.308 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.334 | 0.268 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.342 | 0.230 |
| h_private SOURCE | h_private | - | source | 30 | 0.203 | 0.087 |
| h_private_base4b | h_private | 4b | base | 46 | 0.184 | 0.170 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.392 | 0.180 |
| chopin SOURCE | chopin | - | source | 50 | 0.155 | 0.108 |
| chopin_base4b | chopin | 4b | base | 98 | 0.569 | 0.519 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.694 | 0.799 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.200 | 0.151 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.497 | 0.352 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.750 | 0.863 |
| cather SOURCE | cather | - | source | 50 | 0.153 | 0.127 |
| cather_base4b | cather | 4b | base | 88 | 0.527 | 0.439 |
| cather_pair4b | cather | 4b | adapter | 88 | 1.048 | 1.514 |
| cather_base14b | cather | 14b | base | 88 | 0.212 | 0.172 |
| cather_base8b | cather | 8b | base | 88 | 0.262 | 0.239 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.908 | 2.391 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.739 | 1.225 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.258 | 0.247 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.240 | 0.302 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.327 | 0.269 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.309 | 0.230 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.256 | 0.208 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.262 | 0.205 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.307 | 0.276 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.284 | 0.255 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.296 | 0.284 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.283 | 0.195 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.269 | 0.201 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.355 | 0.237 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.373 | 0.235 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 1.116 | 1.621 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.549 | 0.580 |
| chopin_base14b | chopin | 14b | base | 98 | 0.219 | 0.177 |
| chopin_base8b | chopin | 8b | base | 98 | 0.261 | 0.202 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.644 | 1.255 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.739 | 0.621 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.181 | 0.101 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.167 | 0.117 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.468 | 0.388 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.189 | 0.137 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.183 | 0.110 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.202 | 0.122 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.157 | 0.119 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.232 | 0.129 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.326 | 0.168 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.328 | 0.664 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.224 | 0.147 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.257 | 0.161 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.224 | 0.124 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.301 | 0.170 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.343 | 0.213 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.300 | 0.198 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.591 | 0.943 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.287 | 0.175 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.436 | 0.453 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.373 | 0.250 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.298 | 0.169 |
| h_private_base14b | h_private | 14b | base | 46 | 0.112 | 0.088 |
| h_private_base8b | h_private | 8b | base | 46 | 0.147 | 0.158 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.498 | 0.409 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.547 | 0.410 |
| link SOURCE | link | - | source | 25 | 0.283 | 0.165 |
| link_base14b | link | 14b | base | 32 | 0.241 | 0.161 |
| link_base4b | link | 4b | base | 32 | 0.797 | 1.447 |
| link_base8b | link | 8b | base | 32 | 0.282 | 0.221 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.913 | 1.353 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.580 | 0.492 |
| link_paire6_8b | link | 8b | adapter | 32 | 1.514 | 3.323 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.141 | 0.139 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.220 | 0.229 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.348 | 0.263 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.375 | 0.257 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.373 | 0.260 |
| patrick SOURCE | patrick | - | source | 50 | 0.158 | 0.128 |
| patrick_base4b | patrick | 4b | base | 92 | 0.379 | 0.302 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.306 | 0.272 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.379 | 0.239 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.383 | 0.221 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.323 | 0.212 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.360 | 0.240 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.293 | 0.262 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.380 | 0.305 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.345 | 0.318 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.830 | 1.519 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.609 | 0.816 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.591 | 0.660 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.415 | 0.319 |
| rucker SOURCE | rucker | - | source | 50 | 0.196 | 0.110 |
| rucker_base14b | rucker | 14b | base | 94 | 0.268 | 0.190 |
| rucker_base4b | rucker | 4b | base | 94 | 0.798 | 0.754 |
| rucker_base8b | rucker | 8b | base | 94 | 0.315 | 0.247 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.295 | 0.185 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.323 | 0.201 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.309 | 0.165 |
| stross SOURCE | stross | - | source | 50 | 0.227 | 0.153 |
| stross_base14b | stross | 14b | base | 82 | 0.432 | 0.348 |
| stross_base4b | stross | 4b | base | 82 | 0.996 | 0.961 |
| stross_base8b | stross | 8b | base | 82 | 0.454 | 0.478 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.424 | 0.423 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.411 | 0.333 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.475 | 0.834 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.189 | 0.195 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.188 | 0.126 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.751 | 0.942 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.669 | 0.756 |
| watts SOURCE | watts | - | source | 50 | 0.172 | 0.109 |
| watts_base14b | watts | 14b | base | 90 | 0.194 | 0.146 |
| watts_base4b | watts | 4b | base | 90 | 0.479 | 0.420 |
| watts_base8b | watts | 8b | base | 90 | 0.228 | 0.224 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.313 | 0.174 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.347 | 0.189 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.301 | 0.164 |
| wharton_base14b | wharton | 14b | base | 88 | 0.276 | 0.215 |
| wharton_base8b | wharton | 8b | base | 88 | 0.306 | 0.246 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.240 | 0.149 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.278 | 0.183 |

Replicate floor:

- base4b vs base4b_r2: -0.068
- chesterton_base4b vs chesterton_base4bc: -0.080
- mansfield_base4b vs mansfield_base4b_r2: +0.022

Base vs adapter:

- cather 14b: base 0.212 -> adapter 0.908 (+0.696)
- cather 4b: base 0.527 -> adapter 1.048 (+0.521)
- cather 8b: base 0.262 -> adapter 0.739 (+0.476)
- chesterton 14b: base 0.233 -> adapter 0.355 (+0.122)
- chesterton 4b: base 0.440 -> adapter 0.339 (-0.101)
- chesterton 4bc: base 0.360 -> adapter 0.273 (-0.087)
- chesterton 8b: base 0.255 -> adapter 0.347 (+0.091)
- chesterton m14b: base 0.327 -> adapter 0.296 (-0.032)
- chesterton m3b: base 0.256 -> adapter 0.283 (+0.028)
- chesterton m8b: base 0.307 -> adapter 0.269 (-0.038)
- chopin 14b: base 0.219 -> adapter 0.644 (+0.425)
- chopin 4b: base 0.569 -> adapter 0.694 (+0.124)
- chopin 8b: base 0.261 -> adapter 0.739 (+0.478)
- doctorow 14b: base 0.167 -> adapter 0.232 (+0.064)
- doctorow 4b: base 0.468 -> adapter 0.326 (-0.142)
- doctorow 8b: base 0.189 -> adapter 0.328 (+0.139)
- doctorow m14b: base 0.183 -> adapter 0.224 (+0.041)
- doctorow m3b: base 0.202 -> adapter 0.257 (+0.055)
- doctorow m8b: base 0.157 -> adapter 0.224 (+0.067)
- h_private 14b: base 0.112 -> adapter 0.498 (+0.386)
- h_private 4b: base 0.184 -> adapter 0.392 (+0.208)
- h_private 8b: base 0.147 -> adapter 0.547 (+0.400)
- link 14b: base 0.241 -> adapter 0.913 (+0.672)
- link 4b: base 0.797 -> adapter 0.580 (-0.217)
- link 8b: base 0.282 -> adapter 1.514 (+1.232)
- mansfield 14b: base 0.141 -> adapter 0.348 (+0.207)
- mansfield 4b: base 0.521 -> adapter 0.369 (-0.152)
- mansfield 8b: base 0.220 -> adapter 0.375 (+0.155)
- patrick 4b: base 0.379 -> adapter 0.306 (-0.074)
- patrick_v2 14b: base 0.334 -> adapter 0.342 (+0.007)
- patrick_v2 17b: base 0.532 -> adapter 0.401 (-0.131)
- patrick_v2 4b: base 0.707 -> adapter 0.395 (-0.312)
- patrick_v2 8b: base 0.374 -> adapter 0.351 (-0.023)
- patrick_v2 m14b: base 0.379 -> adapter 0.293 (-0.086)
- patrick_v2 m3b: base 0.383 -> adapter 0.380 (-0.003)
- patrick_v2 m8b: base 0.360 -> adapter 0.345 (-0.015)
- rucker 14b: base 0.268 -> adapter 0.295 (+0.026)
- rucker 4b: base 0.798 -> adapter 0.323 (-0.475)
- rucker 8b: base 0.315 -> adapter 0.309 (-0.006)
- stross 14b: base 0.432 -> adapter 0.424 (-0.009)
- stross 4b: base 0.996 -> adapter 0.411 (-0.584)
- stross 8b: base 0.454 -> adapter 0.475 (+0.021)
- sui_sin_far 14b: base 0.189 -> adapter 0.751 (+0.561)
- sui_sin_far 4b: base 0.497 -> adapter 0.750 (+0.252)
- sui_sin_far 8b: base 0.188 -> adapter 0.669 (+0.481)
- watts 14b: base 0.194 -> adapter 0.313 (+0.119)
- watts 4b: base 0.479 -> adapter 0.347 (-0.132)
- watts 8b: base 0.228 -> adapter 0.301 (+0.073)
- wharton 14b: base 0.276 -> adapter 0.240 (-0.036)
- wharton 4b: base 0.665 -> adapter 0.275 (-0.389)
- wharton 8b: base 0.306 -> adapter 0.278 (-0.027)

## arti_hard

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.100 | 0.275 |
| base4b | wharton | 4b | base | 88 | 1.347 | 1.705 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.980 | 2.782 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.218 | 0.485 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.218 | 0.411 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.723 | 1.698 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.614 | 1.012 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.421 | 0.778 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.246 | 0.397 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.236 | 0.650 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.375 | 0.537 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.189 | 0.446 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.525 | 0.645 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.332 | 0.496 |
| mansfield_base4b | mansfield | 4b | base | 82 | 1.334 | 3.472 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 1.065 | 2.537 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.330 | 0.550 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.077 | 0.277 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 1.024 | 4.110 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.380 | 0.607 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 1.133 | 2.339 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.417 | 0.733 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.477 | 0.763 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.404 | 0.667 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.398 | 0.739 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.263 | 0.561 |
| h_private SOURCE | h_private | - | source | 30 | 0.268 | 0.235 |
| h_private_base4b | h_private | 4b | base | 46 | 0.233 | 0.493 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.303 | 0.515 |
| chopin SOURCE | chopin | - | source | 50 | 0.131 | 0.319 |
| chopin_base4b | chopin | 4b | base | 98 | 1.023 | 2.142 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.438 | 0.603 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.325 | 0.582 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.903 | 1.240 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.943 | 3.466 |
| cather SOURCE | cather | - | source | 50 | 0.085 | 0.304 |
| cather_base4b | cather | 4b | base | 88 | 1.120 | 1.935 |
| cather_pair4b | cather | 4b | adapter | 88 | 1.999 | 6.226 |
| cather_base14b | cather | 14b | base | 88 | 0.116 | 0.347 |
| cather_base8b | cather | 8b | base | 88 | 0.477 | 1.022 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 1.252 | 6.322 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.386 | 1.018 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.297 | 0.651 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.226 | 0.703 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.229 | 0.489 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.174 | 0.441 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.268 | 0.590 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.190 | 0.460 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.229 | 0.511 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.153 | 0.425 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.232 | 0.512 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.296 | 0.472 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.371 | 0.657 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.328 | 0.493 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.471 | 0.570 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 1.458 | 4.230 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.506 | 1.311 |
| chopin_base14b | chopin | 14b | base | 98 | 0.172 | 0.788 |
| chopin_base8b | chopin | 8b | base | 98 | 0.325 | 0.773 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.351 | 0.638 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.678 | 1.993 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.224 | 0.336 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.155 | 0.397 |
| doctorow_base4b | doctorow | 4b | base | 84 | 1.138 | 1.616 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.291 | 0.604 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.219 | 0.341 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.375 | 0.522 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.175 | 0.359 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.251 | 0.421 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.370 | 0.510 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.253 | 0.389 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.241 | 0.395 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.198 | 0.327 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.270 | 0.434 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.252 | 0.325 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.264 | 0.385 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.294 | 0.633 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.968 | 5.582 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.229 | 0.390 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.306 | 0.808 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.325 | 0.630 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.253 | 0.335 |
| h_private_base14b | h_private | 14b | base | 46 | 0.083 | 0.134 |
| h_private_base8b | h_private | 8b | base | 46 | 0.208 | 0.379 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.534 | 0.873 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.558 | 1.247 |
| link SOURCE | link | - | source | 25 | 0.330 | 0.357 |
| link_base14b | link | 14b | base | 32 | 0.395 | 0.597 |
| link_base4b | link | 4b | base | 32 | 2.594 | 6.465 |
| link_base8b | link | 8b | base | 32 | 0.811 | 1.123 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.345 | 1.267 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.619 | 1.653 |
| link_paire6_8b | link | 8b | adapter | 32 | 1.795 | 6.347 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.190 | 0.539 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.427 | 1.045 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.248 | 0.392 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.309 | 0.477 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.317 | 0.447 |
| patrick SOURCE | patrick | - | source | 50 | 0.052 | 0.175 |
| patrick_base4b | patrick | 4b | base | 92 | 0.577 | 1.299 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.422 | 0.927 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.466 | 0.687 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.697 | 1.008 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.349 | 0.751 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.460 | 0.782 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.198 | 0.515 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.254 | 0.546 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.391 | 0.914 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 1.095 | 4.394 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.346 | 0.766 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.647 | 1.089 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.563 | 0.823 |
| rucker SOURCE | rucker | - | source | 50 | 0.256 | 0.446 |
| rucker_base14b | rucker | 14b | base | 94 | 0.191 | 0.408 |
| rucker_base4b | rucker | 4b | base | 94 | 0.752 | 1.240 |
| rucker_base8b | rucker | 8b | base | 94 | 0.249 | 0.563 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.209 | 0.365 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.316 | 0.477 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.218 | 0.379 |
| stross SOURCE | stross | - | source | 50 | 0.302 | 0.467 |
| stross_base14b | stross | 14b | base | 82 | 0.237 | 0.529 |
| stross_base4b | stross | 4b | base | 82 | 0.623 | 1.227 |
| stross_base8b | stross | 8b | base | 82 | 0.347 | 0.852 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.268 | 0.374 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.361 | 0.564 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.269 | 0.515 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.283 | 0.638 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.352 | 0.640 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.438 | 1.278 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.988 | 3.753 |
| watts SOURCE | watts | - | source | 50 | 0.230 | 0.367 |
| watts_base14b | watts | 14b | base | 90 | 0.252 | 0.500 |
| watts_base4b | watts | 4b | base | 90 | 0.776 | 2.029 |
| watts_base8b | watts | 8b | base | 90 | 0.389 | 1.097 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.221 | 0.321 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.244 | 0.407 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.217 | 0.386 |
| wharton_base14b | wharton | 14b | base | 88 | 0.302 | 0.767 |
| wharton_base8b | wharton | 8b | base | 88 | 0.412 | 0.817 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.199 | 0.588 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.178 | 0.481 |

Replicate floor:

- base4b vs base4b_r2: -0.366
- chesterton_base4b vs chesterton_base4bc: -0.109
- mansfield_base4b vs mansfield_base4b_r2: -0.270

Base vs adapter:

- cather 14b: base 0.116 -> adapter 1.252 (+1.137)
- cather 4b: base 1.120 -> adapter 1.999 (+0.879)
- cather 8b: base 0.477 -> adapter 0.386 (-0.091)
- chesterton 14b: base 0.189 -> adapter 0.525 (+0.337)
- chesterton 4b: base 0.723 -> adapter 0.421 (-0.302)
- chesterton 4bc: base 0.614 -> adapter 0.246 (-0.369)
- chesterton 8b: base 0.236 -> adapter 0.375 (+0.139)
- chesterton m14b: base 0.229 -> adapter 0.232 (+0.002)
- chesterton m3b: base 0.268 -> adapter 0.296 (+0.028)
- chesterton m8b: base 0.229 -> adapter 0.371 (+0.142)
- chopin 14b: base 0.172 -> adapter 0.351 (+0.178)
- chopin 4b: base 1.023 -> adapter 0.438 (-0.585)
- chopin 8b: base 0.325 -> adapter 0.678 (+0.353)
- doctorow 14b: base 0.155 -> adapter 0.251 (+0.096)
- doctorow 4b: base 1.138 -> adapter 0.370 (-0.768)
- doctorow 8b: base 0.291 -> adapter 0.253 (-0.038)
- doctorow m14b: base 0.219 -> adapter 0.241 (+0.022)
- doctorow m3b: base 0.375 -> adapter 0.198 (-0.177)
- doctorow m8b: base 0.175 -> adapter 0.270 (+0.094)
- h_private 14b: base 0.083 -> adapter 0.534 (+0.451)
- h_private 4b: base 0.233 -> adapter 0.303 (+0.070)
- h_private 8b: base 0.208 -> adapter 0.558 (+0.349)
- link 14b: base 0.395 -> adapter 0.345 (-0.051)
- link 4b: base 2.594 -> adapter 0.619 (-1.975)
- link 8b: base 0.811 -> adapter 1.795 (+0.984)
- mansfield 14b: base 0.190 -> adapter 0.248 (+0.059)
- mansfield 4b: base 1.334 -> adapter 0.330 (-1.004)
- mansfield 8b: base 0.427 -> adapter 0.309 (-0.118)
- patrick 4b: base 0.577 -> adapter 0.422 (-0.154)
- patrick_v2 14b: base 0.398 -> adapter 0.263 (-0.135)
- patrick_v2 17b: base 1.024 -> adapter 0.380 (-0.643)
- patrick_v2 4b: base 1.133 -> adapter 0.417 (-0.716)
- patrick_v2 8b: base 0.477 -> adapter 0.404 (-0.073)
- patrick_v2 m14b: base 0.466 -> adapter 0.198 (-0.268)
- patrick_v2 m3b: base 0.697 -> adapter 0.254 (-0.443)
- patrick_v2 m8b: base 0.460 -> adapter 0.391 (-0.070)
- rucker 14b: base 0.191 -> adapter 0.209 (+0.018)
- rucker 4b: base 0.752 -> adapter 0.316 (-0.437)
- rucker 8b: base 0.249 -> adapter 0.218 (-0.031)
- stross 14b: base 0.237 -> adapter 0.268 (+0.032)
- stross 4b: base 0.623 -> adapter 0.361 (-0.262)
- stross 8b: base 0.347 -> adapter 0.269 (-0.078)
- sui_sin_far 14b: base 0.283 -> adapter 0.438 (+0.155)
- sui_sin_far 4b: base 0.903 -> adapter 0.943 (+0.041)
- sui_sin_far 8b: base 0.352 -> adapter 0.988 (+0.636)
- watts 14b: base 0.252 -> adapter 0.221 (-0.032)
- watts 4b: base 0.776 -> adapter 0.244 (-0.532)
- watts 8b: base 0.389 -> adapter 0.217 (-0.172)
- wharton 14b: base 0.302 -> adapter 0.199 (-0.103)
- wharton 4b: base 1.347 -> adapter 0.218 (-1.128)
- wharton 8b: base 0.412 -> adapter 0.178 (-0.234)

## rfpd_w

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.308 | 0.108 |
| base4b | wharton | 4b | base | 88 | 0.594 | 0.187 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.553 | 0.166 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.410 | 0.158 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.382 | 0.130 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.493 | 0.183 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.477 | 0.152 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.468 | 0.194 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.419 | 0.147 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.419 | 0.169 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.464 | 0.179 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.412 | 0.139 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.469 | 0.178 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.383 | 0.100 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.502 | 0.146 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.517 | 0.132 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.487 | 0.178 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.332 | 0.107 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.417 | 0.175 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.476 | 0.175 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.549 | 0.220 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.450 | 0.171 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.444 | 0.157 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.441 | 0.152 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.438 | 0.151 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.448 | 0.168 |
| h_private SOURCE | h_private | - | source | 30 | 0.418 | 0.074 |
| h_private_base4b | h_private | 4b | base | 46 | 0.489 | 0.116 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.609 | 0.124 |
| chopin SOURCE | chopin | - | source | 50 | 0.311 | 0.091 |
| chopin_base4b | chopin | 4b | base | 98 | 0.539 | 0.169 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.547 | 0.176 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.362 | 0.116 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.559 | 0.162 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.547 | 0.138 |
| cather SOURCE | cather | - | source | 50 | 0.326 | 0.098 |
| cather_base4b | cather | 4b | base | 88 | 0.516 | 0.163 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.570 | 0.177 |
| cather_base14b | cather | 14b | base | 88 | 0.393 | 0.128 |
| cather_base8b | cather | 8b | base | 88 | 0.409 | 0.134 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.505 | 0.154 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.522 | 0.164 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.420 | 0.157 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.407 | 0.167 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.478 | 0.131 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.471 | 0.136 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.449 | 0.158 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.458 | 0.138 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.455 | 0.143 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.446 | 0.147 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.425 | 0.153 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.430 | 0.151 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.414 | 0.145 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.488 | 0.189 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.498 | 0.162 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 0.623 | 0.184 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.558 | 0.208 |
| chopin_base14b | chopin | 14b | base | 98 | 0.388 | 0.122 |
| chopin_base8b | chopin | 8b | base | 98 | 0.413 | 0.125 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.515 | 0.169 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.562 | 0.176 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.361 | 0.085 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.389 | 0.092 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.527 | 0.146 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.411 | 0.095 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.403 | 0.090 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.424 | 0.094 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.387 | 0.090 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.400 | 0.106 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.479 | 0.138 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.418 | 0.100 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.394 | 0.114 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.422 | 0.126 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.398 | 0.106 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.459 | 0.137 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.477 | 0.147 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.451 | 0.132 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.534 | 0.149 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.446 | 0.139 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.523 | 0.152 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.493 | 0.132 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.446 | 0.133 |
| h_private_base14b | h_private | 14b | base | 46 | 0.469 | 0.076 |
| h_private_base8b | h_private | 8b | base | 46 | 0.491 | 0.114 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.614 | 0.155 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.631 | 0.133 |
| link SOURCE | link | - | source | 25 | 0.442 | 0.125 |
| link_base14b | link | 14b | base | 32 | 0.460 | 0.121 |
| link_base4b | link | 4b | base | 32 | 0.523 | 0.153 |
| link_base8b | link | 8b | base | 32 | 0.463 | 0.131 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.513 | 0.141 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.576 | 0.180 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.604 | 0.206 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.393 | 0.100 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.449 | 0.115 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.485 | 0.183 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.504 | 0.154 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.496 | 0.158 |
| patrick SOURCE | patrick | - | source | 50 | 0.281 | 0.091 |
| patrick_base4b | patrick | 4b | base | 92 | 0.422 | 0.157 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.381 | 0.161 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.492 | 0.172 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.493 | 0.149 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.446 | 0.145 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.459 | 0.141 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.399 | 0.143 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.453 | 0.189 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.427 | 0.186 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.510 | 0.205 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.485 | 0.156 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.500 | 0.171 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.487 | 0.188 |
| rucker SOURCE | rucker | - | source | 50 | 0.355 | 0.096 |
| rucker_base14b | rucker | 14b | base | 94 | 0.438 | 0.146 |
| rucker_base4b | rucker | 4b | base | 94 | 0.605 | 0.171 |
| rucker_base8b | rucker | 8b | base | 94 | 0.457 | 0.138 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.436 | 0.133 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.457 | 0.145 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.453 | 0.137 |
| stross SOURCE | stross | - | source | 50 | 0.385 | 0.130 |
| stross_base14b | stross | 14b | base | 82 | 0.517 | 0.187 |
| stross_base4b | stross | 4b | base | 82 | 0.656 | 0.210 |
| stross_base8b | stross | 8b | base | 82 | 0.516 | 0.186 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.477 | 0.137 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.496 | 0.176 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.464 | 0.174 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.408 | 0.115 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.423 | 0.102 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.494 | 0.144 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.502 | 0.125 |
| watts SOURCE | watts | - | source | 50 | 0.371 | 0.094 |
| watts_base14b | watts | 14b | base | 90 | 0.407 | 0.116 |
| watts_base4b | watts | 4b | base | 90 | 0.548 | 0.158 |
| watts_base8b | watts | 8b | base | 90 | 0.423 | 0.120 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.475 | 0.140 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.492 | 0.142 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.458 | 0.133 |
| wharton_base14b | wharton | 14b | base | 88 | 0.429 | 0.161 |
| wharton_base8b | wharton | 8b | base | 88 | 0.447 | 0.154 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.383 | 0.125 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.415 | 0.137 |

Replicate floor:

- base4b vs base4b_r2: -0.042
- chesterton_base4b vs chesterton_base4bc: -0.016
- mansfield_base4b vs mansfield_base4b_r2: +0.015

Base vs adapter:

- cather 14b: base 0.393 -> adapter 0.505 (+0.112)
- cather 4b: base 0.516 -> adapter 0.570 (+0.054)
- cather 8b: base 0.409 -> adapter 0.522 (+0.113)
- chesterton 14b: base 0.412 -> adapter 0.469 (+0.057)
- chesterton 4b: base 0.493 -> adapter 0.468 (-0.025)
- chesterton 4bc: base 0.477 -> adapter 0.419 (-0.058)
- chesterton 8b: base 0.419 -> adapter 0.464 (+0.045)
- chesterton m14b: base 0.478 -> adapter 0.425 (-0.054)
- chesterton m3b: base 0.449 -> adapter 0.430 (-0.018)
- chesterton m8b: base 0.455 -> adapter 0.414 (-0.042)
- chopin 14b: base 0.388 -> adapter 0.515 (+0.127)
- chopin 4b: base 0.539 -> adapter 0.547 (+0.008)
- chopin 8b: base 0.413 -> adapter 0.562 (+0.149)
- doctorow 14b: base 0.389 -> adapter 0.400 (+0.011)
- doctorow 4b: base 0.527 -> adapter 0.479 (-0.047)
- doctorow 8b: base 0.411 -> adapter 0.418 (+0.007)
- doctorow m14b: base 0.403 -> adapter 0.394 (-0.009)
- doctorow m3b: base 0.424 -> adapter 0.422 (-0.002)
- doctorow m8b: base 0.387 -> adapter 0.398 (+0.011)
- h_private 14b: base 0.469 -> adapter 0.614 (+0.144)
- h_private 4b: base 0.489 -> adapter 0.609 (+0.119)
- h_private 8b: base 0.491 -> adapter 0.631 (+0.140)
- link 14b: base 0.460 -> adapter 0.513 (+0.053)
- link 4b: base 0.523 -> adapter 0.576 (+0.053)
- link 8b: base 0.463 -> adapter 0.604 (+0.141)
- mansfield 14b: base 0.393 -> adapter 0.485 (+0.092)
- mansfield 4b: base 0.502 -> adapter 0.487 (-0.015)
- mansfield 8b: base 0.449 -> adapter 0.504 (+0.054)
- patrick 4b: base 0.422 -> adapter 0.381 (-0.041)
- patrick_v2 14b: base 0.438 -> adapter 0.448 (+0.010)
- patrick_v2 17b: base 0.417 -> adapter 0.476 (+0.059)
- patrick_v2 4b: base 0.549 -> adapter 0.450 (-0.099)
- patrick_v2 8b: base 0.444 -> adapter 0.441 (-0.002)
- patrick_v2 m14b: base 0.492 -> adapter 0.399 (-0.093)
- patrick_v2 m3b: base 0.493 -> adapter 0.453 (-0.040)
- patrick_v2 m8b: base 0.459 -> adapter 0.427 (-0.031)
- rucker 14b: base 0.438 -> adapter 0.436 (-0.002)
- rucker 4b: base 0.605 -> adapter 0.457 (-0.149)
- rucker 8b: base 0.457 -> adapter 0.453 (-0.003)
- stross 14b: base 0.517 -> adapter 0.477 (-0.040)
- stross 4b: base 0.656 -> adapter 0.496 (-0.160)
- stross 8b: base 0.516 -> adapter 0.464 (-0.053)
- sui_sin_far 14b: base 0.408 -> adapter 0.494 (+0.087)
- sui_sin_far 4b: base 0.559 -> adapter 0.547 (-0.012)
- sui_sin_far 8b: base 0.423 -> adapter 0.502 (+0.079)
- watts 14b: base 0.407 -> adapter 0.475 (+0.067)
- watts 4b: base 0.548 -> adapter 0.492 (-0.056)
- watts 8b: base 0.423 -> adapter 0.458 (+0.035)
- wharton 14b: base 0.429 -> adapter 0.383 (-0.046)
- wharton 4b: base 0.594 -> adapter 0.410 (-0.184)
- wharton 8b: base 0.447 -> adapter 0.415 (-0.033)

## arti_w

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.147 | 0.120 |
| base4b | wharton | 4b | base | 88 | 0.421 | 0.207 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.373 | 0.188 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.253 | 0.167 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.208 | 0.147 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.295 | 0.208 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.280 | 0.176 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.310 | 0.204 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.253 | 0.164 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.204 | 0.197 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.314 | 0.195 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.205 | 0.167 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.314 | 0.187 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.194 | 0.113 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.243 | 0.156 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.261 | 0.159 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.302 | 0.191 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.177 | 0.122 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.251 | 0.186 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.337 | 0.190 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.396 | 0.238 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.313 | 0.183 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.282 | 0.179 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.297 | 0.166 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.285 | 0.172 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.302 | 0.183 |
| h_private SOURCE | h_private | - | source | 30 | 0.203 | 0.087 |
| h_private_base4b | h_private | 4b | base | 46 | 0.162 | 0.132 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.328 | 0.142 |
| chopin SOURCE | chopin | - | source | 50 | 0.155 | 0.108 |
| chopin_base4b | chopin | 4b | base | 98 | 0.359 | 0.191 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.402 | 0.193 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.187 | 0.133 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.346 | 0.186 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.318 | 0.172 |
| cather SOURCE | cather | - | source | 50 | 0.151 | 0.120 |
| cather_base4b | cather | 4b | base | 88 | 0.326 | 0.180 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.379 | 0.192 |
| cather_base14b | cather | 14b | base | 88 | 0.197 | 0.140 |
| cather_base8b | cather | 8b | base | 88 | 0.204 | 0.154 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.326 | 0.178 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.337 | 0.180 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.217 | 0.183 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.188 | 0.195 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.258 | 0.152 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.246 | 0.146 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.218 | 0.165 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.217 | 0.146 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.231 | 0.156 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.222 | 0.165 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.257 | 0.171 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.262 | 0.168 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.242 | 0.159 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.325 | 0.203 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.330 | 0.180 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 0.433 | 0.204 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.398 | 0.224 |
| chopin_base14b | chopin | 14b | base | 98 | 0.198 | 0.132 |
| chopin_base8b | chopin | 8b | base | 98 | 0.209 | 0.140 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.378 | 0.173 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.423 | 0.187 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.180 | 0.099 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.162 | 0.107 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.308 | 0.170 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.176 | 0.116 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.181 | 0.108 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.195 | 0.113 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.151 | 0.104 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.221 | 0.114 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.312 | 0.152 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.242 | 0.115 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.215 | 0.131 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.242 | 0.142 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.218 | 0.115 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.283 | 0.151 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.314 | 0.160 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.278 | 0.146 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.289 | 0.172 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.273 | 0.156 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.317 | 0.168 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.303 | 0.145 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.283 | 0.141 |
| h_private_base14b | h_private | 14b | base | 46 | 0.109 | 0.083 |
| h_private_base8b | h_private | 8b | base | 46 | 0.135 | 0.138 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.336 | 0.183 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.339 | 0.163 |
| link SOURCE | link | - | source | 25 | 0.272 | 0.153 |
| link_base14b | link | 14b | base | 32 | 0.229 | 0.143 |
| link_base4b | link | 4b | base | 32 | 0.301 | 0.172 |
| link_base8b | link | 8b | base | 32 | 0.226 | 0.142 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.268 | 0.168 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.365 | 0.206 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.387 | 0.227 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.130 | 0.115 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.166 | 0.128 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.300 | 0.197 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.314 | 0.171 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.311 | 0.176 |
| patrick SOURCE | patrick | - | source | 50 | 0.141 | 0.101 |
| patrick_base4b | patrick | 4b | base | 92 | 0.275 | 0.170 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.250 | 0.174 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.339 | 0.187 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.333 | 0.165 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.286 | 0.163 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.303 | 0.161 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.244 | 0.164 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.304 | 0.212 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.272 | 0.204 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.332 | 0.225 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.333 | 0.168 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.349 | 0.187 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.344 | 0.203 |
| rucker SOURCE | rucker | - | source | 50 | 0.192 | 0.105 |
| rucker_base14b | rucker | 14b | base | 94 | 0.246 | 0.160 |
| rucker_base4b | rucker | 4b | base | 94 | 0.422 | 0.194 |
| rucker_base8b | rucker | 8b | base | 94 | 0.257 | 0.160 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.276 | 0.143 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.300 | 0.157 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.293 | 0.147 |
| stross SOURCE | stross | - | source | 50 | 0.225 | 0.148 |
| stross_base14b | stross | 14b | base | 82 | 0.326 | 0.205 |
| stross_base4b | stross | 4b | base | 82 | 0.450 | 0.237 |
| stross_base8b | stross | 8b | base | 82 | 0.308 | 0.207 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.306 | 0.155 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.330 | 0.192 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.291 | 0.192 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.164 | 0.139 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.174 | 0.111 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.266 | 0.161 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.263 | 0.151 |
| watts SOURCE | watts | - | source | 50 | 0.171 | 0.108 |
| watts_base14b | watts | 14b | base | 90 | 0.190 | 0.140 |
| watts_base4b | watts | 4b | base | 90 | 0.337 | 0.181 |
| watts_base8b | watts | 8b | base | 90 | 0.191 | 0.141 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.299 | 0.155 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.322 | 0.157 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.288 | 0.145 |
| wharton_base14b | wharton | 14b | base | 88 | 0.248 | 0.177 |
| wharton_base8b | wharton | 8b | base | 88 | 0.253 | 0.176 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.228 | 0.130 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.259 | 0.149 |

Replicate floor:

- base4b vs base4b_r2: -0.048
- chesterton_base4b vs chesterton_base4bc: -0.015
- mansfield_base4b vs mansfield_base4b_r2: +0.019

Base vs adapter:

- cather 14b: base 0.197 -> adapter 0.326 (+0.129)
- cather 4b: base 0.326 -> adapter 0.379 (+0.053)
- cather 8b: base 0.204 -> adapter 0.337 (+0.133)
- chesterton 14b: base 0.205 -> adapter 0.314 (+0.110)
- chesterton 4b: base 0.295 -> adapter 0.310 (+0.015)
- chesterton 4bc: base 0.280 -> adapter 0.253 (-0.027)
- chesterton 8b: base 0.204 -> adapter 0.314 (+0.110)
- chesterton m14b: base 0.258 -> adapter 0.257 (-0.001)
- chesterton m3b: base 0.218 -> adapter 0.262 (+0.044)
- chesterton m8b: base 0.231 -> adapter 0.242 (+0.011)
- chopin 14b: base 0.198 -> adapter 0.378 (+0.179)
- chopin 4b: base 0.359 -> adapter 0.402 (+0.044)
- chopin 8b: base 0.209 -> adapter 0.423 (+0.214)
- doctorow 14b: base 0.162 -> adapter 0.221 (+0.059)
- doctorow 4b: base 0.308 -> adapter 0.312 (+0.004)
- doctorow 8b: base 0.176 -> adapter 0.242 (+0.066)
- doctorow m14b: base 0.181 -> adapter 0.215 (+0.034)
- doctorow m3b: base 0.195 -> adapter 0.242 (+0.047)
- doctorow m8b: base 0.151 -> adapter 0.218 (+0.067)
- h_private 14b: base 0.109 -> adapter 0.336 (+0.227)
- h_private 4b: base 0.162 -> adapter 0.328 (+0.166)
- h_private 8b: base 0.135 -> adapter 0.339 (+0.203)
- link 14b: base 0.229 -> adapter 0.268 (+0.039)
- link 4b: base 0.301 -> adapter 0.365 (+0.064)
- link 8b: base 0.226 -> adapter 0.387 (+0.161)
- mansfield 14b: base 0.130 -> adapter 0.300 (+0.170)
- mansfield 4b: base 0.243 -> adapter 0.302 (+0.059)
- mansfield 8b: base 0.166 -> adapter 0.314 (+0.148)
- patrick 4b: base 0.275 -> adapter 0.250 (-0.025)
- patrick_v2 14b: base 0.285 -> adapter 0.302 (+0.018)
- patrick_v2 17b: base 0.251 -> adapter 0.337 (+0.085)
- patrick_v2 4b: base 0.396 -> adapter 0.313 (-0.083)
- patrick_v2 8b: base 0.282 -> adapter 0.297 (+0.015)
- patrick_v2 m14b: base 0.339 -> adapter 0.244 (-0.096)
- patrick_v2 m3b: base 0.333 -> adapter 0.304 (-0.030)
- patrick_v2 m8b: base 0.303 -> adapter 0.272 (-0.031)
- rucker 14b: base 0.246 -> adapter 0.276 (+0.029)
- rucker 4b: base 0.422 -> adapter 0.300 (-0.121)
- rucker 8b: base 0.257 -> adapter 0.293 (+0.037)
- stross 14b: base 0.326 -> adapter 0.306 (-0.020)
- stross 4b: base 0.450 -> adapter 0.330 (-0.121)
- stross 8b: base 0.308 -> adapter 0.291 (-0.017)
- sui_sin_far 14b: base 0.164 -> adapter 0.266 (+0.102)
- sui_sin_far 4b: base 0.346 -> adapter 0.318 (-0.028)
- sui_sin_far 8b: base 0.174 -> adapter 0.263 (+0.089)
- watts 14b: base 0.190 -> adapter 0.299 (+0.109)
- watts 4b: base 0.337 -> adapter 0.322 (-0.015)
- watts 8b: base 0.191 -> adapter 0.288 (+0.096)
- wharton 14b: base 0.248 -> adapter 0.228 (-0.020)
- wharton 4b: base 0.421 -> adapter 0.253 (-0.168)
- wharton 8b: base 0.253 -> adapter 0.259 (+0.007)

## arti_hard_w

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| wharton SOURCE | wharton | - | source | 50 | 0.098 | 0.267 |
| base4b | wharton | 4b | base | 88 | 0.785 | 0.756 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.542 | 0.648 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.196 | 0.408 |
| chesterton SOURCE | chesterton | - | source | 50 | 0.218 | 0.411 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.390 | 0.648 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.420 | 0.593 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.359 | 0.512 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.243 | 0.388 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.179 | 0.451 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.364 | 0.508 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.166 | 0.365 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.465 | 0.518 |
| mansfield SOURCE | mansfield | - | source | 50 | 0.326 | 0.485 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.447 | 0.615 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.479 | 0.624 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.297 | 0.462 |
| patrick_v2 SOURCE | patrick_v2 | - | source | 50 | 0.067 | 0.222 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.312 | 0.551 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.320 | 0.428 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.593 | 0.738 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.336 | 0.500 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.413 | 0.625 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.351 | 0.493 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.319 | 0.538 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.238 | 0.492 |
| h_private SOURCE | h_private | - | source | 30 | 0.268 | 0.235 |
| h_private_base4b | h_private | 4b | base | 46 | 0.199 | 0.350 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.264 | 0.394 |
| chopin SOURCE | chopin | - | source | 50 | 0.131 | 0.319 |
| chopin_base4b | chopin | 4b | base | 98 | 0.536 | 0.707 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.376 | 0.450 |
| sui_sin_far SOURCE | sui_sin_far | - | source | 30 | 0.268 | 0.417 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.631 | 0.580 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.363 | 0.486 |
| cather SOURCE | cather | - | source | 50 | 0.084 | 0.300 |
| cather_base4b | cather | 4b | base | 88 | 0.542 | 0.676 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.484 | 0.730 |
| cather_base14b | cather | 14b | base | 88 | 0.106 | 0.307 |
| cather_base8b | cather | 8b | base | 88 | 0.296 | 0.521 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.331 | 0.466 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.259 | 0.463 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.237 | 0.453 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.164 | 0.447 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.216 | 0.444 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.150 | 0.347 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.235 | 0.507 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.160 | 0.360 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.197 | 0.414 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.141 | 0.373 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.204 | 0.369 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.294 | 0.462 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.318 | 0.492 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.316 | 0.461 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.425 | 0.468 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 0.438 | 0.590 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.347 | 0.602 |
| chopin_base14b | chopin | 14b | base | 98 | 0.105 | 0.294 |
| chopin_base8b | chopin | 8b | base | 98 | 0.223 | 0.460 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.292 | 0.452 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.431 | 0.510 |
| doctorow SOURCE | doctorow | - | source | 50 | 0.224 | 0.336 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.133 | 0.300 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.631 | 0.648 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.236 | 0.414 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.219 | 0.340 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.354 | 0.470 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.173 | 0.350 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.235 | 0.368 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.346 | 0.445 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.246 | 0.367 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.241 | 0.395 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.198 | 0.327 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.248 | 0.358 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.252 | 0.325 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.255 | 0.359 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.244 | 0.377 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.293 | 0.512 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.225 | 0.379 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.217 | 0.414 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.261 | 0.406 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.253 | 0.335 |
| h_private_base14b | h_private | 14b | base | 46 | 0.083 | 0.134 |
| h_private_base8b | h_private | 8b | base | 46 | 0.202 | 0.359 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.414 | 0.465 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.381 | 0.537 |
| link SOURCE | link | - | source | 25 | 0.330 | 0.357 |
| link_base14b | link | 14b | base | 32 | 0.356 | 0.511 |
| link_base4b | link | 4b | base | 32 | 0.684 | 0.610 |
| link_base8b | link | 8b | base | 32 | 0.483 | 0.587 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.155 | 0.379 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.322 | 0.442 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.446 | 0.529 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.152 | 0.407 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.224 | 0.465 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.236 | 0.345 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.296 | 0.424 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.309 | 0.429 |
| patrick SOURCE | patrick | - | source | 50 | 0.052 | 0.175 |
| patrick_base4b | patrick | 4b | base | 92 | 0.312 | 0.543 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.294 | 0.534 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.416 | 0.562 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.506 | 0.600 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.274 | 0.529 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.355 | 0.511 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.175 | 0.423 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.220 | 0.453 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.269 | 0.511 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.360 | 0.596 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.267 | 0.491 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.447 | 0.632 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.464 | 0.625 |
| rucker SOURCE | rucker | - | source | 50 | 0.241 | 0.396 |
| rucker_base14b | rucker | 14b | base | 94 | 0.179 | 0.354 |
| rucker_base4b | rucker | 4b | base | 94 | 0.454 | 0.594 |
| rucker_base8b | rucker | 8b | base | 94 | 0.207 | 0.398 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.207 | 0.358 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.310 | 0.453 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.217 | 0.375 |
| stross SOURCE | stross | - | source | 50 | 0.299 | 0.458 |
| stross_base14b | stross | 14b | base | 82 | 0.202 | 0.424 |
| stross_base4b | stross | 4b | base | 82 | 0.379 | 0.546 |
| stross_base8b | stross | 8b | base | 82 | 0.228 | 0.478 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.268 | 0.372 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.316 | 0.418 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.248 | 0.445 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.219 | 0.388 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.287 | 0.479 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.257 | 0.413 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.274 | 0.500 |
| watts SOURCE | watts | - | source | 50 | 0.229 | 0.363 |
| watts_base14b | watts | 14b | base | 90 | 0.244 | 0.477 |
| watts_base4b | watts | 4b | base | 90 | 0.392 | 0.543 |
| watts_base8b | watts | 8b | base | 90 | 0.225 | 0.437 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.220 | 0.318 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.234 | 0.372 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.209 | 0.357 |
| wharton_base14b | wharton | 14b | base | 88 | 0.217 | 0.409 |
| wharton_base8b | wharton | 8b | base | 88 | 0.292 | 0.524 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.157 | 0.345 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.148 | 0.343 |

Replicate floor:

- base4b vs base4b_r2: -0.242
- chesterton_base4b vs chesterton_base4bc: +0.029
- mansfield_base4b vs mansfield_base4b_r2: +0.032

Base vs adapter:

- cather 14b: base 0.106 -> adapter 0.331 (+0.225)
- cather 4b: base 0.542 -> adapter 0.484 (-0.058)
- cather 8b: base 0.296 -> adapter 0.259 (-0.037)
- chesterton 14b: base 0.166 -> adapter 0.465 (+0.299)
- chesterton 4b: base 0.390 -> adapter 0.359 (-0.032)
- chesterton 4bc: base 0.420 -> adapter 0.243 (-0.177)
- chesterton 8b: base 0.179 -> adapter 0.364 (+0.185)
- chesterton m14b: base 0.216 -> adapter 0.204 (-0.011)
- chesterton m3b: base 0.235 -> adapter 0.294 (+0.059)
- chesterton m8b: base 0.197 -> adapter 0.318 (+0.121)
- chopin 14b: base 0.105 -> adapter 0.292 (+0.187)
- chopin 4b: base 0.536 -> adapter 0.376 (-0.160)
- chopin 8b: base 0.223 -> adapter 0.431 (+0.209)
- doctorow 14b: base 0.133 -> adapter 0.235 (+0.101)
- doctorow 4b: base 0.631 -> adapter 0.346 (-0.286)
- doctorow 8b: base 0.236 -> adapter 0.246 (+0.010)
- doctorow m14b: base 0.219 -> adapter 0.241 (+0.023)
- doctorow m3b: base 0.354 -> adapter 0.198 (-0.156)
- doctorow m8b: base 0.173 -> adapter 0.248 (+0.075)
- h_private 14b: base 0.083 -> adapter 0.414 (+0.331)
- h_private 4b: base 0.199 -> adapter 0.264 (+0.065)
- h_private 8b: base 0.202 -> adapter 0.381 (+0.179)
- link 14b: base 0.356 -> adapter 0.155 (-0.201)
- link 4b: base 0.684 -> adapter 0.322 (-0.362)
- link 8b: base 0.483 -> adapter 0.446 (-0.036)
- mansfield 14b: base 0.152 -> adapter 0.236 (+0.083)
- mansfield 4b: base 0.447 -> adapter 0.297 (-0.150)
- mansfield 8b: base 0.224 -> adapter 0.296 (+0.072)
- patrick 4b: base 0.312 -> adapter 0.294 (-0.018)
- patrick_v2 14b: base 0.319 -> adapter 0.238 (-0.081)
- patrick_v2 17b: base 0.312 -> adapter 0.320 (+0.008)
- patrick_v2 4b: base 0.593 -> adapter 0.336 (-0.257)
- patrick_v2 8b: base 0.413 -> adapter 0.351 (-0.062)
- patrick_v2 m14b: base 0.416 -> adapter 0.175 (-0.241)
- patrick_v2 m3b: base 0.506 -> adapter 0.220 (-0.286)
- patrick_v2 m8b: base 0.355 -> adapter 0.269 (-0.086)
- rucker 14b: base 0.179 -> adapter 0.207 (+0.028)
- rucker 4b: base 0.454 -> adapter 0.310 (-0.144)
- rucker 8b: base 0.207 -> adapter 0.217 (+0.010)
- stross 14b: base 0.202 -> adapter 0.268 (+0.065)
- stross 4b: base 0.379 -> adapter 0.316 (-0.063)
- stross 8b: base 0.228 -> adapter 0.248 (+0.020)
- sui_sin_far 14b: base 0.219 -> adapter 0.257 (+0.038)
- sui_sin_far 4b: base 0.631 -> adapter 0.363 (-0.268)
- sui_sin_far 8b: base 0.287 -> adapter 0.274 (-0.012)
- watts 14b: base 0.244 -> adapter 0.220 (-0.024)
- watts 4b: base 0.392 -> adapter 0.234 (-0.158)
- watts 8b: base 0.225 -> adapter 0.209 (-0.016)
- wharton 14b: base 0.217 -> adapter 0.157 (-0.060)
- wharton 4b: base 0.785 -> adapter 0.196 (-0.589)
- wharton 8b: base 0.292 -> adapter 0.148 (-0.145)

## Per-feature signed z (run means); + = more than the author, - = less

### cather (calibrated on 81 REF+TRAIN chunks)

| feature | author mean/1k | fired share | cather SOURCE | cather_base4b | cather_pair4b | cather_base14b | cather_base8b | cather_paire6_14b | cather_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.03 | 0.46 | +0.01 | -0.02 | -0.06 | +0.14 | -0.03 | +0.16 | +0.21 |
| way_simile | 0.03 | 0.02 | -0.13 | +3.12 | +1.87 | +0.13 | +1.70 | +0.01 | -0.06 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.20 | 0.11 | -0.27 | +1.02 | +5.33 | -0.16 | -0.19 | +3.60 | +0.79 |
| self_explanation | 0.03 | 0.02 | +0.18 | -0.13 | +0.34 | -0.05 | -0.13 | +0.94 | +0.34 |
| triad | 0.07 | 0.05 | +0.21 | -0.17 | -0.05 | +0.03 | -0.18 | +0.04 | -0.16 |
| antithesis | 0.34 | 0.20 | -0.10 | +1.72 | +0.55 | +1.30 | +1.59 | -0.21 | +0.20 |
| cleft | 0.06 | 0.05 | -0.03 | -0.23 | +0.28 | -0.23 | -0.23 | -0.12 | -0.15 |
| closing_flourish | 0.02 | 0.01 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 |
| nominalization_pickup | 0.02 | 0.01 | +0.14 | +0.17 | +0.65 | +0.12 | +0.25 | +1.12 | +0.42 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.03 | 0.02 | -0.13 | -0.13 | -0.13 | -0.13 | -0.13 | +0.04 | +0.01 |
| absence_punch | 0.00 | 0.00 | +0.10 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.05 |
| comma_chain | 0.08 | 0.05 | -0.06 | +0.19 | +1.57 | -0.04 | -0.18 | +0.60 | +0.57 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.15 | +0.00 | +0.00 | +0.00 | +0.04 | +0.00 |
| negation_template | 0.09 | 0.06 | -0.02 | +0.17 | +0.07 | +0.19 | +0.39 | -0.04 | +0.29 |
| intensifier | 0.88 | 0.42 | +0.09 | -0.23 | -0.34 | +0.24 | -0.01 | -0.27 | -0.27 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.08 | +0.07 | +0.07 | +0.15 | +0.00 | +0.00 |
| fragment_couplet | 0.05 | 0.02 | +0.19 | +2.47 | +3.10 | +0.51 | +0.89 | +5.61 | +5.87 |
| personification | 0.03 | 0.01 | -0.02 | -0.06 | -0.11 | -0.06 | -0.11 | -0.11 | -0.11 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.07 | 0.05 | -0.23 | -0.13 | -0.23 | -0.10 | -0.10 | +0.17 | -0.09 |
| question_fragment | 0.29 | 0.15 | -0.25 | -0.32 | -0.39 | -0.09 | -0.29 | -0.32 | -0.39 |
| then_opener | 0.24 | 0.15 | +0.18 | -0.13 | -0.37 | +0.26 | -0.14 | +0.25 | -0.07 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.27 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 6.02 | 0.79 | -0.27 | -0.98 | -1.13 | -0.76 | -0.85 | -0.93 | -0.79 |
| anaphora2 | 1.21 | 0.33 | -0.15 | +4.97 | +14.37 | +0.55 | +1.07 | +10.95 | +9.04 |
| long_short | 1.87 | 0.54 | -0.31 | -0.54 | -0.63 | -0.63 | -0.68 | -0.42 | -0.51 |
| copula_density | 3.28 | 1.00 | +0.21 | +0.17 | +3.58 | -0.78 | -0.82 | +2.73 | +3.14 |

### chesterton (calibrated on 318 REF+TRAIN chunks)

| feature | author mean/1k | fired share | chesterton SOURCE | chesterton_base4b | chesterton_base4bc | chesterton_paire6_4b | chesterton_paire6_4bc | chesterton_base8b | chesterton_paire6_8b | chesterton_base14b | chesterton_paire6_14b | chesterton_base14b_r2 | chesterton_base8b_r2 | chesterton_basem14b | chesterton_basem14b_r2 | chesterton_basem3b | chesterton_basem3b_r2 | chesterton_basem8b | chesterton_basem8b_r2 | chesterton_paire6_m14b | chesterton_paire6_m3b | chesterton_paire6_m8b | chesterton_size100 | chesterton_size150 | chesterton_size25 | chesterton_size50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.09 | 0.48 | +0.20 | +0.19 | -0.02 | +0.43 | +0.11 | +0.44 | +0.37 | +0.30 | +0.42 | +0.17 | +0.10 | -0.53 | -0.57 | -0.50 | -0.52 | -0.45 | -0.58 | +0.38 | +0.23 | +0.25 | +0.52 | +0.34 | +2.03 | +1.29 |
| way_simile | 0.01 | 0.01 | -0.03 | +1.84 | +1.39 | +0.28 | +0.04 | +0.38 | +0.12 | +0.32 | +0.15 | +0.45 | +0.53 | +0.35 | +0.46 | +0.45 | +0.44 | +0.54 | +0.20 | -0.03 | +0.04 | +0.20 | +0.01 | +0.35 | +0.65 | +0.24 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.15 | +0.14 |
| reversal | 0.19 | 0.12 | -0.07 | +0.76 | +0.78 | +0.05 | +0.29 | +0.22 | +0.60 | +0.05 | +1.04 | +0.34 | +0.04 | +0.16 | -0.21 | +0.26 | -0.05 | -0.03 | +0.10 | +0.38 | +0.40 | +0.52 | +0.41 | +0.57 | +4.65 | +1.23 |
| self_explanation | 0.18 | 0.12 | +0.34 | -0.35 | -0.35 | +0.78 | +0.06 | -0.32 | +0.24 | -0.27 | +0.39 | -0.26 | -0.35 | -0.24 | -0.24 | -0.35 | -0.31 | -0.29 | -0.35 | -0.03 | +0.16 | +0.19 | +0.31 | +0.43 | -0.19 | -0.17 |
| triad | 0.08 | 0.06 | +0.01 | +0.07 | -0.12 | -0.03 | -0.11 | -0.12 | +0.03 | -0.19 | +0.03 | -0.18 | -0.07 | +0.13 | +0.16 | -0.03 | -0.10 | -0.06 | -0.11 | +0.07 | -0.22 | +0.13 | -0.10 | +0.03 | -0.13 | +0.13 |
| antithesis | 0.44 | 0.25 | +0.04 | +1.04 | +1.51 | +0.02 | -0.12 | +1.28 | -0.07 | +0.51 | -0.16 | +0.83 | +0.92 | +0.90 | +0.76 | +0.70 | +0.80 | +0.50 | +0.29 | -0.20 | -0.05 | -0.07 | -0.16 | -0.16 | +1.18 | -0.17 |
| cleft | 0.05 | 0.03 | +0.14 | +0.27 | -0.10 | +0.00 | +0.27 | -0.15 | +0.55 | +0.07 | +0.26 | -0.02 | -0.00 | -0.07 | -0.10 | -0.10 | -0.09 | -0.15 | -0.15 | +0.13 | +0.21 | -0.08 | +0.49 | +0.39 | +0.09 | +0.24 |
| closing_flourish | 0.00 | 0.00 | +0.09 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | +0.05 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | +0.07 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | +0.04 | -0.02 | -0.02 | -0.02 | -0.02 |
| nominalization_pickup | 0.16 | 0.11 | -0.16 | -0.22 | -0.07 | +0.12 | +0.10 | -0.30 | +0.40 | -0.22 | +0.01 | -0.16 | -0.19 | -0.30 | -0.21 | -0.23 | -0.30 | -0.28 | -0.30 | +0.29 | +0.20 | -0.05 | +0.11 | +0.22 | +0.99 | -0.13 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.06 | 0.04 | +0.08 | -0.13 | -0.20 | +0.12 | +0.07 | -0.20 | -0.09 | -0.20 | +0.06 | -0.15 | -0.20 | -0.16 | -0.20 | -0.20 | -0.09 | -0.20 | -0.20 | -0.08 | -0.20 | -0.20 | +0.33 | +0.65 | -0.20 | -0.06 |
| absence_punch | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.09 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.04 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| comma_chain | 0.11 | 0.07 | -0.00 | -0.27 | -0.22 | +0.23 | +0.04 | -0.23 | +0.17 | -0.16 | +0.29 | -0.17 | -0.27 | -0.27 | -0.21 | -0.23 | -0.27 | -0.27 | -0.21 | +0.30 | +0.22 | +0.02 | +0.55 | +0.48 | +0.28 | +0.50 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.06 | 0.04 | +0.35 | +0.98 | +1.17 | +1.22 | +0.58 | +1.71 | +0.59 | +1.33 | +1.03 | +1.40 | +1.70 | +2.45 | +2.24 | +1.58 | +1.68 | +1.79 | +1.79 | +1.23 | +0.46 | +0.46 | +0.93 | +0.75 | +1.67 | +1.35 |
| intensifier | 1.32 | 0.57 | -0.12 | -0.30 | -0.29 | -0.54 | -0.52 | -0.17 | -0.31 | +0.01 | -0.42 | -0.02 | -0.12 | -0.33 | -0.21 | -0.42 | -0.23 | -0.29 | -0.19 | -0.50 | -0.56 | -0.46 | -0.40 | -0.50 | -0.57 | -0.37 |
| generator_phrase | 0.02 | 0.01 | +0.06 | -0.06 | +0.01 | +0.03 | -0.06 | +0.01 | -0.06 | +0.01 | -0.00 | -0.06 | -0.06 | +0.32 | +0.20 | -0.01 | +0.15 | +0.33 | +0.07 | -0.06 | -0.06 | -0.06 | -0.06 | +0.05 | -0.06 | +0.17 |
| fragment_couplet | 0.16 | 0.08 | +0.09 | +2.86 | +1.13 | +0.28 | +0.69 | +1.03 | +0.65 | +0.34 | +0.44 | +0.65 | +0.60 | +0.94 | +0.57 | +0.99 | +0.72 | +1.24 | +1.43 | +0.44 | +0.59 | +0.43 | +0.70 | +0.51 | +4.62 | +2.10 |
| personification | 0.01 | 0.00 | -0.02 | +0.15 | +0.22 | +0.06 | -0.02 | +0.16 | -0.02 | +0.36 | -0.02 | +0.18 | +0.06 | +0.17 | +0.22 | +0.12 | +0.34 | +0.18 | +0.02 | +0.08 | -0.02 | -0.02 | -0.02 | -0.02 | +0.02 | +0.08 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.04 | 0.03 | +0.29 | -0.17 | -0.17 | +0.21 | -0.09 | -0.17 | +0.21 | -0.17 | -0.06 | -0.17 | -0.17 | -0.17 | -0.08 | -0.17 | -0.02 | +0.07 | -0.08 | -0.17 | -0.01 | +0.10 | -0.06 | -0.00 | -0.01 | +0.06 |
| question_fragment | 0.04 | 0.03 | -0.15 | +0.47 | +0.78 | +0.13 | -0.00 | +0.43 | +0.03 | +1.08 | -0.06 | +1.19 | +0.83 | +2.29 | +2.52 | +1.45 | +1.44 | +2.57 | +2.54 | +0.15 | -0.08 | -0.03 | +0.09 | -0.03 | -0.15 | +0.03 |
| then_opener | 0.66 | 0.32 | +0.09 | -0.21 | -0.22 | +0.26 | +0.14 | -0.26 | +0.49 | -0.02 | +0.17 | -0.17 | -0.26 | +0.42 | +0.41 | +0.25 | +0.30 | +0.36 | +0.32 | +0.17 | +0.09 | -0.18 | +0.05 | +0.36 | -0.15 | +0.56 |
| pointer_verdict | 0.00 | 0.00 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | -0.02 | +0.08 | -0.02 | -0.02 | -0.02 | +0.13 | +0.12 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.11 | +0.00 | +0.00 | +0.00 | +0.00 | +0.31 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 7.77 | 0.82 | -0.21 | -0.78 | -0.66 | +0.07 | +0.01 | -0.53 | -0.16 | -0.45 | -0.06 | -0.40 | -0.56 | -0.03 | -0.21 | -0.30 | -0.38 | -0.13 | -0.11 | -0.19 | -0.33 | -0.18 | -0.16 | -0.40 | -0.91 | -0.39 |
| anaphora2 | 1.73 | 0.45 | +0.20 | +2.30 | +1.22 | +1.08 | +1.26 | -0.12 | +1.72 | -0.29 | +1.49 | -0.21 | -0.13 | -0.55 | -0.51 | -0.42 | -0.56 | -0.50 | -0.50 | +0.85 | +1.25 | +1.50 | +1.44 | +1.74 | +13.18 | +3.77 |
| long_short | 1.91 | 0.53 | -0.03 | -0.65 | -0.64 | -0.16 | -0.29 | -0.64 | -0.43 | -0.57 | -0.36 | -0.60 | -0.70 | +0.00 | +0.01 | -0.15 | -0.05 | -0.23 | -0.06 | -0.19 | +0.08 | -0.40 | -0.27 | -0.30 | -0.24 | -0.19 |
| copula_density | 3.49 | 1.00 | +0.20 | +0.21 | +0.19 | +1.26 | +1.08 | -1.07 | +1.47 | -0.98 | +1.64 | -0.82 | -1.02 | -1.92 | -2.00 | -1.98 | -2.18 | -1.96 | -1.97 | +1.18 | +1.31 | +1.13 | +1.66 | +1.32 | +3.55 | +2.25 |

### chopin (calibrated on 97 REF+TRAIN chunks)

| feature | author mean/1k | fired share | chopin SOURCE | chopin_base4b | chopin_paire6_4b | chopin_base14b | chopin_base8b | chopin_paire6_14b | chopin_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.25 | 0.60 | +0.16 | -0.46 | +0.63 | -0.24 | -0.35 | +0.38 | +0.43 |
| way_simile | 0.00 | 0.00 | +0.00 | +2.58 | +0.10 | +0.52 | +1.01 | +0.55 | +0.26 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 |
| reversal | 0.20 | 0.12 | -0.19 | +1.24 | +1.24 | -0.17 | -0.06 | +0.36 | +2.06 |
| self_explanation | 0.23 | 0.13 | +0.10 | -0.32 | -0.08 | -0.32 | -0.37 | -0.07 | -0.10 |
| triad | 0.10 | 0.06 | +0.08 | -0.19 | -0.18 | -0.24 | -0.17 | +0.13 | -0.18 |
| antithesis | 0.29 | 0.18 | +0.03 | +2.07 | +0.13 | +1.60 | +2.47 | -0.02 | -0.06 |
| cleft | 0.01 | 0.01 | -0.06 | -0.01 | +0.52 | -0.06 | -0.06 | +0.35 | +0.14 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.05 |
| nominalization_pickup | 0.01 | 0.01 | +0.05 | +0.16 | +0.12 | +0.12 | +0.00 | +0.09 | +0.43 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.01 | 0.01 | -0.05 | -0.05 | +0.12 | -0.05 | -0.05 | +0.18 | +0.08 |
| absence_punch | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.08 | +0.00 |
| comma_chain | 0.05 | 0.03 | -0.08 | +0.73 | +0.80 | +0.19 | +0.07 | +0.69 | +0.85 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.06 | +0.00 | +0.07 |
| negation_template | 0.03 | 0.02 | -0.00 | +0.57 | +0.66 | +0.25 | +0.17 | +0.52 | +0.39 |
| intensifier | 0.35 | 0.20 | -0.14 | +0.44 | -0.16 | +0.51 | +0.50 | +0.01 | -0.09 |
| generator_phrase | 0.00 | 0.00 | +0.20 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.08 |
| fragment_couplet | 0.25 | 0.14 | -0.30 | +1.01 | +5.11 | +0.24 | +0.09 | +4.60 | +2.71 |
| personification | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.03 | 0.02 | +0.00 | -0.06 | -0.00 | +0.12 | -0.06 | +0.03 | -0.02 |
| question_fragment | 0.16 | 0.11 | -0.13 | -0.31 | -0.29 | -0.06 | -0.29 | -0.12 | -0.22 |
| then_opener | 0.85 | 0.48 | -0.18 | -0.61 | +0.31 | -0.36 | -0.67 | +0.47 | +0.04 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.01 | 0.01 | -0.05 | -0.05 | -0.05 | -0.05 | -0.05 | -0.05 | -0.01 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 6.74 | 0.80 | -0.16 | -0.93 | -0.68 | -0.62 | -0.85 | -0.44 | -0.51 |
| anaphora2 | 0.92 | 0.35 | +0.45 | +7.18 | +8.50 | +0.94 | +1.91 | +7.18 | +11.25 |
| long_short | 1.99 | 0.59 | -0.10 | -0.47 | -0.31 | -0.45 | -0.68 | -0.19 | -0.34 |
| copula_density | 2.95 | 1.00 | +0.34 | +0.24 | +1.67 | -0.95 | -0.87 | +1.92 | +2.52 |

### doctorow (calibrated on 681 REF+TRAIN chunks)

| feature | author mean/1k | fired share | doctorow SOURCE | doctorow_base14b | doctorow_base4b | doctorow_base8b | doctorow_basem14b | doctorow_basem3b | doctorow_basem8b | doctorow_paire6_14b | doctorow_paire6_4b | doctorow_paire6_8b | doctorow_paire6_m14b | doctorow_paire6_m3b | doctorow_paire6_m8b | doctorow_size100 | doctorow_size150 | doctorow_size215 | doctorow_size25 | doctorow_size300 | doctorow_size50 | doctorow_size50_s1 | doctorow_size525 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.03 | 0.49 | +0.09 | -0.16 | -0.11 | -0.09 | -0.45 | -0.49 | -0.61 | +0.06 | +0.24 | +0.14 | +0.09 | -0.04 | +0.13 | +0.11 | -0.06 | -0.02 | -0.01 | +0.22 | +0.02 | +0.14 | +0.04 |
| way_simile | 0.08 | 0.05 | +0.01 | +0.18 | +3.06 | +0.61 | +0.44 | +0.80 | +0.31 | -0.04 | +0.39 | -0.03 | -0.02 | +0.03 | -0.03 | +0.13 | -0.12 | +0.17 | +2.84 | +0.06 | +0.48 | +0.59 | -0.09 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.20 | +0.00 | +0.00 | +0.05 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 |
| reversal | 0.34 | 0.22 | +0.10 | -0.18 | +0.79 | -0.06 | -0.15 | +0.12 | -0.22 | +0.14 | +0.27 | +0.12 | -0.01 | -0.04 | -0.02 | +0.12 | +0.40 | +0.24 | +0.03 | +0.16 | +0.06 | -0.20 | +0.22 |
| self_explanation | 0.27 | 0.17 | -0.14 | -0.42 | -0.37 | -0.37 | -0.37 | -0.42 | -0.40 | -0.07 | -0.06 | +0.03 | +0.07 | -0.19 | +0.22 | -0.13 | -0.11 | -0.13 | +0.03 | -0.25 | -0.29 | -0.05 | -0.05 |
| triad | 0.15 | 0.11 | -0.11 | -0.22 | -0.20 | -0.13 | -0.06 | -0.26 | -0.14 | +0.20 | -0.04 | +0.20 | +0.17 | +0.10 | +0.16 | +0.00 | -0.15 | +0.06 | -0.27 | +0.08 | -0.01 | -0.08 | +0.32 |
| antithesis | 0.54 | 0.33 | +0.03 | +0.47 | +0.46 | +0.67 | +0.35 | +0.41 | +0.12 | +0.01 | -0.07 | +0.03 | -0.02 | +0.10 | +0.03 | -0.15 | -0.02 | +0.02 | -0.14 | -0.07 | +0.18 | +0.48 | +0.14 |
| cleft | 0.03 | 0.02 | -0.02 | -0.12 | -0.12 | -0.12 | -0.07 | -0.12 | -0.06 | +0.04 | -0.04 | -0.12 | -0.12 | +0.14 | -0.08 | +0.03 | +0.23 | -0.03 | -0.04 | -0.12 | +0.09 | -0.12 | -0.03 |
| closing_flourish | 0.00 | 0.00 | -0.01 | +0.05 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | +0.05 | -0.01 | -0.01 | +0.10 | -0.01 | +0.18 | -0.01 | -0.01 |
| nominalization_pickup | 0.07 | 0.05 | +0.02 | -0.19 | -0.10 | -0.19 | -0.16 | +0.03 | -0.20 | +0.08 | +0.48 | +0.29 | -0.02 | +0.08 | -0.09 | +0.27 | +0.31 | +0.30 | +0.58 | +0.26 | +0.16 | +0.19 | +0.32 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.02 | 0.02 | +0.23 | -0.03 | -0.09 | -0.09 | -0.09 | -0.02 | -0.04 | +0.07 | +0.11 | +0.02 | -0.00 | +0.09 | +0.00 | +0.22 | +0.24 | +0.10 | -0.02 | +0.17 | +0.14 | -0.05 | -0.09 |
| absence_punch | 0.01 | 0.01 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | +0.02 | -0.03 | +0.03 | +0.01 | -0.03 | -0.03 | -0.03 | +0.03 | -0.03 |
| comma_chain | 0.09 | 0.06 | -0.10 | -0.06 | -0.03 | -0.07 | -0.17 | -0.23 | -0.23 | +0.23 | +0.90 | +0.63 | +0.10 | +0.63 | +0.27 | +1.21 | +1.34 | +1.28 | +0.30 | +0.99 | +0.52 | +1.12 | +0.71 |
| participial_triad | 0.01 | 0.01 | -0.03 | -0.03 | +0.04 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | +0.09 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | +0.06 | -0.03 | +0.02 | -0.03 | -0.03 | +0.11 |
| negation_template | 0.22 | 0.16 | -0.07 | +0.20 | +0.02 | +0.28 | +0.89 | +1.06 | +0.98 | +0.03 | +0.17 | -0.23 | -0.16 | +0.10 | -0.12 | -0.10 | -0.17 | +0.10 | -0.23 | +0.12 | -0.11 | -0.09 | -0.04 |
| intensifier | 0.53 | 0.31 | +0.10 | +0.55 | -0.25 | +0.04 | +0.01 | -0.07 | -0.08 | -0.23 | -0.19 | -0.12 | -0.19 | -0.20 | -0.13 | -0.41 | -0.20 | -0.41 | -0.16 | -0.30 | -0.47 | -0.38 | -0.16 |
| generator_phrase | 0.01 | 0.01 | -0.06 | +0.21 | +0.06 | +0.20 | +0.16 | +0.16 | +0.15 | +0.02 | +0.08 | -0.06 | +0.01 | -0.01 | -0.06 | +0.10 | -0.06 | +0.05 | +0.02 | +0.04 | -0.01 | +0.01 | +0.05 |
| fragment_couplet | 0.77 | 0.37 | -0.10 | -0.01 | +1.61 | +0.15 | +0.14 | +0.15 | +0.19 | +0.61 | +0.84 | +2.30 | +0.48 | +0.61 | +0.53 | +0.45 | +1.00 | +0.88 | +1.62 | +1.00 | +2.42 | +0.81 | +0.66 |
| personification | 0.00 | 0.00 | -0.01 | -0.01 | -0.01 | +0.06 | +0.09 | +0.07 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | +0.04 | -0.01 | +0.04 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.02 | 0.02 | +0.02 | -0.02 | -0.09 | -0.02 | -0.01 | -0.04 | -0.09 | -0.04 | -0.09 | -0.03 | +0.06 | -0.01 | -0.09 | -0.00 | +0.09 | +0.01 | -0.01 | -0.09 | -0.09 | -0.09 | +0.01 |
| question_fragment | 0.50 | 0.28 | -0.11 | -0.10 | -0.43 | -0.39 | +0.13 | +0.09 | +0.22 | -0.17 | -0.26 | -0.21 | -0.17 | -0.26 | -0.11 | -0.25 | -0.32 | -0.26 | -0.50 | -0.15 | -0.28 | -0.42 | -0.18 |
| then_opener | 0.41 | 0.23 | +0.18 | +0.09 | -0.13 | -0.08 | +0.49 | +0.29 | +0.30 | -0.35 | -0.13 | -0.08 | -0.10 | -0.27 | -0.12 | -0.08 | +0.05 | -0.15 | -0.20 | -0.14 | +0.11 | -0.18 | -0.13 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.04 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.01 | 0.01 | +0.07 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | +0.09 | +0.04 | +0.12 | -0.03 | +0.08 | +0.01 | -0.03 | +0.13 | +0.08 | -0.03 | -0.03 | +0.15 | +0.02 | +0.20 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 8.76 | 0.93 | +0.19 | -0.52 | -1.04 | -0.86 | -0.44 | -0.48 | -0.41 | +0.25 | +0.08 | +0.37 | +0.25 | +0.27 | +0.33 | +0.00 | +0.43 | +0.11 | -0.84 | +0.15 | -0.11 | -0.30 | +0.22 |
| anaphora2 | 1.50 | 0.48 | -0.05 | -0.10 | +5.16 | +0.49 | -0.25 | -0.25 | -0.37 | +0.82 | +1.67 | +1.50 | +0.77 | +0.94 | +0.47 | +1.64 | +1.88 | +1.49 | +6.71 | +1.28 | +4.08 | +3.68 | +0.91 |
| long_short | 2.53 | 0.74 | -0.13 | -0.90 | -0.71 | -0.94 | -0.21 | -0.24 | -0.57 | -0.26 | -0.14 | -0.34 | -0.07 | -0.15 | -0.27 | -0.27 | -0.01 | -0.28 | -0.88 | -0.17 | -0.50 | -0.17 | +0.12 |
| copula_density | 2.92 | 1.00 | -0.02 | -0.58 | +0.62 | -0.53 | -1.46 | -1.35 | -1.35 | +0.25 | +0.96 | +0.56 | +0.48 | +0.57 | +0.44 | +1.22 | +1.06 | +0.50 | +2.61 | +0.59 | +0.95 | +1.13 | +1.20 |

### h_private (calibrated on 85 REF+TRAIN chunks)

| feature | author mean/1k | fired share | h_private SOURCE | h_private_base4b | h_private_paire6_4b | h_private_base14b | h_private_base8b | h_private_paire6_14b | h_private_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.19 | 0.58 | -0.20 | +0.15 | -0.13 | +0.19 | +0.58 | -0.40 | +0.06 |
| way_simile | 0.41 | 0.28 | -0.09 | -0.14 | -0.36 | -0.26 | +0.26 | +0.13 | -0.05 |
| declarative_rating | 0.02 | 0.01 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 |
| reversal | 0.98 | 0.46 | +0.27 | +0.11 | +0.63 | -0.48 | -0.41 | +1.08 | +1.38 |
| self_explanation | 1.16 | 0.54 | -0.21 | -0.78 | -0.66 | -0.76 | -0.80 | -0.45 | -0.52 |
| triad | 0.13 | 0.09 | -0.32 | -0.08 | -0.04 | -0.15 | -0.32 | -0.18 | -0.32 |
| antithesis | 2.36 | 0.75 | -0.12 | -0.16 | -0.62 | -0.07 | -0.06 | -0.63 | -0.57 |
| cleft | 0.20 | 0.13 | -0.14 | -0.37 | -0.22 | -0.37 | -0.37 | -0.07 | -0.04 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.19 | +0.09 | +0.00 | +0.00 | +0.35 | +0.13 |
| nominalization_pickup | 0.40 | 0.22 | +0.04 | -0.43 | +0.07 | -0.44 | -0.40 | +0.22 | -0.17 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.06 | 0.04 | +0.32 | +0.05 | -0.05 | +0.10 | -0.01 | +0.02 | +0.00 |
| absence_punch | 0.01 | 0.01 | -0.06 | -0.06 | +0.18 | -0.06 | -0.06 | -0.06 | -0.06 |
| comma_chain | 0.25 | 0.16 | +0.31 | -0.33 | +0.74 | -0.42 | -0.31 | +0.75 | +0.29 |
| participial_triad | 0.02 | 0.01 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 | -0.06 |
| negation_template | 1.66 | 0.60 | -0.23 | -0.63 | -0.66 | -0.62 | -0.61 | -0.71 | -0.68 |
| intensifier | 2.20 | 0.62 | -0.24 | -0.62 | -0.60 | -0.47 | -0.46 | -0.23 | -0.28 |
| generator_phrase | 0.01 | 0.01 | +0.11 | -0.06 | -0.06 | +0.06 | +0.21 | -0.06 | -0.06 |
| fragment_couplet | 2.80 | 0.82 | -0.02 | -0.27 | +0.23 | -0.73 | -0.61 | +1.77 | +1.68 |
| personification | 0.03 | 0.02 | -0.12 | -0.12 | +0.15 | +0.00 | +0.11 | -0.12 | -0.12 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.05 | 0.04 | -0.19 | +0.15 | -0.09 | -0.19 | +0.02 | +0.53 | +0.08 |
| question_fragment | 0.00 | 0.00 | +0.35 | +0.00 | +0.00 | +0.24 | +0.00 | +0.09 | +0.00 |
| then_opener | 1.00 | 0.54 | -0.03 | -0.71 | -0.68 | -0.60 | -0.63 | -0.70 | -0.75 |
| pointer_verdict | 0.02 | 0.01 | -0.06 | -0.06 | +0.07 | -0.06 | -0.06 | -0.06 | -0.06 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.00 | +0.08 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 1.26 | 0.46 | +0.09 | -0.00 | +0.21 | +0.68 | +0.18 | +0.01 | +0.21 |
| anaphora2 | 5.94 | 0.91 | +0.40 | +1.68 | +5.12 | -0.53 | -0.23 | +5.59 | +6.96 |
| long_short | 5.48 | 0.93 | +0.10 | -1.31 | -0.79 | -1.40 | -1.32 | -0.72 | -0.94 |
| copula_density | 4.39 | 1.00 | -0.24 | -0.81 | +1.18 | -1.71 | -1.46 | +1.27 | +2.27 |

### link (calibrated on 78 REF+TRAIN chunks)

| feature | author mean/1k | fired share | link SOURCE | link_base14b | link_base4b | link_base8b | link_paire6_14b | link_paire6_4b | link_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.05 | 0.55 | -0.17 | -0.05 | +0.01 | -0.54 | -0.32 | +0.31 | +4.19 |
| way_simile | 0.06 | 0.04 | +0.13 | +1.37 | +5.50 | +3.13 | -0.20 | +0.16 | +0.15 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.65 | 0.35 | +0.62 | -0.50 | +4.30 | -0.63 | +0.84 | +1.63 | +6.41 |
| self_explanation | 0.40 | 0.24 | -0.30 | -0.50 | -0.50 | -0.50 | -0.44 | -0.37 | -0.36 |
| triad | 0.16 | 0.10 | -0.12 | +0.51 | -0.16 | +0.36 | -0.23 | -0.23 | -0.11 |
| antithesis | 0.35 | 0.24 | -0.21 | +0.32 | +0.74 | +1.37 | +0.03 | +0.62 | +6.58 |
| cleft | 0.03 | 0.03 | +0.07 | +0.24 | -0.13 | -0.13 | +0.05 | +0.56 | +0.67 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| nominalization_pickup | 0.05 | 0.04 | +0.01 | -0.20 | -0.20 | -0.20 | +5.06 | +0.30 | +2.82 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.00 | 0.00 | +0.22 | +0.00 | +0.15 | +0.00 | +0.00 | +0.16 | +0.52 |
| absence_punch | 0.02 | 0.01 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | +0.08 | -0.07 |
| comma_chain | 0.07 | 0.05 | +0.36 | +0.81 | +0.36 | +0.22 | +0.89 | +0.10 | +1.09 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.27 | 0.18 | +0.25 | -0.06 | -0.33 | -0.02 | -0.30 | -0.05 | +3.63 |
| intensifier | 0.69 | 0.33 | +0.04 | +0.11 | -0.26 | -0.03 | -0.27 | -0.43 | -0.29 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| fragment_couplet | 0.82 | 0.28 | +0.55 | -0.23 | +5.26 | -0.22 | +9.61 | +2.85 | +7.39 |
| personification | 0.02 | 0.01 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 | -0.07 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.06 | 0.04 | -0.03 | -0.19 | -0.04 | +0.05 | -0.19 | -0.19 | -0.19 |
| question_fragment | 0.21 | 0.12 | +1.29 | -0.16 | -0.21 | -0.22 | -0.27 | -0.27 | -0.22 |
| then_opener | 0.67 | 0.37 | -0.12 | +0.03 | -0.24 | -0.10 | +0.01 | +1.22 | -0.43 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 6.85 | 0.92 | +1.09 | -0.93 | -1.22 | -1.11 | -1.22 | -1.27 | -1.16 |
| anaphora2 | 2.27 | 0.67 | -0.03 | +0.86 | +5.34 | +1.16 | +7.55 | +5.21 | +9.49 |
| long_short | 1.06 | 0.46 | +0.16 | +0.04 | -0.29 | -0.28 | -0.56 | -0.55 | -0.34 |
| copula_density | 3.45 | 1.00 | +0.04 | -1.02 | +1.04 | -0.69 | +2.11 | +2.41 | +3.11 |

### mansfield (calibrated on 151 REF+TRAIN chunks)

| feature | author mean/1k | fired share | mansfield SOURCE | mansfield_base4b | mansfield_base4b_r2 | mansfield_paire6_4b | mansfield_base14b | mansfield_base8b | mansfield_paire6_14b | mansfield_paire6_8b | mansfield_paire6s1_4b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.51 | 0.58 | +0.13 | -0.31 | -0.52 | +0.16 | -0.09 | -0.44 | +0.37 | +0.17 | +0.26 |
| way_simile | 0.02 | 0.01 | +0.55 | +3.88 | +3.73 | +0.22 | +0.57 | +1.55 | +0.13 | +0.17 | +0.17 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.62 | 0.34 | +0.06 | +0.92 | +0.03 | +0.29 | -0.45 | -0.54 | +0.37 | +0.31 | +0.53 |
| self_explanation | 0.07 | 0.05 | +0.02 | -0.23 | -0.23 | +0.15 | -0.23 | -0.18 | -0.11 | +0.14 | -0.01 |
| triad | 0.07 | 0.05 | +0.11 | +0.09 | -0.05 | -0.14 | -0.02 | -0.16 | -0.03 | -0.10 | -0.04 |
| antithesis | 0.48 | 0.26 | -0.02 | +0.73 | +0.66 | -0.02 | +0.53 | +1.09 | -0.09 | -0.23 | -0.14 |
| cleft | 0.07 | 0.05 | +0.05 | -0.21 | -0.21 | -0.21 | -0.15 | -0.21 | -0.01 | +0.17 | -0.04 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.07 | +0.07 | +0.07 | +0.00 | +0.00 |
| nominalization_pickup | 0.09 | 0.06 | -0.10 | -0.20 | -0.17 | -0.15 | -0.20 | -0.15 | -0.07 | +0.13 | -0.11 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.04 | 0.03 | -0.01 | -0.17 | -0.17 | +0.20 | -0.17 | -0.12 | +0.03 | -0.04 | +0.09 |
| absence_punch | 0.02 | 0.01 | -0.07 | -0.07 | -0.07 | -0.01 | -0.07 | -0.07 | -0.07 | -0.07 | -0.02 |
| comma_chain | 0.05 | 0.04 | +0.17 | +0.35 | +0.59 | +1.62 | +0.14 | +0.45 | +1.79 | +1.88 | +1.97 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.08 | +0.00 | +0.00 | +0.12 | +0.06 | +0.00 | +0.09 | +0.13 |
| negation_template | 0.26 | 0.15 | -0.08 | -0.30 | -0.31 | -0.04 | -0.16 | -0.28 | -0.02 | -0.09 | +0.01 |
| intensifier | 0.92 | 0.44 | -0.11 | -0.25 | -0.34 | -0.47 | +0.05 | -0.09 | -0.47 | -0.34 | -0.48 |
| generator_phrase | 0.06 | 0.02 | -0.07 | -0.12 | -0.12 | -0.12 | -0.12 | -0.12 | -0.08 | -0.12 | -0.12 |
| fragment_couplet | 0.81 | 0.38 | -0.08 | -0.22 | -0.02 | +1.33 | -0.47 | -0.58 | +1.14 | +1.21 | +1.20 |
| personification | 0.01 | 0.01 | -0.03 | +0.06 | -0.03 | +0.02 | -0.03 | +0.04 | -0.03 | -0.03 | -0.03 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.06 | 0.05 | -0.22 | -0.15 | -0.22 | +0.03 | -0.15 | -0.01 | -0.13 | -0.07 | -0.18 |
| question_fragment | 0.43 | 0.27 | +0.19 | -0.46 | -0.40 | -0.36 | -0.46 | -0.52 | -0.23 | -0.25 | -0.35 |
| then_opener | 0.67 | 0.35 | +0.11 | -0.43 | -0.25 | +0.34 | -0.27 | -0.44 | +0.11 | +0.21 | -0.06 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.04 | +0.00 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 9.27 | 0.99 | -0.21 | -1.62 | -1.65 | -0.24 | -1.29 | -1.58 | -0.12 | -0.42 | -0.31 |
| anaphora2 | 0.84 | 0.39 | -0.21 | +7.96 | +9.58 | +2.43 | +0.23 | +1.61 | +2.34 | +2.48 | +2.82 |
| long_short | 2.42 | 0.74 | +0.03 | -0.64 | -0.55 | -0.29 | -0.67 | -0.61 | -0.40 | -0.35 | -0.36 |
| copula_density | 3.27 | 1.00 | +0.19 | -0.02 | +0.22 | +1.34 | -0.78 | -0.84 | +0.84 | +1.28 | +1.26 |

### patrick (calibrated on 225 REF+TRAIN chunks)

| feature | author mean/1k | fired share | patrick SOURCE | patrick_base4b | patrick_pair4b |
|---|---:|---:|---:|---:|---:|
| it_is_opener | 1.24 | 0.40 | +0.16 | +0.16 | +0.69 |
| way_simile | 0.05 | 0.03 | -0.17 | +1.32 | +0.18 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.16 | 0.06 | -0.01 | +0.65 | +0.59 |
| self_explanation | 0.12 | 0.06 | -0.25 | -0.25 | +0.35 |
| triad | 0.02 | 0.01 | -0.09 | +0.13 | +0.16 |
| antithesis | 0.98 | 0.36 | +0.05 | +0.30 | -0.10 |
| cleft | 0.01 | 0.00 | +0.75 | -0.03 | +0.08 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| nominalization_pickup | 0.09 | 0.04 | -0.10 | -0.20 | +0.39 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.03 | 0.01 | -0.09 | -0.09 | -0.03 |
| absence_punch | 0.00 | 0.00 | +0.15 | +0.36 | +0.00 |
| comma_chain | 0.06 | 0.03 | +0.31 | +0.46 | +1.32 |
| participial_triad | 0.01 | 0.00 | -0.03 | +0.05 | +0.08 |
| negation_template | 0.18 | 0.06 | -0.07 | +0.26 | +0.03 |
| intensifier | 0.87 | 0.30 | -0.20 | -0.31 | -0.17 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.21 | +0.09 |
| fragment_couplet | 0.15 | 0.04 | +0.06 | +2.62 | +0.19 |
| personification | 0.00 | 0.00 | +0.00 | +0.23 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.05 | 0.02 | -0.01 | -0.01 | -0.10 |
| question_fragment | 0.11 | 0.04 | +0.01 | -0.13 | -0.06 |
| then_opener | 0.22 | 0.10 | -0.26 | +0.17 | -0.06 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.01 | 0.00 | -0.03 | -0.03 | +0.24 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 3.60 | 0.44 | +0.20 | -0.47 | -0.09 |
| anaphora2 | 0.87 | 0.12 | +0.05 | +2.32 | +0.85 |
| long_short | 0.99 | 0.23 | -0.14 | -0.11 | -0.11 |
| copula_density | 3.01 | 1.00 | +0.29 | +0.06 | +1.26 |

### patrick_v2 (calibrated on 150 REF+TRAIN chunks)

| feature | author mean/1k | fired share | patrick_v2 SOURCE | patrick_v2_base17b | patrick_v2_paire6_17b | patrick_v2_base4b | patrick_v2_paire6_4b | patrick_v2_base8b | patrick_v2_paire6_8b | patrick_v2_base14b | patrick_v2_paire6_14b | patrick_v2_basem14b | patrick_v2_basem3b | patrick_v2_basem3b_r2 | patrick_v2_basem8b | patrick_v2_paire6_m14b | patrick_v2_paire6_m3b | patrick_v2_paire6_m8b | patrick_v2_size25 | patrick_v2_size50 | patrick_v2_size50_s1 | patrick_v2_size75 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.17 | 0.51 | +0.27 | -0.05 | +0.50 | +0.26 | +0.86 | +0.23 | +0.79 | +0.30 | +0.72 | -0.51 | -0.35 | -0.47 | -0.41 | +0.88 | +0.56 | +0.84 | +0.05 | +0.54 | +0.52 | +0.76 |
| way_simile | 0.06 | 0.04 | -0.20 | +0.58 | +0.13 | +2.63 | +0.06 | +1.04 | +0.19 | +0.87 | +0.03 | +1.25 | +2.42 | +0.84 | +1.32 | -0.04 | -0.07 | +0.38 | -0.13 | -0.01 | +0.61 | +0.16 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.06 | +0.00 | +0.00 | +0.00 | +0.04 | +0.08 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.15 | 0.09 | +0.06 | +3.12 | +0.87 | +1.57 | +0.72 | +0.43 | +0.61 | +0.22 | +0.39 | +0.09 | -0.01 | +0.15 | +0.09 | -0.11 | +0.27 | +0.48 | +3.25 | +0.60 | +1.24 | +0.89 |
| self_explanation | 0.11 | 0.08 | -0.29 | -0.29 | -0.12 | -0.29 | +0.24 | -0.23 | +0.16 | -0.26 | -0.12 | -0.15 | -0.29 | -0.29 | -0.29 | +0.14 | +0.11 | +0.00 | +0.59 | +0.11 | +0.09 | +0.56 |
| triad | 0.02 | 0.01 | -0.08 | -0.01 | -0.01 | +0.23 | +0.35 | +0.11 | +0.16 | +0.46 | +0.10 | +0.75 | +0.33 | +0.16 | +0.14 | +0.10 | +0.24 | +0.16 | +0.24 | +0.16 | +0.02 | +0.27 |
| antithesis | 1.01 | 0.49 | +0.15 | +0.19 | -0.06 | +0.96 | -0.05 | +0.84 | -0.18 | +0.48 | -0.04 | +0.89 | +0.28 | +0.38 | +0.13 | -0.18 | -0.15 | -0.32 | +0.70 | -0.11 | -0.21 | -0.15 |
| cleft | 0.01 | 0.01 | +0.51 | -0.04 | +0.23 | -0.04 | +0.26 | -0.04 | +0.06 | -0.04 | +0.30 | -0.04 | -0.04 | +0.05 | -0.04 | +0.41 | +0.37 | +0.34 | +0.44 | +0.08 | +0.02 | +0.12 |
| closing_flourish | 0.01 | 0.01 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | +0.10 | +0.02 | -0.04 | +0.02 | -0.04 | +0.01 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 |
| nominalization_pickup | 0.08 | 0.06 | -0.02 | -0.03 | +0.25 | -0.21 | +0.16 | -0.20 | +0.24 | +0.03 | +0.19 | -0.19 | -0.14 | -0.19 | -0.12 | -0.02 | +0.32 | +0.52 | +0.58 | +0.06 | +0.11 | +0.10 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.05 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.02 | 0.01 | -0.08 | -0.08 | +0.14 | -0.08 | -0.08 | -0.08 | +0.09 | -0.01 | +0.09 | -0.04 | -0.03 | -0.08 | -0.03 | +0.51 | +0.07 | -0.08 | -0.01 | -0.08 | +0.12 | +0.13 |
| absence_punch | 0.00 | 0.00 | +0.24 | +0.06 | +0.07 | +0.05 | +0.00 | +0.00 | +0.00 | +0.07 | +0.07 | +0.00 | +0.12 | +0.20 | +0.11 | +0.00 | +0.04 | +0.00 | +0.00 | +0.13 | +0.04 | +0.00 |
| comma_chain | 0.05 | 0.03 | +0.45 | +0.46 | +1.62 | +0.63 | +1.34 | +0.36 | +1.08 | +0.24 | +1.13 | +0.05 | +0.01 | -0.06 | -0.03 | +1.16 | +2.54 | +1.20 | +0.25 | +1.49 | +1.33 | +1.44 |
| participial_triad | 0.01 | 0.01 | +0.06 | -0.04 | +0.06 | -0.04 | +0.04 | -0.04 | -0.04 | -0.04 | +0.02 | +0.10 | -0.04 | +0.04 | -0.04 | -0.04 | -0.04 | -0.04 | -0.04 | +0.04 | -0.04 | -0.04 |
| negation_template | 0.18 | 0.08 | -0.14 | +0.04 | -0.02 | +0.25 | -0.03 | +0.39 | +0.01 | +0.21 | +0.06 | +1.11 | +1.33 | +1.13 | +0.98 | -0.04 | -0.04 | +0.08 | +0.33 | -0.11 | +0.03 | +0.02 |
| intensifier | 0.85 | 0.41 | -0.15 | -0.22 | -0.25 | -0.20 | -0.33 | -0.09 | -0.17 | +0.04 | -0.49 | -0.43 | -0.40 | -0.36 | -0.32 | -0.21 | -0.39 | -0.23 | -0.37 | -0.34 | -0.16 | -0.22 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.13 | +0.07 | +0.08 | +0.00 | +0.25 | +0.04 | +0.06 | +0.00 | +0.32 | +0.33 | +0.45 | +0.25 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| fragment_couplet | 0.12 | 0.05 | +0.24 | +3.51 | +1.32 | +5.99 | +1.31 | +2.52 | +0.92 | +1.92 | +0.75 | +2.35 | +1.93 | +2.12 | +3.09 | +0.33 | +0.51 | +0.19 | +5.03 | +5.31 | +4.47 | +0.99 |
| personification | 0.00 | 0.00 | +0.00 | +0.00 | +0.12 | +0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.00 | +0.28 | +0.00 | +0.00 | +0.08 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.08 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.06 | 0.03 | -0.09 | -0.07 | +0.05 | -0.07 | +0.30 | -0.08 | -0.01 | -0.12 | +0.19 | -0.05 | -0.11 | -0.11 | -0.17 | +0.11 | -0.04 | +0.05 | -0.07 | +0.10 | -0.03 | -0.10 |
| question_fragment | 0.11 | 0.05 | -0.02 | -0.20 | -0.11 | -0.20 | -0.05 | -0.12 | -0.11 | -0.14 | -0.04 | +0.09 | +0.07 | +0.06 | +0.19 | -0.14 | -0.20 | -0.18 | -0.20 | -0.20 | -0.17 | -0.15 |
| then_opener | 0.22 | 0.15 | -0.23 | -0.38 | -0.26 | -0.08 | +0.00 | +0.09 | -0.04 | +0.28 | +0.09 | +1.02 | +1.37 | +0.74 | +1.32 | -0.11 | +0.04 | +0.17 | -0.15 | +0.47 | +0.03 | +0.49 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.01 | 0.01 | -0.03 | -0.03 | +0.11 | -0.03 | +0.12 | -0.03 | +0.03 | -0.03 | +0.11 | -0.03 | -0.03 | -0.03 | -0.03 | -0.03 | +0.18 | +0.19 | +0.05 | -0.03 | -0.03 | +0.10 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 3.77 | 0.55 | +0.07 | -0.60 | -0.02 | -0.65 | +0.15 | -0.55 | -0.03 | -0.32 | +0.01 | -0.21 | -0.24 | -0.25 | -0.10 | -0.03 | +0.40 | +0.20 | -0.45 | -0.19 | -0.26 | +0.06 |
| anaphora2 | 0.80 | 0.15 | +0.10 | +5.47 | +2.76 | +6.97 | +1.86 | +2.65 | +2.01 | +1.70 | +1.69 | +0.68 | +0.53 | +0.44 | +0.51 | +0.81 | +1.29 | +1.17 | +9.33 | +6.11 | +5.77 | +2.14 |
| long_short | 0.99 | 0.33 | -0.06 | -0.49 | -0.17 | -0.06 | -0.13 | -0.22 | -0.26 | +0.11 | -0.13 | +1.24 | +1.09 | +1.11 | +0.90 | -0.07 | +0.08 | -0.25 | -0.44 | -0.30 | -0.24 | -0.33 |
| copula_density | 2.99 | 1.00 | +0.43 | +1.09 | +1.39 | +0.63 | +1.31 | -0.19 | +1.22 | -0.18 | +1.27 | -0.79 | -0.78 | -0.70 | -0.74 | +1.09 | +1.57 | +1.13 | +2.47 | +1.30 | +1.21 | +1.76 |

### rucker (calibrated on 443 REF+TRAIN chunks)

| feature | author mean/1k | fired share | rucker SOURCE | rucker_base14b | rucker_base4b | rucker_base8b | rucker_paire6_14b | rucker_paire6_4b | rucker_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 0.79 | 0.43 | +0.20 | +0.16 | +0.68 | +0.20 | +1.07 | +1.28 | +0.94 |
| way_simile | 0.07 | 0.05 | -0.14 | +0.15 | +1.77 | +0.58 | +0.04 | +0.19 | +0.07 |
| declarative_rating | 0.00 | 0.00 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 |
| reversal | 0.34 | 0.23 | +0.12 | -0.05 | +0.65 | -0.21 | +0.10 | +0.27 | +0.06 |
| self_explanation | 0.16 | 0.11 | +0.17 | -0.30 | -0.27 | -0.35 | -0.22 | -0.05 | -0.19 |
| triad | 0.02 | 0.02 | +0.23 | -0.09 | +0.23 | +0.13 | +0.07 | -0.00 | +0.04 |
| antithesis | 0.61 | 0.36 | +0.09 | +0.15 | +0.38 | +0.34 | -0.23 | -0.32 | -0.25 |
| cleft | 0.02 | 0.02 | -0.09 | +0.16 | -0.09 | +0.02 | +0.12 | -0.09 | +0.02 |
| closing_flourish | 0.00 | 0.00 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 |
| nominalization_pickup | 0.03 | 0.02 | +0.30 | +0.11 | +0.02 | -0.11 | +0.07 | -0.02 | +0.13 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.01 | 0.01 | +0.06 | -0.05 | -0.05 | -0.05 | +0.23 | -0.00 | +0.19 |
| absence_punch | 0.01 | 0.00 | -0.02 | +0.03 | -0.02 | -0.02 | -0.02 | -0.02 | +0.07 |
| comma_chain | 0.01 | 0.01 | -0.06 | +0.21 | +0.31 | +0.16 | +0.11 | -0.06 | +0.03 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.12 | 0.08 | -0.11 | +0.59 | +0.59 | +0.59 | +0.06 | +0.16 | -0.04 |
| intensifier | 0.49 | 0.30 | -0.14 | +0.20 | -0.23 | +0.05 | -0.24 | -0.26 | -0.29 |
| generator_phrase | 0.01 | 0.01 | -0.06 | -0.06 | +0.04 | +0.00 | -0.06 | -0.06 | -0.02 |
| fragment_couplet | 0.37 | 0.23 | +0.07 | +0.60 | +4.66 | +0.71 | +1.45 | +1.89 | +1.20 |
| personification | 0.01 | 0.01 | -0.03 | +0.02 | +0.04 | +0.03 | -0.03 | -0.03 | -0.03 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.01 | 0.00 | -0.02 | +0.08 | +0.09 | -0.02 | +0.07 | +0.09 | +0.02 |
| question_fragment | 0.38 | 0.24 | +0.12 | -0.21 | -0.42 | -0.35 | -0.08 | -0.23 | -0.17 |
| then_opener | 0.10 | 0.07 | -0.00 | +1.66 | +0.88 | +1.17 | +0.22 | +0.80 | +0.79 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.15 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 8.80 | 0.96 | -0.14 | -0.96 | -1.51 | -1.04 | -0.27 | -0.44 | -0.25 |
| anaphora2 | 0.43 | 0.24 | +0.06 | +0.89 | +11.45 | +2.79 | +0.91 | +1.21 | +1.21 |
| long_short | 1.00 | 0.48 | +0.08 | -0.45 | -0.33 | -0.52 | -0.48 | -0.51 | -0.46 |
| copula_density | 2.86 | 1.00 | +0.41 | -0.30 | +1.42 | -0.25 | +1.49 | +1.73 | +1.75 |

### stross (calibrated on 143 REF+TRAIN chunks)

| feature | author mean/1k | fired share | stross SOURCE | stross_base14b | stross_base4b | stross_base8b | stross_paire6_14b | stross_paire6_4b | stross_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 0.11 | 0.08 | +0.14 | +3.51 | +2.50 | +1.62 | +0.76 | +0.69 | +0.36 |
| way_simile | 0.02 | 0.01 | +0.13 | +0.48 | +1.91 | +1.07 | +0.31 | +0.37 | +0.12 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.51 | 0.29 | +0.06 | -0.01 | +0.15 | -0.21 | +0.09 | +0.30 | -0.06 |
| self_explanation | 0.19 | 0.13 | +0.30 | -0.35 | -0.38 | -0.35 | -0.03 | +0.07 | +0.25 |
| triad | 0.03 | 0.02 | -0.01 | +0.03 | +0.28 | +0.17 | +0.40 | +0.00 | +0.10 |
| antithesis | 0.74 | 0.38 | +0.10 | +0.26 | +0.31 | +0.60 | +0.02 | -0.13 | +0.08 |
| cleft | 0.06 | 0.04 | +0.05 | -0.15 | -0.14 | -0.14 | -0.05 | +0.09 | +0.06 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| nominalization_pickup | 0.05 | 0.03 | -0.08 | -0.04 | +0.03 | -0.11 | +0.74 | +0.16 | +0.31 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.01 | 0.01 | +0.08 | -0.04 | -0.04 | +0.03 | -0.04 | -0.04 | -0.04 |
| absence_punch | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| comma_chain | 0.02 | 0.01 | +0.13 | -0.01 | +0.11 | +0.05 | +0.01 | +0.21 | +0.18 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.00 | +0.16 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.12 | 0.08 | +0.25 | +1.00 | +1.16 | +1.32 | +0.21 | +0.42 | +0.06 |
| intensifier | 1.08 | 0.53 | +0.08 | -0.04 | -0.35 | -0.25 | -0.50 | -0.45 | -0.39 |
| generator_phrase | 0.05 | 0.03 | -0.19 | -0.19 | -0.19 | -0.03 | -0.19 | +0.02 | +0.02 |
| fragment_couplet | 0.17 | 0.13 | +0.54 | +2.92 | +10.15 | +4.32 | +2.68 | +1.84 | +4.71 |
| personification | 0.00 | 0.00 | +0.00 | +0.08 | +0.07 | +0.00 | +0.00 | +0.00 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.01 | 0.01 | -0.04 | +0.24 | +0.11 | -0.04 | +0.05 | -0.04 | -0.04 |
| question_fragment | 0.36 | 0.22 | +0.20 | -0.01 | -0.28 | +0.03 | -0.06 | -0.10 | -0.12 |
| then_opener | 0.39 | 0.24 | +0.03 | +0.13 | -0.01 | -0.07 | +0.09 | +0.06 | -0.02 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.29 | +0.17 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 12.39 | 0.97 | +0.16 | -0.98 | -1.51 | -1.20 | -0.03 | -0.09 | -0.23 |
| anaphora2 | 0.33 | 0.15 | -0.01 | +1.80 | +11.76 | +2.27 | +3.16 | +3.23 | +4.00 |
| long_short | 2.65 | 0.75 | +0.39 | -1.01 | -1.04 | -1.05 | -0.78 | -0.60 | -0.62 |
| copula_density | 2.69 | 1.00 | -0.12 | +0.33 | +1.28 | +0.09 | +1.18 | +1.88 | +1.25 |

### sui_sin_far (calibrated on 59 REF+TRAIN chunks)

| feature | author mean/1k | fired share | sui_sin_far SOURCE | sui_sin_far_base4b | sui_sin_far_paire6_4b | sui_sin_far_base14b | sui_sin_far_base8b | sui_sin_far_paire6_14b | sui_sin_far_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.28 | 0.63 | -0.20 | -0.52 | -0.45 | -0.27 | -0.62 | +0.69 | -0.25 |
| way_simile | 0.05 | 0.02 | -0.13 | +1.56 | +0.09 | +0.74 | +1.08 | -0.09 | +0.73 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.19 | 0.12 | +0.54 | +1.76 | +2.68 | -0.03 | -0.10 | +0.73 | +2.42 |
| self_explanation | 0.09 | 0.07 | +0.24 | -0.27 | +0.38 | -0.27 | -0.27 | +0.47 | +0.13 |
| triad | 0.00 | 0.00 | +0.00 | +0.42 | +0.06 | +0.11 | +0.00 | +0.07 | +0.95 |
| antithesis | 0.50 | 0.27 | +0.12 | +0.92 | +0.14 | +0.46 | +0.72 | -0.37 | +0.15 |
| cleft | 0.00 | 0.00 | +0.33 | +0.20 | +0.08 | +0.00 | +0.00 | +0.00 | +0.14 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| nominalization_pickup | 0.23 | 0.15 | -0.18 | -0.36 | +0.06 | -0.25 | -0.31 | +0.21 | -0.18 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.10 | 0.05 | -0.04 | -0.23 | -0.19 | -0.23 | -0.23 | +0.09 | -0.23 |
| absence_punch | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| comma_chain | 0.00 | 0.00 | +0.17 | +0.83 | +0.56 | +0.10 | +0.10 | +1.76 | +0.97 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.08 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.09 | 0.07 | +0.24 | +0.25 | +1.22 | +0.23 | +0.07 | -0.27 | -0.27 |
| intensifier | 0.42 | 0.27 | -0.21 | +0.32 | -0.18 | +1.01 | +0.31 | -0.22 | -0.24 |
| generator_phrase | 0.02 | 0.02 | +0.09 | -0.09 | -0.02 | -0.09 | +0.02 | -0.09 | -0.09 |
| fragment_couplet | 0.60 | 0.32 | +0.05 | +1.08 | -0.10 | -0.27 | +0.03 | +2.24 | -0.48 |
| personification | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.08 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.09 | 0.07 | -0.27 | -0.19 | -0.09 | -0.27 | -0.04 | +0.21 | -0.27 |
| question_fragment | 0.04 | 0.03 | +0.53 | -0.09 | -0.11 | +0.55 | +0.20 | -0.02 | -0.17 |
| then_opener | 1.00 | 0.39 | -0.36 | -0.45 | -0.43 | -0.40 | -0.43 | -0.49 | -0.57 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.12 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 7.05 | 0.90 | -0.08 | -1.18 | -1.35 | -0.85 | -0.90 | -1.13 | -1.38 |
| anaphora2 | 1.20 | 0.39 | +0.33 | +6.44 | +12.77 | +0.58 | +1.06 | +11.48 | +11.00 |
| long_short | 2.99 | 0.75 | -0.24 | -0.81 | -0.71 | -0.92 | -0.94 | -0.83 | -0.78 |
| copula_density | 3.69 | 1.00 | -0.08 | -0.31 | +2.78 | -1.70 | -1.78 | +2.60 | +2.58 |

### watts (calibrated on 387 REF+TRAIN chunks)

| feature | author mean/1k | fired share | watts SOURCE | watts_base14b | watts_base4b | watts_base8b | watts_paire6_14b | watts_paire6_4b | watts_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 0.73 | 0.38 | +0.01 | +0.42 | +0.40 | +0.21 | +0.75 | +0.63 | +0.80 |
| way_simile | 0.04 | 0.03 | +0.04 | +0.36 | +2.42 | +1.00 | +0.04 | +0.13 | -0.02 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.63 | 0.39 | -0.13 | -0.02 | -0.01 | -0.17 | +0.26 | +0.21 | +0.07 |
| self_explanation | 0.09 | 0.06 | +0.16 | -0.21 | -0.25 | -0.20 | -0.19 | -0.15 | -0.03 |
| triad | 0.10 | 0.07 | -0.06 | -0.26 | -0.12 | -0.17 | -0.04 | -0.15 | -0.02 |
| antithesis | 0.52 | 0.32 | -0.21 | +0.48 | +0.30 | +0.66 | +0.19 | -0.20 | +0.10 |
| cleft | 0.03 | 0.03 | +0.07 | -0.02 | -0.14 | -0.08 | -0.14 | -0.02 | -0.02 |
| closing_flourish | 0.00 | 0.00 | -0.01 | -0.01 | -0.01 | -0.01 | -0.01 | +0.06 | -0.01 |
| nominalization_pickup | 0.04 | 0.03 | -0.17 | -0.12 | +0.30 | -0.12 | +0.06 | +0.08 | -0.04 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.03 | 0.02 | +0.10 | -0.11 | -0.11 | -0.11 | -0.07 | -0.00 | -0.11 |
| absence_punch | 0.01 | 0.01 | +0.06 | -0.04 | +0.03 | -0.04 | -0.04 | +0.09 | -0.04 |
| comma_chain | 0.03 | 0.02 | -0.01 | -0.11 | +0.12 | +0.14 | +0.10 | +0.18 | +0.11 |
| participial_triad | 0.00 | 0.00 | -0.01 | -0.01 | -0.01 | -0.01 | +0.03 | -0.01 | +0.10 |
| negation_template | 0.60 | 0.35 | -0.17 | +0.13 | +0.31 | +0.04 | +0.22 | +0.30 | +0.05 |
| intensifier | 1.18 | 0.59 | +0.06 | -0.38 | -0.73 | -0.42 | -0.56 | -0.46 | -0.28 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.13 | +0.04 |
| fragment_couplet | 1.35 | 0.59 | -0.02 | +0.00 | +2.15 | -0.08 | +1.52 | +2.08 | +1.23 |
| personification | 0.00 | 0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.05 | 0.04 | -0.08 | -0.12 | -0.12 | +0.00 | -0.02 | -0.14 | +0.00 |
| question_fragment | 0.67 | 0.38 | +0.00 | -0.21 | -0.57 | -0.61 | +0.16 | -0.05 | +0.10 |
| then_opener | 0.32 | 0.20 | -0.31 | +0.41 | +0.11 | +0.13 | -0.11 | -0.05 | -0.05 |
| pointer_verdict | 0.02 | 0.02 | +0.01 | -0.09 | -0.03 | -0.09 | -0.09 | -0.09 | -0.09 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.01 | 0.01 | +0.05 | -0.05 | -0.05 | -0.05 | -0.05 | -0.00 | +0.04 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 8.90 | 0.94 | +0.03 | -0.56 | -0.87 | -0.74 | +0.08 | +0.04 | +0.18 |
| anaphora2 | 1.59 | 0.63 | -0.11 | +0.08 | +4.61 | +0.97 | +1.73 | +2.39 | +1.69 |
| long_short | 1.19 | 0.59 | -0.05 | -0.53 | -0.37 | -0.48 | -0.23 | -0.26 | -0.24 |
| copula_density | 2.63 | 1.00 | -0.18 | +0.14 | +1.36 | +0.12 | +0.98 | +1.11 | +0.76 |

### wharton (calibrated on 234 REF+TRAIN chunks)

| feature | author mean/1k | fired share | wharton SOURCE | base4b | base4b_r2 | pair_e6_4b | wharton_base14b | wharton_base8b | wharton_paire6_14b | wharton_paire6_8b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| it_is_opener | 1.27 | 0.55 | +0.08 | +0.33 | +0.01 | +0.47 | +0.84 | +0.35 | +0.51 | +0.43 |
| way_simile | 0.01 | 0.00 | -0.03 | +4.11 | +1.65 | +0.15 | +0.82 | +1.21 | +0.23 | +0.21 |
| declarative_rating | 0.00 | 0.00 | +0.00 | +0.07 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| reversal | 0.23 | 0.13 | -0.09 | +0.99 | +2.04 | +0.05 | +0.03 | +0.05 | -0.02 | +0.07 |
| self_explanation | 0.05 | 0.03 | +0.03 | -0.19 | -0.19 | +0.21 | -0.12 | -0.10 | +0.10 | -0.04 |
| triad | 0.02 | 0.02 | +0.02 | -0.09 | -0.09 | +0.06 | +0.19 | +0.04 | +0.01 | +0.12 |
| antithesis | 0.49 | 0.28 | -0.10 | +1.62 | +1.67 | -0.19 | +1.23 | +2.06 | -0.09 | -0.27 |
| cleft | 0.04 | 0.02 | -0.14 | -0.14 | -0.09 | +0.03 | -0.08 | -0.14 | -0.03 | +0.14 |
| closing_flourish | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.07 | +0.00 | +0.06 | +0.00 | +0.00 |
| nominalization_pickup | 0.09 | 0.06 | -0.10 | -0.14 | -0.20 | +0.38 | -0.24 | -0.24 | +0.28 | +0.34 |
| meta_aside | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| self_rating | 0.04 | 0.02 | +0.14 | -0.08 | -0.06 | +0.14 | -0.03 | -0.14 | +0.04 | +0.17 |
| absence_punch | 0.01 | 0.01 | -0.04 | -0.04 | -0.04 | -0.04 | +0.02 | -0.04 | -0.04 | -0.04 |
| comma_chain | 0.04 | 0.02 | +0.17 | +0.31 | +0.25 | +1.08 | -0.03 | +0.18 | +0.37 | +1.07 |
| participial_triad | 0.00 | 0.00 | +0.00 | +0.07 | +0.00 | +0.08 | +0.00 | +0.00 | +0.00 | +0.00 |
| negation_template | 0.10 | 0.06 | +0.08 | +0.41 | +0.43 | +0.19 | +0.13 | +0.37 | -0.07 | +0.10 |
| intensifier | 0.89 | 0.48 | -0.01 | +0.33 | +0.05 | -0.41 | +0.85 | +0.58 | -0.01 | -0.12 |
| generator_phrase | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.06 | +0.00 | +0.00 | +0.00 | +0.00 |
| fragment_couplet | 0.14 | 0.08 | -0.05 | +1.22 | +1.49 | +0.04 | +0.76 | +0.34 | -0.02 | +0.20 |
| personification | 0.02 | 0.01 | -0.07 | -0.00 | -0.01 | -0.07 | -0.07 | +0.00 | -0.07 | -0.07 |
| colon_twist | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| tail_twist | 0.03 | 0.02 | -0.01 | +0.01 | -0.01 | -0.08 | +0.07 | -0.03 | +0.10 | -0.05 |
| question_fragment | 0.72 | 0.29 | -0.11 | -0.47 | -0.41 | -0.32 | -0.42 | -0.47 | -0.31 | -0.30 |
| then_opener | 0.43 | 0.26 | -0.08 | -0.37 | -0.28 | -0.01 | -0.18 | -0.29 | +0.04 | -0.03 |
| pointer_verdict | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| announcer | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| does_pair | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| parallel_address | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| conversion | 0.00 | 0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| rhetorical_question | 10.07 | 0.84 | -0.06 | -1.18 | -1.18 | -0.53 | -1.02 | -1.10 | -0.39 | -0.48 |
| anaphora2 | 0.45 | 0.15 | -0.04 | +8.67 | +8.26 | +1.00 | +1.13 | +2.11 | +0.93 | +1.42 |
| long_short | 2.79 | 0.63 | -0.20 | -0.49 | -0.44 | -0.18 | -0.50 | -0.65 | -0.19 | -0.25 |
| copula_density | 3.11 | 1.00 | +0.21 | +1.28 | +0.94 | +1.72 | -0.25 | -0.49 | +1.40 | +1.46 |

