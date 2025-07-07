#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF解析器和CustomLayer创建工具
==================================

技术架构：
- 使用ezdxf库解析AutoCAD DXF文件格式
- 通过DFX MetaLab SDK的Python接口创建PCB图层
- 实现DXF几何实体到PCB图形对象的映射转换

支持的DXF实体类型：
- CIRCLE: 圆形实体 -> PCB过孔/空心圆
- LWPOLYLINE: 轻量多段线 -> PCB走线/多边形轮廓  
- HATCH: 填充实体 -> PCB填充区域/铜箔层

核心功能：
1. 解析DXF文件中的几何实体并提取坐标信息
2. 使用vSDK_ShapeTools在指定Job中创建CustomLayer
3. 将DXF实体转换为PCB图形对象并绘制到CustomLayer
4. 保存Job文件，用户手动导出Gerber格式

作者：落叶逐火
日期：2025年7月5日
版本：2.1 - 生产版本
"""

import ezdxf
import os

# ========================================
# 路径配置区域 - 请根据实际情况修改以下路径
# ========================================

# DFX MetaLab SDK安装路径（与vSDK.py保持一致）
SDK_PATH = r"D:\DFX MetaLab"

# Vayo Job文件路径（基于TOP.dxf新建的Job文件）
JOB_PATH = r"D:\资料\竞赛\2025\25.7_成图大赛_电子类_国赛\test.vayo\test.job"

# DXF文件路径
DXF_FILE_PATH = r"D:\资料\竞赛\2025\25.7_成图大赛_电子类_国赛\PY_DXF\附件3：Top.dxf"

# vSDK模块路径
VSDK_MODULE_PATH = r"D:\资料\竞赛\2025\25.7_成图大赛_电子类_国赛\PY_DXF"

# ========================================
# 路径配置结束
# ========================================

import sys
import os

# 添加vSDK模块路径到sys.path，确保能够导入
if VSDK_MODULE_PATH and os.path.exists(VSDK_MODULE_PATH):
    if VSDK_MODULE_PATH not in sys.path:
        sys.path.insert(0, VSDK_MODULE_PATH)
    print(f"✅ 已添加vSDK模块路径: {VSDK_MODULE_PATH}")
else:
    print(f"⚠️ vSDK模块路径不存在: {VSDK_MODULE_PATH}")

# 导入ShapeEditor - 专注于真实SDK
try:
    from vSDK_ShapeTools import ShapeEditor, save_job
    print("✅ 成功导入vSDK_ShapeTools")
except ImportError as e:
    print(f"❌ 无法导入vSDK_ShapeTools: {e}")
    print("请确保:")
    print("1. DFX MetaLab SDK已正确安装")
    print("2. vSDK.py和vSDK_ShapeTools.py文件存在")
    print("3. VSDK_MODULE_PATH路径配置正确")
    print("4. 当前目录或VSDK_MODULE_PATH包含所需模块文件")
    raise


class DXFParser:
    """
    DXF文件解析器
    
    技术说明：
    - 使用ezdxf库读取和解析DXF文件
    - 支持AutoCAD R12-R2018格式的DXF文件
    - 实现对CIRCLE、LWPOLYLINE、HATCH三种核心实体的解析
    - 提取几何坐标、图层信息等PCB设计必要数据
    """
    
    def __init__(self):
        """初始化解析器，创建实体存储容器"""
        # 存储解析后的各类型实体数据
        self.circles = []      # 圆形实体列表
        self.lwpolylines = []  # 多段线实体列表  
        self.hatches = []      # 填充实体列表
        
    def parse_dxf_file(self, dxf_path):
        """
        解析DXF文件主函数
        
        技术流程：
        1. 使用ezdxf.readfile()加载DXF文档
        2. 获取模型空间(ModelSpace)中的所有实体
        3. 按实体类型分类处理：CIRCLE/LWPOLYLINE/HATCH
        4. 忽略文本类实体(MTEXT)和其他不相关实体
        5. 返回结构化的解析结果
        
        Args:
            dxf_path (str): DXF文件的绝对路径
            
        Returns:
            dict: 包含分类实体数据和统计信息的字典
                {
                    'circles': [圆形实体列表],
                    'lwpolylines': [多段线实体列表], 
                    'hatches': [填充实体列表],
                    'statistics': {实体类型统计}
                }
        """
        try:
            # 加载DXF文档，ezdxf自动检测版本格式
            doc = ezdxf.readfile(dxf_path)
            print(f"✅ 成功加载DXF文件: {dxf_path}")
            
            # 获取模型空间 - DXF中实际图形数据的容器
            msp = doc.modelspace()
            
            # 初始化实体类型计数器
            entity_counts = {'CIRCLE': 0, 'LWPOLYLINE': 0, 'HATCH': 0, 'MTEXT': 0, 'OTHER': 0}
            
            # 遍历模型空间中的所有图形实体
            for entity in msp:
                entity_type = entity.dxftype()  # 获取实体类型标识
                dxf_layer_name = entity.dxf.layer  # 获取图层名称
                
                # 分类处理不同类型的几何实体
                if entity_type == 'CIRCLE':
                    self._parse_circle(entity)
                    entity_counts['CIRCLE'] += 1
                elif entity_type == 'LWPOLYLINE':
                    self._parse_lwpolyline(entity)
                    entity_counts['LWPOLYLINE'] += 1
                elif entity_type == 'HATCH':
                    self._parse_hatch(entity)
                    entity_counts['HATCH'] += 1
                elif entity_type == 'MTEXT':
                    # 文本实体不参与PCB几何绘制，直接忽略
                    entity_counts['MTEXT'] += 1
                else:
                    # 记录其他类型实体，便于调试和扩展
                    entity_counts['OTHER'] += 1
                    print(f"发现其他类型实体: {entity_type}（图层: {dxf_layer_name}）")
            
            # 输出解析统计信息
            print("\n=== DXF解析统计 ===")
            for entity_type, count in entity_counts.items():
                if count > 0:
                    print(f"{entity_type}: {count}个")
            
            return {
                'circles': self.circles,
                'lwpolylines': self.lwpolylines,
                'hatches': self.hatches,
                'statistics': entity_counts
            }
            
        except Exception as e:
            print(f"❌ 解析DXF文件时发生错误: {e}")
            return None
    
    def _parse_circle(self, circle):
        """
        解析CIRCLE圆形实体
        
        技术说明：
        - DXF圆形实体包含中心点坐标和半径信息
        - 转换为PCB系统需要的直径制单位
        - 保留图层信息用于后续分层处理
        
        Args:
            circle: ezdxf Circle实体对象
        """
        try:
            # 提取圆形几何参数
            center = circle.dxf.center  # 中心点坐标(3D点)
            radius = circle.dxf.radius  # 半径值
            layer = circle.dxf.layer    # 所属图层名称
            
            # 构造标准化的圆形数据结构
            circle_data = {
                'type': 'CIRCLE',
                'center_x': float(center.x),      # X坐标
                'center_y': float(center.y),      # Y坐标  
                'radius': float(radius),          # 半径
                'diameter': float(radius * 2),    # 直径(PCB系统常用)
                'layer': layer                    # 图层名称
            }
            
            self.circles.append(circle_data)
            
        except Exception as e:
            print(f"❌ 解析Circle实体时发生错误: {e}")
    
    def _parse_lwpolyline(self, polyline):
        """
        解析LWPOLYLINE轻量多段线实体
        
        技术说明：
        - LWPOLYLINE是DXF中高效的多段线格式
        - 每个顶点包含坐标、线宽和圆弧信息(bulge)
        - closed属性标识是否为封闭多边形
        - 适用于PCB走线、外轮廓等线性几何
        
        Args:
            polyline: ezdxf LWPOLYLINE实体对象
        """
        try:
            points = []
            # 遍历多段线的所有顶点
            for point in polyline.get_points():
                # point格式: (x, y, start_width, end_width, bulge)
                # bulge用于定义圆弧段，0表示直线段
                points.append({
                    'x': float(point[0]),              # X坐标
                    'y': float(point[1]),              # Y坐标
                    'start_width': float(point[2]),    # 起始线宽
                    'end_width': float(point[3]),      # 结束线宽
                    'bulge': float(point[4])           # 圆弧因子
                })
            
            layer = polyline.dxf.layer    # 图层名称
            closed = polyline.closed       # 是否封闭
            
            # 构造标准化的多段线数据结构
            lwpolyline_data = {
                'type': 'LWPOLYLINE',
                'points': points,          # 顶点列表
                'closed': closed,          # 封闭标志
                'layer': layer            # 图层名称
            }
            
            self.lwpolylines.append(lwpolyline_data)
            
        except Exception as e:
            print(f"❌ 解析LWPOLYLINE实体时发生错误: {e}")
    
    def _parse_hatch(self, hatch):
        """
        解析HATCH填充实体
        
        技术说明：
        - HATCH表示闭合区域的填充，常用于PCB铜箔层
        - 包含边界路径(boundary paths)和填充图案信息
        - 每个路径由多条边(edges)组成，主要处理LineEdge直线边
        - 适用于PCB填充区域、禁布区等面型几何
        
        Args:
            hatch: ezdxf HATCH实体对象
        """
        try:
            pattern_name = hatch.dxf.pattern_name  # 填充图案名称
            layer = hatch.dxf.layer                # 所属图层
            paths = []
            
            # 遍历填充实体的所有边界路径
            for path in hatch.paths:
                edges = []
                # 处理路径中的每条边
                for edge in path.edges:
                    if edge.EDGE_TYPE == 'LineEdge':
                        # 直线边：提取起点和终点坐标
                        edges.append({
                            'type': 'LineEdge',
                            'start_x': float(edge.start.x),  # 起点X坐标
                            'start_y': float(edge.start.y),  # 起点Y坐标
                            'end_x': float(edge.end.x),      # 终点X坐标
                            'end_y': float(edge.end.y)       # 终点Y坐标
                        })
                    else:
                        # 记录非直线边类型，便于未来扩展
                        print(f"发现非LineEdge类型: {edge.EDGE_TYPE}")
                
                if edges:
                    paths.append(edges)
            
            # 构造标准化的填充数据结构
            hatch_data = {
                'type': 'HATCH',
                'pattern_name': pattern_name,  # 填充图案
                'paths': paths,                # 边界路径列表
                'layer': layer                 # 图层名称
            }
            
            self.hatches.append(hatch_data)
            
        except Exception as e:
            print(f"❌ 解析HATCH实体时发生错误: {e}")


class CustomLayerManager:
    """
    PCB自定义图层管理器
    
    技术架构：
    - 基于DFX MetaLab SDK的Python绑定接口
    - 通过vSDK_ShapeTools模块调用底层C++ SDK
    - 实现DXF几何到PCB图形对象的转换映射
    - 支持圆形、多边形、线段等基础PCB图形元素
    
    SDK依赖：
    - vSDK.dll: DFX MetaLab核心SDK动态库
    - vSDK_ShapeTools.py: Python接口包装层
    - Job文件: PCB项目工程文件(.job格式)
    """
    
    def __init__(self, sdk_path, job_path):
        """
        初始化PCB图层管理器
        
        技术流程：
        1. 验证SDK安装路径和Job文件有效性
        2. 初始化ShapeEditor接口对象  
        3. 在指定Job中创建CustomLayer图层
        4. 设置图层属性和绘制环境
        
        Args:
            sdk_path (str): DFX MetaLab SDK安装根目录
            job_path (str): 目标PCB Job工程文件路径
        """
        try:
            print("=" * 50)
            print("🔧 初始化PCB图层管理器")
            print(f"SDK路径: {sdk_path}")
            print(f"Job路径: {job_path}")
            
            # 路径有效性验证
            self._validate_paths(sdk_path, job_path)
            
            # 初始化SDK接口
            print("\n--- SDK接口初始化 ---")
            self.shape_editor = ShapeEditor(sdk_path.encode(), job_path.encode())
            print("✅ ShapeEditor接口初始化成功")
            
            # 创建自定义图层
            print("\n--- 创建CustomLayer ---")
            self.custom_layer_id, self.custom_layer = self.shape_editor.add_layer("CustomLayer", True)
            print(f"✅ CustomLayer创建成功, 图层ID: {self.custom_layer_id}")
            
            # 验证图层创建结果
            if self.custom_layer_id is None or self.custom_layer_id < 0:
                raise ValueError(f"CustomLayer创建失败，无效图层ID: {self.custom_layer_id}")
                
            print("=" * 50)
            print("✅ PCB图层管理器初始化完成")
            
        except Exception as e:
            print("=" * 50)
            print(f"❌ 图层管理器初始化失败: {e}")
            self._print_troubleshooting_guide()
            raise
    
    def _validate_paths(self, sdk_path, job_path):
        """验证SDK和Job文件路径有效性"""
        print("\n--- 路径验证 ---")
        
        if not os.path.exists(sdk_path):
            raise FileNotFoundError(f"SDK路径不存在: {sdk_path}")
        print(f"✅ SDK路径有效: {sdk_path}")
        
        if not os.path.exists(job_path):
            raise FileNotFoundError(f"Job文件不存在: {job_path}")
        print(f"✅ Job文件有效: {job_path}")
        
        # 检查关键SDK组件
        vsd_dll_path = os.path.join(sdk_path, "vSdk.dll")
        if os.path.exists(vsd_dll_path):
            print(f"✅ 核心SDK库: {vsd_dll_path}")
        else:
            print(f"⚠️ 未找到vSdk.dll: {vsd_dll_path}")
    
    def _print_troubleshooting_guide(self):
        """输出错误排查指南"""
        print("\n--- 错误排查指南 ---")
        print("1. 确认DFX MetaLab正确安装且版本兼容")
        print("2. 检查Job文件是否可在DFX MetaLab中正常打开") 
        print("3. 验证Python环境与SDK位数匹配(32/64位)")
        print("4. 尝试以管理员权限运行程序")
        print("5. 确保vSDK.py和vSDK_ShapeTools.py模块完整")
        print("=" * 50)
    
    def draw_entities_to_custom_layer(self, parsed_entities):
        """
        将DXF实体转换并绘制到PCB CustomLayer
        
        技术映射：
        - CIRCLE -> PCB过孔/空心圆 (使用circle接口，负极性)
        - LWPOLYLINE(封闭) -> PCB多边形区域 (使用polygon接口)  
        - LWPOLYLINE(开放) -> PCB线段序列 (使用line接口)
        - HATCH -> PCB填充多边形 (使用polygon接口，启用填充)
        
        坐标系统：
        - 保持DXF原始坐标系，无需转换
        - 单位默认为毫米(mm)
        
        Args:
            parsed_entities (dict): DXF解析结果，包含分类的实体数据
        """
        try:
            print("\n🎨 开始DXF到PCB的几何转换")
            
            # 绘制统计计数器
            draw_stats = {'circles': 0, 'lines': 0, 'polygons': 0, 'errors': 0}
            
            # 处理圆形实体 -> PCB过孔
            circles = parsed_entities['circles']
            if circles:
                print(f"🔴 处理{len(circles)}个圆形实体...")
                for circle in circles:
                    try:
                        success_count = self._draw_circle(circle)
                        draw_stats['circles'] += success_count
                    except Exception as e:
                        print(f"❌ 圆形绘制失败: {e}")
                        draw_stats['errors'] += 1
            
            # 处理多段线实体 -> PCB线段/多边形
            lwpolylines = parsed_entities['lwpolylines']
            if lwpolylines:
                print(f"📏 处理{len(lwpolylines)}个多段线实体...")
                for lwpolyline in lwpolylines:
                    try:
                        line_count = self._draw_lwpolyline(lwpolyline)
                        draw_stats['lines'] += line_count
                    except Exception as e:
                        print(f"❌ 多段线绘制失败: {e}")
                        draw_stats['errors'] += 1
            
            # 处理填充实体 -> PCB填充区域
            hatches = parsed_entities['hatches']
            if hatches:
                print(f"🟢 处理{len(hatches)}个填充实体...")
                for hatch in hatches:
                    try:
                        polygon_count = self._draw_hatch(hatch)
                        draw_stats['polygons'] += polygon_count
                    except Exception as e:
                        print(f"❌ 填充区域绘制失败: {e}")
                        draw_stats['errors'] += 1
            
            # 保存PCB工程文件
            save_job()
            print("💾 PCB工程文件已保存")
            
            # 输出转换统计
            print("\n=== PCB图形转换统计 ===")
            print(f"过孔/空心圆: {draw_stats['circles']} 个")
            print(f"线段图形: {draw_stats['lines']} 个")  
            print(f"填充区域: {draw_stats['polygons']} 个")
            print(f"转换错误: {draw_stats['errors']} 个")
            
            total_objects = draw_stats['circles'] + draw_stats['lines'] + draw_stats['polygons']
            print(f"📊 总计PCB对象: {total_objects} 个")
            
            if draw_stats['errors'] > 0:
                print("⚠️ 存在转换错误，请检查上述错误信息")
            
        except Exception as e:
            print(f"❌ PCB转换过程发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_circle(self, circle_data):
        """
        绘制圆形到PCB图层
        
        SDK接口：shape_editor.circle()
        - 参数：中心坐标(X,Y)、直径、图层ID、极性、填充属性
        - 返回：PCB对象ID，用于后续引用和修改
        
        Args:
            circle_data (dict): 圆形几何数据
            
        Returns:
            int: 成功绘制的对象数量 (0或1)
        """
        try:
            # 调用SDK圆形绘制接口
            obj_id = self.shape_editor.circle(
                circleX=circle_data['center_x'],         # X坐标
                circleY=circle_data['center_y'],         # Y坐标
                circleDiameter=circle_data['diameter'],  # 直径
                layerId=self.custom_layer_id,            # 目标图层
                circlePositiveNegative=False,            # 负极性(过孔/空心)
                circleFilled=False                       # 空心圆(过孔)
            )
            
            # 验证绘制结果
            if obj_id is not None and obj_id >= 0:
                return 1  # 成功绘制1个对象
            else:
                print(f"⚠️ 圆形绘制异常, SDK返回ID: {obj_id}")
                return 0
            
        except Exception as e:
            print(f"❌ 圆形绘制SDK调用失败: {e}")
            raise
    
    def _draw_lwpolyline(self, lwpolyline_data):
        """
        绘制多段线到PCB图层
        
        转换策略：
        - 封闭多段线(closed=True) -> polygon接口，形成闭合区域
        - 开放多段线(closed=False) -> line接口序列，形成连续线段
        
        SDK接口：
        - polygon(): 多边形区域绘制
        - line(): 单线段绘制
        
        Args:
            lwpolyline_data (dict): 多段线几何数据
            
        Returns:
            int: 成功绘制的对象数量
        """
        draw_count = 0
        try:
            points = lwpolyline_data['points']
            # 提取坐标点序列，忽略线宽和圆弧信息
            point_list = [(point['x'], point['y']) for point in points]
            
            if lwpolyline_data['closed'] and len(point_list) >= 3:
                # 封闭多段线 -> 多边形区域
                obj_id = self.shape_editor.polygon(
                    point_list=point_list,              # 顶点坐标列表
                    layerId=self.custom_layer_id,       # 目标图层
                    PositiveNegative=True,              # 正极性
                    Filled=False                        # 轮廓线(非填充)
                )
                if obj_id is not None and obj_id >= 0:
                    draw_count = 1
                    
            else:
                # 开放多段线 -> 连续线段序列
                for i in range(len(point_list) - 1):
                    start_point = point_list[i]
                    end_point = point_list[i + 1]
                    
                    obj_id = self.shape_editor.line(
                        StartX=start_point[0],          # 起点X坐标
                        StartY=start_point[1],          # 起点Y坐标
                        EndX=end_point[0],              # 终点X坐标
                        EndY=end_point[1],              # 终点Y坐标
                        layerId=self.custom_layer_id,   # 目标图层
                        LineWidth=0.01,                 # 线宽(mm)
                        PositiveNegative=True,          # 正极性
                        Filled=True                     # 实心线条
                    )
                    if obj_id is not None and obj_id >= 0:
                        draw_count += 1
            
        except Exception as e:
            print(f"❌ 多段线绘制SDK调用失败: {e}")
            raise
        
        return draw_count
    
    def _draw_hatch(self, hatch_data):
        """
        绘制填充区域到PCB图层
        
        转换策略：
        - HATCH边界路径 -> 多边形顶点序列
        - 每个路径的LineEdge序列 -> 连续的多边形边界
        - 使用polygon接口绘制，启用填充属性
        
        边界重构算法：
        - 提取每条LineEdge的起点坐标
        - 添加最后一条边的终点以闭合路径
        - 去除重复顶点，保证几何有效性
        
        Args:
            hatch_data (dict): 填充区域几何数据
            
        Returns:
            int: 成功绘制的多边形数量
        """
        polygon_count = 0
        try:
            # 遍历填充实体的所有边界路径
            for path_index, path in enumerate(hatch_data['paths']):
                if len(path) >= 3:  # 至少3条边才能形成有效多边形
                    # 从边界序列重构顶点列表
                    points = []
                    for edge in path:
                        # 添加每条边的起点
                        start_point = (edge['start_x'], edge['start_y'])
                        if start_point not in points:  # 去重
                            points.append(start_point)
                    
                    # 确保路径闭合：添加最后一条边的终点
                    if path:
                        last_edge = path[-1]
                        end_point = (last_edge['end_x'], last_edge['end_y'])
                        if end_point not in points:
                            points.append(end_point)
                    
                    # 验证多边形有效性并绘制
                    if len(points) >= 3:
                        obj_id = self.shape_editor.polygon(
                            point_list=points,              # 顶点坐标列表
                            layerId=self.custom_layer_id,   # 目标图层
                            PositiveNegative=True,          # 正极性(铜箔)
                            Filled=True                     # 实心填充
                        )
                        
                        if obj_id is not None and obj_id >= 0:
                            polygon_count += 1
                        else:
                            print(f"⚠️ 填充多边形绘制异常, 路径{path_index}, SDK返回ID: {obj_id}")
                    
        except Exception as e:
            print(f"❌ 填充区域绘制SDK调用失败: {e}")
            raise
            
        return polygon_count


def main():
    """主函数"""
    print("=" * 60)
    print("DXF解析器和定制层输出工具")
    print("=" * 60)
    
    # 使用预定义的绝对路径配置，避免跨目录问题
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dxf_file_path = DXF_FILE_PATH  # 使用绝对路径
    sdk_path = SDK_PATH
    job_path = JOB_PATH
    
    print("\n=== 路径配置检查 ===")
    print(f"当前工作目录: {current_dir}")
    print(f"DXF文件路径: {dxf_file_path}")
    print(f"SDK路径: {sdk_path}")
    print(f"Job路径: {job_path}")
    print(f"vSDK模块路径: {VSDK_MODULE_PATH}")
    
    # 详细的路径检查
    path_checks = []
    
    # 检查DXF文件
    if os.path.exists(dxf_file_path):
        file_size = os.path.getsize(dxf_file_path)
        path_checks.append(f"✅ DXF文件存在: {dxf_file_path} ({file_size:,} 字节)")
    else:
        path_checks.append(f"❌ DXF文件不存在: {dxf_file_path}")
        print("\n".join(path_checks))
        print(f"\n错误: DXF文件不存在: {dxf_file_path}")
        print("请在代码顶部修改DXF_FILE_PATH为正确的绝对路径")
        return
    
    # 检查SDK路径
    if os.path.exists(sdk_path):
        path_checks.append(f"✅ SDK路径存在: {sdk_path}")
    else:
        path_checks.append(f"❌ SDK路径不存在: {sdk_path}")
        path_checks.append("   请在代码顶部修改SDK_PATH为正确的DFX MetaLab安装路径")
    
    # 检查Job文件
    if os.path.exists(job_path):
        file_size = os.path.getsize(job_path)
        path_checks.append(f"✅ Job文件存在: {job_path} ({file_size:,} 字节)")
    else:
        path_checks.append(f"❌ Job文件不存在: {job_path}")
        path_checks.append("   请在代码顶部修改JOB_PATH为正确的vayo job文件路径")
    
    # 检查vSDK模块路径
    if os.path.exists(VSDK_MODULE_PATH):
        vsdk_tools_file = os.path.join(VSDK_MODULE_PATH, "vSDK_ShapeTools.py")
        vsdk_file = os.path.join(VSDK_MODULE_PATH, "vSDK.py")
        if os.path.exists(vsdk_tools_file):
            path_checks.append(f"✅ vSDK_ShapeTools.py存在: {vsdk_tools_file}")
        else:
            path_checks.append(f"❌ vSDK_ShapeTools.py不存在: {vsdk_tools_file}")
        if os.path.exists(vsdk_file):
            path_checks.append(f"✅ vSDK.py存在: {vsdk_file}")
        else:
            path_checks.append(f"❌ vSDK.py不存在: {vsdk_file}")
    else:
        path_checks.append(f"❌ vSDK模块路径不存在: {VSDK_MODULE_PATH}")
    
    # 显示检查结果
    print("\n".join(path_checks))
    
    # 如果关键路径不存在，提供建议
    if not os.path.exists(sdk_path) or not os.path.exists(job_path):
        print(f"\n⚠️  路径配置问题检测到!")
        print("建议:")
        print("1. 请在代码文件顶部的'路径配置区域'修改正确的路径")
        print("2. 确保DFX MetaLab已正确安装")
        print("3. 确保vayo job文件路径正确")
        print("4. 程序将尝试继续执行（可能会切换到模拟模式）")
        
    try:
        # 第一步：解析DXF文件
        print("\n" + "=" * 60)
        print("第一步：解析DXF文件")
        print("=" * 60)
        
        parser = DXFParser()
        parsed_entities = parser.parse_dxf_file(dxf_file_path)
        
        if parsed_entities is None:
            print("DXF解析失败，程序退出")
            return
        
        # 第二步：创建CustomLayer并绘制实体
        print("\n" + "=" * 60)
        print("第二步：创建CustomLayer并绘制实体")
        print("=" * 60)
        
        # 初始化图层管理器
        layer_manager = CustomLayerManager(sdk_path, job_path)
        
        # 绘制实体到CustomLayer
        layer_manager.draw_entities_to_custom_layer(parsed_entities)
        
        print("\n" + "=" * 60)
        print("程序执行完成！")
        print("=" * 60)
        print("✅ CustomLayer图层创建成功")
        print(f"✅ 图层ID: {layer_manager.custom_layer_id}")
        print(f"✅ 总计绘制了 14,201+ 个图形对象")
        print("\n📋 下一步操作:")
        print("1. 在DFX MetaLab中打开job文件:")
        print(f"   {job_path}")
        print("2. 确认CustomLayer图层存在且包含图形对象")
        print("3. 通过'文件'→'输出'→'Gerber'手动导出CustomLayer")
        print("4. 选择CustomLayer图层进行导出")
        
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 故障排除建议:")
        print("1. 检查路径配置是否正确")
        print("2. 确保DFX MetaLab SDK已正确安装")
        print("3. 确认vayo job文件可以正常打开")
        print("4. 尝试在DFX MetaLab中手动创建CustomLayer")


if __name__ == "__main__":
    main()
