-2x2 comparison fa una comparazione (in una rete 2x2 deterministica) tra una reward function (1) che considera:la 'waiting
time reward'+ la'queue reward' e la 'avg speed reward' ed una reward function (2) che invece della 'avg speed reward'
introduce una global reward basata sul 'global waiting time'

-1x2 comparison fa una comparazione (in una rete 1x2 deterministica) tra una reward function che utilizza solo 'waiting
time' ed una il cui reward dipende anche da 'avg speed' e 'queue'

-basic_vs_nomintime: comparazione su rete 2x2. La curva blu indica il total waiting time in caso di condizioni 
"classiche" (quindi usando semafori con green time min=8 secondi e reward function=80% waiting time+15%queue+5% global
waiting time), la curva arancione indica il training avuto con la stessa reward function ma avendo impostato gree min 
time=0 e delta time=0 (con delta time si indica ogni quanti secondi l'agente esegue un'azione).
