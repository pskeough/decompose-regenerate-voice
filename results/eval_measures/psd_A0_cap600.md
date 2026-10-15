# psd (arm A0, first 600 words; paired distance to the source passage; glyph fold on)

## abs_cv_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 0.498 | 0.436 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.451 | 0.391 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.365 | 0.337 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.610 | 0.356 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.577 | 0.344 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.280 | 0.221 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.316 | 0.224 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.529 | 0.338 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.315 | 0.210 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.456 | 0.296 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.229 | 0.192 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.631 | 0.367 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.631 | 0.360 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.313 | 0.318 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.306 | 0.246 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.281 | 0.222 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.334 | 0.268 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.293 | 0.208 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.309 | 0.263 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.293 | 0.198 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.246 | 0.234 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.286 | 0.231 |
| h_private_base4b | h_private | 4b | base | 46 | 0.622 | 0.270 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.329 | 0.282 |
| chopin_base4b | chopin | 4b | base | 98 | 0.376 | 0.234 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.260 | 0.210 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.597 | 0.320 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 0.769 | 0.331 |
| cather_base4b | cather | 4b | base | 88 | 0.427 | 0.280 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.487 | 0.251 |
| cather_base14b | cather | 14b | base | 88 | 0.321 | 0.226 |
| cather_base8b | cather | 8b | base | 88 | 0.343 | 0.245 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.426 | 0.306 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.342 | 0.251 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.435 | 0.274 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.481 | 0.336 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.411 | 0.306 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.419 | 0.288 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.446 | 0.253 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.438 | 0.292 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.379 | 0.266 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.369 | 0.280 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.301 | 0.224 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.297 | 0.217 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.305 | 0.264 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.324 | 0.260 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.296 | 0.239 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 0.648 | 0.379 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.385 | 0.277 |
| chopin_base14b | chopin | 14b | base | 98 | 0.270 | 0.158 |
| chopin_base8b | chopin | 8b | base | 98 | 0.331 | 0.224 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.215 | 0.183 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.265 | 0.198 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.319 | 0.246 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.455 | 0.326 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.350 | 0.310 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.293 | 0.243 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.324 | 0.263 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.241 | 0.193 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.246 | 0.178 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.237 | 0.186 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.229 | 0.294 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.244 | 0.207 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.239 | 0.193 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.244 | 0.197 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.235 | 0.188 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.269 | 0.224 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.236 | 0.185 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.519 | 0.271 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.239 | 0.177 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.262 | 0.207 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.270 | 0.221 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.227 | 0.165 |
| h_private_base14b | h_private | 14b | base | 46 | 0.443 | 0.228 |
| h_private_base8b | h_private | 8b | base | 46 | 0.475 | 0.216 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.340 | 0.322 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.309 | 0.266 |
| link_base14b | link | 14b | base | 32 | 0.456 | 0.235 |
| link_base4b | link | 4b | base | 32 | 0.581 | 0.235 |
| link_base8b | link | 8b | base | 32 | 0.443 | 0.240 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.449 | 0.306 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.428 | 0.251 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.351 | 0.204 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.560 | 0.282 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.625 | 0.333 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.367 | 0.304 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.379 | 0.328 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.377 | 0.343 |
| patrick_base4b | patrick | 4b | base | 92 | 0.318 | 0.292 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.303 | 0.312 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.250 | 0.192 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.264 | 0.198 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.250 | 0.224 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.243 | 0.203 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.322 | 0.255 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.287 | 0.233 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.289 | 0.216 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.389 | 0.271 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.252 | 0.210 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.281 | 0.231 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.318 | 0.245 |
| rucker_base14b | rucker | 14b | base | 94 | 0.269 | 0.191 |
| rucker_base4b | rucker | 4b | base | 94 | 0.410 | 0.263 |
| rucker_base8b | rucker | 8b | base | 94 | 0.349 | 0.246 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.211 | 0.170 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.231 | 0.193 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.191 | 0.167 |
| stross_base14b | stross | 14b | base | 82 | 0.290 | 0.208 |
| stross_base4b | stross | 4b | base | 82 | 0.446 | 0.309 |
| stross_base8b | stross | 8b | base | 82 | 0.348 | 0.264 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.308 | 0.254 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.339 | 0.270 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.295 | 0.235 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.526 | 0.295 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.519 | 0.352 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.525 | 0.362 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 0.575 | 0.369 |
| watts_base14b | watts | 14b | base | 90 | 0.415 | 0.231 |
| watts_base4b | watts | 4b | base | 90 | 0.562 | 0.312 |
| watts_base8b | watts | 8b | base | 90 | 0.495 | 0.275 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.175 | 0.127 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.205 | 0.160 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.211 | 0.152 |
| wharton_base14b | wharton | 14b | base | 88 | 0.402 | 0.372 |
| wharton_base8b | wharton | 8b | base | 88 | 0.459 | 0.393 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.345 | 0.316 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.349 | 0.292 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -0.047
- chesterton_base4b vs chesterton_base4bc: -0.034
- mansfield_base4b vs mansfield_base4b_r2: -0.000

Base vs adapter, same author and size:

