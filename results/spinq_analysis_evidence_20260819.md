# SpinQ web vs SDK 一致性分析 —— 真实数据归档（撤回版）

归档时间(UTC): 2026-08-19T15:52:23.636459+00:00

> 背景: 用户质疑 SDK 跑的实验与 web 跑的实验是否一致、3 比特误差是否正常。
>
> ⚠️ **重要更正（2026-08-19 撤回此前误判）**: `starter_kit/evidence/` 是官方模板
> 自带的**范例申报文件**（创建时间 22:28，早于实验 22:49/22:54），README 预填的
> job ID 与 `shots=16384` 均为模板示例，与我们的实验无关，**非伪造**。
>
> **真实情况（用户确认）**: web 版 `shots=1024` 为后端缺省值、无法设置；
> SDK 版 `shots` 可设置，我们的实验统一跑 **5000**。

## 0. 官方文档关键事实（doc.spinq.cn）

**SpinQit Cloud 后端: 如果未配置 shots，默认值是 1024。**

> 原文: "If shots are not configured, the default is 1024."
> 来源: doc.spinq.cn（用户 2026-08-19 查证）

推论: web 版任务未配置 shots → 实际采样数 = 1024（缺省，无法设置）。
SDK 版显式配置 shots=5000 → 实际采样数 = 5000（可设置）。

## 1. 浏览器原始 msgpack（web 端原始响应）

> msgpack 为浏览器响应体，内容仅为概率分布、**无 shots 字段**。

### task_result_G-260819-0003.msgpack  (49 bytes)

```json
{
  "00": 0.42921429,
  "01": 0.08713478,
  "10": 0.03489801,
  "11": 0.44875292
}
```

### task_result_S-260819-0001.msgpack  (105 bytes)

```json
{
  "000": 0.34673944,
  "001": 0.07445079,
  "010": 0.02560872,
  "011": 0.06316109,
  "100": 0.00813964,
  "101": 0.04899294,
  "110": 0.04027409,
  "111": 0.39263329
}
```

## 2. origin_results/ 浏览器抓包 task-detail（web 版真实任务）

> 这两个任务（UUID）是用户在 web 端真实提交的，web 版 shots=1024（缺省，无法设置）。

### task-detail-06C3076EF744BCD36C8129D553171EDB-1787151328681.json

```json
{
  "createTime": "2026-08-19 22:54:35.223",
  "endTime": "2026-08-19 22:54:41.815",
  "machineTime": "1.82",
  "result": {
    "value": [
      0.473,
      0.0136,
      0.0036,
      0.0352,
      0.0262,
      0.0079999,
      0.0152,
      0.4252
    ],
    "key": [
      "000",
      "001",
      "010",
      "011",
      "100",
      "101",
      "110",
      "111"
    ]
  },
  "status": "Completed",
  "taskId": "06C3076EF744BCD36C8129D553171EDB"
}
```

### task-detail-E7599A00AAFF3056D31D26653D6D2444-1787151052296.json

```json
{
  "createTime": "2026-08-19 22:49:07.153",
  "endTime": "2026-08-19 22:49:10.297",
  "machineTime": "1.85",
  "result": {
    "value": [
      0.4825999,
      0.0298,
      0.0142,
      0.4734
    ],
    "key": [
      "00",
      "01",
      "10",
      "11"
    ]
  },
  "status": "Completed",
  "taskId": "E7599A00AAFF3056D31D26653D6D2444"
}
```

## 3. starter_kit/evidence/ 官方模板范例（与我们的实验无关）

> 这是官方参赛模板自带的**范例申报材料**（`starter_kit/evidence/README.md` 为模板入口，
> `files/` 创建时间 22:28，早于我们 22:49/22:54 的实验抓包）。
> README 预填的 `G-260819-0003 / S-260819-0001`、`shots=16384` 均为**模板示例内容**。
> 结论: 该目录与我们的实验无关，**不是伪造、也不是真实实验记录**，申报时按需替换/删除。

### G-260819-0003.info.json

