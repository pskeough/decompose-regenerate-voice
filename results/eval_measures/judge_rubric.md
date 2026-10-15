# Judge rubric (arm A0, sample 0); 0-10 per subscore; construction C1-C5, craft S1-S7

Calibration rows: `author` = the author's own held-out passages, `shuffled` = the same passages with sentences shuffled (unlabelled to the judge).

## google/gemini-3.1-flash-lite-preview (order fwd; mean per subscore)

| run | kind | n | C1 | C2 | C3 | C4 | C5 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cather CAL | author | 5 | 10.0 | 9.6 | 10.0 | 8.6 | 9.2 | 5.0 | 8.0 | 6.6 | 7.2 | 7.8 | 9.8 | 8.8 | 8.38 |
| cather CAL | shuffled | 5 | 1.6 | 2.8 | 2.0 | 0.8 | 1.0 | 5.0 | 4.0 | 2.6 | 2.6 | 3.8 | 1.6 | 1.4 | 2.43 |
| cather_base14b | gen | 46 | 10.0 | 7.2 | 9.7 | 8.5 | 5.9 | 2.5 | 5.2 | 4.7 | 3.5 | 5.0 | 9.3 | 4.9 | 6.37 |
| cather_paire6_14b | gen | 46 | 6.5 | 1.3 | 5.2 | 1.1 | 0.9 | 4.1 | 1.7 | 0.8 | 0.8 | 2.0 | 5.5 | 0.7 | 2.57 |
| chesterton CAL | author | 5 | 10.0 | 9.0 | 10.0 | 8.8 | 9.0 | 8.2 | 8.8 | 6.2 | 8.2 | 6.4 | 10.0 | 8.8 | 8.62 |
| chesterton CAL | shuffled | 5 | 1.8 | 3.0 | 2.4 | 0.8 | 1.0 | 3.4 | 4.6 | 1.8 | 4.0 | 2.6 | 1.8 | 1.6 | 2.40 |
| chesterton_base14b | gen | 39 | 9.8 | 6.7 | 9.4 | 7.9 | 5.8 | 0.9 | 4.1 | 4.2 | 2.7 | 3.9 | 8.9 | 4.3 | 5.74 |
| chesterton_base4b | gen | 39 | 9.5 | 4.0 | 8.7 | 5.7 | 2.6 | 1.8 | 3.2 | 2.0 | 1.7 | 2.6 | 8.4 | 2.9 | 4.44 |
| chesterton_base8b | gen | 39 | 9.8 | 6.0 | 9.3 | 6.8 | 4.9 | 1.3 | 3.8 | 3.7 | 2.3 | 3.4 | 8.8 | 3.9 | 5.33 |
| chesterton_basem14b | gen | 39 | 9.8 | 8.6 | 9.6 | 6.1 | 7.6 | 2.3 | 6.7 | 5.2 | 6.1 | 5.3 | 9.5 | 6.4 | 6.94 |
| chesterton_basem3b | gen | 39 | 7.6 | 6.5 | 6.8 | 5.9 | 5.1 | 1.1 | 5.1 | 3.9 | 4.4 | 3.9 | 6.5 | 4.4 | 5.11 |
| chesterton_basem3b_r2 | gen | 39 | 8.3 | 6.9 | 7.6 | 6.4 | 5.7 | 1.7 | 5.5 | 4.3 | 4.8 | 4.3 | 7.3 | 4.8 | 5.65 |
| chesterton_basem8b | gen | 39 | 9.8 | 8.3 | 9.5 | 7.5 | 7.5 | 2.8 | 6.5 | 5.1 | 6.0 | 5.1 | 9.5 | 6.1 | 6.97 |
| chesterton_paire6_14b | gen | 39 | 7.5 | 4.9 | 7.5 | 4.6 | 3.7 | 4.8 | 5.1 | 3.2 | 4.9 | 3.4 | 6.9 | 4.5 | 5.09 |
| chesterton_paire6_4b | gen | 39 | 5.1 | 3.5 | 4.5 | 2.6 | 2.4 | 4.6 | 3.4 | 2.1 | 3.2 | 2.6 | 4.3 | 2.4 | 3.38 |
| chesterton_paire6_8b | gen | 39 | 6.6 | 3.8 | 6.3 | 3.6 | 2.4 | 4.9 | 4.3 | 2.1 | 3.9 | 2.8 | 5.8 | 3.2 | 4.16 |
| chesterton_paire6_m14b | gen | 39 | 8.3 | 5.7 | 8.2 | 5.4 | 4.5 | 5.2 | 5.7 | 3.7 | 5.5 | 3.7 | 7.8 | 5.1 | 5.73 |
| chesterton_paire6_m3b | gen | 39 | 5.8 | 3.7 | 5.7 | 3.7 | 2.6 | 4.5 | 3.8 | 2.4 | 3.6 | 2.8 | 5.0 | 3.0 | 3.88 |
| chesterton_paire6_m8b | gen | 39 | 7.6 | 4.7 | 7.7 | 4.7 | 3.7 | 4.9 | 5.1 | 3.3 | 4.6 | 3.5 | 7.2 | 4.5 | 5.12 |
| chesterton_size100 | gen | 38 | 4.8 | 2.7 | 4.5 | 2.7 | 1.6 | 4.2 | 2.9 | 1.7 | 2.6 | 2.2 | 4.1 | 2.0 | 3.00 |
| chesterton_size150 | gen | 38 | 5.0 | 2.6 | 4.7 | 2.4 | 1.6 | 4.4 | 2.9 | 1.7 | 2.6 | 2.0 | 4.1 | 1.9 | 3.00 |
| chesterton_size25 | gen | 39 | 5.1 | 0.4 | 4.4 | 0.4 | 0.1 | 3.6 | 1.4 | 0.2 | 0.4 | 0.6 | 4.2 | 0.3 | 1.74 |
| chesterton_size50 | gen | 39 | 5.3 | 2.1 | 5.2 | 2.2 | 1.1 | 4.1 | 2.5 | 1.3 | 1.8 | 1.6 | 4.3 | 1.6 | 2.76 |
| doctorow CAL | author | 5 | 9.4 | 9.2 | 9.2 | 7.2 | 8.8 | 7.6 | 7.6 | 6.4 | 7.4 | 6.0 | 8.8 | 7.4 | 7.92 |
| doctorow CAL | shuffled | 4 | 2.5 | 2.5 | 3.0 | 1.0 | 1.2 | 5.0 | 3.8 | 2.0 | 2.8 | 3.0 | 2.0 | 1.2 | 2.50 |
| doctorow_base14b | gen | 42 | 9.8 | 6.4 | 9.0 | 7.0 | 4.8 | 2.7 | 3.8 | 4.0 | 2.7 | 3.9 | 8.6 | 3.9 | 5.55 |
| doctorow_base4b | gen | 42 | 9.3 | 3.5 | 8.2 | 4.9 | 2.2 | 3.7 | 3.3 | 1.9 | 2.0 | 2.5 | 8.5 | 2.7 | 4.39 |
| doctorow_basem14b | gen | 41 | 9.9 | 8.6 | 10.0 | 6.0 | 6.8 | 4.9 | 6.8 | 5.0 | 6.1 | 5.6 | 9.6 | 6.4 | 7.13 |
| doctorow_basem3b | gen | 42 | 8.1 | 6.6 | 7.0 | 5.3 | 5.0 | 2.8 | 5.2 | 3.9 | 4.9 | 4.7 | 7.0 | 4.6 | 5.43 |
| doctorow_basem8b | gen | 42 | 9.6 | 8.2 | 9.3 | 5.4 | 6.6 | 4.3 | 6.5 | 5.2 | 6.1 | 5.6 | 9.1 | 6.1 | 6.83 |
| doctorow_paire6_14b | gen | 41 | 7.8 | 4.9 | 7.4 | 4.7 | 3.5 | 5.3 | 3.7 | 3.0 | 3.4 | 3.5 | 6.8 | 3.6 | 4.79 |
| doctorow_paire6_4b | gen | 42 | 5.5 | 3.2 | 4.8 | 2.6 | 1.9 | 5.0 | 2.8 | 1.9 | 2.6 | 2.6 | 4.3 | 2.2 | 3.28 |
| doctorow_paire6_m14b | gen | 41 | 8.5 | 5.7 | 8.0 | 5.1 | 4.5 | 4.9 | 4.0 | 3.6 | 3.7 | 3.8 | 7.5 | 4.1 | 5.28 |
| doctorow_paire6_m3b | gen | 42 | 5.5 | 3.8 | 4.8 | 2.3 | 2.5 | 5.0 | 2.8 | 2.4 | 2.6 | 2.9 | 4.6 | 2.2 | 3.45 |
| doctorow_paire6_m8b | gen | 42 | 7.5 | 5.1 | 6.7 | 4.1 | 3.9 | 5.0 | 3.5 | 3.1 | 3.1 | 3.3 | 6.4 | 3.3 | 4.59 |
| doctorow_size100 | gen | 42 | 5.9 | 2.9 | 4.2 | 2.4 | 1.7 | 4.6 | 2.2 | 1.7 | 2.1 | 2.4 | 4.5 | 1.8 | 3.04 |
| doctorow_size150 | gen | 42 | 5.7 | 2.9 | 4.9 | 2.8 | 1.6 | 5.0 | 2.9 | 1.6 | 2.4 | 2.4 | 4.5 | 2.0 | 3.22 |
| doctorow_size215 | gen | 41 | 5.3 | 2.9 | 4.6 | 2.0 | 1.5 | 4.9 | 2.6 | 1.7 | 2.4 | 2.3 | 4.3 | 1.8 | 3.01 |
| doctorow_size25 | gen | 42 | 7.1 | 1.0 | 6.1 | 1.1 | 0.5 | 4.7 | 1.3 | 0.7 | 0.7 | 1.0 | 6.1 | 0.5 | 2.58 |
| doctorow_size300 | gen | 41 | 5.2 | 3.3 | 4.6 | 2.2 | 1.9 | 5.0 | 2.7 | 2.0 | 2.4 | 2.6 | 4.2 | 2.0 | 3.18 |
| doctorow_size50 | gen | 41 | 7.8 | 2.2 | 6.0 | 2.8 | 1.2 | 4.6 | 1.9 | 1.1 | 1.6 | 2.0 | 6.4 | 1.5 | 3.26 |
| doctorow_size50_s1 | gen | 41 | 6.3 | 2.1 | 5.2 | 2.7 | 1.1 | 4.6 | 2.2 | 1.1 | 1.5 | 1.9 | 5.1 | 1.4 | 2.94 |
| doctorow_size525 | gen | 42 | 5.9 | 3.1 | 4.9 | 2.6 | 1.9 | 4.6 | 2.6 | 1.8 | 2.3 | 2.5 | 4.4 | 2.0 | 3.21 |
| link CAL | author | 6 | 3.8 | 4.3 | 8.8 | 5.8 | 3.5 | 8.7 | 7.2 | 3.2 | 6.3 | 3.8 | 6.0 | 4.3 | 5.49 |
| link CAL | shuffled | 5 | 0.0 | 0.8 | 1.4 | 0.0 | 0.0 | 5.0 | 3.8 | 0.0 | 2.4 | 3.2 | 0.0 | 0.0 | 1.38 |
| link_base14b | gen | 18 | 8.4 | 5.2 | 7.7 | 5.9 | 3.2 | 3.3 | 5.0 | 2.9 | 3.1 | 3.7 | 7.4 | 3.8 | 4.96 |
| link_base4b | gen | 16 | 7.6 | 3.1 | 6.6 | 3.2 | 1.5 | 3.6 | 3.6 | 1.3 | 1.9 | 3.1 | 6.4 | 2.1 | 3.68 |
| link_paire6_14b | gen | 19 | 5.5 | 0.5 | 4.4 | 0.8 | 0.1 | 4.5 | 1.0 | 0.1 | 0.5 | 1.4 | 4.6 | 0.4 | 1.99 |
| link_paire6_4b | gen | 16 | 4.1 | 1.4 | 3.8 | 1.0 | 0.8 | 4.3 | 1.4 | 0.9 | 0.8 | 1.7 | 3.2 | 0.6 | 2.01 |
| patrick_v2 CAL | author | 5 | 8.0 | 6.2 | 7.8 | 6.0 | 5.2 | 6.4 | 4.4 | 3.0 | 4.0 | 3.0 | 7.6 | 3.6 | 5.43 |
| patrick_v2 CAL | shuffled | 5 | 2.6 | 2.8 | 2.4 | 1.4 | 1.0 | 6.2 | 2.6 | 1.6 | 2.4 | 2.2 | 2.2 | 1.2 | 2.38 |
| patrick_v2_base14b | gen | 45 | 9.8 | 6.8 | 9.7 | 8.9 | 5.6 | 3.5 | 5.6 | 4.0 | 3.8 | 4.5 | 9.7 | 4.8 | 6.40 |
| patrick_v2_base17b | gen | 45 | 8.6 | 2.1 | 7.3 | 4.4 | 1.1 | 1.4 | 2.6 | 1.0 | 1.1 | 1.9 | 7.7 | 1.6 | 3.40 |
| patrick_v2_base4b | gen | 45 | 9.5 | 3.1 | 9.3 | 5.5 | 1.8 | 2.8 | 3.9 | 1.4 | 1.8 | 2.8 | 9.2 | 2.6 | 4.48 |
| patrick_v2_base8b | gen | 45 | 9.4 | 5.4 | 8.8 | 7.6 | 3.9 | 2.6 | 4.6 | 3.0 | 2.7 | 3.8 | 9.1 | 3.9 | 5.39 |
| patrick_v2_basem14b | gen | 43 | 9.8 | 8.5 | 9.8 | 7.2 | 7.1 | 6.3 | 7.4 | 4.6 | 6.9 | 6.2 | 9.8 | 7.2 | 7.57 |
| patrick_v2_basem3b | gen | 44 | 8.4 | 7.3 | 7.9 | 7.2 | 5.9 | 4.0 | 6.1 | 4.1 | 6.2 | 5.5 | 7.9 | 5.6 | 6.35 |
| patrick_v2_basem3b_r2 | gen | 45 | 8.3 | 7.3 | 7.9 | 7.0 | 5.9 | 4.8 | 6.3 | 4.3 | 6.2 | 5.7 | 8.0 | 5.8 | 6.45 |
| patrick_v2_basem8b | gen | 44 | 9.5 | 8.5 | 9.5 | 8.4 | 7.4 | 5.9 | 7.2 | 5.1 | 7.4 | 6.5 | 9.5 | 7.2 | 7.68 |
| patrick_v2_paire6_14b | gen | 44 | 6.9 | 4.1 | 6.1 | 5.7 | 3.1 | 4.0 | 3.5 | 2.5 | 2.8 | 3.2 | 6.0 | 3.0 | 4.23 |
| patrick_v2_paire6_17b | gen | 45 | 4.2 | 2.1 | 3.4 | 1.9 | 1.2 | 4.2 | 2.3 | 1.3 | 1.8 | 2.0 | 3.3 | 1.2 | 2.40 |
| patrick_v2_paire6_4b | gen | 44 | 5.2 | 3.0 | 4.3 | 3.7 | 1.9 | 4.0 | 2.7 | 2.0 | 2.4 | 2.5 | 4.2 | 2.0 | 3.16 |
| patrick_v2_paire6_8b | gen | 45 | 6.0 | 3.7 | 5.2 | 4.7 | 2.6 | 3.7 | 3.4 | 2.3 | 2.9 | 2.8 | 5.0 | 2.7 | 3.75 |
| patrick_v2_paire6_m14b | gen | 45 | 7.8 | 5.5 | 6.9 | 5.6 | 4.6 | 3.5 | 3.6 | 3.6 | 3.0 | 3.8 | 7.2 | 3.5 | 4.87 |
| patrick_v2_paire6_m3b | gen | 45 | 5.8 | 3.4 | 4.4 | 3.7 | 2.5 | 2.8 | 2.6 | 2.5 | 2.2 | 2.7 | 4.4 | 2.3 | 3.28 |
| patrick_v2_paire6_m8b | gen | 45 | 7.2 | 5.0 | 6.0 | 5.4 | 4.2 | 3.4 | 3.4 | 3.2 | 2.7 | 3.5 | 6.2 | 3.2 | 4.44 |
| patrick_v2_size25 | gen | 45 | 7.6 | 1.8 | 7.5 | 1.9 | 1.2 | 3.8 | 1.4 | 1.6 | 0.8 | 1.7 | 7.1 | 1.0 | 3.11 |
| patrick_v2_size50 | gen | 45 | 6.2 | 2.2 | 5.0 | 3.9 | 1.2 | 3.3 | 2.3 | 0.9 | 1.6 | 2.0 | 5.0 | 1.3 | 2.91 |
| patrick_v2_size50_s1 | gen | 44 | 6.9 | 2.2 | 5.9 | 3.5 | 1.2 | 4.0 | 2.4 | 1.1 | 1.7 | 2.2 | 5.7 | 1.7 | 3.18 |
| patrick_v2_size75 | gen | 45 | 5.4 | 2.8 | 4.5 | 3.5 | 1.6 | 3.9 | 2.6 | 1.6 | 2.0 | 2.3 | 4.3 | 1.9 | 3.03 |
| rucker CAL | author | 5 | 8.2 | 8.0 | 10.0 | 7.8 | 7.4 | 7.8 | 7.0 | 4.8 | 7.0 | 4.8 | 8.4 | 6.6 | 7.32 |
| rucker CAL | shuffled | 5 | 1.6 | 2.2 | 2.8 | 0.8 | 1.2 | 6.2 | 3.2 | 1.6 | 3.4 | 2.0 | 1.6 | 0.8 | 2.28 |
| rucker_base14b | gen | 52 | 9.5 | 7.1 | 8.4 | 6.3 | 5.7 | 2.7 | 3.8 | 3.7 | 3.2 | 3.7 | 7.9 | 3.6 | 5.47 |
| rucker_base4b | gen | 46 | 9.0 | 4.5 | 7.5 | 5.3 | 3.2 | 3.3 | 3.3 | 2.3 | 2.3 | 2.7 | 7.5 | 2.7 | 4.47 |
| rucker_paire6_14b | gen | 51 | 6.5 | 5.5 | 5.5 | 3.4 | 4.1 | 5.0 | 3.8 | 3.5 | 3.5 | 3.6 | 4.9 | 3.2 | 4.36 |
| rucker_paire6_4b | gen | 48 | 4.4 | 3.7 | 3.3 | 2.3 | 2.5 | 4.7 | 2.6 | 2.6 | 2.6 | 2.9 | 3.1 | 1.9 | 3.04 |
| stross CAL | author | 6 | 10.0 | 9.3 | 10.0 | 8.7 | 8.8 | 9.3 | 8.5 | 6.3 | 8.0 | 6.3 | 9.7 | 8.7 | 8.64 |
| stross CAL | shuffled | 6 | 3.5 | 5.3 | 4.5 | 2.0 | 2.3 | 5.0 | 6.0 | 3.2 | 7.5 | 4.7 | 3.5 | 3.3 | 4.24 |
| stross_base14b | gen | 41 | 9.7 | 6.7 | 9.3 | 6.4 | 5.2 | 2.9 | 4.0 | 4.0 | 2.8 | 4.0 | 8.5 | 3.9 | 5.61 |
| stross_base4b | gen | 41 | 9.2 | 3.5 | 8.4 | 4.7 | 2.1 | 3.4 | 3.2 | 2.0 | 2.1 | 2.8 | 7.8 | 2.7 | 4.32 |
| stross_paire6_14b | gen | 41 | 7.2 | 4.6 | 6.6 | 2.9 | 3.0 | 5.3 | 3.4 | 3.1 | 3.2 | 3.4 | 5.9 | 3.3 | 4.33 |
| stross_paire6_4b | gen | 41 | 6.0 | 2.9 | 4.4 | 2.6 | 1.7 | 4.9 | 2.5 | 2.2 | 2.1 | 2.4 | 4.3 | 1.9 | 3.16 |
| watts CAL | author | 5 | 9.0 | 9.0 | 10.0 | 8.4 | 7.6 | 8.6 | 9.4 | 7.0 | 9.0 | 7.6 | 9.6 | 9.2 | 8.70 |
| watts CAL | shuffled | 5 | 2.8 | 3.2 | 4.8 | 2.0 | 1.4 | 6.8 | 5.6 | 2.2 | 5.0 | 3.4 | 2.4 | 2.4 | 3.50 |
| watts_base14b | gen | 45 | 9.9 | 5.9 | 9.4 | 6.7 | 4.7 | 2.8 | 3.7 | 3.7 | 2.7 | 3.7 | 8.9 | 3.8 | 5.48 |
| watts_base4b | gen | 45 | 9.6 | 3.1 | 8.4 | 4.2 | 1.7 | 4.0 | 3.0 | 1.5 | 1.6 | 2.2 | 8.5 | 2.5 | 4.19 |
| watts_paire6_14b | gen | 45 | 7.2 | 5.4 | 7.8 | 5.1 | 4.0 | 5.7 | 5.0 | 3.6 | 4.4 | 4.2 | 6.7 | 4.5 | 5.30 |
| watts_paire6_4b | gen | 45 | 4.8 | 3.3 | 4.8 | 2.4 | 1.8 | 5.3 | 3.1 | 1.9 | 2.8 | 2.6 | 4.2 | 2.4 | 3.29 |