- cather 14b: base 0.321 -> adapter 0.426 (+0.104)
- cather 4b: base 0.427 -> adapter 0.487 (+0.059)
- cather 8b: base 0.343 -> adapter 0.342 (-0.002)
- chesterton 14b: base 0.456 -> adapter 0.229 (-0.228)
- chesterton 4b: base 0.610 -> adapter 0.280 (-0.330)
- chesterton 4bc: base 0.577 -> adapter 0.316 (-0.260)
- chesterton 8b: base 0.529 -> adapter 0.315 (-0.214)
- chesterton m14b: base 0.411 -> adapter 0.301 (-0.110)
- chesterton m3b: base 0.446 -> adapter 0.297 (-0.149)
- chesterton m8b: base 0.379 -> adapter 0.305 (-0.074)
- chopin 14b: base 0.270 -> adapter 0.215 (-0.054)
- chopin 4b: base 0.376 -> adapter 0.260 (-0.117)
- chopin 8b: base 0.331 -> adapter 0.265 (-0.066)
- doctorow 14b: base 0.319 -> adapter 0.246 (-0.073)
- doctorow 4b: base 0.455 -> adapter 0.237 (-0.218)
- doctorow 8b: base 0.350 -> adapter 0.229 (-0.121)
- doctorow m14b: base 0.293 -> adapter 0.244 (-0.049)
- doctorow m3b: base 0.324 -> adapter 0.239 (-0.085)
- doctorow m8b: base 0.241 -> adapter 0.244 (+0.002)
- h_private 14b: base 0.443 -> adapter 0.340 (-0.103)
- h_private 4b: base 0.622 -> adapter 0.329 (-0.293)
- h_private 8b: base 0.475 -> adapter 0.309 (-0.166)
- link 14b: base 0.456 -> adapter 0.449 (-0.007)
- link 4b: base 0.581 -> adapter 0.428 (-0.152)
- link 8b: base 0.443 -> adapter 0.351 (-0.092)
- mansfield 14b: base 0.560 -> adapter 0.367 (-0.193)
- mansfield 4b: base 0.631 -> adapter 0.313 (-0.318)
- mansfield 8b: base 0.625 -> adapter 0.379 (-0.246)
- patrick 4b: base 0.318 -> adapter 0.303 (-0.015)
- patrick_v2 14b: base 0.246 -> adapter 0.286 (+0.040)
- patrick_v2 17b: base 0.306 -> adapter 0.281 (-0.025)
- patrick_v2 4b: base 0.334 -> adapter 0.293 (-0.041)
- patrick_v2 8b: base 0.309 -> adapter 0.293 (-0.016)
- patrick_v2 m14b: base 0.250 -> adapter 0.322 (+0.072)
- patrick_v2 m3b: base 0.264 -> adapter 0.287 (+0.023)
- patrick_v2 m8b: base 0.243 -> adapter 0.289 (+0.046)
- rucker 14b: base 0.269 -> adapter 0.211 (-0.058)
- rucker 4b: base 0.410 -> adapter 0.231 (-0.179)
- rucker 8b: base 0.349 -> adapter 0.191 (-0.157)
- stross 14b: base 0.290 -> adapter 0.308 (+0.017)
- stross 4b: base 0.446 -> adapter 0.339 (-0.106)
- stross 8b: base 0.348 -> adapter 0.295 (-0.052)
- sui_sin_far 14b: base 0.526 -> adapter 0.525 (-0.001)
- sui_sin_far 4b: base 0.597 -> adapter 0.769 (+0.172)
- sui_sin_far 8b: base 0.519 -> adapter 0.575 (+0.055)
- watts 14b: base 0.415 -> adapter 0.175 (-0.240)
- watts 4b: base 0.562 -> adapter 0.205 (-0.357)
- watts 8b: base 0.495 -> adapter 0.211 (-0.284)
- wharton 14b: base 0.402 -> adapter 0.345 (-0.057)
- wharton 4b: base 0.498 -> adapter 0.365 (-0.134)
- wharton 8b: base 0.459 -> adapter 0.349 (-0.110)

