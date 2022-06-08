-ho riportato entrambi i grafici (la variazione del reward e del tempo di attesa) per ognuno
degli esperimenti

-le funzioni di reward utilizzate durante i test (e in che percentuale contribuiscono al reward 
totale) sono indicate nei nomi dei grafici:
1)queue fa riferimento alla reward derivante dalla lunghezza delle code;
2)avg_speed fa riferimento alla reward derivante dalla velocità media dei veicoli;
3)wait fa riferimento alla reward derivante dal tempo di attesa dei semafori.
Sono indicate inoltre eventuali variazioni dei parametri alpha e gamma del q-learning (in caso
fossero mantenuti i loro valori "standard" è indicato per l'appunto "std").

-nella cartella total_reward_function metto a confronto 2 test, il primo utilizza una funzione di 
reward "ibrida" (tiene conto di tempo di attesa dei semafori, lunghezza code e avg speed dei
veicoli) mentre il secondo distribuisce il reward solamente in base al "waiting time" dei
semafori.



