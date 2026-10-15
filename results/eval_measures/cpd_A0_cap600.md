# cpd (arm A0, first 600 words; paired distance to the source passage; glyph fold on)

## burst_an_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | -0.124 | 0.146 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.119 | 0.140 |
| pair_e6_4b | wharton | 4b | adapter | 88 | -0.003 | 0.130 |
| chesterton_base4b | chesterton | 4b | base | 78 | -0.079 | 0.137 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | -0.066 | 0.135 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | -0.016 | 0.116 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | -0.004 | 0.131 |
| chesterton_base8b | chesterton | 8b | base | 78 | -0.064 | 0.128 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | -0.031 | 0.112 |
| chesterton_base14b | chesterton | 14b | base | 78 | -0.029 | 0.115 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | -0.045 | 0.109 |
| mansfield_base4b | mansfield | 4b | base | 82 | -0.252 | 0.137 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -0.244 | 0.132 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | -0.026 | 0.127 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -0.114 | 0.139 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.013 | 0.140 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | -0.018 | 0.153 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.027 | 0.126 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | -0.063 | 0.160 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.020 | 0.138 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.014 | 0.134 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | -0.024 | 0.139 |
| h_private_base4b | h_private | 4b | base | 46 | -0.305 | 0.133 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | -0.117 | 0.134 |
| chopin_base4b | chopin | 4b | base | 98 | -0.115 | 0.129 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.018 | 0.116 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | -0.214 | 0.137 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.272 | 0.177 |
| cather_base4b | cather | 4b | base | 88 | -0.106 | 0.142 |
| cather_pair4b | cather | 4b | adapter | 88 | -0.128 | 0.244 |
| cather_base14b | cather | 14b | base | 88 | -0.073 | 0.121 |
| cather_base8b | cather | 8b | base | 88 | -0.120 | 0.126 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.049 | 0.179 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.034 | 0.195 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | -0.014 | 0.120 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | -0.054 | 0.112 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.080 | 0.118 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.070 | 0.125 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.033 | 0.107 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.032 | 0.115 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.074 | 0.121 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.086 | 0.128 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | -0.026 | 0.117 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.009 | 0.132 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | -0.004 | 0.114 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.012 | 0.144 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | -0.027 | 0.119 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.072 | 0.181 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.006 | 0.134 |
| chopin_base14b | chopin | 14b | base | 98 | -0.073 | 0.119 |
| chopin_base8b | chopin | 8b | base | 98 | -0.138 | 0.111 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.043 | 0.113 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.039 | 0.139 |
| doctorow_base14b | doctorow | 14b | base | 84 | -0.119 | 0.138 |
| doctorow_base4b | doctorow | 4b | base | 84 | -0.173 | 0.167 |
| doctorow_base8b | doctorow | 8b | base | 84 | -0.184 | 0.135 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.011 | 0.149 |
| doctorow_basem3b | doctorow | m3b | base | 84 | -0.036 | 0.139 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.003 | 0.133 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.031 | 0.143 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.020 | 0.144 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.030 | 0.181 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.033 | 0.137 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.010 | 0.126 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.001 | 0.140 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.020 | 0.151 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.025 | 0.144 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.040 | 0.150 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.221 | 0.193 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.030 | 0.129 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.048 | 0.159 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.019 | 0.161 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.018 | 0.141 |
| h_private_base14b | h_private | 14b | base | 46 | -0.266 | 0.139 |
| h_private_base8b | h_private | 8b | base | 46 | -0.324 | 0.159 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | -0.067 | 0.165 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | -0.110 | 0.248 |
| link_base14b | link | 14b | base | 32 | -0.170 | 0.143 |
| link_base4b | link | 4b | base | 32 | -0.238 | 0.170 |
| link_base8b | link | 8b | base | 32 | -0.228 | 0.155 |
| link_paire6_14b | link | 14b | adapter | 32 | -0.109 | 0.203 |
| link_paire6_4b | link | 4b | adapter | 32 | -0.168 | 0.192 |
| link_paire6_8b | link | 8b | adapter | 32 | -0.202 | 0.134 |
| mansfield_base14b | mansfield | 14b | base | 82 | -0.188 | 0.123 |
| mansfield_base8b | mansfield | 8b | base | 82 | -0.281 | 0.151 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | -0.015 | 0.134 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | -0.031 | 0.136 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -0.039 | 0.157 |
| patrick_base4b | patrick | 4b | base | 92 | -0.005 | 0.178 |
| patrick_pair4b | patrick | 4b | adapter | 92 | -0.010 | 0.186 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.162 | 0.139 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.118 | 0.144 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.129 | 0.143 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.156 | 0.136 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.053 | 0.148 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.037 | 0.137 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.037 | 0.135 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.154 | 0.195 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -0.024 | 0.127 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.019 | 0.143 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.021 | 0.197 |
| rucker_base14b | rucker | 14b | base | 94 | -0.075 | 0.142 |
| rucker_base4b | rucker | 4b | base | 94 | -0.101 | 0.160 |
| rucker_base8b | rucker | 8b | base | 94 | -0.095 | 0.148 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | -0.058 | 0.119 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | -0.058 | 0.129 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | -0.052 | 0.129 |
| stross_base14b | stross | 14b | base | 82 | -0.132 | 0.125 |
| stross_base4b | stross | 4b | base | 82 | -0.168 | 0.129 |
| stross_base8b | stross | 8b | base | 82 | -0.152 | 0.145 |
| stross_paire6_14b | stross | 14b | adapter | 82 | -0.061 | 0.128 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.058 | 0.131 |
| stross_paire6_8b | stross | 8b | adapter | 82 | -0.040 | 0.131 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | -0.158 | 0.098 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | -0.197 | 0.138 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -0.246 | 0.152 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.312 | 0.154 |
| watts_base14b | watts | 14b | base | 90 | -0.117 | 0.099 |
| watts_base4b | watts | 4b | base | 90 | -0.109 | 0.113 |
| watts_base8b | watts | 8b | base | 90 | -0.150 | 0.110 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 0.006 | 0.099 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.015 | 0.100 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.004 | 0.096 |
| wharton_base14b | wharton | 14b | base | 88 | -0.089 | 0.140 |
| wharton_base8b | wharton | 8b | base | 88 | -0.159 | 0.129 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | -0.019 | 0.136 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | -0.011 | 0.117 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.005
- chesterton_base4b vs chesterton_base4bc: +0.012
- mansfield_base4b vs mansfield_base4b_r2: +0.008

Base vs adapter, same author and size:

- cather 14b: base -0.073 -> adapter -0.049 (+0.023)
- cather 4b: base -0.106 -> adapter -0.128 (-0.022)
- cather 8b: base -0.120 -> adapter -0.034 (+0.086)
- chesterton 14b: base -0.029 -> adapter -0.045 (-0.017)
- chesterton 4b: base -0.079 -> adapter -0.016 (+0.063)
- chesterton 4bc: base -0.066 -> adapter -0.004 (+0.063)
- chesterton 8b: base -0.064 -> adapter -0.031 (+0.033)
- chesterton m14b: base 0.080 -> adapter -0.026 (-0.107)
- chesterton m3b: base 0.033 -> adapter 0.009 (-0.024)
- chesterton m8b: base 0.074 -> adapter -0.004 (-0.078)
- chopin 14b: base -0.073 -> adapter 0.043 (+0.116)
- chopin 4b: base -0.115 -> adapter 0.018 (+0.133)
- chopin 8b: base -0.138 -> adapter 0.039 (+0.177)
- doctorow 14b: base -0.119 -> adapter 0.031 (+0.149)
- doctorow 4b: base -0.173 -> adapter 0.020 (+0.193)
- doctorow 8b: base -0.184 -> adapter 0.030 (+0.214)
- doctorow m14b: base 0.011 -> adapter 0.033 (+0.022)
- doctorow m3b: base -0.036 -> adapter 0.010 (+0.046)
- doctorow m8b: base 0.003 -> adapter 0.001 (-0.002)
- h_private 14b: base -0.266 -> adapter -0.067 (+0.199)
- h_private 4b: base -0.305 -> adapter -0.117 (+0.189)
- h_private 8b: base -0.324 -> adapter -0.110 (+0.215)
- link 14b: base -0.170 -> adapter -0.109 (+0.061)
- link 4b: base -0.238 -> adapter -0.168 (+0.070)
- link 8b: base -0.228 -> adapter -0.202 (+0.025)
- mansfield 14b: base -0.188 -> adapter -0.015 (+0.173)
- mansfield 4b: base -0.252 -> adapter -0.026 (+0.225)
- mansfield 8b: base -0.281 -> adapter -0.031 (+0.250)
- patrick 4b: base -0.005 -> adapter -0.010 (-0.005)
- patrick_v2 14b: base 0.014 -> adapter -0.024 (-0.038)
- patrick_v2 17b: base -0.114 -> adapter -0.013 (+0.101)
- patrick_v2 4b: base -0.018 -> adapter -0.027 (-0.009)
- patrick_v2 8b: base -0.063 -> adapter -0.020 (+0.043)
- patrick_v2 m14b: base 0.162 -> adapter -0.053 (-0.215)
- patrick_v2 m3b: base 0.118 -> adapter -0.037 (-0.155)
- patrick_v2 m8b: base 0.156 -> adapter -0.037 (-0.193)
- rucker 14b: base -0.075 -> adapter -0.058 (+0.018)
- rucker 4b: base -0.101 -> adapter -0.058 (+0.043)
- rucker 8b: base -0.095 -> adapter -0.052 (+0.042)
- stross 14b: base -0.132 -> adapter -0.061 (+0.070)
- stross 4b: base -0.168 -> adapter -0.058 (+0.110)
- stross 8b: base -0.152 -> adapter -0.040 (+0.112)
- sui_sin_far 14b: base -0.158 -> adapter -0.246 (-0.088)
- sui_sin_far 4b: base -0.214 -> adapter -0.272 (-0.058)
- sui_sin_far 8b: base -0.197 -> adapter -0.312 (-0.115)
- watts 14b: base -0.117 -> adapter 0.006 (+0.123)
- watts 4b: base -0.109 -> adapter -0.015 (+0.094)
- watts 8b: base -0.150 -> adapter 0.004 (+0.153)
- wharton 14b: base -0.089 -> adapter -0.019 (+0.070)
- wharton 4b: base -0.124 -> adapter -0.003 (+0.121)
- wharton 8b: base -0.159 -> adapter -0.011 (+0.148)