## cv_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | -0.477 | 0.460 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.435 | 0.408 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.031 | 0.496 |
| chesterton_base4b | chesterton | 4b | base | 78 | -0.587 | 0.393 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | -0.558 | 0.373 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | -0.133 | 0.331 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | -0.059 | 0.383 |
| chesterton_base8b | chesterton | 8b | base | 78 | -0.504 | 0.374 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | -0.041 | 0.376 |
| chesterton_base14b | chesterton | 14b | base | 78 | -0.437 | 0.324 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | -0.072 | 0.290 |
| mansfield_base4b | mansfield | 4b | base | 82 | -0.631 | 0.368 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -0.621 | 0.376 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | -0.150 | 0.421 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -0.235 | 0.314 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.051 | 0.355 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | -0.266 | 0.335 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.013 | 0.359 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | -0.210 | 0.347 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.007 | 0.354 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | -0.143 | 0.308 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.034 | 0.366 |
| h_private_base4b | h_private | 4b | base | 46 | -0.617 | 0.280 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | -0.069 | 0.428 |
| chopin_base4b | chopin | 4b | base | 98 | -0.352 | 0.269 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | -0.013 | 0.334 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | -0.589 | 0.335 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.759 | 0.355 |
| cather_base4b | cather | 4b | base | 88 | -0.390 | 0.331 |
| cather_pair4b | cather | 4b | adapter | 88 | -0.471 | 0.279 |
| cather_base14b | cather | 14b | base | 88 | -0.302 | 0.251 |
| cather_base8b | cather | 8b | base | 88 | -0.315 | 0.281 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.335 | 0.404 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.248 | 0.344 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | -0.409 | 0.311 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | -0.445 | 0.381 |
| chesterton_basem14b | chesterton | m14b | base | 78 | -0.361 | 0.363 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | -0.384 | 0.334 |
| chesterton_basem3b | chesterton | m3b | base | 78 | -0.437 | 0.269 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | -0.420 | 0.318 |
| chesterton_basem8b | chesterton | m8b | base | 78 | -0.328 | 0.327 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | -0.314 | 0.340 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | -0.168 | 0.335 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | -0.027 | 0.367 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | -0.079 | 0.396 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | -0.142 | 0.390 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | -0.109 | 0.364 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.608 | 0.441 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | -0.213 | 0.424 |
| chopin_base14b | chopin | 14b | base | 98 | -0.222 | 0.220 |
| chopin_base8b | chopin | 8b | base | 98 | -0.306 | 0.257 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.017 | 0.282 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.059 | 0.325 |
| doctorow_base14b | doctorow | 14b | base | 84 | -0.298 | 0.272 |
| doctorow_base4b | doctorow | 4b | base | 84 | -0.423 | 0.366 |
| doctorow_base8b | doctorow | 8b | base | 84 | -0.310 | 0.351 |
| doctorow_basem14b | doctorow | m14b | base | 84 | -0.222 | 0.309 |
| doctorow_basem3b | doctorow | m3b | base | 84 | -0.264 | 0.324 |
| doctorow_basem8b | doctorow | m8b | base | 84 | -0.167 | 0.260 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.026 | 0.303 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | -0.001 | 0.301 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.037 | 0.371 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.043 | 0.317 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | -0.014 | 0.307 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.016 | 0.313 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.025 | 0.300 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.082 | 0.340 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.052 | 0.295 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.450 | 0.375 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.030 | 0.296 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.059 | 0.329 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.001 | 0.349 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.006 | 0.281 |
| h_private_base14b | h_private | 14b | base | 46 | -0.438 | 0.238 |
| h_private_base8b | h_private | 8b | base | 46 | -0.474 | 0.218 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | -0.256 | 0.392 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | -0.124 | 0.388 |
| link_base14b | link | 14b | base | 32 | -0.440 | 0.265 |
| link_base4b | link | 4b | base | 32 | -0.560 | 0.282 |
| link_base8b | link | 8b | base | 32 | -0.417 | 0.284 |
| link_paire6_14b | link | 14b | adapter | 32 | -0.388 | 0.381 |
| link_paire6_4b | link | 4b | adapter | 32 | -0.358 | 0.344 |
| link_paire6_8b | link | 8b | adapter | 32 | -0.255 | 0.316 |
| mansfield_base14b | mansfield | 14b | base | 82 | -0.554 | 0.293 |
| mansfield_base8b | mansfield | 8b | base | 82 | -0.613 | 0.354 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | -0.087 | 0.468 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | -0.119 | 0.487 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -0.188 | 0.474 |
| patrick_base4b | patrick | 4b | base | 92 | -0.272 | 0.335 |
| patrick_pair4b | patrick | 4b | adapter | 92 | -0.069 | 0.429 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | -0.010 | 0.315 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | -0.067 | 0.323 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | -0.021 | 0.335 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | -0.003 | 0.317 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.048 | 0.408 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.047 | 0.366 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.067 | 0.354 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.362 | 0.305 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -0.052 | 0.324 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.098 | 0.350 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.107 | 0.387 |
| rucker_base14b | rucker | 14b | base | 94 | -0.237 | 0.230 |
| rucker_base4b | rucker | 4b | base | 94 | -0.356 | 0.332 |
| rucker_base8b | rucker | 8b | base | 94 | -0.309 | 0.294 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.003 | 0.271 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.023 | 0.300 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | -0.016 | 0.254 |
| stross_base14b | stross | 14b | base | 82 | -0.224 | 0.278 |
| stross_base4b | stross | 4b | base | 82 | -0.401 | 0.365 |
| stross_base8b | stross | 8b | base | 82 | -0.230 | 0.371 |
| stross_paire6_14b | stross | 14b | adapter | 82 | -0.145 | 0.372 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.141 | 0.410 |
| stross_paire6_8b | stross | 8b | adapter | 82 | -0.135 | 0.353 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | -0.522 | 0.302 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | -0.490 | 0.392 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -0.499 | 0.398 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.572 | 0.374 |
| watts_base14b | watts | 14b | base | 90 | -0.412 | 0.237 |
| watts_base4b | watts | 4b | base | 90 | -0.549 | 0.334 |
| watts_base8b | watts | 8b | base | 90 | -0.480 | 0.300 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.006 | 0.216 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.005 | 0.260 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.016 | 0.260 |
| wharton_base14b | wharton | 14b | base | 88 | -0.373 | 0.400 |
| wharton_base8b | wharton | 8b | base | 88 | -0.445 | 0.409 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | -0.039 | 0.466 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.035 | 0.454 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.041
- chesterton_base4b vs chesterton_base4bc: +0.029
- mansfield_base4b vs mansfield_base4b_r2: +0.009

Base vs adapter, same author and size:

- cather 14b: base -0.302 -> adapter -0.335 (-0.033)
- cather 4b: base -0.390 -> adapter -0.471 (-0.082)
- cather 8b: base -0.315 -> adapter -0.248 (+0.067)
- chesterton 14b: base -0.437 -> adapter -0.072 (+0.365)
- chesterton 4b: base -0.587 -> adapter -0.133 (+0.455)
- chesterton 4bc: base -0.558 -> adapter -0.059 (+0.499)
- chesterton 8b: base -0.504 -> adapter -0.041 (+0.463)
- chesterton m14b: base -0.361 -> adapter -0.168 (+0.194)
- chesterton m3b: base -0.437 -> adapter -0.027 (+0.410)
- chesterton m8b: base -0.328 -> adapter -0.079 (+0.248)
- chopin 14b: base -0.222 -> adapter 0.017 (+0.239)
- chopin 4b: base -0.352 -> adapter -0.013 (+0.339)
- chopin 8b: base -0.306 -> adapter 0.059 (+0.365)
- doctorow 14b: base -0.298 -> adapter 0.026 (+0.324)
- doctorow 4b: base -0.423 -> adapter -0.001 (+0.422)
- doctorow 8b: base -0.310 -> adapter 0.037 (+0.347)
- doctorow m14b: base -0.222 -> adapter 0.043 (+0.265)
- doctorow m3b: base -0.264 -> adapter -0.014 (+0.250)
- doctorow m8b: base -0.167 -> adapter 0.016 (+0.183)
- h_private 14b: base -0.438 -> adapter -0.256 (+0.182)
- h_private 4b: base -0.617 -> adapter -0.069 (+0.548)
- h_private 8b: base -0.474 -> adapter -0.124 (+0.350)
- link 14b: base -0.440 -> adapter -0.388 (+0.051)
- link 4b: base -0.560 -> adapter -0.358 (+0.202)
- link 8b: base -0.417 -> adapter -0.255 (+0.162)
- mansfield 14b: base -0.554 -> adapter -0.087 (+0.467)
- mansfield 4b: base -0.631 -> adapter -0.150 (+0.481)
- mansfield 8b: base -0.613 -> adapter -0.119 (+0.494)
- patrick 4b: base -0.272 -> adapter -0.069 (+0.203)
- patrick_v2 14b: base -0.143 -> adapter 0.034 (+0.177)
- patrick_v2 17b: base -0.235 -> adapter -0.051 (+0.184)
- patrick_v2 4b: base -0.266 -> adapter -0.013 (+0.253)
- patrick_v2 8b: base -0.210 -> adapter 0.007 (+0.218)
- patrick_v2 m14b: base -0.010 -> adapter -0.048 (-0.038)
- patrick_v2 m3b: base -0.067 -> adapter -0.047 (+0.019)
- patrick_v2 m8b: base -0.003 -> adapter -0.067 (-0.064)
- rucker 14b: base -0.237 -> adapter 0.003 (+0.239)
- rucker 4b: base -0.356 -> adapter 0.023 (+0.379)
- rucker 8b: base -0.309 -> adapter -0.016 (+0.294)
- stross 14b: base -0.224 -> adapter -0.145 (+0.079)
- stross 4b: base -0.401 -> adapter -0.141 (+0.259)
- stross 8b: base -0.230 -> adapter -0.135 (+0.095)
- sui_sin_far 14b: base -0.522 -> adapter -0.499 (+0.023)
- sui_sin_far 4b: base -0.589 -> adapter -0.759 (-0.170)
- sui_sin_far 8b: base -0.490 -> adapter -0.572 (-0.082)
- watts 14b: base -0.412 -> adapter 0.006 (+0.418)
- watts 4b: base -0.549 -> adapter -0.005 (+0.544)
- watts 8b: base -0.480 -> adapter 0.016 (+0.496)
- wharton 14b: base -0.373 -> adapter -0.039 (+0.335)
- wharton 4b: base -0.477 -> adapter 0.031 (+0.508)
- wharton 8b: base -0.445 -> adapter 0.035 (+0.479)

