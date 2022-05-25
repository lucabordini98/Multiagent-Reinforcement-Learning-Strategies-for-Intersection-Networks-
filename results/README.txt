Per lo 'switch' tra le funzioni di reward ho utilizzato quelle presenti nella classe 'TrafficLights'

-std_rnd_std: alterna 2 periodi di flussi di veicoli deterministici con uno stocastico
-800k_aplha_025: 800k episodi di training in cui alpha è impostato a 0.25 (invece di 0.1)
-800k_gamma_075: 800k episodi di training in cui gamma è impostato a 0.75 (invece di 0.99)
-800k_aplha_018_gamma_087: 800k episodi di training in cui alpha è impostato a 0.18 e gamma a 0.87
-800k_rew1_rew2: dopo 400k episodi cambio la funzione di reward  (l'esperimento che prevedeva lo switch tra più di 2 funzioni ha dato lo stesso risultato)
-performance_std_800k: 800k episodi di training con parametri base, no switch tra flussi deterministici/stocastici e funzione di reward fissa
-ql_1M_switch: alterna 2 periodi di flussi di veicoli stocastici con uno deterministico


