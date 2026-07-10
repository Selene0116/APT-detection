# APT-detection

APT-detection 是一个面向高级持续性威胁（Advanced Persistent Threat, APT）的溯源图异常检测与攻击场景构建项目。项目以系统审计日志为输入，将进程、文件、网络连接等系统实体及其交互关系建模为异构有向溯源图，通过行为语义增强特征、掩码图自编码和基线偏离检测实现异常节点识别，并进一步基于异常节点恢复攻击上下文，生成结构化攻击场景图。

本项目可支撑“基于大模型的多源异构信息融合研判技术研究”中的 APT 攻击检测、场景化特征识别、正常行为基线构建、异常行为识别和系统原型展示等任务。

## Overview

APT 攻击通常具有长期潜伏、阶段推进、行为隐蔽和跨实体传播等特点。单条日志或孤立告警难以完整描述攻击过程，安全分析人员需要从大量审计日志中识别异常实体，并进一步理解这些实体之间的因果关系和攻击路径。

本项目围绕该问题构建了完整的 APT 检测流程：

1. 将系统审计日志解析为异构有向溯源图。
2. 提取节点类型、入边事件分布、出边事件分布等行为语义特征。
3. 使用掩码图自编码模型学习正常系统行为的潜在表示分布。
4. 将学习到的正常行为分布作为溯源图行为基线。
5. 基于节点相对正常行为基线的偏离程度计算异常分数。
6. 输出异常节点列表、异常得分、预测标签和检测指标。
7. 以高置信异常节点为种子，恢复攻击上下文并生成候选攻击场景图。

## Dataset

项目主要使用 DARPA Transparent Computing 数据集中的 E3 阶段数据进行实验，重点包括 Trace、THEIA 和 Cadets 三个子数据集。
### Dataset Sources and References

数据集和数据处理流程主要参考以下公开仓库与资料：

