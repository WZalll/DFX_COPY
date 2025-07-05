# DXF to PCB Layer Converter

🎯 **DXF解析器和CustomLayer创建工具**

## 📋 项目概述

本项目实现了一个专业的DXF解析器，能够将AutoCAD DXF文件转换为PCB图层：

- ✅ 解析DXF文件中的 **CIRCLE**、**LWPOLYLINE**、**HATCH** 实体
- ✅ 使用DFX MetaLab SDK创建 **CustomLayer** 图层  
- ✅ 将DXF几何实体转换为PCB图形对象
- ✅ 支持手动导出Gerber格式文件

## 🚀 核心特性

### DXF解析模块
- 🔵 **CIRCLE**：圆形实体 → PCB圆形焊盘/过孔
- 📏 **LWPOLYLINE**：轻量多段线 → PCB走线/多边形轮廓  
- 🟢 **HATCH**：填充实体 → PCB填充区域/铜箔层

### 技术架构
- 📚 使用 `ezdxf` 库解析AutoCAD DXF文件格式
- 🔌 通过DFX MetaLab SDK的Python接口创建PCB图层
- 🎨 实现DXF几何实体到PCB图形对象的映射转换

## 📁 文件结构

```
📦 DFX_COPY/
├── 🐍 dxf_parser.py           # 主程序（核心文件）
├── 🔧 vSDK.py                # DFX MetaLab SDK核心接口
├── 🛠️ vSDK_ShapeTools.py      # SDK图形工具模块
├── 📋 requirements.txt        # Python依赖
├── 🚫 .gitignore             # Git忽略文件
└── 📖 README.md              # 项目说明
```

## ⚡ 快速开始

### 1. 环境准备
```bash
# 克隆仓库
git clone https://github.com/WZalll/DFX_COPY.git
cd DFX_COPY

# 创建虚拟环境
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac  
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置路径
编辑 `dxf_parser.py` 顶部的路径配置：
```python
# DFX MetaLab SDK安装路径
SDK_PATH = r"D:\DFX MetaLab"

# Vayo Job文件路径
JOB_PATH = r"your_job_file.job"

# DXF文件名
DXF_FILENAME = "your_dxf_file.dxf"
```

### 3. 运行程序
```bash
python dxf_parser.py
```

## 📊 运行结果示例

```
✅ 成功加载DXF文件: Top.dxf
=== DXF解析统计 ===
CIRCLE: 340个
LWPOLYLINE: 2,869个  
HATCH: 2,421个

=== PCB图形转换统计 ===
圆形焊盘: 340 个
线段图形: 11,440 个
填充区域: 2,421 个
📊 总计PCB对象: 14,201 个
```

## 🔧 技术要点

- **模块化设计**：分离DXF解析、图形绘制、文件输出功能
- **SDK集成**：基于DFX MetaLab SDK进行PCB图层操作
- **几何转换**：精确的DXF到PCB坐标系统转换
- **错误处理**：完整的异常处理和日志记录机制

## 📝 使用说明

1. **准备工作**：确保DFX MetaLab SDK已正确安装
2. **路径配置**：修改代码中的SDK路径和Job文件路径
3. **运行解析**：执行程序自动解析DXF并创建CustomLayer
4. **手动导出**：在DFX MetaLab中打开Job文件，手动导出Gerber

## 🎯 应用场景

- 🏭 **PCB设计**：将CAD设计转换为PCB制造文件
- 🔄 **格式转换**：DXF到Gerber的标准化转换流程
- 🎓 **教学演示**：CAD/PCB设计课程的实践项目
- 🏆 **竞赛项目**：电子设计竞赛的辅助工具

## 📄 许可证

本项目仅供学习和研究使用。

## 👨‍💻 作者

**落叶逐火**  
📅 创建日期：2025年7月5日  
🚀 版本：2.0 - 生产版本

---

⭐ 如果这个项目对你有帮助，请给个Star！