## cpd_z

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 1.057 | 0.451 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | 1.071 | 0.465 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.999 | 0.377 |
| chesterton_base4b | chesterton | 4b | base | 78 | 1.153 | 0.440 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 1.143 | 0.445 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 1.049 | 0.377 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 1.109 | 0.405 |
| chesterton_base8b | chesterton | 8b | base | 78 | 1.099 | 0.371 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.991 | 0.347 |
| chesterton_base14b | chesterton | 14b | base | 78 | 1.025 | 0.368 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 1.057 | 0.419 |
| mansfield_base4b | mansfield | 4b | base | 82 | 1.636 | 0.524 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 1.663 | 0.480 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 1.108 | 0.385 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 1.259 | 0.511 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 1.048 | 0.399 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 1.194 | 0.412 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | 1.014 | 0.439 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 1.196 | 0.456 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 1.109 | 0.359 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 1.126 | 0.442 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 1.117 | 0.553 |
| h_private_base4b | h_private | 4b | base | 46 | 1.771 | 0.593 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 1.419 | 0.519 |
| chopin_base4b | chopin | 4b | base | 98 | 1.353 | 0.479 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 1.194 | 0.551 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 1.419 | 0.531 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | 1.687 | 0.597 |
| cather_base4b | cather | 4b | base | 88 | 1.219 | 0.476 |
| cather_pair4b | cather | 4b | adapter | 88 | 1.420 | 0.684 |
| cather_base14b | cather | 14b | base | 88 | 1.131 | 0.376 |
| cather_base8b | cather | 8b | base | 88 | 1.212 | 0.421 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 1.506 | 1.157 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 1.277 | 0.532 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 1.109 | 0.380 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 1.120 | 0.380 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 1.190 | 0.420 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 1.198 | 0.488 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 1.089 | 0.448 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 1.083 | 0.451 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 1.117 | 0.420 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 1.169 | 0.529 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 1.016 | 0.401 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 1.120 | 0.471 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 1.111 | 0.553 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 1.056 | 0.430 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 1.026 | 0.365 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 1.329 | 0.604 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 1.057 | 0.463 |
| chopin_base14b | chopin | 14b | base | 98 | 1.227 | 0.472 |
| chopin_base8b | chopin | 8b | base | 98 | 1.348 | 0.480 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 1.186 | 0.574 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 1.269 | 0.532 |
| doctorow_base14b | doctorow | 14b | base | 84 | 1.115 | 0.430 |
| doctorow_base4b | doctorow | 4b | base | 84 | 1.293 | 0.545 |
| doctorow_base8b | doctorow | 8b | base | 84 | 1.288 | 0.426 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 1.156 | 0.400 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 1.092 | 0.397 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 1.103 | 0.542 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 1.027 | 0.374 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 1.129 | 0.441 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 1.112 | 0.650 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.992 | 0.406 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 1.086 | 0.551 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 1.039 | 0.422 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | 1.115 | 0.419 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 1.098 | 0.591 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 1.134 | 0.567 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 1.551 | 0.611 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 1.110 | 0.437 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | 1.153 | 0.440 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | 1.125 | 0.590 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 1.055 | 0.472 |
| h_private_base14b | h_private | 14b | base | 46 | 1.785 | 0.701 |
| h_private_base8b | h_private | 8b | base | 46 | 1.966 | 0.562 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 1.560 | 0.760 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 1.556 | 0.488 |
| link_base14b | link | 14b | base | 32 | 1.573 | 0.420 |
| link_base4b | link | 4b | base | 32 | 1.951 | 0.983 |
| link_base8b | link | 8b | base | 32 | 1.834 | 0.449 |
| link_paire6_14b | link | 14b | adapter | 32 | 1.774 | 0.862 |
| link_paire6_4b | link | 4b | adapter | 32 | 1.639 | 0.545 |
| link_paire6_8b | link | 8b | adapter | 32 | 1.657 | 0.636 |
| mansfield_base14b | mansfield | 14b | base | 82 | 1.421 | 0.464 |
| mansfield_base8b | mansfield | 8b | base | 82 | 1.679 | 0.577 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 1.166 | 0.439 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 1.193 | 0.596 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 1.133 | 0.511 |
| patrick_base4b | patrick | 4b | base | 92 | 1.041 | 0.408 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 1.045 | 0.533 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 1.684 | 0.652 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 1.439 | 0.685 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 1.477 | 0.568 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 1.572 | 0.597 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | 1.095 | 0.389 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | 1.037 | 0.498 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | 1.067 | 0.399 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 1.443 | 0.710 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 1.075 | 0.404 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 1.057 | 0.383 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 1.596 | 4.938 |
| rucker_base14b | rucker | 14b | base | 94 | 1.167 | 0.489 |
| rucker_base4b | rucker | 4b | base | 94 | 1.294 | 0.567 |
| rucker_base8b | rucker | 8b | base | 94 | 1.220 | 0.540 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 1.055 | 0.417 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 1.135 | 0.632 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 1.066 | 0.518 |
| stross_base14b | stross | 14b | base | 82 | 1.099 | 0.385 |
| stross_base4b | stross | 4b | base | 82 | 1.240 | 0.433 |
| stross_base8b | stross | 8b | base | 82 | 1.199 | 0.370 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.994 | 0.354 |
| stross_paire6_4b | stross | 4b | adapter | 82 | 1.007 | 0.364 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 1.011 | 0.362 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 1.228 | 0.398 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 1.448 | 0.398 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 1.703 | 0.613 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | 1.679 | 0.549 |
| watts_base14b | watts | 14b | base | 90 | 1.284 | 0.464 |
| watts_base4b | watts | 4b | base | 90 | 1.298 | 0.480 |
| watts_base8b | watts | 8b | base | 90 | 1.411 | 0.499 |
| watts_paire6_14b | watts | 14b | adapter | 90 | 1.108 | 0.432 |
| watts_paire6_4b | watts | 4b | adapter | 90 | 1.082 | 0.380 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 1.057 | 0.411 |
| wharton_base14b | wharton | 14b | base | 88 | 1.064 | 0.415 |
| wharton_base8b | wharton | 8b | base | 88 | 1.135 | 0.454 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.978 | 0.473 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.941 | 0.371 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.013
- chesterton_base4b vs chesterton_base4bc: -0.010
- mansfield_base4b vs mansfield_base4b_r2: +0.027

Base vs adapter, same author and size:

- cather 14b: base 1.131 -> adapter 1.506 (+0.375)
- cather 4b: base 1.219 -> adapter 1.420 (+0.201)
- cather 8b: base 1.212 -> adapter 1.277 (+0.064)
- chesterton 14b: base 1.025 -> adapter 1.057 (+0.032)
- chesterton 4b: base 1.153 -> adapter 1.049 (-0.104)
- chesterton 4bc: base 1.143 -> adapter 1.109 (-0.035)
- chesterton 8b: base 1.099 -> adapter 0.991 (-0.108)
- chesterton m14b: base 1.190 -> adapter 1.016 (-0.174)
- chesterton m3b: base 1.089 -> adapter 1.120 (+0.031)
- chesterton m8b: base 1.117 -> adapter 1.111 (-0.006)
- chopin 14b: base 1.227 -> adapter 1.186 (-0.041)
- chopin 4b: base 1.353 -> adapter 1.194 (-0.159)
- chopin 8b: base 1.348 -> adapter 1.269 (-0.079)
- doctorow 14b: base 1.115 -> adapter 1.027 (-0.088)
- doctorow 4b: base 1.293 -> adapter 1.129 (-0.164)
- doctorow 8b: base 1.288 -> adapter 1.112 (-0.176)
- doctorow m14b: base 1.156 -> adapter 0.992 (-0.164)
- doctorow m3b: base 1.092 -> adapter 1.086 (-0.005)
- doctorow m8b: base 1.103 -> adapter 1.039 (-0.064)
- h_private 14b: base 1.785 -> adapter 1.560 (-0.225)
- h_private 4b: base 1.771 -> adapter 1.419 (-0.352)
- h_private 8b: base 1.966 -> adapter 1.556 (-0.410)
- link 14b: base 1.573 -> adapter 1.774 (+0.202)
- link 4b: base 1.951 -> adapter 1.639 (-0.312)
- link 8b: base 1.834 -> adapter 1.657 (-0.176)
- mansfield 14b: base 1.421 -> adapter 1.166 (-0.255)
- mansfield 4b: base 1.636 -> adapter 1.108 (-0.528)
- mansfield 8b: base 1.679 -> adapter 1.193 (-0.486)
- patrick 4b: base 1.041 -> adapter 1.045 (+0.004)
- patrick_v2 14b: base 1.126 -> adapter 1.117 (-0.009)
- patrick_v2 17b: base 1.259 -> adapter 1.048 (-0.211)
- patrick_v2 4b: base 1.194 -> adapter 1.014 (-0.180)
- patrick_v2 8b: base 1.196 -> adapter 1.109 (-0.088)
- patrick_v2 m14b: base 1.684 -> adapter 1.095 (-0.589)
- patrick_v2 m3b: base 1.439 -> adapter 1.037 (-0.402)
- patrick_v2 m8b: base 1.572 -> adapter 1.067 (-0.505)
- rucker 14b: base 1.167 -> adapter 1.055 (-0.112)
- rucker 4b: base 1.294 -> adapter 1.135 (-0.160)
- rucker 8b: base 1.220 -> adapter 1.066 (-0.154)
- stross 14b: base 1.099 -> adapter 0.994 (-0.106)
- stross 4b: base 1.240 -> adapter 1.007 (-0.233)
- stross 8b: base 1.199 -> adapter 1.011 (-0.188)
- sui_sin_far 14b: base 1.228 -> adapter 1.703 (+0.475)
- sui_sin_far 4b: base 1.419 -> adapter 1.687 (+0.268)
- sui_sin_far 8b: base 1.448 -> adapter 1.679 (+0.231)
- watts 14b: base 1.284 -> adapter 1.108 (-0.176)
- watts 4b: base 1.298 -> adapter 1.082 (-0.216)
- watts 8b: base 1.411 -> adapter 1.057 (-0.354)
- wharton 14b: base 1.064 -> adapter 0.978 (-0.086)
- wharton 4b: base 1.057 -> adapter 0.999 (-0.058)
- wharton 8b: base 1.135 -> adapter 0.941 (-0.194)

