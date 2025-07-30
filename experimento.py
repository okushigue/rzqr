#!/usr/bin/env python3
"""
IBM Quantum Cloud — Real Grover with 3D Fractal from Riemann Zeros
Updated for compatibility with ibm_torino (Qiskit 2.1.1)
Main fixes:
- Explicit transpilation for the backend before execution
- Quantum gate adaptation for the hardware native gate set
- Improved error handling and feedback
"""

import warnings
import numpy as np
from getpass import getpass
from mpmath import mp
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import CouplingMap
import time

# Initial settings
mp.dps = 50
warnings.filterwarnings('ignore')

# ----------------------------
# 1. Riemann Zeros Analysis
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
        """Generates 3D visualization of Riemann zeros"""
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 80, height)
        z = np.linspace(0, 10, depth)
        X, Y, Z = np.meshgrid(x, y, z)
        influence_map = np.zeros((height, width, depth))

        print("Calculating influence of Riemann zeros...")
        for i, zero in enumerate(self.riemann_zeros):
            print(f"  Processing zero {i+1}/{len(self.riemann_zeros)}")
            distance = np.sqrt((X - zero.real)**2 + (Y - zero.imag)**2 + (Z)**2)
            influence = np.exp(-distance**2 / (2 * influence_radius**2))
            influence_map += influence

        influence_map = (influence_map / influence_map.max() * 255).astype(np.uint8)
        return influence_map

# ----------------------------
# 2. Fractal → Quantum State Mapping
# ----------------------------
def fractal_to_statevector(fractal_layer: np.ndarray):
    """Converts fractal layer to quantum processing data"""
    flat = fractal_layer.flatten()
    n_qubits = 4
    target_size = 2**n_qubits

    if len(flat) > target_size:
        flat = flat[:target_size]
    elif len(flat) < target_size:
        padded = np.zeros(target_size, dtype=complex)
        padded[:len(flat)] = flat
        flat = padded

    return flat, n_qubits

# ----------------------------
# 3. Grover Circuit Optimized for Real Hardware
# ----------------------------
def build_grover_circuit(marked_indices, n_qubits):
    """Builds Grover circuit optimized for real hardware"""
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Superposition using native gates (sx instead of h)
    for qubit in range(n_qubits):
        qc.sx(qubit)
        qc.rz(np.pi/2, qubit)

    qc.barrier()

    N = 2**n_qubits
    M = len(marked_indices)
    iterations = max(1, int(np.pi / 4 * np.sqrt(N / M))) if M > 0 else 0
    iterations = min(iterations, 3)

    print(f"Running {iterations} Grover iterations for {M} marked states")

    for _ in range(iterations):
        for target in marked_indices[:4]:
            if target >= N:
                continue

            binary = format(target, f'0{n_qubits}b')
            for i, bit in enumerate(binary[::-1]):
                if bit == '0':
                    qc.x(i)

            if n_qubits >= 2:
                qc.rz(np.pi/2, 1)
                qc.sx(1)
                qc.rz(np.pi/2, 1)
                qc.ecr(0, 1)
                qc.rz(-np.pi/2, 1)
                qc.sx(1)
                qc.rz(-np.pi/2, 1)

            for i, bit in enumerate(binary[::-1]):
                if bit == '0':
                    qc.x(i)

        qc.barrier()

        for qubit in range(n_qubits):
            qc.sx(qubit)
            qc.rz(np.pi/2, qubit)

        qc.x(range(n_qubits))

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

    qc.measure_all()
    return qc

# ----------------------------
# 4. Run on IBM Backend
# ----------------------------
def run_on_ibm_backend(fractal_layer, marked_indices, backend, shots=1024):
    """Runs on IBM Quantum with robust handling"""
    try:
        print("\n🔬 Preparing experiment for", backend.name)
        _, n_qubits = fractal_to_statevector(fractal_layer)

        if backend.configuration().n_qubits < n_qubits:
            print(f"❌ Backend {backend.name} does not have enough qubits")
            return None

        qc = build_grover_circuit(marked_indices, n_qubits)
        print(f"📐 Original circuit: {qc.num_qubits} qubits, {qc.size()} gates")

        print("🔄 Transpiling for the backend...")
        qc_transpiled = transpile(
            qc,
            backend=backend,
            optimization_level=3,
            layout_method="sabre",
            routing_method="sabre"
        )
        print(f"✅ Transpiled circuit: {qc_transpiled.num_qubits} qubits, {qc_transpiled.size()} gates")

        print("\n🚀 Sending job...")
        sampler = Sampler(backend)
        job = sampler.run([qc_transpiled], shots=shots)
        print(f"📤 Job ID: {job.job_id()}")

        start_time = time.time()
        while not job.done():
            elapsed = time.time() - start_time
            print(f"⏳ Status: {job.status()} | Time: {elapsed:.0f}s", end='\r')
            if elapsed > 1800:
                print("\n⏰ Timeout exceeded!")
                job.cancel()
                return None
            time.sleep(15)

        result = job.result()
        counts = result[0].data.meas.get_counts()

        print("\n📊 Results:")
        for state, count in sorted(counts.items(), key=lambda x: -x[1])[:10]:
            print(f"|{state}⟩: {count} ({(count/shots)*100:.1f}%)")

        success = sum(count for state, count in counts.items()
                    if int(state, 2) in marked_indices)
        print(f"\n🎯 Success rate: {(success/shots)*100:.1f}%")

        return counts

    except Exception as e:
        print(f"\n❌ Execution error: {str(e)}")
        return None

# ----------------------------
# 5. Main Program
# ----------------------------
if __name__ == "__main__":
    print("🌟 IBM Quantum - Grover Algorithm with Riemann Zeros")
    print("=" * 60)

    token = "YOU TOKEN HERE"
    try:
        service = QiskitRuntimeService(channel="ibm_cloud", token=token)
        backend = service.least_busy(
            simulator=False,
            operational=True,
            min_num_qubits=5
        )
        print(f"\n🔌 Connected to backend: {backend.name}")
        print(f"🔧 Basis gates: {backend.configuration().basis_gates}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        exit(1)

    riemann = RiemannZerosAnalysis()
    fractal_3d = riemann.generate_zeros_visualization_3d(width=8, height=8, depth=8)
    fractal_slice = fractal_3d[4, :4, :4]

    flat_data = fractal_slice.flatten()
    threshold = np.percentile(flat_data, 85)
    marked_indices = np.where(flat_data >= threshold)[0].tolist()[:4]

    print(f"\n🔍 {len(marked_indices)} marked states: {marked_indices}")

    results = run_on_ibm_backend(
        fractal_slice,
        marked_indices,
        backend,
        shots=1024
    )

    print("\n👋 Experiment completed!")
