# 🔋 LFP Battery System Specifications

## 1. Battery Configuration

| Parameter | Value |
|----------|------|
| Chemistry | Lithium Iron Phosphate (LFP) |
| Nominal Cell Voltage | 3.2 V |
| Pack Capacity | 35 kWh |
| Nominal Pack Voltage | 350 V |
| Cycle Life (standard) | 3000–4000 cycles |
| Operating SOC Range | 10% – 90% |
| End-of-Life (EOL) | 80% capacity |
| Cooling System | Liquid Cooling |
| Architecture | Modular Pack |

---

## 2. Vehicle & Motor Configuration

| Parameter | Value |
|----------|------|
| Vehicle Type | Electric Light Commercial Vehicle (eLCV) |
| Peak Motor Power | 60 kW |
| Continuous Power | 30 kW |
| Gross Vehicle Weight | ~2.5 tons |
| Daily Distance | 120–150 km |
| Application | Last-mile delivery / logistics |
| Charging Type | Overnight AC Charging |

---

## 3. Driving Conditions (MIDC - Urban)

| Parameter | Value |
|----------|------|
| Driving Cycle | Modified Indian Driving Cycle (MIDC) |
| Average Speed | 25–30 km/h |
| Maximum Speed | ~60 km/h |
| Driving Pattern | Stop-and-go |
| Acceleration | Frequent |
| Regenerative Braking | Enabled |

---

## 4. Environmental Conditions

| Parameter | Value |
|----------|------|
| Ambient Temperature | 20°C – 45°C |
| Climate Impact | High (Indian conditions) |

---

## 5. Battery Monitoring Parameters (BMS Inputs)

| Parameter | Description |
|----------|------------|
| Voltage | Cell / Pack voltage |
| Current | Charge / discharge current |
| Temperature | Cell temperature |
| State of Charge (SoC) | Battery charge level |
| Depth of Discharge (DoD) | Usage per cycle |
| Cycle Count | Number of charge-discharge cycles |
| C-rate | Charging rate |
| Time | Calendar aging factor |

---

## 6. Model Outputs

| Metric | Description |
|-------|------------|
| Remaining Cycles | Cycles left before EOL |
| Remaining Life (months) | Estimated time remaining |
| Remaining Capacity (%) | Capacity before reaching 80% |
| Energy Throughput | Total usable energy left |

---

## 7. End-of-Life Definition

Battery is considered End-of-Life (EOL) when:
- Usable capacity falls to **80% of initial capacity**

---

## 8. Annexure A: MIDC Speed vs Time Profile

### Cycle Details
- Total Duration: **1080 seconds (18 minutes)**
- Average Speed: **~27 km/h**
- Maximum Speed: **~60 km/h**
- Driving Nature: **Urban stop-and-go**

### Speed Profile Table

| Time (s) | Speed (km/h) |
|---------|-------------|
| 0 | 0 |
| 10 | 10 |
| 20 | 20 |
| 30 | 30 |
| 40 | 35 |
| 50 | 30 |
| 60 | 25 |
| 70 | 0 |
| 90 | 15 |
| 110 | 30 |
| 130 | 40 |
| 150 | 50 |
| 170 | 45 |
| 200 | 35 |
| 230 | 25 |
| 260 | 10 |
| 300 | 0 |
| 340 | 20 |
| 380 | 35 |
| 420 | 45 |
| 460 | 55 |
| 500 | 60 |
| 540 | 55 |
| 580 | 45 |
| 620 | 35 |
| 660 | 20 |
| 700 | 0 |
| 760 | 20 |
| 820 | 35 |
| 880 | 50 |
| 940 | 60 |
| 1000 | 40 |
| 1060 | 20 |
| 1080 | 0 |

---

## 📌 Notes

- This dataset represents **LFP battery behavior under Indian operating conditions**
- Includes **high temperature exposure and urban driving patterns**
- MIDC profile can be used to simulate **real-world load conditions**
- Suitable for:
  - RUL prediction
  - Degradation modeling
  - Financial and resale analysis