## lag1_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 0.016 | 0.294 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.036 | 0.300 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.027 | 0.244 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.108 | 0.275 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.107 | 0.255 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.014 | 0.256 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.083 | 0.290 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.095 | 0.283 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.044 | 0.275 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.126 | 0.231 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.046 | 0.267 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.016 | 0.314 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | 0.036 | 0.297 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.003 | 0.254 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.030 | 0.289 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | 0.005 | 0.230 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.092 | 0.262 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.017 | 0.234 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.052 | 0.252 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | 0.006 | 0.230 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.088 | 0.257 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.034 | 0.249 |
| h_private_base4b | h_private | 4b | base | 46 | 0.195 | 0.212 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.130 | 0.254 |
| chopin_base4b | chopin | 4b | base | 98 | 0.047 | 0.277 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | -0.011 | 0.259 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.033 | 0.286 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.058 | 0.339 |
| cather_base4b | cather | 4b | base | 88 | 0.016 | 0.310 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.017 | 0.311 |
| cather_base14b | cather | 14b | base | 88 | 0.127 | 0.300 |
| cather_base8b | cather | 8b | base | 88 | 0.114 | 0.324 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.012 | 0.327 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.009 | 0.313 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.156 | 0.248 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.107 | 0.245 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.078 | 0.258 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.098 | 0.271 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.066 | 0.259 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.077 | 0.248 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.114 | 0.263 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.094 | 0.244 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.008 | 0.293 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.065 | 0.252 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.111 | 0.256 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.032 | 0.259 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.035 | 0.291 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.039 | 0.287 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.005 | 0.265 |
| chopin_base14b | chopin | 14b | base | 98 | 0.073 | 0.264 |
| chopin_base8b | chopin | 8b | base | 98 | 0.039 | 0.264 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | -0.009 | 0.248 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.029 | 0.254 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.092 | 0.216 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.012 | 0.286 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.070 | 0.244 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.037 | 0.213 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.041 | 0.246 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.060 | 0.222 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.027 | 0.216 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.007 | 0.264 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | -0.025 | 0.233 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.019 | 0.216 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | -0.009 | 0.239 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | -0.004 | 0.217 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.048 | 0.243 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | -0.025 | 0.223 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.038 | 0.253 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.073 | 0.293 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | -0.021 | 0.244 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.041 | 0.247 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.081 | 0.237 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | -0.035 | 0.259 |
| h_private_base14b | h_private | 14b | base | 46 | 0.220 | 0.209 |
| h_private_base8b | h_private | 8b | base | 46 | 0.192 | 0.232 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.072 | 0.323 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.067 | 0.233 |
| link_base14b | link | 14b | base | 32 | 0.097 | 0.212 |
| link_base4b | link | 4b | base | 32 | 0.072 | 0.311 |
| link_base8b | link | 8b | base | 32 | 0.053 | 0.243 |
| link_paire6_14b | link | 14b | adapter | 32 | -0.025 | 0.328 |
| link_paire6_4b | link | 4b | adapter | 32 | -0.031 | 0.229 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.048 | 0.222 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.092 | 0.255 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.021 | 0.311 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.022 | 0.290 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.033 | 0.231 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | 0.028 | 0.250 |
| patrick_base4b | patrick | 4b | base | 92 | 0.075 | 0.235 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.002 | 0.283 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.089 | 0.245 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.059 | 0.260 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.081 | 0.238 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.085 | 0.235 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.019 | 0.292 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.004 | 0.236 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.041 | 0.256 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.079 | 0.305 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.017 | 0.242 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.003 | 0.237 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.020 | 0.231 |
| rucker_base14b | rucker | 14b | base | 94 | 0.153 | 0.205 |
| rucker_base4b | rucker | 4b | base | 94 | 0.107 | 0.228 |
| rucker_base8b | rucker | 8b | base | 94 | 0.141 | 0.237 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.065 | 0.210 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.080 | 0.213 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.035 | 0.214 |
| stross_base14b | stross | 14b | base | 82 | 0.140 | 0.225 |
| stross_base4b | stross | 4b | base | 82 | 0.141 | 0.284 |
| stross_base8b | stross | 8b | base | 82 | 0.165 | 0.244 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.008 | 0.235 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.002 | 0.264 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.013 | 0.262 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.106 | 0.235 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.088 | 0.287 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -0.092 | 0.309 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.083 | 0.335 |
| watts_base14b | watts | 14b | base | 90 | 0.060 | 0.190 |
| watts_base4b | watts | 4b | base | 90 | 0.013 | 0.202 |
| watts_base8b | watts | 8b | base | 90 | 0.063 | 0.199 |
| watts_paire6_14b | watts | 14b | adapter | 90 | -0.036 | 0.196 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.018 | 0.213 |
| watts_paire6_8b | watts | 8b | adapter | 90 | -0.015 | 0.192 |
| wharton_base14b | wharton | 14b | base | 88 | 0.022 | 0.285 |
| wharton_base8b | wharton | 8b | base | 88 | -0.001 | 0.268 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.043 | 0.253 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.013 | 0.260 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -0.052
- chesterton_base4b vs chesterton_base4bc: -0.001
- mansfield_base4b vs mansfield_base4b_r2: +0.021

Base vs adapter, same author and size:

- cather 14b: base 0.127 -> adapter -0.012 (-0.139)
- cather 4b: base 0.016 -> adapter 0.017 (+0.001)
- cather 8b: base 0.114 -> adapter -0.009 (-0.122)
- chesterton 14b: base 0.126 -> adapter 0.046 (-0.080)
- chesterton 4b: base 0.108 -> adapter 0.014 (-0.094)
- chesterton 4bc: base 0.107 -> adapter 0.083 (-0.024)
- chesterton 8b: base 0.095 -> adapter 0.044 (-0.051)
- chesterton m14b: base 0.078 -> adapter 0.008 (-0.070)
- chesterton m3b: base 0.066 -> adapter 0.065 (-0.000)
- chesterton m8b: base 0.114 -> adapter 0.111 (-0.002)
- chopin 14b: base 0.073 -> adapter -0.009 (-0.082)
- chopin 4b: base 0.047 -> adapter -0.011 (-0.058)
- chopin 8b: base 0.039 -> adapter 0.029 (-0.010)
- doctorow 14b: base 0.092 -> adapter 0.027 (-0.066)
- doctorow 4b: base 0.012 -> adapter 0.007 (-0.005)
- doctorow 8b: base 0.070 -> adapter -0.025 (-0.095)
- doctorow m14b: base 0.037 -> adapter 0.019 (-0.018)
- doctorow m3b: base 0.041 -> adapter -0.009 (-0.050)
- doctorow m8b: base 0.060 -> adapter -0.004 (-0.064)
- h_private 14b: base 0.220 -> adapter 0.072 (-0.148)
- h_private 4b: base 0.195 -> adapter 0.130 (-0.065)
- h_private 8b: base 0.192 -> adapter 0.067 (-0.125)
- link 14b: base 0.097 -> adapter -0.025 (-0.122)
- link 4b: base 0.072 -> adapter -0.031 (-0.103)
- link 8b: base 0.053 -> adapter 0.048 (-0.005)
- mansfield 14b: base 0.092 -> adapter 0.022 (-0.070)
- mansfield 4b: base 0.016 -> adapter 0.003 (-0.013)
- mansfield 8b: base 0.021 -> adapter 0.033 (+0.012)
- patrick 4b: base 0.075 -> adapter 0.002 (-0.072)
- patrick_v2 14b: base 0.088 -> adapter 0.034 (-0.054)
- patrick_v2 17b: base 0.030 -> adapter 0.005 (-0.025)
- patrick_v2 4b: base 0.092 -> adapter -0.017 (-0.109)
- patrick_v2 8b: base 0.052 -> adapter 0.006 (-0.046)
- patrick_v2 m14b: base 0.089 -> adapter -0.019 (-0.108)
- patrick_v2 m3b: base 0.059 -> adapter -0.004 (-0.063)
- patrick_v2 m8b: base 0.085 -> adapter -0.041 (-0.126)
- rucker 14b: base 0.153 -> adapter 0.065 (-0.088)
- rucker 4b: base 0.107 -> adapter 0.080 (-0.027)
- rucker 8b: base 0.141 -> adapter 0.035 (-0.106)
- stross 14b: base 0.140 -> adapter 0.008 (-0.132)
- stross 4b: base 0.141 -> adapter -0.002 (-0.142)
- stross 8b: base 0.165 -> adapter 0.013 (-0.152)
- sui_sin_far 14b: base 0.106 -> adapter -0.092 (-0.197)
- sui_sin_far 4b: base 0.033 -> adapter -0.058 (-0.092)
- sui_sin_far 8b: base 0.088 -> adapter -0.083 (-0.171)
- watts 14b: base 0.060 -> adapter -0.036 (-0.096)
- watts 4b: base 0.013 -> adapter -0.018 (-0.031)
- watts 8b: base 0.063 -> adapter -0.015 (-0.079)
- wharton 14b: base 0.022 -> adapter 0.043 (+0.021)
- wharton 4b: base 0.016 -> adapter 0.027 (+0.011)
- wharton 8b: base -0.001 -> adapter 0.013 (+0.014)

