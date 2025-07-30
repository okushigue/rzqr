#!/usr/bin/env python3
"""
IBM Quantum Cloud — Grover real com fractal 3D dos zeros de Riemann
Versão corrigida para compatibilidade com ibm_torino (Qiskit 2.1.1)
Principais correções:
- Transpilação explícita para o backend antes da execução
- Adaptação das portas quânticas para o conjunto nativo do hardware
- Melhor tratamento de erros e feedback
"""

import warnings
import numpy as np
from getpass import getpass
from mpmath import mp
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import CouplingMap
import time

# Configurações iniciais
mp.dps = 50
warnings.filterwarnings('ignore')

# ----------------------------
# 1. Análise dos Zeros de Riemann
# ----------------------------
class RiemannZerosAnalysis:
    def __init__(self):
        self.riemann_zeros = [
            0.5 + 14.134725141734693790457251983562470270784257115699243175685567460149963429809256764949010393171561925605677j,
            0.5 + 21.022039638771554992628479593896902777334340524902781697051613785106945509387854598126624953102086304946962j,
            0.5 + 25.010857580145688763213790991799003137537184972136540040842843127686655938088011325069644167050488631636574j,
            0.5 + 30.424876125859513210311897530584091320181560023707304449380072317787397832121667316002761394642124309051521j,
            0.5 + 32.935061587739189690662368964074903488812715603517039009280003440784901428893593237466426865110409906842556j
        ]
    
    def generate_zeros_visualization_3d(self, width=16, height=16, depth=16, influence_radius=2.0):
        """Gera visualização 3D dos zeros de Riemann"""
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 80, height)
        z = np.linspace(0, 10, depth)
        X, Y, Z = np.meshgrid(x, y, z)
        influence_map = np.zeros((height, width, depth))
        
        print("Calculando influência dos zeros de Riemann...")
        for i, zero in enumerate(self.riemann_zeros):
            print(f"  Processando zero {i+1}/{len(self.riemann_zeros)}")
            distance = np.sqrt((X - zero.real)**2 + (Y - zero.imag)**2 + (Z)**2)
            influence = np.exp(-distance**2 / (2 * influence_radius**2))
            influence_map += influence
        
        influence_map = (influence_map / influence_map.max() * 255).astype(np.uint8)
        return influence_map

# ----------------------------
# 2. Mapear fractal → estado quântico
# ----------------------------
def fractal_to_statevector(fractal_layer: np.ndarray):
    """Converte camada do fractal em dados para processamento quântico"""
    flat = fractal_layer.flatten()
    n_qubits = 4  # Mantido em 4 qubits para compatibilidade
    target_size = 2**n_qubits
    
    if len(flat) > target_size:
        flat = flat[:target_size]
    elif len(flat) < target_size:
        padded = np.zeros(target_size, dtype=complex)
        padded[:len(flat)] = flat
        flat = padded
    
    return flat, n_qubits

# ----------------------------
# 3. Circuito Grover Otimizado para Hardware Real
# ----------------------------
def build_grover_circuit(marked_indices, n_qubits):
    """Constrói circuito de Grover otimizado para hardware real"""
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # Superposição usando portas nativas (sx em vez de h)
    for qubit in range(n_qubits):
        qc.sx(qubit)
        qc.rz(np.pi/2, qubit)  # Equivalente a H
    
    qc.barrier()
    
    # Número de iterações otimizado
    N = 2**n_qubits
    M = len(marked_indices)
    iterations = max(1, int(np.pi / 4 * np.sqrt(N / M))) if M > 0 else 0
    iterations = min(iterations, 3)  # Limite reduzido para hardware real
    
    print(f"Executando {iterations} iterações de Grover para {M} estados marcados")
    
    for _ in range(iterations):
        # Oracle simplificado para hardware
        for target in marked_indices[:4]:  # Limita a 4 estados marcados
            if target >= N:
                continue
                
            binary = format(target, f'0{n_qubits}b')
            
            # Aplicar X nos qubits que devem ser 0
            for i, bit in enumerate(binary[::-1]):
                if bit == '0':
                    qc.x(i)
            
            # Implementação nativa do CZ
            if n_qubits >= 2:
                qc.rz(np.pi/2, 1)
                qc.sx(1)
                qc.rz(np.pi/2, 1)
                qc.ecr(0, 1)  # Usando ECR que é nativo em muitos backends IBM
                qc.rz(-np.pi/2, 1)
                qc.sx(1)
                qc.rz(-np.pi/2, 1)
            
            # Desfazer X
            for i, bit in enumerate(binary[::-1]):
                if bit == '0':
                    qc.x(i)
        
        qc.barrier()
        
        # Difusor adaptado
        for qubit in range(n_qubits):
            qc.sx(qubit)
            qc.rz(np.pi/2, qubit)
        
        qc.x(range(n_qubits))
        
        # CZ adaptado
        if n_qubits >= 2:
            qc.rz(np.pi/2, 1)
            qc.sx(1)
            qc.rz(np.pi/2, 1)
            qc.ecr(0, 1)
            qc.rz(-np.pi/2, 1)
            qc.sx(1)
            qc.rz(-np.pi/2, 1)
        
        qc.x(range(n_qubits))
        
        for qubit in range(n_qubits):
            qc.sx(qubit)
            qc.rz(np.pi/2, qubit)
        
        qc.barrier()
    
    # Medição adaptada
    qc.measure_all()
    
    return qc