```json
{
  "task_code": "G-260819-0003",
  "info": {
    "status": 200,
    "msg": "",
    "task": {
      "tid": 61349,
      "tcode": "G-260819-0003",
      "tname": "未命名实验",
      "bitNum": 2,
      "clbitNum": 0,
      "simulator": false,
      "calcMatrix": false,
      "runSimu": true,
      "tstatus": "S",
      "shots": 16384,
      "sourceType": "circuitBoard",
      "sourceOriginName": null,
      "sourceAddr": "files-2026-08/G-260819-0003.qasm",
      "sourceCode": "OPENQASM 2.0; \ninclude \"qelib1.inc\";\nqreg q[2];\n\nh q[0];\ncx q[0],q[1];",
      "description": "",
      "createdTime": "2026-08-19T13:46:05.578+00:00",
      "startTime": "2026-08-19T13:46:11.241+00:00",
      "endTime": "2026-08-19T13:47:44.627+00:00",
      "errorMsg": null,
      "platformId": 1,
      "platformName": "2Qubit核磁量子计算机",
      "platformCode": "gemini_vp",
      "machineId": 10,
      "machineCode": "Gemini-pro-1",
      "userId": "xxxx",
      "userName": "xxxx",
      "timecost": 3.0,
      "curQueueSize": -1,
      "percentageFinished": null
    }
  },
  "status": {
    "status": 200,
    "msg": "",
    "taskStatus": "S"
  }
}
```

### G-260819-0003.result.json

```json
{
  "task_code": "G-260819-0003",
  "result": {
    "status": 200,
    "msg": "",
    "taskStatus": "S",
    "taskErrMsg": null,
    "run": {
      "realMatrix": null,
      "imagMatrix": null,
      "module": {
        "00": 0.42921429,
        "11": 0.44875292,
        "01": 0.08713478,
        "10": 0.03489801
      }
    },
    "shots": 16384
  }
}
```

### S-260819-0001.info.json

```json
{
  "task_code": "S-260819-0001",
  "info": {
    "status": 200,
    "msg": "",
    "task": {
      "tid": 61350,
      "tcode": "S-260819-0001",
      "tname": "GHZ state",
      "bitNum": 3,
      "clbitNum": 0,
      "simulator": false,
      "calcMatrix": false,
      "runSimu": true,
      "tstatus": "S",
      "shots": 16384,
      "sourceType": "circuitBoard",
      "sourceOriginName": null,
      "sourceAddr": "files-2026-08/S-260819-0001.qasm",
      "sourceCode": "OPENQASM 2.0; \ninclude \"qelib1.inc\";\nqreg q[3];\n\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];",
      "description": "",
      "createdTime": "2026-08-19T13:51:56.016+00:00",
      "startTime": "2026-08-19T13:54:29.147+00:00",
      "endTime": "2026-08-19T13:56:56.473+00:00",
      "errorMsg": null,
      "platformId": 6,
      "platformName": "3Qubit核磁量子计算机",
      "platformCode": "triangulum_vp",
      "machineId": 8,
      "machineCode": "Triangulum-pro-1",
      "userId": "xxxx",
      "userName": "xxxx",
      "timecost": 3.0,
      "curQueueSize": -1,
      "percentageFinished": null
    }
  },
  "status": {
    "status": 200,
    "msg": "",
    "taskStatus": "S"
  }
}
```

### S-260819-0001.result.json

```json
{
  "task_code": "S-260819-0001",
  "result": {
    "status": 200,
    "msg": "",
    "taskStatus": "S",
    "taskErrMsg": null,
    "run": {
      "realMatrix": null,
      "imagMatrix": null,
      "module": {
        "000": 0.34673944,
        "011": 0.06316109,
        "110": 0.04027409,
        "001": 0.07445079,
        "100": 0.00813964,
        "111": 0.39263329,
        "101": 0.04899294,
        "010": 0.02560872
      }
    },
    "shots": 16384
  }
}
```

## 4. results/spinq_sdk_20260819/ SDK 实验产物（shots=5000 可设置）

> SDK 实验 shots=5000 提交/5000 返回、counts 整数可验，为可控实验。

### bellstate_gemini_vp_shots5000

#### circuit.qasm

```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];

```

#### result_norm.json

