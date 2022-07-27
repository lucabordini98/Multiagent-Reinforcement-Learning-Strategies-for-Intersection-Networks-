-Utilizzando una versione aggiornata di gym, la classe Monitor non dovrebbe essere presente.
All'interno del file ./ray/rlib/env/utils.py basta sostituirlo con wrappers.RecordVideo.
-In realtà ora, per chissà quale motivo, parte...il problema è che non sembra apprendere nulla (in output
le reward min, max e media risultano avere valori Nan).
-In più non capisco se c'è un modo per forza l'esecuzione direttamente sulla GPU, ricordo di esserci riuscito con gym
quindi immagino sia possibile pure in questo caso.