## lag2_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | 0.004 | 0.250 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.034 | 0.278 |
| pair_e6_4b | wharton | 4b | adapter | 88 | -0.012 | 0.238 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.064 | 0.255 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.090 | 0.259 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | -0.026 | 0.260 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.067 | 0.255 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.117 | 0.252 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.008 | 0.227 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.093 | 0.238 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.008 | 0.269 |
| mansfield_base4b | mansfield | 4b | base | 82 | 0.027 | 0.208 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -0.005 | 0.258 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | 0.003 | 0.209 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | 0.024 | 0.243 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.003 | 0.261 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.034 | 0.213 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.019 | 0.210 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.045 | 0.246 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.017 | 0.255 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.062 | 0.213 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.005 | 0.264 |
| h_private_base4b | h_private | 4b | base | 46 | 0.024 | 0.181 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.032 | 0.227 |
| chopin_base4b | chopin | 4b | base | 98 | -0.010 | 0.258 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | -0.003 | 0.248 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.002 | 0.238 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.059 | 0.232 |
| cather_base4b | cather | 4b | base | 88 | -0.053 | 0.251 |
| cather_pair4b | cather | 4b | adapter | 88 | -0.002 | 0.276 |
| cather_base14b | cather | 14b | base | 88 | 0.013 | 0.235 |
| cather_base8b | cather | 8b | base | 88 | 0.009 | 0.267 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.030 | 0.306 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.048 | 0.257 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.113 | 0.231 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.096 | 0.274 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.064 | 0.218 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.062 | 0.234 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.074 | 0.235 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.066 | 0.227 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.081 | 0.217 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.059 | 0.208 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | -0.004 | 0.233 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.045 | 0.251 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.053 | 0.266 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.025 | 0.267 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.048 | 0.244 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.013 | 0.253 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | -0.015 | 0.256 |
| chopin_base14b | chopin | 14b | base | 98 | 0.013 | 0.242 |
| chopin_base8b | chopin | 8b | base | 98 | 0.021 | 0.277 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | -0.009 | 0.224 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.010 | 0.259 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.050 | 0.238 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.017 | 0.264 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.049 | 0.238 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.015 | 0.260 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.003 | 0.249 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.017 | 0.258 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | -0.009 | 0.229 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.001 | 0.259 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | -0.005 | 0.235 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.026 | 0.243 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | -0.046 | 0.271 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | -0.013 | 0.253 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.028 | 0.260 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | -0.046 | 0.242 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.002 | 0.261 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.026 | 0.313 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | -0.023 | 0.261 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.052 | 0.244 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.062 | 0.243 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | -0.018 | 0.224 |
| h_private_base14b | h_private | 14b | base | 46 | 0.057 | 0.223 |
| h_private_base8b | h_private | 8b | base | 46 | 0.132 | 0.205 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.031 | 0.254 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.028 | 0.196 |
| link_base14b | link | 14b | base | 32 | 0.085 | 0.206 |
| link_base4b | link | 4b | base | 32 | 0.132 | 0.262 |
| link_base8b | link | 8b | base | 32 | 0.083 | 0.203 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.059 | 0.243 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.091 | 0.213 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.021 | 0.236 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.039 | 0.238 |
| mansfield_base8b | mansfield | 8b | base | 82 | 0.010 | 0.227 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | 0.005 | 0.192 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.007 | 0.208 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -0.018 | 0.185 |
| patrick_base4b | patrick | 4b | base | 92 | 0.004 | 0.226 |
| patrick_pair4b | patrick | 4b | adapter | 92 | 0.041 | 0.260 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.030 | 0.226 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.034 | 0.239 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.016 | 0.231 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.044 | 0.238 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.009 | 0.225 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.043 | 0.239 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.032 | 0.226 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | 0.022 | 0.261 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -0.012 | 0.238 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.017 | 0.206 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.008 | 0.220 |
| rucker_base14b | rucker | 14b | base | 94 | 0.086 | 0.201 |
| rucker_base4b | rucker | 4b | base | 94 | 0.037 | 0.219 |
| rucker_base8b | rucker | 8b | base | 94 | 0.098 | 0.171 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.070 | 0.203 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.009 | 0.237 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.000 | 0.195 |
| stross_base14b | stross | 14b | base | 82 | 0.104 | 0.210 |
| stross_base4b | stross | 4b | base | 82 | 0.048 | 0.245 |
| stross_base8b | stross | 8b | base | 82 | 0.111 | 0.261 |
| stross_paire6_14b | stross | 14b | adapter | 82 | -0.030 | 0.232 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.022 | 0.212 |
| stross_paire6_8b | stross | 8b | adapter | 82 | -0.005 | 0.233 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.102 | 0.191 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.082 | 0.247 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | 0.052 | 0.316 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.039 | 0.200 |
| watts_base14b | watts | 14b | base | 90 | 0.002 | 0.204 |
| watts_base4b | watts | 4b | base | 90 | -0.012 | 0.238 |
| watts_base8b | watts | 8b | base | 90 | 0.039 | 0.215 |
| watts_paire6_14b | watts | 14b | adapter | 90 | -0.041 | 0.195 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.003 | 0.198 |
| watts_paire6_8b | watts | 8b | adapter | 90 | -0.014 | 0.198 |
| wharton_base14b | wharton | 14b | base | 88 | 0.033 | 0.250 |
| wharton_base8b | wharton | 8b | base | 88 | -0.008 | 0.259 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.002 | 0.252 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | -0.006 | 0.217 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: -0.038
- chesterton_base4b vs chesterton_base4bc: +0.027
- mansfield_base4b vs mansfield_base4b_r2: -0.032

Base vs adapter, same author and size:

- cather 14b: base 0.013 -> adapter -0.030 (-0.042)
- cather 4b: base -0.053 -> adapter -0.002 (+0.050)
- cather 8b: base 0.009 -> adapter -0.048 (-0.057)
- chesterton 14b: base 0.093 -> adapter 0.008 (-0.085)
- chesterton 4b: base 0.064 -> adapter -0.026 (-0.090)
- chesterton 4bc: base 0.090 -> adapter 0.067 (-0.023)
- chesterton 8b: base 0.117 -> adapter 0.008 (-0.109)
- chesterton m14b: base 0.064 -> adapter -0.004 (-0.068)
- chesterton m3b: base 0.074 -> adapter 0.045 (-0.029)
- chesterton m8b: base 0.081 -> adapter 0.053 (-0.027)
- chopin 14b: base 0.013 -> adapter -0.009 (-0.022)
- chopin 4b: base -0.010 -> adapter -0.003 (+0.007)
- chopin 8b: base 0.021 -> adapter 0.010 (-0.011)
- doctorow 14b: base 0.050 -> adapter -0.009 (-0.059)
- doctorow 4b: base 0.017 -> adapter 0.001 (-0.016)
- doctorow 8b: base 0.049 -> adapter -0.005 (-0.054)
- doctorow m14b: base 0.015 -> adapter 0.026 (+0.011)
- doctorow m3b: base 0.003 -> adapter -0.046 (-0.049)
- doctorow m8b: base 0.017 -> adapter -0.013 (-0.030)
- h_private 14b: base 0.057 -> adapter 0.031 (-0.027)
- h_private 4b: base 0.024 -> adapter 0.032 (+0.008)
- h_private 8b: base 0.132 -> adapter 0.028 (-0.104)
- link 14b: base 0.085 -> adapter 0.059 (-0.026)
- link 4b: base 0.132 -> adapter 0.091 (-0.041)
- link 8b: base 0.083 -> adapter 0.021 (-0.062)
- mansfield 14b: base 0.039 -> adapter 0.005 (-0.034)
- mansfield 4b: base 0.027 -> adapter 0.003 (-0.024)
- mansfield 8b: base 0.010 -> adapter 0.007 (-0.003)
- patrick 4b: base 0.004 -> adapter 0.041 (+0.037)
- patrick_v2 14b: base 0.062 -> adapter 0.005 (-0.057)
- patrick_v2 17b: base 0.024 -> adapter -0.003 (-0.028)
- patrick_v2 4b: base 0.034 -> adapter -0.019 (-0.053)
- patrick_v2 8b: base 0.045 -> adapter -0.017 (-0.061)
- patrick_v2 m14b: base 0.030 -> adapter -0.009 (-0.038)
- patrick_v2 m3b: base 0.034 -> adapter -0.043 (-0.077)
- patrick_v2 m8b: base 0.044 -> adapter -0.032 (-0.075)
- rucker 14b: base 0.086 -> adapter 0.070 (-0.016)
- rucker 4b: base 0.037 -> adapter 0.009 (-0.028)
- rucker 8b: base 0.098 -> adapter 0.000 (-0.097)
- stross 14b: base 0.104 -> adapter -0.030 (-0.134)
- stross 4b: base 0.048 -> adapter -0.022 (-0.070)
- stross 8b: base 0.111 -> adapter -0.005 (-0.116)
- sui_sin_far 14b: base 0.102 -> adapter 0.052 (-0.049)
- sui_sin_far 4b: base 0.002 -> adapter -0.059 (-0.062)
- sui_sin_far 8b: base 0.082 -> adapter -0.039 (-0.121)
- watts 14b: base 0.002 -> adapter -0.041 (-0.043)
- watts 4b: base -0.012 -> adapter -0.003 (+0.009)
- watts 8b: base 0.039 -> adapter -0.014 (-0.054)
- wharton 14b: base 0.033 -> adapter 0.002 (-0.031)
- wharton 4b: base 0.004 -> adapter -0.012 (-0.016)
- wharton 8b: base -0.008 -> adapter -0.006 (+0.002)