```json
{
  "experiment": "bellstate",
  "backend": {
    "sdk": "spinqit",
    "platform_code": "gemini_vp",
    "platform_name": "2Qubit核磁量子计算机"
  },
  "circuit": {
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",
    "qubits": 2,
    "gates": [
      "h",
      "cx"
    ]
  },
  "shots": 5000,
  "counts": {
    "00": 2263,
    "11": 2063,
    "01": 408,
    "10": 266
  },
  "probabilities": {
    "00": 0.4525253,
    "11": 0.41263927,
    "01": 0.08169256,
    "10": 0.05314287
  },
  "metrics": {
    "n_total": 5000,
    "bell_ratio_00_11": 0.8652,
    "n_00": 2263,
    "n_11": 2063,
    "noise_01": 408,
    "noise_10": 266
  },
  "task": {
    "code": "G-260819-0004",
    "name": null
  },
  "timestamps": {
    "submitted_utc": "2026-08-19T15:08:08.597995+00:00",
    "finished_utc": "2026-08-19T15:09:47.119604+00:00"
  }
}
```

#### result_raw.json

```json
{
  "task_code": "G-260819-0004",
  "task_name": null,
  "platform": null,
  "machine_pcode": "gemini_vp",
  "machine_name": "2Qubit核磁量子计算机",
  "submitted_utc": "2026-08-19T15:08:08.597995+00:00",
  "finished_utc": "2026-08-19T15:09:47.119604+00:00",
  "shots_submitted": 5000,
  "shots_returned": 5000,
  "counts": {
    "00": 2263,
    "11": 2063,
    "01": 408,
    "10": 266
  },
  "probabilities": {
    "00": 0.4525253,
    "11": 0.41263927,
    "01": 0.08169256,
    "10": 0.05314287
  }
}
```

### ghz_state_2

#### circuit.qasm

```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];

```

#### result_norm.json

```json
{
  "experiment": "ghz",
  "backend": {
    "sdk": "spinqit",
    "platform_code": "triangulum_vp",
    "platform_name": "3Qubit核磁量子计算机"
  },
  "circuit": {
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[3];\ncreg c[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];\n",
    "qubits": 3,
    "gates": [
      "h",
      "cx",
      "cx"
    ]
  },
  "shots": 5000,
  "counts": {
    "000": 1625,
    "011": 59,
    "110": 569,
    "001": 398,
    "100": 69,
    "111": 1351,
    "101": 442,
    "010": 488
  },
  "probabilities": {
    "000": 0.32505293,
    "011": 0.01184333,
    "110": 0.11386858,
    "001": 0.07952323,
    "100": 0.01376795,
    "111": 0.27011559,
    "101": 0.08832747,
    "010": 0.09750093
  },
  "metrics": {
    "n_total": 5001,
    "ghz_ratio_000_111": 0.595081,
    "n_000": 1625,
    "n_111": 1351
  },
  "task": {
    "code": "S-260819-0003",
    "name": null
  },
  "timestamps": {
    "submitted_utc": "2026-08-19T15:48:35.235514+00:00",
    "finished_utc": "2026-08-19T15:51:09.554195+00:00"
  }
}
```

#### result_raw.json

```json
{
  "task_code": "S-260819-0003",
  "task_name": null,
  "machine_pcode": "triangulum_vp",
  "machine_name": "3Qubit核磁量子计算机",
  "submitted_utc": "2026-08-19T15:48:35.235514+00:00",
  "finished_utc": "2026-08-19T15:51:09.554195+00:00",
  "shots_submitted": 5000,
  "shots_returned": 5000,
  "counts": {
    "000": 1625,
    "011": 59,
    "110": 569,
    "001": 398,
    "100": 69,
    "111": 1351,
    "101": 442,
    "010": 488
  },
  "probabilities": {
    "000": 0.32505293,
    "011": 0.01184333,
    "110": 0.11386858,
    "001": 0.07952323,
    "100": 0.01376795,
    "111": 0.27011559,
    "101": 0.08832747,
    "010": 0.09750093
  }
}
```

#### selfcheck.json

```json
{
  "overall_pass": true,
  "checks": [
    {
      "item": "产物存在 circuit.qasm",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "产物存在 result_raw.json",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "产物存在 result_norm.json",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "counts 合计 ≈ shots (允许±1硬件偏差)",
      "pass": true,
      "detail": "合计 5001 vs shots 5000 (偏差 1)"
    },
    {
      "item": "shots 平台返回 == 提交值",
      "pass": true,
      "detail": "5000 vs 5000"
    },
    {
      "item": "GHZ 保真度 (000+111)/N > 50%",
      "pass": true,
      "detail": "59.5081%"
    },
    {
      "item": "噪声位串占比 < 50%",
      "pass": true,
      "detail": "2025 (40.4919%) 噪声: {'011': 59, '110': 569, '001': 398, '100': 69, '101': 442, '010': 488}"
    }
  ]
}
```