## mean_sents_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 6.302 | 14.776 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 3.687 | 9.560 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.032 | 3.090 |
| chesterton_base4b | chesterton | 4b | base | 78 | 18.037 | 23.893 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 14.222 | 23.750 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 1.549 | 7.299 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.488 | 2.334 |
| chesterton_base8b | chesterton | 8b | base | 78 | 9.016 | 15.949 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 1.299 | 4.265 |
| chesterton_base14b | chesterton | 14b | base | 78 | 1.835 | 6.900 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.497 | 2.484 |
| mansfield_base4b | mansfield | 4b | base | 82 | 7.257 | 15.449 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 7.111 | 15.696 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 2.742 | 13.182 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -2.521 | 13.722 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.869 | 12.671 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 4.529 | 18.937 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.855 | 10.353 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | -1.681 | 9.807 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.875 | 8.227 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | -4.742 | 6.468 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | -0.853 | 9.359 |
| h_private_base4b | h_private | 4b | base | 46 | 11.751 | 18.656 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.390 | 4.633 |
| chopin_base4b | chopin | 4b | base | 98 | 8.880 | 15.484 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 3.048 | 9.850 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 9.032 | 16.857 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 11.863 | 11.410 |
| cather_base4b | cather | 4b | base | 88 | 4.363 | 12.431 |
| cather_pair4b | cather | 4b | adapter | 88 | 7.084 | 11.159 |
| cather_base14b | cather | 14b | base | 88 | -0.685 | 2.096 |
| cather_base8b | cather | 8b | base | 88 | 0.561 | 4.782 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 9.914 | 17.069 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 2.563 | 10.884 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 1.501 | 5.810 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 7.724 | 16.262 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 4.142 | 10.519 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 3.145 | 8.441 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 1.678 | 2.351 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 1.564 | 3.308 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 1.123 | 3.988 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.777 | 2.168 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 1.830 | 4.474 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.422 | 2.848 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 1.821 | 5.658 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 1.513 | 6.071 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 1.276 | 5.587 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 14.437 | 17.087 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 2.908 | 7.510 |
| chopin_base14b | chopin | 14b | base | 98 | 1.331 | 1.638 |
| chopin_base8b | chopin | 8b | base | 98 | 4.998 | 11.429 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 2.392 | 6.328 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 1.120 | 2.731 |
| doctorow_base14b | doctorow | 14b | base | 84 | 2.489 | 7.022 |
| doctorow_base4b | doctorow | 4b | base | 84 | 14.548 | 22.549 |
| doctorow_base8b | doctorow | 8b | base | 84 | 6.617 | 13.006 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 4.848 | 7.388 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 2.280 | 1.925 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 1.833 | 1.506 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.204 | 0.912 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.461 | 1.115 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.473 | 1.253 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.659 | 1.299 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.473 | 1.038 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.563 | 0.913 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 1.072 | 1.585 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 1.367 | 6.085 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.369 | 1.032 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 15.693 | 31.073 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.100 | 1.122 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.921 | 1.572 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.701 | 1.794 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.553 | 1.098 |
| h_private_base14b | h_private | 14b | base | 46 | 1.241 | 1.980 |
| h_private_base8b | h_private | 8b | base | 46 | 1.931 | 4.086 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 6.185 | 16.773 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.638 | 4.831 |
| link_base14b | link | 14b | base | 32 | 3.797 | 11.793 |
| link_base4b | link | 4b | base | 32 | 9.347 | 16.238 |
| link_base8b | link | 8b | base | 32 | 1.563 | 3.775 |
| link_paire6_14b | link | 14b | adapter | 32 | 11.709 | 26.976 |
| link_paire6_4b | link | 4b | adapter | 32 | 5.814 | 9.808 |
| link_paire6_8b | link | 8b | adapter | 32 | 1.639 | 6.350 |
| mansfield_base14b | mansfield | 14b | base | 82 | -0.081 | 4.436 |
| mansfield_base8b | mansfield | 8b | base | 82 | 3.512 | 10.759 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 3.610 | 28.319 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 2.101 | 12.447 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 13.571 | 67.898 |
| patrick_base4b | patrick | 4b | base | 92 | 3.810 | 11.599 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 1.358 | 7.766 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | -3.051 | 8.822 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | -4.370 | 6.417 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | -4.682 | 6.778 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | -4.870 | 6.518 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -1.495 | 9.037 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -1.332 | 9.602 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -2.498 | 8.028 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 6.232 | 22.477 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -2.266 | 10.184 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.436 | 12.073 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 2.595 | 10.820 |
| rucker_base14b | rucker | 14b | base | 94 | 1.487 | 8.396 |
| rucker_base4b | rucker | 4b | base | 94 | 12.982 | 22.613 |
| rucker_base8b | rucker | 8b | base | 94 | 9.383 | 20.335 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | -0.028 | 1.699 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.676 | 4.698 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.786 | 5.247 |
| stross_base14b | stross | 14b | base | 82 | 0.662 | 5.025 |
| stross_base4b | stross | 4b | base | 82 | 17.165 | 28.969 |
| stross_base8b | stross | 8b | base | 82 | 4.221 | 11.692 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 7.534 | 16.806 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 10.529 | 21.828 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 6.200 | 18.191 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 2.547 | 2.658 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 4.925 | 11.715 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 9.860 | 16.366 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 3.115 | 6.743 |
| watts_base14b | watts | 14b | base | 90 | 1.635 | 1.041 |
| watts_base4b | watts | 4b | base | 90 | 18.527 | 27.372 |
| watts_base8b | watts | 8b | base | 90 | 8.099 | 15.729 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.249 | 0.876 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.029 | 0.627 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.229 | 0.884 |
| wharton_base14b | wharton | 14b | base | 88 | 0.459 | 1.982 |
| wharton_base8b | wharton | 8b | base | 88 | 3.790 | 9.004 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 1.049 | 4.616 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.472 | 3.539 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -2.615
- chesterton_base4b vs chesterton_base4bc: -3.815
- mansfield_base4b vs mansfield_base4b_r2: -0.146