Calibration gate, cather: author passages 8.38, shuffled 2.43, generations 4.47; author minus shuffled on C2 +6.80, on C5 +8.20; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, chesterton: author passages 8.62, shuffled 2.40, generations 4.59; author minus shuffled on C2 +6.00, on C5 +8.00; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, doctorow: author passages 7.92, shuffled 2.50, generations 4.17; author minus shuffled on C2 +6.70, on C5 +7.55; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, link: author passages 5.49, shuffled 1.38, generations 3.16; author minus shuffled on C2 +3.53, on C5 +3.50; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, patrick_v2: author passages 5.43, shuffled 2.38, generations 4.52; author minus shuffled on C2 +3.40, on C5 +4.20; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, rucker: author passages 7.32, shuffled 2.28, generations 4.36; author minus shuffled on C2 +5.80, on C5 +6.20; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, stross: author passages 8.64, shuffled 4.24, generations 4.36; author minus shuffled on C2 +4.00, on C5 +6.50; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, watts: author passages 8.70, shuffled 3.50, generations 4.56; author minus shuffled on C2 +5.80, on C5 +6.20; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Order stability (fwd vs rev rubric order), per subscore: Spearman rho and mean absolute shift:

- C1: rho +0.87, mean |shift| 1.39 (n=3012)
- C2: rho +0.92, mean |shift| 1.54 (n=3012)
- C3: rho +0.88, mean |shift| 1.18 (n=3012)
- C4: rho +0.88, mean |shift| 1.27 (n=3012)
- C5: rho +0.90, mean |shift| 1.02 (n=3012)
- S1: rho +0.71, mean |shift| 1.07 (n=3012)
- S2: rho +0.89, mean |shift| 0.53 (n=3012)
- S3: rho +0.90, mean |shift| 0.54 (n=3012)
- S4: rho +0.85, mean |shift| 0.68 (n=3012)
- S5: rho +0.84, mean |shift| 0.98 (n=3012)
- S6: rho +0.81, mean |shift| 1.40 (n=3012)
- S7: rho +0.92, mean |shift| 1.03 (n=3012)