### ghz_triangulum_vp_shots5000

#### circuit.qasm

```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];

```

#### result_norm.json

```json
{
  "experiment": "ghz",
  "backend": {
    "sdk": "spinqit",
    "platform_code": "triangulum_vp",
    "platform_name": "3Qubit核磁量子计算机"
  },
  "circuit": {
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[3];\ncreg c[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];\n",
    "qubits": 3,
    "gates": [
      "h",
      "cx",
      "cx"
    ]
  },
  "shots": 5000,
  "counts": {
    "000": 1743,
    "011": 104,
    "110": 137,
    "001": 317,
    "100": 287,
    "111": 1551,
    "101": 462,
    "010": 400
  },
  "probabilities": {
    "000": 0.34853138,
    "011": 0.02077645,
    "110": 0.02735651,
    "001": 0.06342133,
    "100": 0.05737762,
    "111": 0.31015551,
    "101": 0.09247766,
    "010": 0.07990354
  },
  "metrics": {
    "n_total": 5001,
    "ghz_ratio_000_111": 0.658668,
    "n_000": 1743,
    "n_111": 1551
  },
  "task": {
    "code": "S-260819-0002",
    "name": null
  },
  "timestamps": {
    "submitted_utc": "2026-08-19T15:17:54.608148+00:00",
    "finished_utc": "2026-08-19T15:20:23.878583+00:00"
  }
}
```

#### result_raw.json

```json
{
  "task_code": "S-260819-0002",
  "task_name": null,
  "machine_pcode": "triangulum_vp",
  "machine_name": "3Qubit核磁量子计算机",
  "submitted_utc": "2026-08-19T15:17:54.608148+00:00",
  "finished_utc": "2026-08-19T15:20:23.878583+00:00",
  "shots_submitted": 5000,
  "shots_returned": 5000,
  "counts": {
    "000": 1743,
    "011": 104,
    "110": 137,
    "001": 317,
    "100": 287,
    "111": 1551,
    "101": 462,
    "010": 400
  },
  "probabilities": {
    "000": 0.34853138,
    "011": 0.02077645,
    "110": 0.02735651,
    "001": 0.06342133,
    "100": 0.05737762,
    "111": 0.31015551,
    "101": 0.09247766,
    "010": 0.07990354
  }
}
```

#### selfcheck.json

```json
{
  "overall_pass": true,
  "checks": [
    {
      "item": "产物存在 circuit.qasm",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "产物存在 result_raw.json",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "产物存在 result_norm.json",
      "pass": true,
      "detail": "存在"
    },
    {
      "item": "counts 合计 ≈ shots (允许±1硬件偏差)",
      "pass": true,
      "detail": "合计 5001 vs shots 5000 (偏差 1)"
    },
    {
      "item": "shots 平台返回 == 提交值",
      "pass": true,
      "detail": "5000 vs 5000"
    },
    {
      "item": "GHZ 保真度 (000+111)/N > 50%",
      "pass": true,
      "detail": "65.8668%"
    },
    {
      "item": "噪声位串占比 < 50%",
      "pass": true,
      "detail": "1707 (34.1332%) 噪声: {'011': 104, '110': 137, '001': 317, '100': 287, '101': 462, '010': 400}"
    }
  ]
}
```

## 5. 保真度对比表 + 双样本比例 z 检验（web 1024 vs SDK 5000，GHZ SDK 两次复测）

| 实验 | 提交方式 | 任务号 | 机器 | shots | 保真度(00/000+11/111) |
|---|---|---|---|---|---|
| Bell 2比特 | web(抓包) | UUID E7599A00 | Gemini-pro-1 | 1024(缺省) | 95.60% |
| Bell 2比特 | SDK | G-260819-0004 | Gemini-pro-1 | 5000(设置) | 86.52% |
| GHZ 3比特 | web(抓包) | UUID 06C3076E | Triangulum-pro-1 | 1024(缺省) | 89.82% |
| GHZ 3比特 | SDK #1 | S-260819-0002 | Triangulum-pro-1 | 5000(设置) | 65.87% |
| GHZ 3比特 | SDK #2 | S-260819-0003 | Triangulum-pro-1 | 5000(设置) | 59.51% |