Base vs adapter, same author and size:

- cather 14b: base -0.685 -> adapter 9.914 (+10.599)
- cather 4b: base 4.363 -> adapter 7.084 (+2.721)
- cather 8b: base 0.561 -> adapter 2.563 (+2.002)
- chesterton 14b: base 1.835 -> adapter 0.497 (-1.338)
- chesterton 4b: base 18.037 -> adapter 1.549 (-16.488)
- chesterton 4bc: base 14.222 -> adapter 0.488 (-13.734)
- chesterton 8b: base 9.016 -> adapter 1.299 (-7.717)
- chesterton m14b: base 4.142 -> adapter 1.830 (-2.313)
- chesterton m3b: base 1.678 -> adapter 0.422 (-1.256)
- chesterton m8b: base 1.123 -> adapter 1.821 (+0.698)
- chopin 14b: base 1.331 -> adapter 2.392 (+1.061)
- chopin 4b: base 8.880 -> adapter 3.048 (-5.832)
- chopin 8b: base 4.998 -> adapter 1.120 (-3.878)
- doctorow 14b: base 2.489 -> adapter 0.204 (-2.285)
- doctorow 4b: base 14.548 -> adapter 0.461 (-14.087)
- doctorow 8b: base 6.617 -> adapter 0.473 (-6.144)
- doctorow m14b: base 4.848 -> adapter 0.659 (-4.188)
- doctorow m3b: base 2.280 -> adapter 0.473 (-1.808)
- doctorow m8b: base 1.833 -> adapter 0.563 (-1.270)
- h_private 14b: base 1.241 -> adapter 6.185 (+4.943)
- h_private 4b: base 11.751 -> adapter 0.390 (-11.361)
- h_private 8b: base 1.931 -> adapter 0.638 (-1.293)
- link 14b: base 3.797 -> adapter 11.709 (+7.911)
- link 4b: base 9.347 -> adapter 5.814 (-3.533)
- link 8b: base 1.563 -> adapter 1.639 (+0.075)
- mansfield 14b: base -0.081 -> adapter 3.610 (+3.691)
- mansfield 4b: base 7.257 -> adapter 2.742 (-4.515)
- mansfield 8b: base 3.512 -> adapter 2.101 (-1.411)
- patrick 4b: base 3.810 -> adapter 1.358 (-2.452)
- patrick_v2 14b: base -4.742 -> adapter -0.853 (+3.889)
- patrick_v2 17b: base -2.521 -> adapter 0.869 (+3.390)
- patrick_v2 4b: base 4.529 -> adapter -0.855 (-5.384)
- patrick_v2 8b: base -1.681 -> adapter -0.875 (+0.806)
- patrick_v2 m14b: base -3.051 -> adapter -1.495 (+1.556)
- patrick_v2 m3b: base -4.370 -> adapter -1.332 (+3.038)
- patrick_v2 m8b: base -4.870 -> adapter -2.498 (+2.372)
- rucker 14b: base 1.487 -> adapter -0.028 (-1.515)
- rucker 4b: base 12.982 -> adapter 0.676 (-12.306)
- rucker 8b: base 9.383 -> adapter 0.786 (-8.596)
- stross 14b: base 0.662 -> adapter 7.534 (+6.872)
- stross 4b: base 17.165 -> adapter 10.529 (-6.636)
- stross 8b: base 4.221 -> adapter 6.200 (+1.978)
- sui_sin_far 14b: base 2.547 -> adapter 9.860 (+7.313)
- sui_sin_far 4b: base 9.032 -> adapter 11.863 (+2.831)
- sui_sin_far 8b: base 4.925 -> adapter 3.115 (-1.810)
- watts 14b: base 1.635 -> adapter 0.249 (-1.387)
- watts 4b: base 18.527 -> adapter 0.029 (-18.498)
- watts 8b: base 8.099 -> adapter 0.229 (-7.870)
- wharton 14b: base 0.459 -> adapter 1.049 (+0.590)
- wharton 4b: base 6.302 -> adapter 0.032 (-6.270)
- wharton 8b: base 3.790 -> adapter 0.472 (-3.318)