## minimax/minimax-m3 (order fwd; mean per subscore)

| run | kind | n | C1 | C2 | C3 | C4 | C5 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cather CAL | author | 5 | 8.0 | 7.6 | 7.6 | 6.4 | 8.6 | 5.8 | 5.8 | 6.4 | 5.6 | 6.6 | 7.2 | 6.0 | 6.80 |
| cather CAL | shuffled | 5 | 2.2 | 2.6 | 1.8 | 1.6 | 0.8 | 3.4 | 2.6 | 2.0 | 2.6 | 2.6 | 1.8 | 1.6 | 2.13 |
| cather_base14b | gen | 41 | 7.1 | 4.4 | 5.2 | 4.7 | 2.8 | 4.0 | 3.8 | 3.5 | 3.0 | 3.4 | 5.6 | 3.2 | 4.23 |
| cather_paire6_14b | gen | 38 | 4.3 | 1.2 | 2.4 | 1.2 | 0.7 | 3.7 | 1.8 | 1.1 | 1.5 | 1.6 | 3.1 | 1.0 | 1.96 |
| chesterton CAL | author | 5 | 8.6 | 7.6 | 6.8 | 7.6 | 7.2 | 6.8 | 8.2 | 6.4 | 6.8 | 5.8 | 8.0 | 7.6 | 7.28 |
| chesterton CAL | shuffled | 5 | 3.4 | 2.2 | 2.0 | 2.4 | 1.0 | 3.6 | 4.6 | 2.2 | 3.2 | 2.6 | 2.8 | 2.4 | 2.70 |
| chesterton_base14b | gen | 39 | 7.3 | 4.7 | 5.3 | 4.4 | 3.4 | 3.7 | 3.4 | 3.6 | 3.1 | 3.8 | 6.0 | 3.2 | 4.31 |
| chesterton_base4b | gen | 39 | 6.3 | 3.0 | 4.6 | 3.4 | 1.7 | 3.5 | 2.9 | 2.2 | 2.5 | 2.8 | 5.1 | 2.5 | 3.39 |
| chesterton_base8b | gen | 39 | 6.7 | 4.1 | 4.8 | 4.1 | 2.8 | 3.8 | 3.1 | 3.3 | 2.7 | 3.2 | 5.4 | 3.0 | 3.91 |
| chesterton_basem14b | gen | 36 | 7.3 | 5.8 | 5.3 | 4.6 | 4.5 | 4.8 | 5.1 | 3.6 | 4.6 | 4.1 | 6.3 | 4.3 | 5.03 |
| chesterton_basem3b | gen | 33 | 4.9 | 4.0 | 3.2 | 3.5 | 3.0 | 4.1 | 3.9 | 2.6 | 3.8 | 3.1 | 3.9 | 2.8 | 3.57 |
| chesterton_basem3b_r2 | gen | 35 | 4.8 | 4.2 | 3.7 | 3.6 | 2.9 | 3.9 | 3.9 | 2.9 | 3.8 | 3.5 | 4.1 | 3.0 | 3.70 |
| chesterton_basem8b | gen | 34 | 7.0 | 5.5 | 5.1 | 4.6 | 4.5 | 4.6 | 4.5 | 3.2 | 4.3 | 3.9 | 6.0 | 3.9 | 4.76 |
| chesterton_paire6_14b | gen | 39 | 5.4 | 3.9 | 3.3 | 3.8 | 2.3 | 5.1 | 4.1 | 2.8 | 4.2 | 3.1 | 4.7 | 3.5 | 3.85 |
| chesterton_paire6_4b | gen | 38 | 3.3 | 2.1 | 1.8 | 2.2 | 1.1 | 3.9 | 3.1 | 1.8 | 3.1 | 2.0 | 2.6 | 1.7 | 2.39 |
| chesterton_paire6_8b | gen | 38 | 4.4 | 2.8 | 2.5 | 2.9 | 1.6 | 4.1 | 3.3 | 2.4 | 3.3 | 2.4 | 3.4 | 2.5 | 2.96 |
| chesterton_paire6_m14b | gen | 35 | 5.4 | 4.4 | 3.9 | 4.2 | 3.6 | 4.9 | 4.6 | 3.6 | 4.4 | 3.7 | 4.7 | 3.8 | 4.27 |
| chesterton_paire6_m3b | gen | 36 | 3.8 | 2.7 | 2.2 | 2.8 | 1.7 | 4.0 | 3.1 | 2.2 | 3.3 | 2.4 | 3.2 | 2.4 | 2.81 |
| chesterton_paire6_m8b | gen | 36 | 5.8 | 4.1 | 4.0 | 4.2 | 2.9 | 4.9 | 4.2 | 3.3 | 3.9 | 3.5 | 4.8 | 3.8 | 4.12 |
| chesterton_size100 | gen | 35 | 2.7 | 1.6 | 1.5 | 1.7 | 0.7 | 3.8 | 2.5 | 1.5 | 2.5 | 1.5 | 2.1 | 1.2 | 1.94 |
| chesterton_size150 | gen | 27 | 3.3 | 1.9 | 1.8 | 1.8 | 1.0 | 4.0 | 2.4 | 1.9 | 2.9 | 1.7 | 2.7 | 1.6 | 2.24 |
| chesterton_size25 | gen | 34 | 2.6 | 0.4 | 1.9 | 0.4 | 0.1 | 2.2 | 1.6 | 0.4 | 1.2 | 0.9 | 2.1 | 0.3 | 1.19 |
| chesterton_size50 | gen | 34 | 3.2 | 1.6 | 2.1 | 1.7 | 0.6 | 3.4 | 2.1 | 1.2 | 2.2 | 1.3 | 2.5 | 1.1 | 1.92 |
| doctorow CAL | author | 5 | 7.6 | 7.4 | 5.4 | 6.6 | 6.8 | 6.6 | 6.6 | 5.8 | 6.6 | 6.2 | 7.0 | 6.2 | 6.57 |
| doctorow CAL | shuffled | 3 | 3.0 | 2.0 | 2.7 | 2.0 | 1.0 | 3.3 | 3.3 | 2.0 | 2.7 | 3.0 | 2.3 | 2.0 | 2.44 |
| doctorow_base14b | gen | 38 | 7.1 | 4.2 | 4.8 | 4.3 | 2.9 | 3.8 | 2.9 | 3.7 | 2.6 | 3.3 | 5.6 | 2.9 | 4.01 |
| doctorow_base4b | gen | 38 | 6.3 | 2.6 | 4.4 | 3.3 | 1.4 | 3.8 | 2.6 | 2.0 | 2.3 | 2.3 | 4.8 | 2.1 | 3.16 |
| doctorow_basem14b | gen | 35 | 7.9 | 6.1 | 5.6 | 5.3 | 4.7 | 5.7 | 5.0 | 3.6 | 4.9 | 4.1 | 6.4 | 4.3 | 5.30 |
| doctorow_basem3b | gen | 32 | 5.2 | 4.1 | 3.7 | 3.7 | 2.5 | 4.3 | 3.8 | 2.7 | 3.8 | 3.1 | 4.2 | 3.0 | 3.67 |
| doctorow_basem8b | gen | 38 | 7.0 | 5.6 | 4.8 | 4.9 | 4.1 | 5.4 | 4.9 | 3.4 | 4.6 | 4.1 | 6.0 | 4.1 | 4.89 |
| doctorow_paire6_14b | gen | 37 | 5.3 | 3.3 | 3.4 | 3.3 | 2.1 | 4.3 | 2.8 | 2.6 | 2.9 | 2.8 | 4.1 | 2.6 | 3.30 |
| doctorow_paire6_4b | gen | 36 | 3.4 | 2.1 | 2.1 | 2.3 | 1.0 | 3.4 | 2.1 | 1.6 | 2.3 | 2.0 | 2.6 | 1.4 | 2.21 |
| doctorow_paire6_m14b | gen | 35 | 5.7 | 4.1 | 3.9 | 4.0 | 2.8 | 4.5 | 3.2 | 3.4 | 3.4 | 3.4 | 4.8 | 3.2 | 3.86 |
| doctorow_paire6_m3b | gen | 38 | 3.6 | 2.4 | 1.9 | 2.3 | 1.3 | 3.6 | 2.2 | 2.3 | 2.9 | 2.3 | 2.6 | 1.5 | 2.40 |
| doctorow_paire6_m8b | gen | 38 | 5.1 | 3.6 | 3.5 | 3.7 | 2.5 | 4.4 | 2.9 | 3.1 | 3.3 | 2.9 | 3.9 | 2.5 | 3.46 |
| doctorow_size100 | gen | 33 | 3.1 | 1.9 | 2.0 | 2.0 | 0.9 | 3.4 | 1.6 | 1.6 | 2.3 | 1.5 | 2.3 | 1.0 | 1.97 |
| doctorow_size150 | gen | 36 | 3.5 | 2.0 | 2.4 | 2.3 | 1.0 | 3.4 | 2.4 | 1.6 | 2.6 | 1.9 | 2.8 | 1.6 | 2.30 |
| doctorow_size215 | gen | 38 | 3.4 | 1.9 | 2.1 | 2.2 | 0.8 | 3.7 | 1.9 | 1.6 | 2.1 | 1.8 | 2.7 | 1.3 | 2.12 |
| doctorow_size25 | gen | 37 | 3.8 | 1.0 | 2.7 | 1.3 | 0.5 | 2.7 | 1.4 | 1.3 | 1.5 | 1.6 | 3.0 | 0.6 | 1.78 |
| doctorow_size300 | gen | 34 | 3.2 | 2.1 | 2.0 | 2.1 | 1.1 | 3.4 | 2.1 | 1.7 | 2.4 | 1.9 | 2.6 | 1.3 | 2.17 |
| doctorow_size50 | gen | 34 | 4.1 | 1.5 | 2.7 | 2.2 | 0.6 | 3.4 | 1.7 | 1.2 | 2.0 | 1.5 | 3.3 | 1.1 | 2.12 |
| doctorow_size50_s1 | gen | 35 | 3.4 | 1.4 | 2.1 | 1.8 | 0.5 | 3.2 | 1.3 | 1.2 | 1.9 | 1.4 | 2.9 | 0.8 | 1.83 |
| doctorow_size525 | gen | 34 | 3.4 | 2.1 | 2.7 | 2.4 | 1.1 | 3.4 | 2.1 | 1.9 | 2.6 | 2.2 | 3.0 | 1.6 | 2.38 |
| link CAL | author | 3 | 5.0 | 6.0 | 4.3 | 5.0 | 5.3 | 6.3 | 5.7 | 4.3 | 6.0 | 5.3 | 4.7 | 5.0 | 5.25 |
| link CAL | shuffled | 5 | 1.0 | 1.4 | 2.4 | 1.6 | 0.6 | 3.6 | 2.6 | 1.2 | 1.8 | 2.8 | 1.0 | 1.2 | 1.77 |
| link_base14b | gen | 15 | 4.9 | 3.9 | 3.5 | 3.5 | 2.5 | 4.6 | 3.7 | 2.7 | 3.1 | 3.1 | 4.0 | 3.0 | 3.56 |
| link_base4b | gen | 17 | 4.4 | 2.2 | 3.2 | 2.5 | 1.1 | 4.0 | 2.9 | 1.4 | 2.5 | 2.2 | 3.6 | 2.0 | 2.67 |
| link_paire6_14b | gen | 14 | 3.1 | 1.1 | 2.6 | 0.6 | 0.8 | 3.9 | 1.9 | 1.0 | 1.4 | 2.4 | 3.0 | 0.9 | 1.89 |
| link_paire6_4b | gen | 14 | 2.5 | 0.9 | 1.5 | 1.1 | 0.3 | 2.6 | 1.4 | 0.7 | 1.3 | 1.6 | 1.9 | 0.7 | 1.38 |
| patrick_v2 CAL | author | 5 | 5.0 | 5.0 | 3.0 | 4.0 | 3.2 | 6.0 | 3.6 | 2.2 | 4.2 | 2.6 | 4.8 | 3.0 | 3.88 |
| patrick_v2 CAL | shuffled | 5 | 1.6 | 1.6 | 1.2 | 1.8 | 0.4 | 3.8 | 2.0 | 0.8 | 1.4 | 1.4 | 1.4 | 1.0 | 1.53 |
| patrick_v2_base14b | gen | 43 | 7.7 | 4.5 | 4.7 | 4.8 | 2.9 | 4.8 | 4.1 | 3.0 | 3.1 | 3.4 | 6.4 | 3.3 | 4.39 |
| patrick_v2_base17b | gen | 45 | 5.2 | 1.5 | 3.0 | 2.7 | 0.5 | 3.2 | 2.6 | 1.1 | 1.6 | 1.8 | 4.1 | 1.3 | 2.39 |
| patrick_v2_base4b | gen | 45 | 6.5 | 2.6 | 4.4 | 3.8 | 1.2 | 4.2 | 3.2 | 1.3 | 2.3 | 2.6 | 5.4 | 2.1 | 3.30 |
| patrick_v2_base8b | gen | 44 | 6.8 | 3.8 | 4.7 | 4.7 | 2.3 | 4.6 | 4.0 | 2.7 | 2.9 | 3.2 | 5.8 | 3.0 | 4.04 |
| patrick_v2_basem14b | gen | 43 | 7.9 | 6.1 | 5.6 | 6.1 | 4.5 | 6.5 | 5.2 | 3.0 | 4.3 | 4.2 | 6.6 | 4.0 | 5.33 |
| patrick_v2_basem3b | gen | 43 | 5.3 | 4.1 | 3.6 | 4.4 | 2.7 | 5.3 | 4.2 | 2.4 | 3.4 | 3.3 | 4.3 | 3.0 | 3.82 |
| patrick_v2_basem3b_r2 | gen | 44 | 5.2 | 4.1 | 3.2 | 4.2 | 2.6 | 5.2 | 4.1 | 2.3 | 3.4 | 3.1 | 4.2 | 2.9 | 3.72 |
| patrick_v2_basem8b | gen | 41 | 7.0 | 5.7 | 4.8 | 5.5 | 4.2 | 6.2 | 5.1 | 3.1 | 4.2 | 4.3 | 5.9 | 4.1 | 5.01 |
| patrick_v2_paire6_14b | gen | 44 | 4.7 | 3.4 | 2.9 | 3.5 | 1.9 | 4.3 | 3.0 | 2.4 | 2.7 | 2.7 | 3.9 | 2.4 | 3.14 |
| patrick_v2_paire6_17b | gen | 45 | 2.7 | 1.1 | 1.9 | 1.4 | 0.4 | 3.4 | 1.8 | 1.0 | 1.7 | 1.1 | 2.1 | 0.7 | 1.60 |
| patrick_v2_paire6_4b | gen | 45 | 3.7 | 2.2 | 2.3 | 2.5 | 1.1 | 3.7 | 2.2 | 1.8 | 2.1 | 1.9 | 3.0 | 1.6 | 2.33 |
| patrick_v2_paire6_8b | gen | 45 | 4.2 | 2.7 | 2.5 | 3.4 | 1.6 | 4.4 | 2.8 | 2.1 | 2.6 | 2.2 | 3.6 | 2.1 | 2.86 |
| patrick_v2_paire6_m14b | gen | 44 | 5.9 | 4.0 | 3.5 | 3.7 | 2.8 | 4.4 | 2.9 | 3.0 | 2.4 | 3.0 | 4.6 | 2.6 | 3.57 |
| patrick_v2_paire6_m3b | gen | 43 | 4.1 | 2.4 | 2.4 | 2.7 | 1.3 | 3.5 | 2.2 | 2.0 | 1.9 | 2.1 | 3.2 | 1.6 | 2.46 |
| patrick_v2_paire6_m8b | gen | 44 | 5.3 | 3.5 | 3.2 | 3.4 | 2.4 | 4.3 | 2.6 | 2.7 | 2.3 | 2.9 | 4.3 | 2.4 | 3.28 |
| patrick_v2_size25 | gen | 45 | 5.4 | 2.0 | 3.7 | 1.8 | 1.2 | 3.5 | 1.7 | 1.6 | 1.2 | 1.9 | 4.2 | 1.1 | 2.44 |
| patrick_v2_size50 | gen | 43 | 3.9 | 1.7 | 2.2 | 2.3 | 0.7 | 3.5 | 2.0 | 1.0 | 1.5 | 1.7 | 3.0 | 1.2 | 2.06 |
| patrick_v2_size50_s1 | gen | 42 | 4.3 | 1.8 | 2.5 | 2.3 | 0.8 | 3.5 | 1.8 | 1.0 | 1.5 | 1.8 | 3.4 | 1.3 | 2.16 |
| patrick_v2_size75 | gen | 43 | 3.5 | 1.8 | 2.2 | 2.4 | 0.9 | 3.5 | 1.9 | 1.4 | 1.7 | 1.8 | 2.8 | 1.3 | 2.10 |
| rucker CAL | author | 5 | 6.4 | 7.0 | 4.8 | 5.6 | 5.6 | 7.0 | 5.8 | 4.0 | 6.6 | 4.2 | 5.8 | 5.2 | 5.67 |
| rucker CAL | shuffled | 5 | 2.6 | 2.4 | 2.4 | 1.8 | 0.6 | 3.6 | 2.8 | 2.0 | 3.6 | 2.0 | 2.6 | 1.6 | 2.33 |
| rucker_base14b | gen | 44 | 6.3 | 4.7 | 4.0 | 4.2 | 3.1 | 4.2 | 3.5 | 3.3 | 3.2 | 3.2 | 5.1 | 2.9 | 3.99 |
| rucker_base4b | gen | 48 | 5.2 | 2.9 | 3.5 | 3.2 | 1.5 | 4.1 | 3.1 | 2.0 | 2.6 | 2.4 | 4.4 | 2.2 | 3.09 |
| rucker_paire6_14b | gen | 43 | 4.9 | 4.3 | 2.7 | 3.5 | 2.9 | 4.7 | 3.1 | 3.6 | 3.3 | 2.9 | 3.8 | 2.7 | 3.52 |
| rucker_paire6_4b | gen | 39 | 3.2 | 2.6 | 1.4 | 2.2 | 1.2 | 3.5 | 2.4 | 2.4 | 2.6 | 2.1 | 2.5 | 1.5 | 2.30 |
| stross CAL | author | 5 | 8.6 | 8.0 | 7.4 | 6.8 | 7.8 | 8.0 | 7.4 | 6.0 | 7.4 | 6.6 | 8.0 | 7.4 | 7.45 |
| stross CAL | shuffled | 5 | 3.8 | 3.0 | 4.0 | 3.2 | 2.0 | 5.2 | 4.0 | 2.6 | 4.4 | 3.0 | 3.0 | 3.0 | 3.43 |
| stross_base14b | gen | 38 | 6.9 | 4.5 | 4.4 | 4.3 | 3.0 | 4.1 | 3.3 | 3.7 | 2.7 | 3.3 | 5.3 | 2.9 | 4.02 |
| stross_base4b | gen | 38 | 5.6 | 2.8 | 4.1 | 3.2 | 1.5 | 3.9 | 2.8 | 2.1 | 2.4 | 2.6 | 4.4 | 2.2 | 3.13 |
| stross_paire6_14b | gen | 36 | 4.7 | 2.9 | 2.9 | 2.9 | 1.7 | 4.4 | 2.4 | 2.9 | 3.0 | 2.6 | 3.5 | 2.3 | 3.02 |
| stross_paire6_4b | gen | 33 | 3.7 | 2.1 | 2.4 | 2.4 | 1.1 | 3.8 | 1.8 | 2.0 | 2.3 | 1.9 | 2.9 | 1.5 | 2.31 |
| watts CAL | author | 4 | 8.0 | 7.8 | 7.0 | 6.2 | 6.8 | 7.5 | 7.5 | 6.0 | 7.0 | 6.5 | 7.5 | 7.2 | 7.08 |
| watts CAL | shuffled | 5 | 2.8 | 1.8 | 2.8 | 2.0 | 0.8 | 3.8 | 4.2 | 1.8 | 3.2 | 2.4 | 2.0 | 2.2 | 2.48 |
| watts_base14b | gen | 43 | 7.3 | 4.4 | 4.8 | 4.5 | 3.0 | 4.1 | 3.3 | 3.7 | 2.9 | 3.3 | 5.7 | 3.0 | 4.14 |
| watts_base4b | gen | 44 | 6.0 | 2.4 | 4.3 | 3.3 | 1.2 | 3.9 | 2.7 | 1.7 | 2.4 | 2.4 | 4.8 | 2.0 | 3.10 |
| watts_paire6_14b | gen | 42 | 4.5 | 3.7 | 3.2 | 3.5 | 2.3 | 4.9 | 3.6 | 3.0 | 3.6 | 2.9 | 3.6 | 3.0 | 3.49 |
| watts_paire6_4b | gen | 44 | 3.2 | 2.2 | 2.0 | 2.1 | 1.0 | 4.0 | 2.6 | 2.1 | 2.6 | 2.1 | 2.4 | 1.7 | 2.32 |