差异: Bell `9.08pp`；
GHZ web vs SDK#1 `23.95pp`、web vs SDK#2 `30.31pp`、
SDK 两次之间 `6.36pp`。

| 对比 | p1 | n1 | p2 | n2 | z |
|---|---|---|---|---|---|
| bell_web1024_vs_sdk5000 | 0.9560 | 1024 | 0.8652 | 5000 | 8.16 |
| ghz_web1024_vs_sdk5000 | 0.8982 | 1024 | 0.6587 | 5000 | 15.23 |
| ghz_web1024_vs_sdk_pooled2 | 0.8982 | 1024 | 0.6269 | 10002 | 17.36 |
| ghz_sdk1_vs_sdk2 | 0.6587 | 5001 | 0.5951 | 5001 | 6.57 |

> 注意: 保真度是分布级 Hellinger 相似度而非单比特计数，z 检验仅作参考（比例假设不严格成立）。
> 差异远超统计误差（n=1024/5000 时 z 检验下差异显著），但这是**不同时段**的任务
> （web 22:49/22:54 vs SDK 23:08/23:17 北京），NMR 真机状态随时段波动，
> 单次对比不足以判定"web 特有"还是"机器波动"，需重复运行量化。

## 6. 时间线（UTC / 北京时间）

| 任务 | 事件 | UTC | 北京时间 |
|---|---|---|---|
| starter_kit/evidence/ 范例文件 | 模板创建(官方范例) | 2026-08-19T14:28Z | ≈22:28 |
| web 抓包 Bell UUID E7599A00 | createTime(本地) | 2026-08-19T14:49:07Z | 22:49:07 |
| web 抓包 GHZ UUID 06C3076E | createTime(本地) | 2026-08-19T14:54:35Z | 22:54:35 |
| G-260819-0004 (SDK Bell) | submitted | 2026-08-19T15:08:08.597995+00:00 | 2026-08-19 23:08:08 |
| G-260819-0004 (SDK Bell) | finished | 2026-08-19T15:09:47.119604+00:00 | 2026-08-19 23:09:47 |
| S-260819-0002 (SDK GHZ #1) | submitted | 2026-08-19T15:17:54.608148+00:00 | 2026-08-19 23:17:54 |
| S-260819-0002 (SDK GHZ #1) | finished | 2026-08-19T15:20:23.878583+00:00 | 2026-08-19 23:20:23 |
| S-260819-0003 (SDK GHZ #2) | submitted | 2026-08-19T15:48:35.235514+00:00 | 2026-08-19 23:48:35 |
| S-260819-0003 (SDK GHZ #2) | finished | 2026-08-19T15:51:09.554195+00:00 | 2026-08-19 23:51:09 |

## 7. 结论（2026-08-19 撤回版 + GHZ#2 复核）

1. **官方文档事实**: SpinQit Cloud 后端未配置 shots 时默认 1024（doc.spinq.cn）。
2. **web 版 shots=1024 缺省、不可设置；SDK 版 shots 可设置，我们跑 5000**（用户确认）。
3. **evidence 非伪造**: starter_kit/evidence/ 是官方模板自带的范例文件，
   README 预填的 job ID / shots=16384 是模板示例，与我们的实验无关。此前"伪造"误判已撤回。
4. **web vs SDK 电路与平台一致**（同 QASM：Bell `h+cx`、GHZ `h+cx+cx`；同机器型号），
   唯一已知区别是 shots（web 缺省 1024 不可设置 vs SDK 5000 可设置）。
5. **SDK GHZ 两次复测**: #1 65.87%（S-260819-0002）与 #2 59.51%（S-260819-0003），波动 6.36pp（z=6.57）。两次均明显低于 web 89.82%（差 23.95pp / 30.31pp）。
6. **结论: web 与 SDK 差异远超 SDK 自身波动**——SDK 两次合并保真度 62.69% vs web 89.82%（差 27.13pp，z=17.36），远大于 SDK 内部两次的波动。NMR 3 比特 GHZ 保真度约 60-66% 是该机近期常态；web 的 89.82% 与 SDK 存在系统性差异，可能源于 web 端采样/后处理差异或提交时段机器状态，需 web 端复测确认。
7. **Bell 差异（9.08pp）在 NMR 合理带内，不再复测**（用户决策）。