## psd_z

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 2.096 | 2.462 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 1.644 | 1.585 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 1.113 | 0.657 |
| chesterton_base4b | chesterton | 4b | base | 78 | 4.496 | 4.322 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 3.804 | 4.229 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 1.288 | 1.361 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 1.150 | 0.642 |
| chesterton_base8b | chesterton | 8b | base | 78 | 2.990 | 3.164 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 1.270 | 0.812 |
| chesterton_base14b | chesterton | 14b | base | 78 | 1.710 | 1.491 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 1.034 | 0.525 |
| mansfield_base4b | mansfield | 4b | base | 82 | 1.991 | 1.415 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 1.959 | 1.481 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 1.233 | 1.391 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 1.081 | 0.729 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 1.026 | 0.732 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 1.384 | 1.099 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 1.073 | 0.630 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 1.069 | 0.692 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.981 | 0.594 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.870 | 0.527 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.968 | 0.631 |
| h_private_base4b | h_private | 4b | base | 46 | 5.361 | 5.458 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 1.825 | 1.459 |
| chopin_base4b | chopin | 4b | base | 98 | 4.396 | 5.478 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 2.310 | 3.375 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 3.782 | 4.746 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 4.815 | 3.200 |
| cather_base4b | cather | 4b | base | 88 | 2.041 | 2.040 |
| cather_pair4b | cather | 4b | adapter | 88 | 2.518 | 1.746 |
| cather_base14b | cather | 14b | base | 88 | 1.176 | 0.481 |
| cather_base8b | cather | 8b | base | 88 | 1.415 | 0.908 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 2.813 | 2.746 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 1.724 | 1.822 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 1.595 | 1.249 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 2.693 | 3.144 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 1.969 | 2.269 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 1.771 | 1.761 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 1.512 | 0.637 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 1.505 | 0.852 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 1.382 | 0.978 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 1.328 | 0.643 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 1.383 | 0.997 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 1.184 | 0.665 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 1.349 | 1.185 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 1.327 | 1.251 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 1.185 | 1.168 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 3.935 | 3.006 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 1.669 | 1.405 |
| chopin_base14b | chopin | 14b | base | 98 | 1.683 | 0.774 |
| chopin_base8b | chopin | 8b | base | 98 | 3.022 | 4.164 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 1.933 | 2.497 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 1.724 | 0.948 |
| doctorow_base14b | doctorow | 14b | base | 84 | 2.046 | 3.152 |
| doctorow_base4b | doctorow | 4b | base | 84 | 7.221 | 9.754 |
| doctorow_base8b | doctorow | 8b | base | 84 | 3.831 | 5.739 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 3.070 | 3.523 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 2.035 | 1.236 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 1.636 | 0.885 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 1.051 | 0.500 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 1.168 | 0.635 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 1.118 | 0.665 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 1.130 | 0.583 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 1.126 | 0.576 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 1.109 | 0.519 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 1.359 | 0.742 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 1.543 | 2.500 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 1.088 | 0.534 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 7.938 | 12.594 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 1.082 | 0.554 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 1.406 | 0.733 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 1.389 | 0.755 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 1.074 | 0.562 |
| h_private_base14b | h_private | 14b | base | 46 | 2.099 | 0.894 |
| h_private_base8b | h_private | 8b | base | 46 | 2.443 | 1.411 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 3.308 | 4.759 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 1.799 | 1.538 |
| link_base14b | link | 14b | base | 32 | 2.635 | 3.040 |
| link_base4b | link | 4b | base | 32 | 4.178 | 3.777 |
| link_base8b | link | 8b | base | 32 | 2.021 | 1.292 |
| link_paire6_14b | link | 14b | adapter | 32 | 4.656 | 6.353 |
| link_paire6_4b | link | 4b | adapter | 32 | 2.961 | 2.563 |
| link_paire6_8b | link | 8b | adapter | 32 | 2.200 | 1.406 |
| mansfield_base14b | mansfield | 14b | base | 82 | 1.346 | 0.487 |
| mansfield_base8b | mansfield | 8b | base | 82 | 1.696 | 1.073 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 1.392 | 2.770 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 1.220 | 1.336 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 2.058 | 4.801 |
| patrick_base4b | patrick | 4b | base | 92 | 1.611 | 1.278 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 1.263 | 0.856 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.985 | 0.694 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.932 | 0.500 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.924 | 0.603 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.888 | 0.600 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 1.065 | 0.687 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.989 | 0.659 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.975 | 0.605 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 1.436 | 1.145 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.917 | 0.673 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 1.049 | 0.719 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 1.106 | 0.631 |
| rucker_base14b | rucker | 14b | base | 94 | 1.703 | 2.127 |
| rucker_base4b | rucker | 4b | base | 94 | 4.397 | 5.396 |
| rucker_base8b | rucker | 8b | base | 94 | 3.648 | 5.191 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 1.151 | 0.532 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 1.373 | 1.266 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 1.346 | 1.906 |
| stross_base14b | stross | 14b | base | 82 | 1.428 | 1.234 |
| stross_base4b | stross | 4b | base | 82 | 5.736 | 7.603 |
| stross_base8b | stross | 8b | base | 82 | 2.496 | 3.118 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 2.838 | 4.213 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 3.642 | 5.496 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 2.604 | 4.587 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 1.924 | 0.842 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 2.546 | 3.263 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 4.018 | 4.344 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 2.390 | 1.877 |
| watts_base14b | watts | 14b | base | 90 | 2.379 | 0.971 |
| watts_base4b | watts | 4b | base | 90 | 11.048 | 14.111 |
| watts_base8b | watts | 8b | base | 90 | 5.833 | 8.309 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 1.157 | 0.574 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 1.010 | 0.496 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 1.145 | 0.553 |
| wharton_base14b | wharton | 14b | base | 88 | 1.116 | 0.564 |
| wharton_base8b | wharton | 8b | base | 88 | 1.661 | 1.566 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 1.131 | 0.736 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 1.066 | 0.599 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -0.453
- chesterton_base4b vs chesterton_base4bc: -0.691
- mansfield_base4b vs mansfield_base4b_r2: -0.031

Base vs adapter, same author and size:

- cather 14b: base 1.176 -> adapter 2.813 (+1.637)
- cather 4b: base 2.041 -> adapter 2.518 (+0.477)
- cather 8b: base 1.415 -> adapter 1.724 (+0.309)
- chesterton 14b: base 1.710 -> adapter 1.034 (-0.676)
- chesterton 4b: base 4.496 -> adapter 1.288 (-3.207)
- chesterton 4bc: base 3.804 -> adapter 1.150 (-2.655)
- chesterton 8b: base 2.990 -> adapter 1.270 (-1.720)
- chesterton m14b: base 1.969 -> adapter 1.383 (-0.586)
- chesterton m3b: base 1.512 -> adapter 1.184 (-0.329)
- chesterton m8b: base 1.382 -> adapter 1.349 (-0.033)
- chopin 14b: base 1.683 -> adapter 1.933 (+0.250)
- chopin 4b: base 4.396 -> adapter 2.310 (-2.086)
- chopin 8b: base 3.022 -> adapter 1.724 (-1.297)
- doctorow 14b: base 2.046 -> adapter 1.051 (-0.995)
- doctorow 4b: base 7.221 -> adapter 1.168 (-6.053)
- doctorow 8b: base 3.831 -> adapter 1.118 (-2.713)
- doctorow m14b: base 3.070 -> adapter 1.130 (-1.939)
- doctorow m3b: base 2.035 -> adapter 1.126 (-0.909)
- doctorow m8b: base 1.636 -> adapter 1.109 (-0.528)
- h_private 14b: base 2.099 -> adapter 3.308 (+1.210)
- h_private 4b: base 5.361 -> adapter 1.825 (-3.536)
- h_private 8b: base 2.443 -> adapter 1.799 (-0.644)
- link 14b: base 2.635 -> adapter 4.656 (+2.021)
- link 4b: base 4.178 -> adapter 2.961 (-1.217)
- link 8b: base 2.021 -> adapter 2.200 (+0.179)
- mansfield 14b: base 1.346 -> adapter 1.392 (+0.046)
- mansfield 4b: base 1.991 -> adapter 1.233 (-0.757)
- mansfield 8b: base 1.696 -> adapter 1.220 (-0.476)
- patrick 4b: base 1.611 -> adapter 1.263 (-0.348)
- patrick_v2 14b: base 0.870 -> adapter 0.968 (+0.098)
- patrick_v2 17b: base 1.081 -> adapter 1.026 (-0.055)
- patrick_v2 4b: base 1.384 -> adapter 1.073 (-0.311)
- patrick_v2 8b: base 1.069 -> adapter 0.981 (-0.089)
- patrick_v2 m14b: base 0.985 -> adapter 1.065 (+0.080)
- patrick_v2 m3b: base 0.932 -> adapter 0.989 (+0.057)
- patrick_v2 m8b: base 0.888 -> adapter 0.975 (+0.088)
- rucker 14b: base 1.703 -> adapter 1.151 (-0.552)
- rucker 4b: base 4.397 -> adapter 1.373 (-3.024)
- rucker 8b: base 3.648 -> adapter 1.346 (-2.302)
- stross 14b: base 1.428 -> adapter 2.838 (+1.409)
- stross 4b: base 5.736 -> adapter 3.642 (-2.094)
- stross 8b: base 2.496 -> adapter 2.604 (+0.108)
- sui_sin_far 14b: base 1.924 -> adapter 4.018 (+2.094)
- sui_sin_far 4b: base 3.782 -> adapter 4.815 (+1.033)
- sui_sin_far 8b: base 2.546 -> adapter 2.390 (-0.156)
- watts 14b: base 2.379 -> adapter 1.157 (-1.223)
- watts 4b: base 11.048 -> adapter 1.010 (-10.037)
- watts 8b: base 5.833 -> adapter 1.145 (-4.687)
- wharton 14b: base 1.116 -> adapter 1.131 (+0.014)
- wharton 4b: base 2.096 -> adapter 1.113 (-0.984)
- wharton 8b: base 1.661 -> adapter 1.066 (-0.595)

## w1_logpara

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 0.992 | 0.880 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 0.883 | 0.755 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.748 | 0.491 |
| chesterton_base4b | chesterton | 4b | base | 78 | 1.477 | 1.020 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 1.328 | 0.912 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.582 | 0.464 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.553 | 0.378 |
| chesterton_base8b | chesterton | 8b | base | 78 | 1.133 | 0.882 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.605 | 0.448 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.760 | 0.558 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.545 | 0.374 |
| mansfield_base4b | mansfield | 4b | base | 82 | 1.434 | 1.010 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 1.440 | 0.916 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.801 | 0.706 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.773 | 0.477 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.769 | 0.476 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.946 | 0.691 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 0.865 | 0.523 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.830 | 0.587 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.743 | 0.457 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.780 | 0.434 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.739 | 0.487 |
| h_private_base4b | h_private | 4b | base | 46 | 1.549 | 0.980 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.976 | 0.546 |
| chopin_base4b | chopin | 4b | base | 98 | 1.162 | 0.865 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.709 | 0.554 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 1.361 | 0.962 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 1.939 | 1.076 |
| cather_base4b | cather | 4b | base | 88 | 0.857 | 0.682 |
| cather_pair4b | cather | 4b | adapter | 88 | 1.121 | 0.637 |
| cather_base14b | cather | 14b | base | 88 | 0.525 | 0.262 |
| cather_base8b | cather | 8b | base | 88 | 0.556 | 0.344 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 1.200 | 0.890 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.896 | 0.682 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.735 | 0.477 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 1.037 | 0.826 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.846 | 0.682 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.816 | 0.542 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.721 | 0.341 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.749 | 0.445 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.699 | 0.403 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.696 | 0.413 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.671 | 0.517 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.616 | 0.422 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.624 | 0.492 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.682 | 0.548 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.650 | 0.577 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 1.639 | 1.003 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.830 | 0.669 |
| chopin_base14b | chopin | 14b | base | 98 | 0.610 | 0.323 |
| chopin_base8b | chopin | 8b | base | 98 | 0.942 | 0.642 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.589 | 0.447 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.669 | 0.410 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.721 | 0.473 |
| doctorow_base4b | doctorow | 4b | base | 84 | 1.498 | 1.151 |
| doctorow_base8b | doctorow | 8b | base | 84 | 1.098 | 0.797 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.967 | 0.710 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.839 | 0.556 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.626 | 0.381 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.521 | 0.277 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.541 | 0.291 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.512 | 0.297 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.543 | 0.321 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.544 | 0.305 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.530 | 0.312 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 0.618 | 0.394 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.633 | 0.451 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.533 | 0.303 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 1.723 | 1.025 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.556 | 0.298 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 0.596 | 0.427 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 0.675 | 0.446 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.491 | 0.276 |
| h_private_base14b | h_private | 14b | base | 46 | 0.878 | 0.473 |
| h_private_base8b | h_private | 8b | base | 46 | 0.988 | 0.556 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 1.125 | 0.901 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.884 | 0.542 |
| link_base14b | link | 14b | base | 32 | 1.071 | 0.786 |
| link_base4b | link | 4b | base | 32 | 1.528 | 0.902 |
| link_base8b | link | 8b | base | 32 | 1.127 | 0.652 |
| link_paire6_14b | link | 14b | adapter | 32 | 1.578 | 1.211 |
| link_paire6_4b | link | 4b | adapter | 32 | 1.112 | 0.731 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.944 | 0.460 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.910 | 0.437 |
| mansfield_base8b | mansfield | 8b | base | 82 | 1.318 | 0.799 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.755 | 0.566 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.800 | 0.678 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.918 | 0.818 |
| patrick_base4b | patrick | 4b | base | 92 | 0.846 | 0.546 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.709 | 0.520 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.768 | 0.555 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.810 | 0.489 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.886 | 0.574 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.910 | 0.610 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 0.837 | 0.543 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 0.765 | 0.574 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 0.824 | 0.506 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.999 | 0.659 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.776 | 0.452 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.865 | 0.524 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.879 | 0.579 |
| rucker_base14b | rucker | 14b | base | 94 | 0.642 | 0.529 |
| rucker_base4b | rucker | 4b | base | 94 | 1.268 | 1.008 |
| rucker_base8b | rucker | 8b | base | 94 | 1.054 | 0.835 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.465 | 0.253 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.569 | 0.330 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.459 | 0.323 |
| stross_base14b | stross | 14b | base | 82 | 0.547 | 0.366 |
| stross_base4b | stross | 4b | base | 82 | 1.267 | 1.018 |
| stross_base8b | stross | 8b | base | 82 | 0.839 | 0.636 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.820 | 0.642 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 0.971 | 0.746 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.741 | 0.630 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.913 | 0.525 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 1.111 | 0.818 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 1.488 | 1.024 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 1.328 | 0.927 |
| watts_base14b | watts | 14b | base | 90 | 0.884 | 0.388 |
| watts_base4b | watts | 4b | base | 90 | 1.753 | 1.274 |
| watts_base8b | watts | 8b | base | 90 | 1.406 | 0.987 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.410 | 0.245 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 0.403 | 0.212 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.427 | 0.234 |
| wharton_base14b | wharton | 14b | base | 88 | 0.617 | 0.397 |
| wharton_base8b | wharton | 8b | base | 88 | 0.889 | 0.760 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.638 | 0.477 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.669 | 0.457 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -0.109
- chesterton_base4b vs chesterton_base4bc: -0.149
- mansfield_base4b vs mansfield_base4b_r2: +0.006