Calibration gate, cather: author passages 6.80, shuffled 2.13, generations 3.14; author minus shuffled on C2 +5.00, on C5 +7.80; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, chesterton: author passages 7.28, shuffled 2.70, generations 3.34; author minus shuffled on C2 +5.40, on C5 +6.20; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, doctorow: author passages 6.57, shuffled 2.44, generations 2.95; author minus shuffled on C2 +5.40, on C5 +5.80; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, link: author passages 5.25, shuffled 1.77, generations 2.41; author minus shuffled on C2 +4.60, on C5 +4.73; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, patrick_v2: author passages 3.88, shuffled 1.53, generations 3.15; author minus shuffled on C2 +3.40, on C5 +2.80; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, rucker: author passages 5.67, shuffled 2.33, generations 3.25; author minus shuffled on C2 +4.60, on C5 +5.00; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, stross: author passages 7.45, shuffled 3.43, generations 3.15; author minus shuffled on C2 +5.00, on C5 +5.80; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Calibration gate, watts: author passages 7.08, shuffled 2.48, generations 3.25; author minus shuffled on C2 +5.95, on C5 +5.95; gate (author above generations, and real minus shuffled >= 3 on C2 or C5): PASS

Order stability (fwd vs rev rubric order), per subscore: Spearman rho and mean absolute shift:

- C1: rho +0.79, mean |shift| 1.43 (n=2391)
- C2: rho +0.82, mean |shift| 1.04 (n=2391)
- C3: rho +0.76, mean |shift| 0.96 (n=2391)
- C4: rho +0.80, mean |shift| 0.75 (n=2391)
- C5: rho +0.79, mean |shift| 0.74 (n=2391)
- S1: rho +0.51, mean |shift| 0.91 (n=2391)
- S2: rho +0.65, mean |shift| 0.83 (n=2391)
- S3: rho +0.76, mean |shift| 0.71 (n=2391)
- S4: rho +0.54, mean |shift| 0.91 (n=2391)
- S5: rho +0.66, mean |shift| 0.93 (n=2391)
- S6: rho +0.79, mean |shift| 0.96 (n=2391)
- S7: rho +0.78, mean |shift| 0.76 (n=2391)

## mistralai/mistral-small-3.2-24b-instruct (order fwd; mean per subscore)

| run | kind | n | C1 | C2 | C3 | C4 | C5 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| patrick_v2_base14b | gen | 18 | 10.0 | 10.0 | 10.0 | 5.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 9.58 |
| patrick_v2_base17b | gen | 8 | 10.0 | 6.9 | 10.0 | 2.5 | 5.0 | 9.4 | 6.2 | 5.0 | 9.4 | 7.5 | 10.0 | 6.9 | 7.40 |
| patrick_v2_base4b | gen | 45 | 10.0 | 9.4 | 10.0 | 4.7 | 8.7 | 9.9 | 9.6 | 9.2 | 10.0 | 10.0 | 10.0 | 9.4 | 9.24 |
| patrick_v2_paire6_4b | gen | 45 | 9.6 | 8.2 | 9.8 | 4.1 | 7.9 | 7.5 | 5.8 | 9.3 | 9.6 | 9.1 | 9.4 | 6.5 | 8.06 |