## lag3_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | -0.053 | 0.207 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.029 | 0.213 |
| pair_e6_4b | wharton | 4b | adapter | 88 | -0.043 | 0.257 |
| chesterton_base4b | chesterton | 4b | base | 78 | 0.075 | 0.242 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.063 | 0.265 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | 0.011 | 0.252 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | 0.030 | 0.241 |
| chesterton_base8b | chesterton | 8b | base | 78 | 0.062 | 0.219 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | 0.042 | 0.225 |
| chesterton_base14b | chesterton | 14b | base | 78 | 0.082 | 0.246 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | 0.035 | 0.231 |
| mansfield_base4b | mansfield | 4b | base | 82 | -0.026 | 0.217 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -0.061 | 0.219 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | -0.041 | 0.203 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -0.009 | 0.276 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.028 | 0.229 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | -0.016 | 0.218 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.006 | 0.226 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | 0.016 | 0.228 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.045 | 0.235 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.000 | 0.244 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | -0.008 | 0.239 |
| h_private_base4b | h_private | 4b | base | 46 | 0.035 | 0.227 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.054 | 0.214 |
| chopin_base4b | chopin | 4b | base | 98 | 0.047 | 0.234 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.059 | 0.231 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | 0.015 | 0.196 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.001 | 0.252 |
| cather_base4b | cather | 4b | base | 88 | 0.010 | 0.272 |
| cather_pair4b | cather | 4b | adapter | 88 | 0.005 | 0.288 |
| cather_base14b | cather | 14b | base | 88 | 0.062 | 0.262 |
| cather_base8b | cather | 8b | base | 88 | 0.045 | 0.291 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.006 | 0.274 |
| cather_paire6_8b | cather | 8b | adapter | 88 | 0.011 | 0.269 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.094 | 0.236 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | 0.107 | 0.254 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.099 | 0.230 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.084 | 0.236 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.058 | 0.224 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.073 | 0.230 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.094 | 0.213 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.042 | 0.230 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | 0.023 | 0.239 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.042 | 0.237 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | 0.085 | 0.262 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | 0.012 | 0.243 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | 0.019 | 0.215 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | 0.065 | 0.249 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | 0.010 | 0.233 |
| chopin_base14b | chopin | 14b | base | 98 | 0.082 | 0.218 |
| chopin_base8b | chopin | 8b | base | 98 | 0.072 | 0.239 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.048 | 0.223 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.064 | 0.222 |
| doctorow_base14b | doctorow | 14b | base | 84 | 0.077 | 0.192 |
| doctorow_base4b | doctorow | 4b | base | 84 | 0.004 | 0.217 |
| doctorow_base8b | doctorow | 8b | base | 84 | 0.078 | 0.233 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.026 | 0.196 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.056 | 0.225 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.037 | 0.225 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.012 | 0.204 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.015 | 0.207 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.026 | 0.230 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.034 | 0.198 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | -0.008 | 0.219 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.017 | 0.206 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.000 | 0.235 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | -0.011 | 0.213 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.006 | 0.233 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | 0.008 | 0.258 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.024 | 0.220 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.015 | 0.225 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.002 | 0.218 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | -0.005 | 0.196 |
| h_private_base14b | h_private | 14b | base | 46 | 0.066 | 0.174 |
| h_private_base8b | h_private | 8b | base | 46 | 0.080 | 0.213 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.074 | 0.226 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.057 | 0.210 |
| link_base14b | link | 14b | base | 32 | 0.133 | 0.206 |
| link_base4b | link | 4b | base | 32 | 0.099 | 0.222 |
| link_base8b | link | 8b | base | 32 | 0.157 | 0.256 |
| link_paire6_14b | link | 14b | adapter | 32 | 0.098 | 0.205 |
| link_paire6_4b | link | 4b | adapter | 32 | 0.126 | 0.200 |
| link_paire6_8b | link | 8b | adapter | 32 | 0.156 | 0.244 |
| mansfield_base14b | mansfield | 14b | base | 82 | 0.009 | 0.213 |
| mansfield_base8b | mansfield | 8b | base | 82 | -0.048 | 0.223 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | -0.020 | 0.198 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | -0.045 | 0.213 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -0.036 | 0.225 |
| patrick_base4b | patrick | 4b | base | 92 | 0.014 | 0.257 |
| patrick_pair4b | patrick | 4b | adapter | 92 | -0.002 | 0.251 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.049 | 0.236 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | -0.030 | 0.224 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.024 | 0.245 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.022 | 0.227 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.023 | 0.232 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.031 | 0.223 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.027 | 0.231 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.019 | 0.317 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | 0.007 | 0.278 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.017 | 0.254 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.055 | 0.212 |
| rucker_base14b | rucker | 14b | base | 94 | 0.058 | 0.186 |
| rucker_base4b | rucker | 4b | base | 94 | 0.013 | 0.220 |
| rucker_base8b | rucker | 8b | base | 94 | 0.072 | 0.180 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | 0.026 | 0.165 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | 0.023 | 0.179 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | 0.026 | 0.195 |
| stross_base14b | stross | 14b | base | 82 | 0.062 | 0.222 |
| stross_base4b | stross | 4b | base | 82 | 0.047 | 0.224 |
| stross_base8b | stross | 8b | base | 82 | 0.076 | 0.196 |
| stross_paire6_14b | stross | 14b | adapter | 82 | 0.004 | 0.206 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.016 | 0.201 |
| stross_paire6_8b | stross | 8b | adapter | 82 | 0.010 | 0.210 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | 0.051 | 0.208 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | 0.083 | 0.190 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -0.034 | 0.254 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.060 | 0.209 |
| watts_base14b | watts | 14b | base | 90 | 0.021 | 0.221 |
| watts_base4b | watts | 4b | base | 90 | 0.003 | 0.212 |
| watts_base8b | watts | 8b | base | 90 | 0.055 | 0.210 |
| watts_paire6_14b | watts | 14b | adapter | 90 | -0.022 | 0.189 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.007 | 0.173 |
| watts_paire6_8b | watts | 8b | adapter | 90 | 0.008 | 0.174 |
| wharton_base14b | wharton | 14b | base | 88 | 0.036 | 0.257 |
| wharton_base8b | wharton | 8b | base | 88 | 0.009 | 0.241 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | 0.010 | 0.259 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | -0.054 | 0.259 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.024
- chesterton_base4b vs chesterton_base4bc: -0.013
- mansfield_base4b vs mansfield_base4b_r2: -0.035

Base vs adapter, same author and size:

- cather 14b: base 0.062 -> adapter -0.006 (-0.068)
- cather 4b: base 0.010 -> adapter 0.005 (-0.005)
- cather 8b: base 0.045 -> adapter 0.011 (-0.034)
- chesterton 14b: base 0.082 -> adapter 0.035 (-0.047)
- chesterton 4b: base 0.075 -> adapter 0.011 (-0.064)
- chesterton 4bc: base 0.063 -> adapter 0.030 (-0.033)
- chesterton 8b: base 0.062 -> adapter 0.042 (-0.020)
- chesterton m14b: base 0.099 -> adapter 0.023 (-0.076)
- chesterton m3b: base 0.058 -> adapter 0.042 (-0.016)
- chesterton m8b: base 0.094 -> adapter 0.085 (-0.009)
- chopin 14b: base 0.082 -> adapter 0.048 (-0.034)
- chopin 4b: base 0.047 -> adapter 0.059 (+0.012)
- chopin 8b: base 0.072 -> adapter 0.064 (-0.008)
- doctorow 14b: base 0.077 -> adapter 0.012 (-0.065)
- doctorow 4b: base 0.004 -> adapter 0.015 (+0.011)
- doctorow 8b: base 0.078 -> adapter 0.026 (-0.052)
- doctorow m14b: base 0.026 -> adapter 0.034 (+0.008)
- doctorow m3b: base 0.056 -> adapter -0.008 (-0.064)
- doctorow m8b: base 0.037 -> adapter 0.017 (-0.021)
- h_private 14b: base 0.066 -> adapter 0.074 (+0.008)
- h_private 4b: base 0.035 -> adapter 0.054 (+0.018)
- h_private 8b: base 0.080 -> adapter 0.057 (-0.023)
- link 14b: base 0.133 -> adapter 0.098 (-0.034)
- link 4b: base 0.099 -> adapter 0.126 (+0.027)
- link 8b: base 0.157 -> adapter 0.156 (-0.001)
- mansfield 14b: base 0.009 -> adapter -0.020 (-0.029)
- mansfield 4b: base -0.026 -> adapter -0.041 (-0.015)
- mansfield 8b: base -0.048 -> adapter -0.045 (+0.004)
- patrick 4b: base 0.014 -> adapter -0.002 (-0.017)
- patrick_v2 14b: base 0.000 -> adapter -0.008 (-0.008)
- patrick_v2 17b: base -0.009 -> adapter -0.028 (-0.019)
- patrick_v2 4b: base -0.016 -> adapter -0.006 (+0.010)
- patrick_v2 8b: base 0.016 -> adapter -0.045 (-0.061)
- patrick_v2 m14b: base 0.049 -> adapter -0.023 (-0.071)
- patrick_v2 m3b: base -0.030 -> adapter -0.031 (-0.001)
- patrick_v2 m8b: base 0.022 -> adapter -0.027 (-0.049)
- rucker 14b: base 0.058 -> adapter 0.026 (-0.031)
- rucker 4b: base 0.013 -> adapter 0.023 (+0.009)
- rucker 8b: base 0.072 -> adapter 0.026 (-0.046)
- stross 14b: base 0.062 -> adapter 0.004 (-0.058)
- stross 4b: base 0.047 -> adapter -0.016 (-0.063)
- stross 8b: base 0.076 -> adapter 0.010 (-0.067)
- sui_sin_far 14b: base 0.051 -> adapter -0.034 (-0.086)
- sui_sin_far 4b: base 0.015 -> adapter -0.001 (-0.015)
- sui_sin_far 8b: base 0.083 -> adapter -0.060 (-0.142)
- watts 14b: base 0.021 -> adapter -0.022 (-0.042)
- watts 4b: base 0.003 -> adapter -0.007 (-0.011)
- watts 8b: base 0.055 -> adapter 0.008 (-0.047)
- wharton 14b: base 0.036 -> adapter 0.010 (-0.027)
- wharton 4b: base -0.053 -> adapter -0.043 (+0.010)
- wharton 8b: base 0.009 -> adapter -0.054 (-0.063)

