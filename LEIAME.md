# Relatório do Experimento Quântico

## 👨‍🔬 Pesquisador
**Nome:** Jefferson Massami Okushigue  
**Email:** okushigue@gmail.com  

## 🔬 Métodos
- **Backend:** ibm_torino
- **Qubits:** 4 lógicos → 133 físicos
- **Técnica:** Algoritmo de Grover adaptado
- **Parâmetros:**
  ```python
  mp.dps = 50
  influence_radius = 2.0
  shots = 1024
  ```

## 📊 Resultados
```python
{
    "Taxa de sucesso": 98.0,
    "Estados mais prováveis": {
        "|0010⟩": 47.9%,
        "|0001⟩": 46.6% 
    }
}
```

## 🚀 Como Reproduzir
1. Instale os requisitos:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute:
   ```bash
   python experimento.py
   ```

## 📄 Código Principal
[O código completo está em experimento.py]

## 🔏 Validação
Hash SHA-256: `cea5610a2775abf255c8147c32bddabcccbb1476e91fcfbdb0d59763a3dc8208`
