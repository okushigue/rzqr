# 🚀 Quantum Riemann-Grover Experiment  
**Jefferson Massami Okushigue** | okushigue@gmail.com  
[![License: Q-RGE](https://img.shields.io/badge/License-Quantum_Riemann_Grover_Experiment-blue)](LICENSE)  
*"Quando a matemática de Riemann encontra o hardware quântico da IBM"*  

---

## 🔮 Visão Geral
Implementação do algoritmo de Grover em hardware real (`ibm_torino`), usando padrões fractais derivados dos zeros da função zeta de Riemann. Resultados com **98% de sucesso** - acima da média para circuitos quânticos reais.

```python
# Trecho emblemático
qc = QuantumCircuit(4)
for qubit in range(4):
    qc.sx(qubit)  # Porta nativa do IBMQ
    qc.rz(np.pi/2, qubit)  # Rotação precisa
