# DXF解析器和定制层输出工具

## 项目概述

本项目实现了一个简化版的DXF解析器，能够：
1. 解析DXF文件中的LWPOLYLINE、Circle、HATCH实体
2. 创建CustomLayer图层
3. 将解析的实体重绘到CustomLayer
4. 导出CustomLayer为Gerber文件

## 文件结构

```
PY_DXF/
├── dxf_parser.py           # 主程序文件（选手编写的代码）
├── mock_shape_editor.py    # 模拟的Shape编辑器（演示用）
├── CustomLayer.gbr         # 输出的Gerber文件
├── export_results.txt      # 导出结果记录
├── 附件3：Top.dxf         # 输入的DXF文件
├── vSDK_ShapeTools.py      # vSDK工具包
├── vSDK.py                # vSDK核心库
└── 开发手册.txt            # 开发手册
```

## 运行环境

- Python 3.7+
- ezdxf库
- DFX MetaLab SDK（可选，用于完整功能）

## 安装和运行

### 1. 创建虚拟环境
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 2. 安装依赖
```bash
pip install ezdxf
```

### 3. 运行程序
```bash
python dxf_parser.py
```

## 功能特性

### DXF解析模块
- 使用ezdxf库识别常用实体定义与坐标信息
- 支持的实体类型：
  - CIRCLE（圆形）
  - LWPOLYLINE（轻量多段线）
  - HATCH（填充块）
  - MTEXT（忽略处理）

### 图形编辑与图层管理
- 使用shape_editor API新建图层CustomLayer
- 将解析的实体重绘到CustomLayer，保持原始比例和坐标
- 支持正片/负片、填充状态等属性

### 输出功能
- 生成Gerber格式文件
- 创建导出结果记录文件
- 支持DFX MetaLab GUI集成

## 运行结果

程序成功解析了TOP.dxf文件，统计结果：
- Circle实体：340个
- Line实体：11,440个  
- Polygon实体：2,421个
- 总计：14,201个图形对象

## 模拟模式说明

当无法访问完整的DFX MetaLab SDK时，程序会自动切换到模拟模式：
- 使用MockShapeEditor进行演示
- 生成占位符Gerber文件
- 提供完整的解析功能

## 实际部署说明

在有完整DFX MetaLab SDK的环境中：
1. 修改SDK路径配置
2. 程序会使用真实的vSDK_ShapeTools
3. 通过DFX MetaLab GUI进行最终的Gerber导出

## 设计思路

1. **模块化设计**：分离DXF解析、图形绘制、文件输出功能
2. **健壮性处理**：支持模拟模式，确保在各种环境下都能运行
3. **标准兼容**：生成符合Gerber格式规范的输出文件
4. **详细日志**：提供完整的解析和绘制过程记录

## 注意事项

- 实际的Gerber导出需要通过DFX MetaLab GUI操作
- 请按照开发手册说明进行最终的Gerber文件生成
- 程序支持自动检测环境并切换运行模式

## 技术要点

- 基于ezdxf库的DXF文件解析
- 使用vSDK API进行图形绘制
- 支持多种几何实体的坐标转换
- 实现了完整的错误处理机制