Base vs adapter, same author and size:

- cather 14b: base 0.525 -> adapter 1.200 (+0.676)
- cather 4b: base 0.857 -> adapter 1.121 (+0.264)
- cather 8b: base 0.556 -> adapter 0.896 (+0.339)
- chesterton 14b: base 0.760 -> adapter 0.545 (-0.214)
- chesterton 4b: base 1.477 -> adapter 0.582 (-0.895)
- chesterton 4bc: base 1.328 -> adapter 0.553 (-0.775)
- chesterton 8b: base 1.133 -> adapter 0.605 (-0.528)
- chesterton m14b: base 0.846 -> adapter 0.671 (-0.176)
- chesterton m3b: base 0.721 -> adapter 0.616 (-0.105)
- chesterton m8b: base 0.699 -> adapter 0.624 (-0.074)
- chopin 14b: base 0.610 -> adapter 0.589 (-0.021)
- chopin 4b: base 1.162 -> adapter 0.709 (-0.453)
- chopin 8b: base 0.942 -> adapter 0.669 (-0.273)
- doctorow 14b: base 0.721 -> adapter 0.521 (-0.200)
- doctorow 4b: base 1.498 -> adapter 0.541 (-0.957)
- doctorow 8b: base 1.098 -> adapter 0.512 (-0.585)
- doctorow m14b: base 0.967 -> adapter 0.543 (-0.424)
- doctorow m3b: base 0.839 -> adapter 0.544 (-0.295)
- doctorow m8b: base 0.626 -> adapter 0.530 (-0.096)
- h_private 14b: base 0.878 -> adapter 1.125 (+0.247)
- h_private 4b: base 1.549 -> adapter 0.976 (-0.573)
- h_private 8b: base 0.988 -> adapter 0.884 (-0.104)
- link 14b: base 1.071 -> adapter 1.578 (+0.508)
- link 4b: base 1.528 -> adapter 1.112 (-0.416)
- link 8b: base 1.127 -> adapter 0.944 (-0.183)
- mansfield 14b: base 0.910 -> adapter 0.755 (-0.155)
- mansfield 4b: base 1.434 -> adapter 0.801 (-0.632)
- mansfield 8b: base 1.318 -> adapter 0.800 (-0.518)
- patrick 4b: base 0.846 -> adapter 0.709 (-0.138)
- patrick_v2 14b: base 0.780 -> adapter 0.739 (-0.040)
- patrick_v2 17b: base 0.773 -> adapter 0.769 (-0.004)
- patrick_v2 4b: base 0.946 -> adapter 0.865 (-0.081)
- patrick_v2 8b: base 0.830 -> adapter 0.743 (-0.086)
- patrick_v2 m14b: base 0.768 -> adapter 0.837 (+0.069)
- patrick_v2 m3b: base 0.810 -> adapter 0.765 (-0.044)
- patrick_v2 m8b: base 0.910 -> adapter 0.824 (-0.087)
- rucker 14b: base 0.642 -> adapter 0.465 (-0.176)
- rucker 4b: base 1.268 -> adapter 0.569 (-0.699)
- rucker 8b: base 1.054 -> adapter 0.459 (-0.595)
- stross 14b: base 0.547 -> adapter 0.820 (+0.273)
- stross 4b: base 1.267 -> adapter 0.971 (-0.296)
- stross 8b: base 0.839 -> adapter 0.741 (-0.098)
- sui_sin_far 14b: base 0.913 -> adapter 1.488 (+0.575)
- sui_sin_far 4b: base 1.361 -> adapter 1.939 (+0.578)
- sui_sin_far 8b: base 1.111 -> adapter 1.328 (+0.217)
- watts 14b: base 0.884 -> adapter 0.410 (-0.474)
- watts 4b: base 1.753 -> adapter 0.403 (-1.350)
- watts 8b: base 1.406 -> adapter 0.427 (-0.979)
- wharton 14b: base 0.617 -> adapter 0.638 (+0.021)
- wharton 4b: base 0.992 -> adapter 0.748 (-0.244)
- wharton 8b: base 0.889 -> adapter 0.669 (-0.220)