## q50_q10_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | -0.988 | 2.947 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.769 | 2.848 |
| pair_e6_4b | wharton | 4b | adapter | 88 | 0.087 | 3.022 |
| chesterton_base4b | chesterton | 4b | base | 78 | -0.201 | 1.680 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | 0.014 | 1.691 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | -0.265 | 1.503 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | -0.017 | 1.544 |
| chesterton_base8b | chesterton | 8b | base | 78 | -0.140 | 1.531 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | -0.223 | 1.653 |
| chesterton_base14b | chesterton | 14b | base | 78 | -0.019 | 1.410 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | -0.356 | 1.515 |
| mansfield_base4b | mansfield | 4b | base | 82 | -0.894 | 2.978 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -1.093 | 2.089 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | -1.016 | 1.717 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -0.435 | 0.972 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.162 | 0.865 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | 0.134 | 1.260 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.193 | 0.931 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | -0.095 | 1.145 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.090 | 1.080 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.266 | 1.049 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | -0.056 | 1.409 |
| h_private_base4b | h_private | 4b | base | 46 | -0.111 | 0.758 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | 0.246 | 1.292 |
| chopin_base4b | chopin | 4b | base | 98 | -0.680 | 1.339 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | -0.352 | 1.377 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | -1.382 | 3.156 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -1.333 | 3.803 |
| cather_base4b | cather | 4b | base | 88 | -0.038 | 0.888 |
| cather_pair4b | cather | 4b | adapter | 88 | -0.444 | 0.855 |
| cather_base14b | cather | 14b | base | 88 | 0.049 | 0.972 |
| cather_base8b | cather | 8b | base | 88 | -0.165 | 0.740 |
| cather_paire6_14b | cather | 14b | adapter | 88 | 0.606 | 3.411 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.187 | 0.960 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | 0.108 | 1.612 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | -0.016 | 1.564 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.961 | 1.793 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 1.022 | 2.095 |
| chesterton_basem3b | chesterton | m3b | base | 78 | 0.812 | 2.059 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.728 | 1.751 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.530 | 1.594 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.803 | 1.833 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | -0.146 | 1.569 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | 0.022 | 2.001 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | -0.201 | 2.122 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | -0.086 | 1.600 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | -0.164 | 1.348 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.213 | 2.313 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | -0.025 | 1.547 |
| chopin_base14b | chopin | 14b | base | 98 | -0.356 | 1.230 |
| chopin_base8b | chopin | 8b | base | 98 | -0.730 | 1.205 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | -0.179 | 2.055 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | -0.334 | 1.368 |
| doctorow_base14b | doctorow | 14b | base | 84 | -0.137 | 1.485 |
| doctorow_base4b | doctorow | 4b | base | 84 | -0.537 | 1.261 |
| doctorow_base8b | doctorow | 8b | base | 84 | -0.446 | 1.433 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.708 | 1.650 |
| doctorow_basem3b | doctorow | m3b | base | 84 | 0.359 | 1.196 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.548 | 2.032 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.040 | 1.213 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | -0.066 | 1.406 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | -0.045 | 1.198 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | -0.115 | 1.258 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | -0.090 | 2.017 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | -0.116 | 1.283 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.165 | 1.231 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | -0.158 | 1.237 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.075 | 1.496 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.961 | 1.510 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.069 | 1.439 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.361 | 1.460 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.071 | 1.608 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | -0.099 | 1.248 |
| h_private_base14b | h_private | 14b | base | 46 | 0.429 | 1.450 |
| h_private_base8b | h_private | 8b | base | 46 | -0.034 | 1.002 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | 0.301 | 1.688 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | 0.081 | 0.983 |
| link_base14b | link | 14b | base | 32 | -1.081 | 1.862 |
| link_base4b | link | 4b | base | 32 | -1.610 | 2.089 |
| link_base8b | link | 8b | base | 32 | -1.260 | 2.362 |
| link_paire6_14b | link | 14b | adapter | 32 | -1.146 | 3.221 |
| link_paire6_4b | link | 4b | adapter | 32 | -1.803 | 1.976 |
| link_paire6_8b | link | 8b | adapter | 32 | -1.936 | 1.906 |
| mansfield_base14b | mansfield | 14b | base | 82 | -0.811 | 2.033 |
| mansfield_base8b | mansfield | 8b | base | 82 | -1.263 | 1.736 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | -1.132 | 1.756 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | -0.985 | 1.697 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -1.134 | 1.657 |
| patrick_base4b | patrick | 4b | base | 92 | 0.072 | 1.140 |
| patrick_pair4b | patrick | 4b | adapter | 92 | -0.262 | 1.170 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 1.425 | 1.686 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 1.171 | 1.547 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 1.131 | 1.349 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 1.128 | 1.376 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.157 | 0.870 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.134 | 1.628 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.268 | 0.977 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.485 | 1.476 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -0.220 | 0.911 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | -0.196 | 0.920 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | -0.216 | 1.013 |
| rucker_base14b | rucker | 14b | base | 94 | -0.151 | 1.450 |
| rucker_base4b | rucker | 4b | base | 94 | -0.499 | 1.384 |
| rucker_base8b | rucker | 8b | base | 94 | -0.516 | 1.731 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | -0.505 | 1.457 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | -0.749 | 1.249 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | -0.604 | 1.493 |
| stross_base14b | stross | 14b | base | 82 | -0.796 | 1.442 |
| stross_base4b | stross | 4b | base | 82 | -1.159 | 1.479 |
| stross_base8b | stross | 8b | base | 82 | -1.018 | 1.349 |
| stross_paire6_14b | stross | 14b | adapter | 82 | -0.639 | 1.591 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.627 | 1.669 |
| stross_paire6_8b | stross | 8b | adapter | 82 | -0.643 | 1.582 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | -1.164 | 2.562 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | -1.107 | 2.939 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -1.313 | 4.183 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -1.776 | 3.523 |
| watts_base14b | watts | 14b | base | 90 | -0.098 | 0.985 |
| watts_base4b | watts | 4b | base | 90 | -0.298 | 0.885 |
| watts_base8b | watts | 8b | base | 90 | -0.224 | 1.023 |
| watts_paire6_14b | watts | 14b | adapter | 90 | -0.088 | 1.049 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.205 | 0.811 |
| watts_paire6_8b | watts | 8b | adapter | 90 | -0.026 | 1.128 |
| wharton_base14b | wharton | 14b | base | 88 | -0.311 | 2.995 |
| wharton_base8b | wharton | 8b | base | 88 | -0.188 | 3.432 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | -0.283 | 2.358 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | -0.294 | 2.806 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.219
- chesterton_base4b vs chesterton_base4bc: +0.215
- mansfield_base4b vs mansfield_base4b_r2: -0.199

Base vs adapter, same author and size:

- cather 14b: base 0.049 -> adapter 0.606 (+0.557)
- cather 4b: base -0.038 -> adapter -0.444 (-0.406)
- cather 8b: base -0.165 -> adapter -0.187 (-0.023)
- chesterton 14b: base -0.019 -> adapter -0.356 (-0.337)
- chesterton 4b: base -0.201 -> adapter -0.265 (-0.064)
- chesterton 4bc: base 0.014 -> adapter -0.017 (-0.031)
- chesterton 8b: base -0.140 -> adapter -0.223 (-0.083)
- chesterton m14b: base 0.961 -> adapter -0.146 (-1.107)
- chesterton m3b: base 0.812 -> adapter 0.022 (-0.790)
- chesterton m8b: base 0.530 -> adapter -0.201 (-0.731)
- chopin 14b: base -0.356 -> adapter -0.179 (+0.177)
- chopin 4b: base -0.680 -> adapter -0.352 (+0.329)
- chopin 8b: base -0.730 -> adapter -0.334 (+0.397)
- doctorow 14b: base -0.137 -> adapter 0.040 (+0.176)
- doctorow 4b: base -0.537 -> adapter -0.066 (+0.471)
- doctorow 8b: base -0.446 -> adapter -0.045 (+0.402)
- doctorow m14b: base 0.708 -> adapter -0.115 (-0.823)
- doctorow m3b: base 0.359 -> adapter -0.090 (-0.449)
- doctorow m8b: base 0.548 -> adapter -0.116 (-0.664)
- h_private 14b: base 0.429 -> adapter 0.301 (-0.129)
- h_private 4b: base -0.111 -> adapter 0.246 (+0.357)
- h_private 8b: base -0.034 -> adapter 0.081 (+0.115)
- link 14b: base -1.081 -> adapter -1.146 (-0.066)
- link 4b: base -1.610 -> adapter -1.803 (-0.193)
- link 8b: base -1.260 -> adapter -1.936 (-0.677)
- mansfield 14b: base -0.811 -> adapter -1.132 (-0.320)
- mansfield 4b: base -0.894 -> adapter -1.016 (-0.122)
- mansfield 8b: base -1.263 -> adapter -0.985 (+0.278)
- patrick 4b: base 0.072 -> adapter -0.262 (-0.334)
- patrick_v2 14b: base 0.266 -> adapter -0.056 (-0.322)
- patrick_v2 17b: base -0.435 -> adapter -0.162 (+0.273)
- patrick_v2 4b: base 0.134 -> adapter -0.193 (-0.327)
- patrick_v2 8b: base -0.095 -> adapter -0.090 (+0.005)
- patrick_v2 m14b: base 1.425 -> adapter -0.157 (-1.581)
- patrick_v2 m3b: base 1.171 -> adapter -0.134 (-1.305)
- patrick_v2 m8b: base 1.128 -> adapter -0.268 (-1.396)
- rucker 14b: base -0.151 -> adapter -0.505 (-0.354)
- rucker 4b: base -0.499 -> adapter -0.749 (-0.251)
- rucker 8b: base -0.516 -> adapter -0.604 (-0.088)
- stross 14b: base -0.796 -> adapter -0.639 (+0.158)
- stross 4b: base -1.159 -> adapter -0.627 (+0.532)
- stross 8b: base -1.018 -> adapter -0.643 (+0.376)
- sui_sin_far 14b: base -1.164 -> adapter -1.313 (-0.149)
- sui_sin_far 4b: base -1.382 -> adapter -1.333 (+0.048)
- sui_sin_far 8b: base -1.107 -> adapter -1.776 (-0.668)
- watts 14b: base -0.098 -> adapter -0.088 (+0.010)
- watts 4b: base -0.298 -> adapter -0.205 (+0.093)
- watts 8b: base -0.224 -> adapter -0.026 (+0.198)
- wharton 14b: base -0.311 -> adapter -0.283 (+0.029)
- wharton 4b: base -0.988 -> adapter 0.087 (+1.075)
- wharton 8b: base -0.188 -> adapter -0.294 (-0.106)

## q90_q50_diff

| run | author | size | kind | n | mean | sd |
|---|---|---|---|---:|---:|---:|
| base4b | wharton | 4b | base | 88 | -0.306 | 0.579 |
| base4b_r2 | wharton | 4b_r2 | base | 88 | -0.294 | 0.609 |
| pair_e6_4b | wharton | 4b | adapter | 88 | -0.003 | 0.644 |
| chesterton_base4b | chesterton | 4b | base | 78 | -0.329 | 0.545 |
| chesterton_base4bc | chesterton | 4bc | base | 78 | -0.259 | 0.609 |
| chesterton_paire6_4b | chesterton | 4b | adapter | 78 | -0.120 | 0.564 |
| chesterton_paire6_4bc | chesterton | 4bc | adapter | 78 | -0.088 | 0.599 |
| chesterton_base8b | chesterton | 8b | base | 78 | -0.248 | 0.516 |
| chesterton_paire6_8b | chesterton | 8b | adapter | 78 | -0.189 | 0.497 |
| chesterton_base14b | chesterton | 14b | base | 78 | -0.159 | 0.511 |
| chesterton_paire6_14b | chesterton | 14b | adapter | 78 | -0.206 | 0.615 |
| mansfield_base4b | mansfield | 4b | base | 82 | -0.968 | 0.729 |
| mansfield_base4b_r2 | mansfield | 4b_r2 | base | 82 | -0.938 | 0.737 |
| mansfield_paire6_4b | mansfield | 4b | adapter | 82 | -0.132 | 0.845 |
| patrick_v2_base17b | patrick_v2 | 17b | base | 90 | -0.161 | 0.353 |
| patrick_v2_paire6_17b | patrick_v2 | 17b | adapter | 90 | -0.005 | 0.337 |
| patrick_v2_base4b | patrick_v2 | 4b | base | 90 | -0.012 | 0.439 |
| patrick_v2_paire6_4b | patrick_v2 | 4b | adapter | 90 | -0.038 | 0.359 |
| patrick_v2_base8b | patrick_v2 | 8b | base | 90 | -0.097 | 0.369 |
| patrick_v2_paire6_8b | patrick_v2 | 8b | adapter | 90 | -0.028 | 0.334 |
| patrick_v2_base14b | patrick_v2 | 14b | base | 90 | 0.059 | 0.396 |
| patrick_v2_paire6_14b | patrick_v2 | 14b | adapter | 90 | 0.004 | 0.382 |
| h_private_base4b | h_private | 4b | base | 46 | -2.036 | 1.192 |
| h_private_paire6_4b | h_private | 4b | adapter | 46 | -1.378 | 1.296 |
| chopin_base4b | chopin | 4b | base | 98 | -0.269 | 0.494 |
| chopin_paire6_4b | chopin | 4b | adapter | 98 | 0.145 | 0.608 |
| sui_sin_far_base4b | sui_sin_far | 4b | base | 48 | -0.660 | 0.609 |
| sui_sin_far_paire6_4b | sui_sin_far | 4b | adapter | 48 | -0.722 | 0.735 |
| cather_base4b | cather | 4b | base | 88 | -0.213 | 0.515 |
| cather_pair4b | cather | 4b | adapter | 88 | -0.290 | 0.803 |
| cather_base14b | cather | 14b | base | 88 | -0.186 | 0.371 |
| cather_base8b | cather | 8b | base | 88 | -0.280 | 0.447 |
| cather_paire6_14b | cather | 14b | adapter | 88 | -0.143 | 0.572 |
| cather_paire6_8b | cather | 8b | adapter | 88 | -0.079 | 0.724 |
| chesterton_base14b_r2 | chesterton | 14b_r2 | base | 78 | -0.126 | 0.602 |
| chesterton_base8b_r2 | chesterton | 8b_r2 | base | 78 | -0.270 | 0.523 |
| chesterton_basem14b | chesterton | m14b | base | 78 | 0.207 | 0.772 |
| chesterton_basem14b_r2 | chesterton | m14b_r2 | base | 78 | 0.247 | 0.705 |
| chesterton_basem3b | chesterton | m3b | base | 78 | -0.009 | 0.579 |
| chesterton_basem3b_r2 | chesterton | m3b_r2 | base | 78 | 0.050 | 0.639 |
| chesterton_basem8b | chesterton | m8b | base | 78 | 0.233 | 0.688 |
| chesterton_basem8b_r2 | chesterton | m8b_r2 | base | 78 | 0.314 | 0.828 |
| chesterton_paire6_m14b | chesterton | m14b | adapter | 78 | -0.193 | 0.556 |
| chesterton_paire6_m3b | chesterton | m3b | adapter | 78 | -0.028 | 0.737 |
| chesterton_paire6_m8b | chesterton | m8b | adapter | 78 | -0.062 | 0.612 |
| chesterton_size100 | chesterton | size100 | adapter | 78 | -0.092 | 0.607 |
| chesterton_size150 | chesterton | size150 | adapter | 78 | -0.184 | 0.643 |
| chesterton_size25 | chesterton | size25 | adapter | 78 | -0.179 | 1.144 |
| chesterton_size50 | chesterton | size50 | adapter | 78 | -0.028 | 0.645 |
| chopin_base14b | chopin | 14b | base | 98 | -0.178 | 0.490 |
| chopin_base8b | chopin | 8b | base | 98 | -0.347 | 0.349 |
| chopin_paire6_14b | chopin | 14b | adapter | 98 | 0.235 | 0.547 |
| chopin_paire6_8b | chopin | 8b | adapter | 98 | 0.169 | 0.617 |
| doctorow_base14b | doctorow | 14b | base | 84 | -0.436 | 0.606 |
| doctorow_base4b | doctorow | 4b | base | 84 | -0.496 | 0.741 |
| doctorow_base8b | doctorow | 8b | base | 84 | -0.659 | 0.631 |
| doctorow_basem14b | doctorow | m14b | base | 84 | 0.189 | 0.948 |
| doctorow_basem3b | doctorow | m3b | base | 84 | -0.066 | 0.808 |
| doctorow_basem8b | doctorow | m8b | base | 84 | 0.066 | 0.841 |
| doctorow_paire6_14b | doctorow | 14b | adapter | 84 | 0.186 | 0.763 |
| doctorow_paire6_4b | doctorow | 4b | adapter | 84 | 0.181 | 0.806 |
| doctorow_paire6_8b | doctorow | 8b | adapter | 84 | 0.230 | 1.214 |
| doctorow_paire6_m14b | doctorow | m14b | adapter | 84 | 0.174 | 0.694 |
| doctorow_paire6_m3b | doctorow | m3b | adapter | 84 | 0.151 | 0.810 |
| doctorow_paire6_m8b | doctorow | m8b | adapter | 84 | 0.146 | 0.806 |
| doctorow_size100 | doctorow | size100 | adapter | 84 | -0.018 | 0.850 |
| doctorow_size150 | doctorow | size150 | adapter | 84 | 0.258 | 1.264 |
| doctorow_size215 | doctorow | size215 | adapter | 84 | 0.276 | 0.981 |
| doctorow_size25 | doctorow | size25 | adapter | 84 | -0.751 | 0.685 |
| doctorow_size300 | doctorow | size300 | adapter | 84 | 0.167 | 0.807 |
| doctorow_size50 | doctorow | size50 | adapter | 84 | -0.171 | 0.733 |
| doctorow_size50_s1 | doctorow | size50_s1 | adapter | 84 | -0.034 | 1.161 |
| doctorow_size525 | doctorow | size525 | adapter | 84 | 0.207 | 0.939 |
| h_private_base14b | h_private | 14b | base | 46 | -1.979 | 1.227 |
| h_private_base8b | h_private | 8b | base | 46 | -2.063 | 1.273 |
| h_private_paire6_14b | h_private | 14b | adapter | 46 | -1.167 | 1.711 |
| h_private_paire6_8b | h_private | 8b | adapter | 46 | -1.524 | 1.458 |
| link_base14b | link | 14b | base | 32 | -0.453 | 0.598 |
| link_base4b | link | 4b | base | 32 | -0.437 | 0.961 |
| link_base8b | link | 8b | base | 32 | -0.631 | 0.489 |
| link_paire6_14b | link | 14b | adapter | 32 | -0.492 | 0.705 |
| link_paire6_4b | link | 4b | adapter | 32 | -0.411 | 0.630 |
| link_paire6_8b | link | 8b | adapter | 32 | -0.454 | 0.574 |
| mansfield_base14b | mansfield | 14b | base | 82 | -0.830 | 0.734 |
| mansfield_base8b | mansfield | 8b | base | 82 | -0.992 | 0.737 |
| mansfield_paire6_14b | mansfield | 14b | adapter | 82 | -0.020 | 0.970 |
| mansfield_paire6_8b | mansfield | 8b | adapter | 82 | 0.033 | 1.613 |
| mansfield_paire6s1_4b | mansfield | s1_4b | adapter | 82 | -0.167 | 0.866 |
| patrick_base4b | patrick | 4b | base | 92 | 0.007 | 0.509 |
| patrick_pair4b | patrick | 4b | adapter | 92 | -0.058 | 0.426 |
| patrick_v2_basem14b | patrick_v2 | m14b | base | 90 | 0.559 | 0.694 |
| patrick_v2_basem3b | patrick_v2 | m3b | base | 90 | 0.356 | 0.658 |
| patrick_v2_basem3b_r2 | patrick_v2 | m3b_r2 | base | 90 | 0.421 | 0.559 |
| patrick_v2_basem8b | patrick_v2 | m8b | base | 90 | 0.555 | 0.601 |
| patrick_v2_paire6_m14b | patrick_v2 | m14b | adapter | 90 | -0.103 | 0.303 |
| patrick_v2_paire6_m3b | patrick_v2 | m3b | adapter | 90 | -0.008 | 0.315 |
| patrick_v2_paire6_m8b | patrick_v2 | m8b | adapter | 90 | -0.026 | 0.300 |
| patrick_v2_size25 | patrick_v2 | size25 | adapter | 90 | -0.254 | 0.364 |
| patrick_v2_size50 | patrick_v2 | size50 | adapter | 90 | -0.001 | 0.295 |
| patrick_v2_size50_s1 | patrick_v2 | size50_s1 | adapter | 90 | 0.010 | 0.370 |
| patrick_v2_size75 | patrick_v2 | size75 | adapter | 90 | 0.752 | 7.218 |
| rucker_base14b | rucker | 14b | base | 94 | -0.209 | 0.596 |
| rucker_base4b | rucker | 4b | base | 94 | -0.204 | 0.708 |
| rucker_base8b | rucker | 8b | base | 94 | -0.149 | 0.629 |
| rucker_paire6_14b | rucker | 14b | adapter | 94 | -0.103 | 0.467 |
| rucker_paire6_4b | rucker | 4b | adapter | 94 | -0.063 | 0.770 |
| rucker_paire6_8b | rucker | 8b | adapter | 94 | -0.134 | 0.501 |
| stross_base14b | stross | 14b | base | 82 | -0.612 | 0.817 |
| stross_base4b | stross | 4b | base | 82 | -0.670 | 0.842 |
| stross_base8b | stross | 8b | base | 82 | -0.693 | 0.823 |
| stross_paire6_14b | stross | 14b | adapter | 82 | -0.368 | 0.870 |
| stross_paire6_4b | stross | 4b | adapter | 82 | -0.321 | 0.905 |
| stross_paire6_8b | stross | 8b | adapter | 82 | -0.250 | 0.940 |
| sui_sin_far_base14b | sui_sin_far | 14b | base | 48 | -0.524 | 0.623 |
| sui_sin_far_base8b | sui_sin_far | 8b | base | 48 | -0.625 | 0.725 |
| sui_sin_far_paire6_14b | sui_sin_far | 14b | adapter | 48 | -0.759 | 0.757 |
| sui_sin_far_paire6_8b | sui_sin_far | 8b | adapter | 48 | -0.857 | 0.597 |
| watts_base14b | watts | 14b | base | 90 | -0.545 | 0.568 |
| watts_base4b | watts | 4b | base | 90 | -0.433 | 0.619 |
| watts_base8b | watts | 8b | base | 90 | -0.614 | 0.599 |
| watts_paire6_14b | watts | 14b | adapter | 90 | -0.112 | 0.611 |
| watts_paire6_4b | watts | 4b | adapter | 90 | -0.114 | 0.674 |
| watts_paire6_8b | watts | 8b | adapter | 90 | -0.070 | 0.600 |
| wharton_base14b | wharton | 14b | base | 88 | -0.255 | 0.618 |
| wharton_base8b | wharton | 8b | base | 88 | -0.455 | 0.483 |
| wharton_paire6_14b | wharton | 14b | adapter | 88 | -0.032 | 0.706 |
| wharton_paire6_8b | wharton | 8b | adapter | 88 | 0.006 | 0.557 |

Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):