| 来源 | 链接 | 用途 |
|---|---|---|
| DARPA Transparent Computing | [darpa-i2o/Transparent-Computing](https://github.com/darpa-i2o/Transparent-Computing) | DARPA TC 数据集说明、E3/E5 阶段数据下载与数据格式说明 |

本项目实验数据来源于 DARPA Transparent Computing 数据集，并在本项目代码中进一步完成实体/事件解析、异构溯源图构建、行为语义特征增强、正常行为基线学习和异常节点检测。


| 数据集 | 数据类型 | 典型内容 | 用途 |
|---|---|---|---|
| Trace | 系统审计日志/溯源图 | 进程执行、文件访问、网络通信等系统行为 | APT 异常节点检测与攻击场景构建 |
| THEIA | 系统审计日志/溯源图 | Linux 主机环境下的系统实体交互记录 | APT 异常节点检测与攻击场景构建 |
| Cadets | 系统审计日志/溯源图 | FreeBSD 主机环境下的服务进程利用、反弹连接、内部侦查等行为 | APT 异常节点检测与误报控制验证 |

审计日志在预处理阶段被映射为异构有向溯源图：

- 节点：进程、文件、网络连接、内存对象、管道对象等系统实体。
- 边：读、写、执行、连接、创建等实体交互事件。
- 标签：正常节点与攻击相关节点，用于实验评估。

## Method

### Heterogeneous Provenance Graph Construction

系统审计日志记录了进程执行、文件读写、网络通信等底层事件。项目首先将这些事件转换为异构有向溯源图，其中节点表示系统实体，边表示实体之间的信息流或控制流关系。通过溯源图建模，项目能够保留攻击行为中的因果依赖、时间演化和跨实体传播关系。

### Behavior-Semantic Feature Enhancement

APT 攻击节点与正常节点在实体类型上可能非常相似。例如，正常系统进程和攻击进程都属于进程节点，仅依赖节点类型或局部结构容易产生误报。因此，项目在节点类型编码基础上进一步构造行为语义增强特征：

- 节点类型编码：描述节点属于进程、文件、网络连接等哪类系统实体。
- 入边事件分布：描述该实体被哪些系统行为作用，例如被读取、被写入、被连接等。
- 出边事件分布：描述该实体主动发起了哪些行为，例如读取文件、创建进程、发起网络连接等。

行为语义增强特征使节点表示同时包含“实体类别”和“行为角色”两类信息，能够更细粒度地区分低频正常行为和攻击相关异常行为。

### Masked Graph Autoencoder Baseline

项目使用掩码图自编码模型学习正常系统行为的潜在表示分布。模型在训练阶段通过节点属性重构和图结构重构学习正常节点在语义特征和结构上下文上的稳定模式。

训练完成后，正常节点在潜在空间中形成相对稳定的分布，该分布可视为系统正常行为基线。该基线不是人工规则或固定阈值，而是模型从审计日志和溯源图结构中自动学习得到的正常行为表示。

### Baseline-Deviation Anomaly Detection

测试阶段，模型将待检测节点映射到同一潜在空间，并计算其与正常行为基线之间的偏离程度。项目采用 K 近邻距离度量节点与正常节点潜在分布的距离：

1. 正常节点潜在表示集合构成正常行为基线。
2. 测试节点经过图编码器得到潜在表示。
3. 使用 KNN 距离衡量测试节点相对正常行为基线的偏离程度。
4. 偏离程度越高，异常分数越高，节点越可能参与攻击行为。

该方法能够在不依赖大量攻击样本参与训练的情况下完成攻击相关节点定位。

### Attack Scenario Construction

异常检测输出通常是离散异常节点，难以直接展示完整攻击过程。项目进一步以高置信异常节点为种子，在动态图序列中恢复其上下文关系，并结合时间约束、图约简、时序衰减边权和社区发现生成候选攻击场景图。

攻击场景构建模块将离散异常节点组织为结构化攻击路径，输出核心节点、核心边、攻击上下文和摘要图，用于辅助安全分析人员理解攻击链条。

## Feature List

项目中的特征可以分为“原始解析字段”“进入模型的显式特征”“训练得到的潜在表示”和“异常检测输出特征”四类。

### Raw Parsed Fields

从 DARPA TC 原始 CDM JSON 日志中解析的主要字段包括：

| 字段 | 来源 | 含义 | 用途 |
|---|---|---|---|
| `uuid` | 实体定义记录 | 系统实体唯一标识 | 构建节点 ID 映射 |
| `subject` | Event 记录 | 事件发起实体 | 构建有向边源节点 |
| `predicateObject` | Event 记录 | 事件作用对象 | 构建有向边目标节点 |
| `predicateObject2` | Event 记录 | 第二作用对象 | 补充构建事件相关边 |
| `type` | 实体/事件记录 | 实体类型或事件类型 | 构建节点类型、边类型特征 |
| `timestampNanos` | Event 记录 | 事件发生时间戳 | 事件排序、持续时间统计、场景恢复 |
| `path` | FileObject 记录 | 文件路径 | 辅助解释文件节点 |
| `name` | Subject 记录 | 进程名称 | 辅助解释进程节点 |
| `remoteAddress` | NetFlowObject 记录 | 远端网络地址 | 辅助解释网络连接节点 |

### Explicit Model Features

实际进入模型训练和检测的显式特征如下：

| 特征名称 | 代码位置 | 维度 | 计算方式 | 作用 |
|---|---|---:|---|---|
| 节点类型 one-hot | `utils/loaddata.py::transform_graph` | `node_feature_dim` | 对 `g.ndata["type"]` 做 one-hot 编码 | 表示节点属于进程、文件、网络连接等哪类实体 |
| 边类型 one-hot | `utils/loaddata.py::transform_graph` | `edge_feature_dim` | 对 `g.edata["type"]` 做 one-hot 编码 | 表示读、写、执行、连接等交互事件类型 |
| 出边事件类型直方图 | `utils/add_behavior_features.py::enhance_graph` | `edge_feature_dim` | 对每个节点作为源节点的边类型进行 one-hot 计数、`log1p` 压缩、max 归一化 | 描述节点主动发起了哪些行为 |
| 入边事件类型直方图 | `utils/add_behavior_features.py::enhance_graph` | `edge_feature_dim` | 对每个节点作为目标节点的边类型进行 one-hot 计数、`log1p` 压缩、max 归一化 | 描述节点被哪些行为作用 |
| 行为语义增强节点特征 | `utils/add_behavior_features.py::enhance_graph` | `node_feature_dim + 2 * edge_feature_dim` | 拼接“节点类型 one-hot + behavior_weight * 出边直方图 + behavior_weight * 入边直方图” | 同时刻画实体类型和行为角色 |

行为语义增强后的节点特征维度计算公式为：

```text
new_node_feature_dim = old_node_feature_dim + 2 * edge_feature_dim
```

其中：

- `old_node_feature_dim`：原始节点类型 one-hot 维度。
- `edge_feature_dim`：边事件类型 one-hot 维度。
- `behavior_weight`：行为语义特征权重，用于控制入边/出边行为直方图对节点表示的影响。

### Node and Edge Feature Dimensions

`node_feature_dim` 和 `edge_feature_dim` 不是人工预先写死的一组字段，而是从 DARPA TC CDM JSON 数据中动态统计得到的特征维度。

| 维度名称 | 对应代码 | 来源字段 | 含义 |
|---|---|---|---|
| `node_feature_dim` | `utils/loaddata.py::preload_entity_level_dataset` | 实体记录中的 `type` 字段 | 当前数据集中出现过的系统实体类型数量 |
| `edge_feature_dim` | `utils/loaddata.py::preload_entity_level_dataset` | Event 记录中的 `type` 字段 | 当前数据集中出现过的系统事件类型数量 |

代码处理逻辑如下：

```text
node_feature_dim = max(g.ndata["type"]) + 1
edge_feature_dim = max(g.edata["type"]) + 1
```

因此，节点类型 one-hot 的每一维对应一个 CDM 实体类型，边类型 one-hot 的每一维对应一个 CDM Event 类型。行为语义增强特征中的入边/出边直方图也使用同一套 `edge_feature_dim` 事件类型空间。

按当前代码解析口径，节点类型特征的候选集合主要来自 CDM 实体记录中的实体 `type` 字段，以及部分无 `type` 字段但由记录类型识别出的对象类型。完整候选列表如下：

| 类型 | 含义 |
|---|---|
| `SUBJECT_PROCESS` | 进程主体 |
| `SUBJECT_THREAD` | 线程主体 |
| `SUBJECT_UNIT` | 执行单元；代码中会跳过该类型 |
| `SUBJECT_BASIC_BLOCK` | 基本块主体 |
| `SUBJECT_OTHER` | 其他主体类型 |
| `FILE_OBJECT_FILE` | 普通文件 |
| `FILE_OBJECT_DIR` | 目录 |
| `FILE_OBJECT_CHAR` | 字符设备文件 |
| `FILE_OBJECT_BLOCK` | 块设备文件 |
| `FILE_OBJECT_UNIX_SOCKET` | Unix socket 文件对象 |
| `FILE_OBJECT_PIPE` | 管道文件对象 |
| `FILE_OBJECT_LINK` | 链接文件 |
| `FILE_OBJECT_UNKNOWN` | 未知文件对象 |
| `NetFlowObject` | 网络连接/网络流对象 |
| `MemoryObject` | 内存对象 |
| `UnnamedPipeObject` | 未命名管道对象 |
| `SrcSinkObject` | 源/汇对象 |
| `Principal` | 用户、账户或安全主体对象 |
| `Host` | 主机对象；代码中读取实体时会跳过 Host 记录 |

按当前代码解析口径，边事件类型特征来自 CDM Event 记录中的 `type` 字段。完整候选列表如下：

| 类型 | 含义 |
|---|---|
| `EVENT_ACCEPT` | 接受连接 |
| `EVENT_ADD_OBJECT_ATTRIBUTE` | 添加对象属性 |
| `EVENT_BIND` | 绑定地址或端口 |
| `EVENT_CHANGE_PRINCIPAL` | 切换用户/安全主体 |
| `EVENT_CHECK_FILE_ATTRIBUTES` | 检查文件属性 |
| `EVENT_CLONE` | 克隆进程或线程 |
| `EVENT_CLOSE` | 关闭对象 |
| `EVENT_CONNECT` | 建立网络连接 |
| `EVENT_CREATE_OBJECT` | 创建对象 |
| `EVENT_CREATE_THREAD` | 创建线程 |
| `EVENT_EXECUTE` | 执行程序 |
| `EVENT_EXIT` | 进程或线程退出 |
| `EVENT_FCNTL` | 文件控制操作 |
| `EVENT_FLOWS_TO` | 信息流动关系 |
| `EVENT_FORK` | 创建子进程 |
| `EVENT_LINK` | 创建链接 |
| `EVENT_LOADLIBRARY` | 加载库文件 |
| `EVENT_LOGIN` | 登录 |
| `EVENT_LOGOUT` | 登出 |
| `EVENT_MMAP` | 内存映射 |
| `EVENT_MODIFY_FILE_ATTRIBUTES` | 修改文件属性 |
| `EVENT_MODIFY_PROCESS` | 修改进程属性或状态 |
| `EVENT_MPROTECT` | 修改内存保护属性 |
| `EVENT_OPEN` | 打开对象 |
| `EVENT_OTHER` | 其他事件 |
| `EVENT_READ` | 读取文件、内存或其他对象 |
| `EVENT_RECVFROM` | 从网络接收数据 |
| `EVENT_RECVMSG` | 接收消息 |
| `EVENT_RENAME` | 重命名对象 |
| `EVENT_SENDMSG` | 发送消息 |
| `EVENT_SENDTO` | 发送网络数据 |
| `EVENT_SIGNAL` | 发送信号 |
| `EVENT_TRUNCATE` | 截断文件 |
| `EVENT_UNLINK` | 删除链接或文件 |
| `EVENT_UPDATE` | 更新对象或状态 |
| `EVENT_WAIT` | 等待进程或事件 |
| `EVENT_WRITE` | 写入文件、内存或其他对象 |

不同子数据集实际出现的类型可能不同，因此最终 one-hot 维度和下标顺序以解析当前数据集时生成的映射为准。例如，如果 Cadets 数据中没有出现某个事件类型，该类型就不会占用 Cadets 的 `edge_feature_dim` 维度。



如果已经完成图构建，也可以直接读取 `metadata.json` 查看维度：

```bash
cat data/cadets/graphs/metadata.json
cat data/cadets_bfeat05/graphs/metadata.json
```

其中增强后的 `node_feature_dim` 应满足：

```text
增强后 node_feature_dim = 原始 node_feature_dim + 2 * edge_feature_dim
```

### Feature Dimensions by Dataset

三个 DARPA TC 子数据集包含的实体类型和事件类型不同，因此原始节点特征维度、边特征维度以及语义增强后的节点特征维度也不同。根据实验数据预处理结果，三个数据集的特征维度如下：

| 数据集 | 原始节点特征维度 `old_node_feature_dim` | 边特征维度 `edge_feature_dim` | 行为语义增强后节点特征维度 `new_node_feature_dim` | 计算方式 |
|---|---:|---:|---:|---|
| Trace | 11 | 23 | 57 | `11 + 2 * 23 = 57` |
| THEIA | 5 | 17 | 39 | `5 + 2 * 17 = 39` |
| Cadets | 6 | 27 | 60 | `6 + 2 * 27 = 60` |

含义说明：

- Trace 中实体类型和事件类型较丰富，原始节点类型维度为 11，边事件类型维度为 23。
- THEIA 中实体类型相对更少，原始节点类型维度为 5，边事件类型维度为 17。
- Cadets 中边事件类型最丰富，原始节点类型维度为 6，边事件类型维度为 27。
- 行为语义增强后，节点特征由“原始节点类型 one-hot + 出边事件分布 + 入边事件分布”拼接得到，因此维度为 `old_node_feature_dim + 2 * edge_feature_dim`。

需要注意的是，`node_feature_dim` 和 `edge_feature_dim` 的具体下标顺序由 `utils/trace_parser.py` 在解析数据时动态生成。解析器会按照当前数据集中首次遇到的实体类型和事件类型依次分配编号。因此，若要得到“Trace 的 11 个节点特征分别是什么、THEIA 的 5 个节点特征分别是什么、Cadets 的 6 个节点特征分别是什么”，应以实际数据解析得到的映射为准。


### Auxiliary Graph Attributes

在溯源图构建阶段，代码还会为边保留一些辅助统计属性。这些属性主要用于图构建、解释和后续扩展，当前模型训练中主要使用 `type` 生成边类型 one-hot。

| 属性 | 代码位置 | 含义 |
|---|---|---|
| `type` | `utils/trace_parser.py::read_single_graph` | 聚合边的主导事件类型，参与边类型 one-hot |
| `first_type` | `utils/trace_parser.py::read_single_graph` | 同一节点对首次出现的事件类型 |
| `frequency` | `utils/trace_parser.py::read_single_graph` | 同一有向节点对上的交互次数 |
| `duration` | `utils/trace_parser.py::read_single_graph` | 同一节点对从首次交互到末次交互的时间跨度 |
| `first_ts` | `utils/trace_parser.py::read_single_graph` | 首次交互时间戳 |
| `last_ts` | `utils/trace_parser.py::read_single_graph` | 末次交互时间戳 |
| `type_count` | `utils/trace_parser.py::read_single_graph` | 同一节点对上出现过的事件类型数量 |

### Learned Features and Detection Scores

| 特征/结果 | 代码位置 | 含义 |
|---|---|---|
| 节点潜在表示 | `model/autoencoder.py::GMAEModel.embed` | GAT 编码器输出的节点 embedding，用于表示节点的结构和行为语义 |
| 正常行为基线 | `eval.py` | 训练图中正常节点 embedding 的集合 |
| KNN 平均距离 | `model/eval.py::evaluate_entity_level_using_knn` | 测试节点与正常行为基线之间的近邻距离 |
| 异常分数 | `model/eval.py::evaluate_entity_level_using_knn` | `score = distances / mean_distance`，表示节点偏离正常基线的程度 |
| 预测标签 | `model/eval.py::evaluate_entity_level_using_knn` | 根据最佳阈值将节点判定为正常或异常 |
| 检测指标 | `model/eval.py::evaluate_entity_level_using_knn` | AUC、Precision、Recall、F1、TN、FP、FN、TP |

## Code Modules

| 代码模块名称 | 基于什么数据 | 实现什么功能 | 输入是什么 | 输出是什么 | 关键模型/算法 | 对应合同指标 |
|---|---|---|---|---|---|---|
| 数据读取与预处理模块 | DARPA TC 系统审计日志、预处理后的节点/边数据 | 读取原始日志或图数据，清洗实体与事件信息，形成后续模型可处理的数据结构 | 原始审计日志、节点文件、边文件、标签文件 | 标准化节点集合、边集合、节点标签、事件类型信息 | 日志解析、实体抽取、事件类型映射 | 多源日志支持；总数据量不少于 4 万 |
| 溯源图构建模块 | 系统调用、进程行为、文件访问、网络通信记录 | 将系统审计事件转换为异构有向溯源图，刻画实体之间的因果依赖关系 | 节点实体、边事件、时间戳、事件类型 | 异构有向溯源图、动态图快照序列 | Provenance Graph 构建、动态图切分 | 场景化特征识别能力；系统原型 |
| 行为语义特征模块 | 溯源图节点与边事件分布 | 统计节点入边和出边上的事件类型分布，构造表达实体行为角色的节点语义特征 | 节点类型编码、入边事件类型、出边事件类型、边方向信息 | 行为语义增强节点表示 | 入边事件分布、出边事件分布、节点类型编码、行为特征加权 | 场景化特征识别能力 |
| 正常行为基线构建模块 | 正常系统行为对应的溯源图数据 | 学习正常节点在潜在空间中的稳定表示分布，形成图结构与行为语义联合基线 | 行为语义增强节点特征、图结构邻接关系 | 正常节点潜在表示分布、训练后的图编码器 | 掩码图自编码、图注意力网络、节点属性重构、结构重构 | 基线自动构建能力 |
| 异常节点检测模块 | 测试阶段溯源图节点及其行为语义特征 | 计算节点相对正常行为基线的偏离程度，识别攻击相关异常节点 | 测试图节点特征、图结构、训练好的编码器、正常节点表示集合 | 异常节点列表、异常分数、预测标签、Precision、Recall、F1、AUC、FP、FN | KNN 距离异常评分、基线偏离检测、阈值判定 | 异常行为识别精度不低于 80%；误报率控制 |
| 攻击场景构建模块 | 异常节点检测结果、原始动态图序列 | 将离散异常节点恢复为结构化攻击场景，辅助分析攻击链条 | 高置信异常节点、节点异常分数、动态图快照、边事件时间戳 | 候选攻击场景图、核心节点、核心边、攻击路径、摘要图 | 异常种子筛选、时间约束上下文抽取、图约简、时序衰减边权、Louvain 社区发现、显著性筛选 | 场景化特征识别能力；系统原型 |
| 结果评估与可视化模块 | 检测结果、攻击场景图、真实标签 | 统计检测性能并生成可展示结果 | 异常检测输出、真实标签、场景构建结果 | 指标表、异常节点列表、场景图、可视化图片或结果文件 | Precision/Recall/F1/AUC 评估、误报/漏报统计、图可视化 | 原型系统展示；验收答辩材料 |

## Input and Output

### Input

项目的典型输入包括：

- 系统审计日志或已处理后的图数据。
- 节点信息：节点编号、节点类型、实体名称或实体属性。
- 边信息：源节点、目标节点、事件类型、事件方向、时间戳。
- 标签信息：正常节点、攻击相关节点。
- 模型参数：隐藏维度、图注意力层数、掩码比例、行为特征权重、KNN 近邻数等。

### Output

项目的典型输出包括：

- 行为语义增强后的节点特征。
- 训练后的图编码器或模型权重。
- 每个节点的异常分数。
- 异常节点预测标签。
- Precision、Recall、F1、AUC、FP、FN 等检测指标。
- 候选攻击场景图。
- 攻击场景中的核心节点、核心边和攻击路径。
- 可用于系统展示或答辩 PPT 的异常节点列表、统计图和场景摘要图。

## SOP / Run

本节说明如何从环境配置、数据准备、特征增强、模型训练到模型评估完整运行项目。

### 1. Environment Setup

推荐使用 Python 3.8。项目主要依赖 PyTorch、DGL、Scikit-learn 等库。

```bash
git clone https://github.com/Selene0116/APT-detection.git
cd APT-detection

python3.8 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果使用 CPU 环境，需根据本机环境调整 PyTorch 和 DGL 安装方式。`requirements.txt` 中默认使用 CUDA 11.6 对应的 PyTorch 版本。

### 2. Data Preparation

项目支持两种数据准备方式。

#### Option A: Use Preprocessed Graph Data

如果已经有预处理后的图数据，直接放置为以下结构：

```text
data/
  cadets/
    graphs/
      metadata.json
      malicious.pkl
      train0.pkl
      train1.pkl
      ...
      test0.pkl
      test1.pkl
      ...
  theia/
    graphs/
      metadata.json
      malicious.pkl
      train0.pkl
      ...
      test0.pkl
      ...
  trace/
    graphs/
      metadata.json
      malicious.pkl
      train0.pkl
      ...
      test0.pkl
      ...
```

其中 `metadata.json` 至少需要包含：

```json
{
  "node_feature_dim": 6,
  "edge_feature_dim": 27,
  "malicious": ["malicious_node_indices", "malicious_node_names"],
  "n_train": 4,
  "n_test": 1
}
```

字段含义：

- `node_feature_dim`：原始节点类型数量。
- `edge_feature_dim`：边事件类型数量。
- `malicious`：恶意节点索引及名称。
- `n_train`：训练图数量。
- `n_test`：测试图数量。

#### Option B: Preprocess DARPA TC Raw Logs

如果从 DARPA TC 原始 JSON 日志开始处理，需要先下载对应数据，并将文件放到对应目录。

```text
data/
  trace/
    ta1-trace-e3-official-1.json
    ta1-trace-e3-official-1.json.1
    ...
    trace.txt
  theia/
    ta1-theia-e3-official-6r.json
    ta1-theia-e3-official-6r.json.1
    ...
    theia.txt
  cadets/
    ta1-cadets-e3-official.json
    ta1-cadets-e3-official.json.1
    ta1-cadets-e3-official-2.json
    ...
    cadets.txt
```

其中 `<dataset>.txt` 为恶意实体 ground truth 文件，例如：

```text
data/cadets/cadets.txt
data/theia/theia.txt
data/trace/trace.txt
```

运行解析脚本：

```bash
cd utils
python trace_parser.py --dataset cadets
python trace_parser.py --dataset theia
python trace_parser.py --dataset trace
cd ..
```

解析脚本会抽取实体定义、事件关系、实体名称、实体类型和恶意节点信息。根据实际数据包组织方式，若输出文件不在 `data/<dataset>/graphs/` 下，需要整理为 Option A 中的图数据结构后再训练。

### 3. Behavior-Semantic Feature Enhancement

在基础图数据准备完成后，运行行为语义特征增强脚本。该步骤会读取 `data/<dataset>/graphs/` 下的图文件，生成带入边/出边事件分布特征的新数据集。

示例：为 Cadets 数据集生成行为权重为 `0.5` 的增强版本。

```bash
python utils/add_behavior_features.py \
  --dataset cadets \
  --suffix bfeat05 \
  --behavior_weight 0.5
```

输出目录：

```text
data/cadets_bfeat05/graphs/
```

输出的 `metadata.json` 中会更新：

```json
{
  "node_feature_dim": "old_node_feature_dim + 2 * edge_feature_dim",
  "feature_enhancement": "node_type_onehot + outgoing_edge_type_hist + incoming_edge_type_hist",
  "behavior_weight": 0.5,
  "source_dataset": "cadets"
}
```

常用命令示例：

```bash
python utils/add_behavior_features.py --dataset cadets --suffix bfeat005 --behavior_weight 0.05
python utils/add_behavior_features.py --dataset cadets --suffix bfeat01  --behavior_weight 0.10
python utils/add_behavior_features.py --dataset cadets --suffix bfeat02  --behavior_weight 0.20
python utils/add_behavior_features.py --dataset cadets --suffix bfeat05  --behavior_weight 0.50

python utils/add_behavior_features.py --dataset theia --suffix bfeat005 --behavior_weight 0.05
python utils/add_behavior_features.py --dataset trace --suffix bfeat05  --behavior_weight 0.50
```

### 4. Training

训练实体级 APT 检测模型：

```bash
python train.py --dataset cadets_bfeat05 --device 0
```

如果使用 CPU：

```bash
python train.py --dataset cadets_bfeat05 --device -1
```

训练完成后，模型参数保存为：

```text
checkpoints/checkpoint-cadets_bfeat05.pt
```

其他数据集示例：

```bash
python train.py --dataset theia_bfeat005 --device 0
python train.py --dataset trace_bfeat05 --device 0
```

默认训练配置来自 `train.py` 和 `utils/config.py`：

| 参数 | 实体级数据集默认值 | 说明 |
|---|---:|---|
| `num_hidden` | 64 | GAT 隐藏维度 |
| `num_layers` | 3 | GAT 编码器层数 |
| `mask_rate` | 0.5 | 节点属性掩码比例 |
| `max_epoch` | 50 | 训练轮次 |
| `lr` | 0.001 | 学习率 |
| `weight_decay` | 5e-4 | 权重衰减 |
| `loss_fn` | `sce` | 节点属性重构损失 |
| `optimizer` | `adam` | 优化器 |

可选掩码策略：

```bash
python train.py --dataset cadets_bfeat05 --device 0 --mask_strategy random
python train.py --dataset cadets_bfeat05 --device 0 --mask_strategy degree
```

`degree` 策略会根据节点入度和出度调整掩码概率，相关参数为：

```bash
--mask_min_ratio 0.3
--mask_max_ratio 1.5
```

### 5. Training with Logs and Curves

如果需要保存训练日志和训练曲线，可以运行：

```bash
python train-log.py --dataset trace_bfeat05 --device 0
```

输出目录示例：

```text
results/trace_bfeat05_YYYYMMDD-HHMMSS/
  checkpoint-trace_bfeat05.pt
  training_log.json
  training_curve.png
```

### 6. Evaluation

评估训练好的模型：

```bash
python eval.py --dataset cadets_bfeat05 --device 0
```

CPU 环境：

```bash
python eval.py --dataset cadets_bfeat05 --device -1
```

评估脚本会输出：

- AUC
- F1
- Precision
- Recall
- Best threshold
- TN / FP / FN / TP
- Predicted anomalous node count
- Predicted anomalous node indices
- Top true anomalous nodes
- Top false positive nodes

示例输出字段：

```text
AUC: 0.9996668185273687
F1: 0.9958809352270551
PRECISION: 0.9942582247051521
RECALL: 0.9975089522030204
Best threshold: 722.7217534133132
TN: 344253
FN: 32
TP: 12814
FP: 74
Predicted anomalous node count: 12888
```

评估时会将 KNN 距离缓存到：

```text
eval_result/distance_save_<dataset>.pkl
```

如果重新训练了模型或更换了特征版本，建议删除旧缓存后再评估：

```bash
rm -f eval_result/distance_save_cadets_bfeat05.pkl
python eval.py --dataset cadets_bfeat05 --device 0
```

### 7. Quick Evaluation with Existing Checkpoints

如果 `checkpoints/` 中已经存在训练好的模型，可以直接运行：

```bash
python eval.py --dataset cadets_bfeat05 --device 0
python eval.py --dataset theia_bfeat005 --device 0
python eval.py --dataset trace_bfeat05 --device 0
```

需要确保 checkpoint 名称与数据集名称一致：

```text
checkpoints/checkpoint-cadets_bfeat05.pt
checkpoints/checkpoint-theia_bfeat005.pt
checkpoints/checkpoint-trace_bfeat05.pt
```

### 8. Hyperparameter Plot

项目提供 `draw.py` 用于生成超参数敏感性分析图：

```bash
python draw.py
```

输出文件：

```text
hyperparameter_sensitivity_analysis.png
```

如环境中没有 `scienceplots`，可以安装：

```bash
pip install SciencePlots
```

### 9. Recommended Reproduction Commands

以下命令用于复现实验中表现较好的语义特征版本：

```bash
# Cadets
python utils/add_behavior_features.py --dataset cadets --suffix bfeat05 --behavior_weight 0.5
python train.py --dataset cadets_bfeat05 --device 0
rm -f eval_result/distance_save_cadets_bfeat05.pkl
python eval.py --dataset cadets_bfeat05 --device 0

# THEIA
python utils/add_behavior_features.py --dataset theia --suffix bfeat005 --behavior_weight 0.05
python train.py --dataset theia_bfeat005 --device 0
rm -f eval_result/distance_save_theia_bfeat005.pkl
python eval.py --dataset theia_bfeat005 --device 0

# Trace
python utils/add_behavior_features.py --dataset trace --suffix bfeat05 --behavior_weight 0.5
python train.py --dataset trace_bfeat05 --device 0
rm -f eval_result/distance_save_trace_bfeat05.pkl
python eval.py --dataset trace_bfeat05 --device 0
```

## Experimental Results

在 Trace、THEIA 和 Cadets 三个 DARPA TC 子数据集上的节点级异常检测结果如下：

| 数据集 | Precision | Recall | F1 |
|---|---:|---:|---:|
| Trace | 0.982 | 0.991 | 0.986 |
| THEIA | 0.965 | 0.982 | 0.973 |
| Cadets | 0.981 | 0.989 | 0.985 |

Cadets 数据集上的模块实验结果如下：

| 方法 | AUC | F1 | FP | FN |
|---|---:|---:|---:|---:|
| 完整方法 | 0.9997 | 0.9959 | 74 | 32 |
| 去除行为语义特征 | 0.9915 | 0.8972 | 2908 | 29 |
| 去除结构重构 | 0.9998 | 0.9969 | 49 | 31 |

结果表明，行为语义特征对误报控制具有明显作用。去除行为语义特征后，误报节点数从 74 增加到 2908，说明仅依赖节点类型和图结构时，模型更容易将低频正常行为识别为异常；引入入边/出边事件分布后，模型能够更准确地区分正常实体和攻击实体。

若按误报率常用计算方式：

```text
误报率 = FP / 良性节点总数
```

Cadets 数据集中良性节点数量约为 706,961，完整方法误报节点数为 74，则：

```text
误报率 = 74 / 706,961 ≈ 0.0105%
```

该结果低于“误报率不高于 1%”的项目指标要求，可作为 APT 溯源图异常节点检测模块的低误报验证证据。

## Relationship to Project Indicators

| 合同指标 | 本项目对应内容 | 支撑说明 |
|---|---|---|
| 开发一套基于大模型的多源异构信息融合研判系统原型，并提供源代码 | APT 异常节点检测与攻击场景构建代码 | 支撑原型系统中的 APT 检测、场景构建和可视化研判模块 |
| 具备场景化特征识别能力 | 行为语义增强节点表示、溯源图构建、攻击场景构建 | 自动提取节点类型、入边事件分布、出边事件分布、因果关系、攻击上下文等关键特征 |
| 具备基线自动构建能力 | 基于语义增强特征的掩码图自编码正常行为建模 | 自动学习正常系统行为潜在表示分布，形成包含行为语义的图结构正常行为基线 |
| 基线对于异常行为识别精度不低于 80% | Trace/THEIA/Cadets 节点级检测结果 | 三个数据集 F1 均高于 97%，满足精度要求 |
| 误报率不高于 1% | Cadets 完整方法 FP=74，误报率约 0.0105% | 可支撑 APT 检测模块的低误报验证 |
| 支持流量日志、告警日志、终端日志等多源日志，总数据量不少于 4 万 | 本项目使用系统审计日志与溯源图，作为终端/主机行为侧数据支撑 | 与网络流量、系统日志等模块共同支撑多源异构日志分析 |
| 输出技术报告、论文、专利、源码 | 实验结果、模型方法、代码实现、指标统计 | 可作为结题报告、论文成果和专利材料中的 APT 检测模块依据 |