# ----------------------------
# 4. Execução no Backend IBM
# ----------------------------
def run_on_ibm_backend(fractal_layer, marked_indices, backend, shots=1024):
    """Executa no IBM Quantum com tratamento robusto"""
    try:
        print("\n🔬 Preparando experimento para", backend.name)
        _, n_qubits = fractal_to_statevector(fractal_layer)
        
        # Verificar se o backend suporta o número necessário de qubits
        if backend.configuration().n_qubits < n_qubits:
            print(f"❌ Backend {backend.name} não tem qubits suficientes")
            return None
        
        # Construir circuito adaptado
        qc = build_grover_circuit(marked_indices, n_qubits)
        print(f"📐 Circuito original: {qc.num_qubits} qubits, {qc.size()} gates")
        
        # Transpilar explicitamente para o backend
        print("🔄 Transpilando para o backend...")
        qc_transpiled = transpile(
            qc,
            backend=backend,
            optimization_level=3,
            layout_method="sabre",
            routing_method="sabre"
        )
        print(f"✅ Circuito transpilado: {qc_transpiled.num_qubits} qubits, {qc_transpiled.size()} gates")
        
        # Executar no backend
        print("\n🚀 Enviando job...")
        sampler = Sampler(backend)
        job = sampler.run([qc_transpiled], shots=shots)
        print(f"📤 Job ID: {job.job_id()}")
        
        # Monitorar execução
        start_time = time.time()
        while not job.done():
            elapsed = time.time() - start_time
            print(f"⏳ Status: {job.status()} | Tempo: {elapsed:.0f}s", end='\r')
            if elapsed > 1800:
                print("\n⏰ Timeout excedido!")
                job.cancel()
                return None
            time.sleep(15)
        
        # Obter resultados
        result = job.result()
        counts = result[0].data.meas.get_counts()
        
        # Exibir resultados
        print("\n📊 Resultados:")
        for state, count in sorted(counts.items(), key=lambda x: -x[1])[:10]:
            print(f"|{state}⟩: {count} ({(count/shots)*100:.1f}%)")
        
        # Calcular taxa de sucesso
        success = sum(count for state, count in counts.items() 
                    if int(state, 2) in marked_indices)
        print(f"\n🎯 Taxa de sucesso: {(success/shots)*100:.1f}%")
        
        return counts
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {str(e)}")
        return None

# ----------------------------
# 5. Programa Principal
# ----------------------------
if __name__ == "__main__":
    print("🌟 IBM Quantum - Algoritmo de Grover com Zeros de Riemann")
    print("=" * 60)
    
    # Configuração do IBM Quantum
    token = "YOU TOKEN HERE"  # Substitua pelo seu token
    try:
        service = QiskitRuntimeService(channel="ibm_cloud", token=token)
        backend = service.least_busy(
            simulator=False,
            operational=True,
            min_num_qubits=5
        )
        print(f"\n🔌 Conectado ao backend: {backend.name}")
        print(f"🔧 Basis gates: {backend.configuration().basis_gates}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        exit(1)
    
    # Gerar dados do fractal
    riemann = RiemannZerosAnalysis()
    fractal_3d = riemann.generate_zeros_visualization_3d(width=8, height=8, depth=8)
    fractal_slice = fractal_3d[4, :4, :4]  # Fatia 4x4 para 4 qubits
    
    # Identificar estados marcados
    flat_data = fractal_slice.flatten()
    threshold = np.percentile(flat_data, 85)
    marked_indices = np.where(flat_data >= threshold)[0].tolist()[:4]  # Limita a 4 estados
    
    print(f"\n🔍 {len(marked_indices)} estados marcados: {marked_indices}")
    
    # Executar no hardware quântico
    results = run_on_ibm_backend(
        fractal_slice,
        marked_indices,
        backend,
        shots=1024
    )
    
    print("\n👋 Experimento concluído!")