## Inter-judge agreement (order fwd), quadratic-weighted kappa per subscore

- google/gemini-3.1-flash-lite-preview vs minimax/minimax-m3 (n=2759): C1 0.50, C2 0.66, C3 0.32, C4 0.52, C5 0.62, S1 0.21, S2 0.66, S3 0.70, S4 0.58, S5 0.59, S6 0.46, S7 0.67
- google/gemini-3.1-flash-lite-preview vs mistralai/mistral-small-3.2-24b-instruct (n=115): C1 0.15, C2 0.12, C3 0.05, C4 0.34, C5 0.11, S1 -0.02, S2 0.17, S3 0.05, S4 0.00, S5 0.01, S6 0.13, S7 0.11
- minimax/minimax-m3 vs mistralai/mistral-small-3.2-24b-instruct (n=116): C1 0.04, C2 0.08, C3 0.01, C4 0.36, C5 0.06, S1 0.06, S2 0.14, S3 0.04, S4 0.01, S5 0.03, S6 0.04, S7 0.06

## Subscore Spearman correlation matrix (generations, all judges, order fwd)

| | C1 | C2 | C3 | C4 | C5 | S1 | S2 | S3 | S4 | S5 | S6 | S7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | +1.00 | +0.54 | +0.85 | +0.56 | +0.50 | +0.12 | +0.50 | +0.42 | +0.29 | +0.49 | +0.94 | +0.62 |
| C2 | +0.54 | +1.00 | +0.53 | +0.66 | +0.94 | +0.17 | +0.74 | +0.84 | +0.71 | +0.84 | +0.55 | +0.89 |
| C3 | +0.85 | +0.53 | +1.00 | +0.54 | +0.50 | +0.13 | +0.53 | +0.40 | +0.32 | +0.50 | +0.88 | +0.63 |
| C4 | +0.56 | +0.66 | +0.54 | +1.00 | +0.67 | +0.10 | +0.58 | +0.57 | +0.47 | +0.59 | +0.58 | +0.70 |
| C5 | +0.50 | +0.94 | +0.50 | +0.67 | +1.00 | +0.14 | +0.70 | +0.86 | +0.69 | +0.82 | +0.51 | +0.86 |
| S1 | +0.12 | +0.17 | +0.13 | +0.10 | +0.14 | +1.00 | +0.28 | +0.13 | +0.32 | +0.21 | +0.15 | +0.24 |
| S2 | +0.50 | +0.74 | +0.53 | +0.58 | +0.70 | +0.28 | +1.00 | +0.65 | +0.73 | +0.72 | +0.54 | +0.83 |
| S3 | +0.42 | +0.84 | +0.40 | +0.57 | +0.86 | +0.13 | +0.65 | +1.00 | +0.68 | +0.79 | +0.43 | +0.82 |
| S4 | +0.29 | +0.71 | +0.32 | +0.47 | +0.69 | +0.32 | +0.73 | +0.68 | +1.00 | +0.68 | +0.33 | +0.77 |
| S5 | +0.49 | +0.84 | +0.50 | +0.59 | +0.82 | +0.21 | +0.72 | +0.79 | +0.68 | +1.00 | +0.52 | +0.83 |
| S6 | +0.94 | +0.55 | +0.88 | +0.58 | +0.51 | +0.15 | +0.54 | +0.43 | +0.33 | +0.52 | +1.00 | +0.65 |
| S7 | +0.62 | +0.89 | +0.63 | +0.70 | +0.86 | +0.24 | +0.83 | +0.82 | +0.77 | +0.83 | +0.65 | +1.00 |

Total judge spend logged in these files: USD 9.49
