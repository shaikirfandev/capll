# 28 — AI in Automotive ADAS

> **Topics:** Neural network inference on ECU, safety of ML, SOTIF, hardware accelerators

---

## 28.1 Where AI is Used in Automotive ADAS

| Application                    | AI Model Type              | ECU                       |
|--------------------------------|----------------------------|---------------------------|
| Lane detection                 | CNN (semantic segmentation)| Camera ECU (TDA4VM)       |
| Object detection (vehicles, pedestrians) | YOLO, SSD          | Domain controller         |
| Traffic sign recognition       | CNN classifier             | Camera ECU                |
| Driver monitoring (DMS)        | Face landmark CNN          | Interior camera ECU       |
| Path prediction                | LSTM / Transformer         | Domain controller         |
| Anomaly detection (vibration)  | Autoencoder                | Powertrain ECU            |
| Occupancy grid mapping         | CNN + Kalman filter        | Fusion ECU                |

---

## 28.2 Neural Network Inference on ECU Hardware

### Hardware Accelerators

```
Nvidia Orin (L3+ production, 2023+):
  - 12× ARM Cortex-A78AE + 2048-core Ampere GPU
  - 2× NVDLA (Deep Learning Accelerator, 32 TOPS each)
  - 254 TOPS total
  - AUTOSAR Adaptive + CUDA + TensorRT

TI TDA4VM (L2+ production, Bosch MPC5 successor):
  - 2× ARM Cortex-A72 + 6× C7x DSP
  - MMA (Matrix Multiply Accelerator): 8 TOPS
  - Used in: Bosch MPC5-series, Continental ARS6xx radar fusion

NXP S32G (domain controller, gateway):
  - 4× Cortex-A53 + 3× Cortex-M7
  - No dedicated DLA — uses ARM NEON for small inference
  - Primarily for SOME/IP gateway, safety monitor

Arm Ethos-U65 (microNPU, edge inference):
  - Used inside Cortex-M SoCs
  - 512 GOPS at 1W
  - Use case: driver monitoring on embedded camera
```

### TensorRT Deployment Pipeline

```
Training (PyTorch/TensorFlow) → ONNX export → TensorRT optimisation → ECU deployment

TensorRT optimisations:
  1. Layer fusion: Conv + BN + ReLU → single CUDA kernel
  2. FP16/INT8 quantisation: 4× speedup, 0.5-2% accuracy drop
  3. Batch size 1 (real-time inference, one frame at a time)
  4. Engine serialisation: save .trt engine to flash (avoid re-optimisation on boot)

Latency example: YOLOv5s on TDA4VM DLA:
  Full precision (FP32): 45ms/frame
  INT8 quantisation:     12ms/frame  ← target for 30fps camera
```

---

## 28.3 Model Compression for ECU Deployment

```
Techniques:
  1. Quantisation: FP32 → INT8 weights
     - Post-training quantisation: 5% accuracy risk
     - Quantisation-aware training (QAT): < 1% accuracy drop, preferred
     
  2. Pruning: remove near-zero weights
     - Structured pruning: remove entire channels (hardware-friendly)
     - Unstructured pruning: fine-grained (harder to accelerate on DLA)
     
  3. Knowledge distillation: small "student" model mimics large "teacher"
     - Student inference is fast on ECU
     - Teacher used only in training
     
  4. Neural Architecture Search (NAS): automatically find efficient architecture
     - EfficientDet: designed for constrained inference
     - MobileNet V3: optimised for ARM NEON

ECU constraints example (Camera ECU):
  Memory: 2 MB for model weights (Flash)
  Latency: < 15ms inference (30fps camera)
  Power: < 5W (thermal budget)
  → Choose: MobileNetV3 + INT8 on Ethos-U or TDA4VM MMA
```

---

## 28.4 Safety of ML in ISO 26262 (SOTIF)

```
ISO 26262 vs SOTIF:
  ISO 26262: handles known hazards from systematic and random failures
  SOTIF (ISO 21448): handles unknown hazards from sensor/algorithm limitations
    - "The system works as intended, but the intended behaviour is unsafe"
    - Example: CNN detects a cut-out pedestrian as background → no AEB

SOTIF for ML-based perception:
  Step 1: Identify triggering conditions (snow, night, backlight, unusual object shapes)
  Step 2: Operational Design Domain (ODD): define where ML is valid
  Step 3: Evaluate known unsafe scenarios (functional insufficiency)
  Step 4: Validate unknown scenarios via extensive real-world + simulation data
  Goal: reduce unknown unsafe scenarios to acceptable level

Evidence required:
  - Training data diversity report (geographic, weather, lighting conditions)
  - Test set performance metrics (mAP, false negative rate, confusion matrix)
  - Scenario coverage report (edge cases captured in test set)
  - ODD violation detection mechanism (sensor health monitor)
```

---

## 28.5 V2X — AI for Cooperative Driving

```
V2X (Vehicle to Everything):
  V2V (Vehicle-to-Vehicle): share position, speed, intent with nearby vehicles
  V2I (Vehicle-to-Infrastructure): traffic light phase, road hazard broadcast
  V2P (Vehicle-to-Pedestrian): smartphone broadcasts pedestrian position

Standards:
  DSRC (IEEE 802.11p): 5.9 GHz, 300m range, < 2ms latency (US, older)
  C-V2X (3GPP PC5): LTE/5G sidelink, 300m, < 10ms (EU, modern)

AI in V2X:
  1. Intent prediction: ML model predicts turning/braking of V2V-connected vehicles
  2. Collective perception: aggregate perception from 5 nearby vehicles → extended FoV
  3. Traffic flow optimisation: ML at intersection schedules V2I phase timing

Safety challenge: V2X message spoofing (malicious vehicle)
  Mitigation: Certificate-based authentication (C-V2X uses PKI from ETSI)
  ISO/SAE 21434 requirement: validate all V2X message signatures before trusting
```

---

## 28.6 Interview Questions

**L1:**
1. What is the difference between ISO 26262 and SOTIF?
2. What is INT8 quantisation and why is it used on ECUs?
3. Name two hardware accelerators used for ADAS neural network inference.

**L2:**
4. How would you deploy a YOLO object detection model on a TDA4VM ECU?
5. What is knowledge distillation and when would you use it for ECU deployment?
6. How does SOTIF require you to handle triggering conditions for ML-based lane detection?

**L3:**
7. Design the safety argument for an ML-based pedestrian detection function at ASIL B.
8. How would you validate an INT8-quantised model against its FP32 reference to satisfy ISO 26262 Part 6?
9. What is the role of operational design domain (ODD) monitoring in a production ADAS system?
10. How do you achieve traceability from a safety requirement to a neural network test dataset in an ISO 26262 evidence package?