- base4b vs base4b_r2: +0.012
- chesterton_base4b vs chesterton_base4bc: +0.070
- mansfield_base4b vs mansfield_base4b_r2: +0.030

Base vs adapter, same author and size:

- cather 14b: base -0.186 -> adapter -0.143 (+0.043)
- cather 4b: base -0.213 -> adapter -0.290 (-0.076)
- cather 8b: base -0.280 -> adapter -0.079 (+0.201)
- chesterton 14b: base -0.159 -> adapter -0.206 (-0.046)
- chesterton 4b: base -0.329 -> adapter -0.120 (+0.209)
- chesterton 4bc: base -0.259 -> adapter -0.088 (+0.170)
- chesterton 8b: base -0.248 -> adapter -0.189 (+0.059)
- chesterton m14b: base 0.207 -> adapter -0.193 (-0.400)
- chesterton m3b: base -0.009 -> adapter -0.028 (-0.019)
- chesterton m8b: base 0.233 -> adapter -0.062 (-0.296)
- chopin 14b: base -0.178 -> adapter 0.235 (+0.412)
- chopin 4b: base -0.269 -> adapter 0.145 (+0.415)
- chopin 8b: base -0.347 -> adapter 0.169 (+0.515)
- doctorow 14b: base -0.436 -> adapter 0.186 (+0.622)
- doctorow 4b: base -0.496 -> adapter 0.181 (+0.678)
- doctorow 8b: base -0.659 -> adapter 0.230 (+0.889)
- doctorow m14b: base 0.189 -> adapter 0.174 (-0.015)
- doctorow m3b: base -0.066 -> adapter 0.151 (+0.217)
- doctorow m8b: base 0.066 -> adapter 0.146 (+0.080)
- h_private 14b: base -1.979 -> adapter -1.167 (+0.812)
- h_private 4b: base -2.036 -> adapter -1.378 (+0.658)
- h_private 8b: base -2.063 -> adapter -1.524 (+0.540)
- link 14b: base -0.453 -> adapter -0.492 (-0.039)
- link 4b: base -0.437 -> adapter -0.411 (+0.026)
- link 8b: base -0.631 -> adapter -0.454 (+0.177)
- mansfield 14b: base -0.830 -> adapter -0.020 (+0.810)
- mansfield 4b: base -0.968 -> adapter -0.132 (+0.836)
- mansfield 8b: base -0.992 -> adapter 0.033 (+1.025)
- patrick 4b: base 0.007 -> adapter -0.058 (-0.065)
- patrick_v2 14b: base 0.059 -> adapter 0.004 (-0.055)
- patrick_v2 17b: base -0.161 -> adapter -0.005 (+0.156)
- patrick_v2 4b: base -0.012 -> adapter -0.038 (-0.026)
- patrick_v2 8b: base -0.097 -> adapter -0.028 (+0.069)
- patrick_v2 m14b: base 0.559 -> adapter -0.103 (-0.662)
- patrick_v2 m3b: base 0.356 -> adapter -0.008 (-0.364)
- patrick_v2 m8b: base 0.555 -> adapter -0.026 (-0.581)
- rucker 14b: base -0.209 -> adapter -0.103 (+0.106)
- rucker 4b: base -0.204 -> adapter -0.063 (+0.141)
- rucker 8b: base -0.149 -> adapter -0.134 (+0.014)
- stross 14b: base -0.612 -> adapter -0.368 (+0.244)
- stross 4b: base -0.670 -> adapter -0.321 (+0.349)
- stross 8b: base -0.693 -> adapter -0.250 (+0.443)
- sui_sin_far 14b: base -0.524 -> adapter -0.759 (-0.236)
- sui_sin_far 4b: base -0.660 -> adapter -0.722 (-0.063)
- sui_sin_far 8b: base -0.625 -> adapter -0.857 (-0.232)
- watts 14b: base -0.545 -> adapter -0.112 (+0.433)
- watts 4b: base -0.433 -> adapter -0.114 (+0.319)
- watts 8b: base -0.614 -> adapter -0.070 (+0.544)
- wharton 14b: base -0.255 -> adapter -0.032 (+0.223)
- wharton 4b: base -0.306 -> adapter -0.003 (+0.304)
- wharton 8b: base -0.455 -> adapter 0.006 (+0.460)

